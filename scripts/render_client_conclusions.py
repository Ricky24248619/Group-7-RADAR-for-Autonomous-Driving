"""Write plain-language conclusions with traceable measurements and limits."""
import csv
import json
from pathlib import Path

from analyse_sprint_followup import hash_repository_text

ROOT = Path(__file__).resolve().parents[1]
BASE = "results/evidence/sprint-followup-oct01/"
OUT = ROOT / BASE


def load(name):
    with (OUT / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def row(table, **keys):
    selected = [value for value in table if all(value[key] == str(expected) for key, expected in keys.items())]
    if len(selected) != 1:
        raise ValueError("Expected one evidence row: " + str(keys))
    return selected[0]


def percent(value):
    return f"{float(value):.2f}%"


def main():
    classes = load("class_range_support.csv")
    terrain = load("terrain/pooled_class_comparison.csv")
    frames = load("terrain/frame_comparison.csv")
    weather = load("weather_support.csv")
    distant = row(load("truckdrive_holdout_support.csv"), variant="aligned", margin_m="0", cohort="vehicles", band_m="200-400")
    conclusions = []
    def add(number, theme, headline, evidence, implication, limitation, sources, origin="New analysis or inference"):
        conclusions.append(dict(id=f"C{number:02}", theme=theme, headline=headline, evidence=evidence,
                                implication=implication, limitation=limitation, sources=sources, origin=origin,
                                status="Supported within stated scope"))
    def file(name):
        return BASE + name
    add(1,"Distance and object types", "LiDAR gave more complete distant-vehicle coverage in the systems we tested.",
        f"The new TruckDrive clips have {distant['observations']} vehicle observations at 200–400 m across {distant['tracks']} tracks: LiDAR {percent(distant['lidar_percent'])}, radar {percent(distant['radar_percent'])}. LiDAR leads in both clips, including static/expanded-box sensitivities; the earlier five-clip cohort showed the same pooled ordering.",
        "Use LiDAR as the stronger distant-vehicle geometry reference for these configurations.",
        "Two new clips, 12 timing-eligible frames; observations repeat tracks. LiDAR-conditioned annotations and acquisition-alignment hypothesis. Coverage is an in-box return, not recognition accuracy or a universal hardware ranking.",
        [file("truckdrive_holdout_support.csv"),"docs/truckdrive-multiscene-result.md"])
    for number, category, title, implication in (
        (2,"vehicle.truck","Radar coverage of nearby trucks was almost as complete as LiDAR coverage.","Radar is a credible complementary source for large nearby truck targets in this sample."),
        (3,"human.pedestrian.adult","LiDAR covered nearby adult pedestrians more consistently than radar.","Evaluate pedestrian coverage separately from large-vehicle averages."),
        (4,"vehicle.bicycle","LiDAR covered nearby bicycles more consistently than radar.","Keep cyclists as a separate evaluation group; strong truck results do not establish cyclist coverage."),
        (5,"movable_object.trafficcone","LiDAR covered nearby traffic cones much more consistently than radar.","Include small roadwork obstacles when evaluating perception coverage."),
        (6,"static_object.traffic_sign","LiDAR covered nearby road signs much more consistently than radar.","Assess signs separately; these returns alone do not establish reading or understanding a sign.")):
        value = row(classes, category=category, band_m="0-25")
        add(number,"Distance and object types",title,
            f"At 0–25 m in TruckScenes, LiDAR support is {percent(value['lidar_percent'])} and radar support {percent(value['radar_percent'])}, across {value['observations']} observations, {value['tracks']} tracks and {value['scenes']} scenes. Equal-track support is {percent(value['equal_track_lidar_percent'])} and {percent(value['equal_track_radar_percent'])} respectively.",
            implication,"All six sensors per modality; exact boxes and pointwise ego correction. Repeated observations and LiDAR-conditioned labels. Class/viewpoint/occlusion differences remain; not detector recall or an isolated material/reflectivity effect.",
            [file("class_range_support.csv")], "Expanded class/track reanalysis of existing paired scans")
    add(7,"Distance and object types","Radar coverage of the same car tracks was less consistent at greater distances.",
        "For 237 matched car tracks in TruckScenes, equal-track radar coverage falls from 79.95% at 0–50 m to 52.46% at 50–100 m; LiDAR changes from 99.81% to 98.55%.",
        "Choose operating-range checks using the same targets across distances.",
        "Recorded tracks, not independent trials; changing view, occlusion and motion remain. This is a range association, not a controlled distance-only effect.",
        ["docs/evidence/missing-support/matched_track_summary.csv"],"Consolidated earlier matched-track evidence")
    add(8,"Sensor combination and weather","Radar sometimes adds object evidence where LiDAR has none.",
        f"In the new distant vehicle sample, one radar-only observation raises geometric union from {percent(distant['lidar_percent'])} to {percent(distant['union_percent'])}. The earlier distant cohort had 25 radar-only observations. Radar-only cases remain sensitive to alignment and box definitions.",
        "Inspect these cases and test fusion before discarding radar based on its average coverage.",
        "Union of sensor support, not added true detector positives. Labels cannot reveal unannotated radar-only objects; repeated observations are not new independently recovered vehicles.",
        [file("truckdrive_holdout_support.csv"),"docs/truckdrive-multiscene-result.md"])
    add(9,"Sensor combination and weather","Our fog sample suggests radar can provide evidence when LiDAR is sparse.",
        "At 50–75 m in RADIATE, 9/19 vehicle observations pass a strict local radar-contrast test; 0/19 exact footprints have above-ground LiDAR returns. Expanding footprints and allowing adjacent scans raises LiDAR support to 2/19.",
        "Prioritise a matched fog/clear-weather recognition test to assess radar backup.",
        "Tiny radar-annotated fog pilot, four tracks overall, no clear-weather control. Contrast and point presence are different measurements; fog causality and detector superiority are unproven.",
        ["docs/radiate-fog-pilot.md","docs/evidence/radiate-fog/observations.csv"],"Consolidated earlier weather pilot")
    rain = row(weather, weather="rain", category="vehicle.car", band_m="50-100")
    snow = row(weather, weather="snow", category="vehicle.car", band_m="50-100")
    add(10,"Sensor combination and weather","LiDAR retained strong car coverage in the sampled rain and snow recordings.",
        f"At 50–100 m, rain car observations have LiDAR {percent(rain['lidar_percent'])} and radar {percent(rain['radar_percent'])} ({rain['observations']} observations, {rain['tracks']} tracks); snow has LiDAR {percent(snow['lidar_percent'])} and radar {percent(snow['radar_percent'])} ({snow['observations']} observations, {snow['tracks']} tracks). Each band uses one recording per weather condition.",
        "Evaluate particular hardware and conditions before assuming radar will always have better adverse-weather object coverage.",
        "Descriptive results from different scenes with different targets and LiDAR-conditioned labels. No causal rain/snow penalty, controlled weather comparison or all-weather superiority measured.",
        [file("weather_support.csv")])
    add(11,"Terrain understanding","The terrain model can mistake low rock surfaces for ground.",
        "In the earlier difficult-frame diagnosis, 84.52% of 394 rock points near labelled-ground elevation are called ground, versus 23.46% of 260 higher points. Changing context reduces ground confusion in the three-frame tuning cohort, but correct rock classification reaches only 24.90%.",
        "Retain low protruding rocks as explicit failure cases in off-road evaluation.",
        "Nearest-ground height proxy and selected correlated cases; association does not isolate geometry or snow. The new seven-frame cohort has no rock points and does not validate rock generalisation.",
        ["docs/goose-failure-causes.md","docs/evidence/goose-failure-causes/nearest_ground_diagnostic.csv"],"Consolidated earlier case-level evidence")
    def fine(category, variant="p128"):
        return row(terrain,category=category,variant=variant,band_m="0+")
    grass = fine("high_grass")
    add(12,"Terrain understanding","Tall grass is a recurring ground-versus-vegetation weakness in the new terrain sample.",
        f"Across all seven selected recordings, {grass['called_ground_points']}/{grass['points']} high-grass points ({percent(grass['called_ground_percent'])}) are called ground at patch 128; correct vegetation classification is {percent(grass['correct_percent'])}. Patch 64 calls 52.06% ground.",
        "Treat a ground prediction on tall vegetation as a failure mode to inspect, rather than evidence of a clear route.",
        "Returned-point semantic labels; one selected frame per recording. No height measurement, physical traversability or obstacle detection scored. Correct class is vegetation under the challenge taxonomy.",
        [file("terrain/pooled_class_comparison.csv")])
    poles_a, poles_b = fine("pole","p64"), fine("pole")
    add(13,"Terrain understanding","More context improved the model's classification of poles in the new sample.",
        f"On the same {poles_a['points']} pole points from {poles_a['recordings']} recordings, correct obstacle-category labels rise from {percent(poles_a['correct_percent'])} at patch 64 to {percent(poles_b['correct_percent'])} at patch 128.",
        "Include thin structures when checking a candidate model configuration.",
        "Point-category correctness, not individual-pole recall. A fixed-cohort intervention with the same checkpoint; improvement on these recordings does not establish universal pole performance.",
        [file("terrain/pooled_class_comparison.csv"),file("terrain/manifest.json")])
    gravel, asphalt = fine("gravel"), fine("asphalt")
    add(14,"Terrain understanding","Recognising a surface as ground does not mean the model understands its surface type.",
        f"At patch 128, gravel is called ground for {percent(gravel['called_ground_percent'])} of {gravel['points']} points but correctly called natural ground for {percent(gravel['correct_percent'])}. Asphalt is called ground for {percent(asphalt['called_ground_percent'])} of {asphalt['points']} points but correctly called artificial ground for {percent(asphalt['correct_percent'])}.",
        "Keep material-category checks alongside the broad ground/obstacle summary.",
        "Eight-class model taxonomy, not a 64-class material classifier. Four gravel and three asphalt recordings, correlated points; safe driveability is unmeasured.",
        [file("terrain/pooled_class_comparison.csv")])
    wall = fine("wall")
    add(15,"Terrain understanding","The terrain model struggled with walls in one newly evaluated recording.",
        f"Only {wall['correct_points']}/{wall['points']} wall points ({percent(wall['correct_percent'])}) receive the correct artificial-structure category at patch 128; 7.44% are called ground. Building-category points elsewhere in the subset have 90.00% correct structure labels.",
        "Inspect separate structure types instead of treating a good building score as coverage of all structures.",
        "One recording with wall points; this is a case finding, not a general wall score or whole-object miss rate. Building and wall point populations differ.",
        [file("terrain/fine_class_comparison.csv"),file("terrain/pooled_class_comparison.csv")])
    bike, car = fine("bicycle"), fine("car")
    add(16,"Terrain understanding","Bicycle surfaces were harder for the terrain model to classify than car surfaces in the inspected recording.",
        f"In the same newly selected rainy recording, correct vehicle-category labels at patch 128 are {bike['correct_points']}/{bike['points']} ({percent(bike['correct_percent'])}) for bicycle points and {car['correct_points']}/{car['points']} ({percent(car['correct_percent'])}) for car points.",
        "Report vulnerable-road-user categories separately from the overall vehicle score.",
        "One recording and only 256 bicycle points. Point correctness is not bike/car object detection; shape, view and occlusion are not isolated.",
        [file("terrain/fine_class_comparison.csv")])
    by_variant={variant:{value['scenario']:value for value in frames if value['variant']==variant} for variant in ("p64","p128")}
    better=sum(float(by_variant['p128'][name]['correct_percent'])>float(value['correct_percent']) for name,value in by_variant['p64'].items())
    weighted={variant:100*sum(int(value['correct_points']) for value in group.values())/sum(int(value['points']) for value in group.values()) for variant,group in by_variant.items()}
    add(17,"Configuration and generalisation","More model context helped most new cases, but made one case worse.",
        f"Patch 128 improves all-point accuracy in {better}/7 unseen frames. Pooled eight-class point accuracy rises from {weighted['p64']:.2f}% to {weighted['p128']:.2f}%; the flight frame falls from 86.37% to 83.69%. Baseline repetition is prediction-identical.",
        "Treat patch 128 as a candidate with explicit trade-offs; retain regression cases before changing the default.",
        "Seven unseen frames in existing recordings, excluding the tuning recording; not full validation or an external dataset. No new default is adopted. Sampled total GPU memory approached the device limit.",
        [file("terrain/frame_comparison.csv"),file("terrain/manifest.json")])
    obstacle = fine("obstacle")
    add(18,"Configuration and generalisation","Obstacles can still be misclassified even when they are rarely called ground.",
        f"For {obstacle['points']} points with the generic obstacle label in {obstacle['recordings']} new recordings, patch 128 correctly assigns the obstacle category to {percent(obstacle['correct_percent'])}; only {percent(obstacle['called_ground_percent'])} are called ground. Most wrong predictions therefore fall into other categories.",
        "Measure correct recognition as well as ground-confusion reduction.",
        "Generic fine-label group and coarse eight-class predictions; two recordings with correlated points. This is not a count of independent obstacles or safe navigation decisions.",
        [file("terrain/pooled_class_comparison.csv")])
    add(19,"Configuration and generalisation","A high pooled terrain score can hide serious failures in another environment.",
        "At patch 128, pooled soil correctness is 99.53% over 51,020 points, dominated by 50,247 field-path points with 100.00% rounded correctness. The rainy recording's 240 soil points have only 7.92% correct natural-ground labels. All 2,401 asphalt points in the flight frame are assigned a wrong coarse category despite 89.78% pooled asphalt correctness.",
        "Publish class-by-recording results and inspect failures alongside aggregate scores.",
        "Small class populations in some recordings; one frame per recording. These are scenario-specific observations, not causal effects of rain or a population generalisation estimate.",
        [file("terrain/fine_class_comparison.csv"),file("terrain/pooled_class_comparison.csv")])
    add(20,"Practical feasibility","The available model pair cannot yet tell us which sensor recognises distant vehicles better.",
        "The inspected pretrained LiDAR/radar PointPillars pair accepts inputs only to about 70 m; zero of the earlier 504 vehicle centres at 200–400 m lie in its input region. Official TruckDrive/L-RadSet release documentation was refreshed on 1 October and remains at the same inspected revisions; the reviewed TruckDrive instructions provide a training workflow rather than a compatible pretrained radar/LiDAR pair.",
        "Obtain compatible long-range weights and feature definitions before a fair distant-recognition comparison; more GPU memory alone does not resolve the input-range mismatch.",
        "Verified limitation of the inspected releases/checkpoints, not proof no suitable model exists anywhere. No new detector accuracy, training or author contact claimed.",
        ["docs/detector-compatibility-decision.md",file("models/release-documents.json")],"Refreshed feasibility finding")
    if len(conclusions)!=20 or len({value['id'] for value in conclusions})!=20:
        raise ValueError("Conclusion count/identity mismatch")
    for value in conclusions:
        if value["id"]=="C09":
            value["status"]="Suggestive weather pilot"
        elif value["id"] in ("C11","C15","C16"):
            value["status"]="Supported case finding"
        elif value["id"]=="C20":
            value["status"]="Verified feasibility limitation"
    for value in conclusions:
        for source in value['sources']:
            if not (ROOT/source).is_file():
                raise ValueError("Missing evidence source: "+source)
    (OUT/"conclusions.json").write_text(json.dumps(conclusions,indent=2,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
    markdown=["# Twenty plain-language dataset conclusions — 1 October 2026", "",
              "These conclusions consolidate earlier results and new studies. The new work adds two previously unexamined TruckDrive clips, seven unseen GOOSE frames with controlled model variants, and expanded class/visibility/weather analyses. Findings describe the tested hardware, recordings and model configuration. Coverage means an in-box sensor return; terrain scores measure classification of returned points. Neither is a general detector or safe-driving score.", "",
              "The client report and planning register remain local. This page is the findings/evidence summary. Individual case findings are explicitly marked; the count does not establish twelve weeks of labour or client acceptance.", ""]
    theme=None
    for value in conclusions:
        if value['theme']!=theme:
            theme=value['theme'];markdown.extend(["## "+theme,""])
        markdown.extend(["### "+value['id']+" — "+value['headline'],"", "**Evidence:** "+value['evidence'],"",
                         "**Why it matters:** "+value['implication'],"", "**Limit:** "+value['limitation'],"",
                         "**Status / basis:** "+value['status']+"; "+value['origin']+". Sources: "+"; ".join("["+Path(source).name+"]("+"../"+source+")" for source in value['sources'])+".",""])
    markdown.extend(["## Supporting figures", "", "![Nearby object coverage](../"+BASE+"nearby_object_coverage.png)","",
                    "![New distant vehicle sample](../"+BASE+"new_clip_vehicle_coverage.png)","",
                    "![Model context across recordings](../"+BASE+"terrain_context_by_recording.png)",""])
    (ROOT/"docs/client-level-conclusions-oct01.md").write_text("\n".join(markdown),encoding="utf-8",newline="\n")
    sources=sorted({source for value in conclusions for source in value['sources']})
    (OUT/"conclusion_sources.json").write_text(json.dumps(dict(hash_definition="Repository UTF-8 text with LF endings", sources_sha256={source:hash_repository_text(ROOT/source) for source in sources}),indent=2)+"\n",encoding="utf-8",newline="\n")
    print("Wrote 20 scoped client-level conclusions with",len(sources),"evidence sources")


if __name__=="__main__":
    main()
