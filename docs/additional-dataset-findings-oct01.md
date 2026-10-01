# Additional dataset findings and LiDAR/radar evidence

1 October 2026. This expands the analysis alongside GOOSE; it does not remove the
client's requested GOOSE strand or infer approval of a revised project scope.

## Which additions answer a distinct question?

| Addition | Evidence checked in this update | Useful project question | Current boundary |
|---|---|---|---|
| **Boreas** | Official source/docs pinned to `8e100ff`; three public radar scans and their nearest LiDAR scans decoded; 16,441,068 raw bytes, SHA-256 recorded | Repeat-route sensor robustness and rolling-scan alignment; independent 2D scanning radar context | New sample analysis complete, F29–F30. No shared object scoring, weather effect or detector comparison. It is not a 4D point radar dataset. |
| **WildScenes** | Six official split CSVs pinned to `9eb4e10`; frame IDs, recording groups and cross-modal intersections audited | Independent natural-terrain semantic generalisation from GOOSE | Metadata analysis complete, F31–F32. No raw terrain download or inference. Camera/LiDAR, not radar. |
| **Dual-Radar** | Official repository, paper reference and sensor table pinned to `9a972df` | Distinguish radar hardware and processing from the blanket category “radar”; paired Arbe Phoenix/ARS548, LiDAR and camera | Literature/source review only. No raw download, licence acceptance, checkpoint inference or scores. |
| **RADIal** | Official dataset/label documentation and signal-processing code pinned to `02f52fc` | Test how raw ADC processing versus sparse radar detections affects available evidence | Source review only. Vehicle labels and free-space masks answer different tasks from TruckDrive's oriented 3D boxes. No download or trained-model result. |
| **View of Delft (VoD)** | Official release documentation pinned to `d39b519`; published example-set structure inspected | A bounded urban radar/LiDAR detection study, especially pedestrians and cyclists | Source review only. Full-data access is request-based and the listed eligibility is master/PhD/postdoc/faculty. Eligibility/permission for this undergraduate project is not established; no example/raw data used here. |

These are additions to the *analysis*, not five completed detector benchmarks.
Raw source files remain outside Git. The pinned URLs, revisions, lengths and
hashes are in the [additional-source manifest](../results/evidence/findings-oct01/additional-datasets/manifest.json).

**Recommended use:** WildScenes is the strongest new independent terrain candidate;
its validation recording concentration needs group-specific reporting. Boreas is
an accessible independent repeat-route/weather candidate, but the inspected
three scans establish decoding/timing/range representation only. Dual-Radar can
test whether two radar configurations behave differently on the same platform.
RADIal can test the radar representation/processing question. VoD remains an
access-qualified option; do not represent its full data as available to this team.

Existing **K-Radar** remains a useful 4D radar/LiDAR weather reference; **RADIATE**
already supplies the measured public fog pilot, and **STONE** already supplies
the conditional terrain pilot. CORD and Great Outdoors remain prospective
off-road resources from the [earlier shortlist](offroad-dataset-next-steps.md).
Those entries are not new independent model results. STONE's older dropped-scope
decision remains historical; the later recorded pilot does not itself establish
client approval of a scope change.

## What the sensor literature supports

| Question | Evidence-based interpretation | Project consequence |
|---|---|---|
| **What is 4D radar?** | In K-Radar's formulation, radar resolves range, azimuth, elevation and Doppler. Detection point clouds are a processed representation; raw power tensors retain different information. A 2D scanning radar image is not an equivalent 4D point cloud. | Keep imaging radar in TruckScenes/Dual-Radar separate from Navtech images in Boreas/RADIATE. Do not put their return or pixel counts on one sensor-density leaderboard. |
| **Which works farther?** | There is no hardware-independent ranking. Dual-Radar lists different ranges and angular fields for the two radars on one platform. Boreas records a finite radar image range; our three LiDAR scans contain farther returns. TruckDrive's distant object-support result is a separate released-sensor comparison. | Quote the dataset, hardware, preprocessing and observed endpoint. Use F01/F08 as qualified geometric results, not a claim that LiDAR always outranges radar. |
| **What about bad weather?** | K-Radar's authors study diverse weather and report radar robustness; RADIATE provides actual adverse-weather data. Our short radar-annotated fog pilot has no matched clear-weather control. | Weather robustness is a promising radar contribution; the team has not measured a causal fog penalty or all-weather superiority. |
| **What extra motion information is available?** | Doppler is radial velocity relative to the radar, not full object velocity. Radar-derived motion needs ego-motion treatment. Some FMCW LiDAR streams also provide Doppler: Boreas Road Trip explicitly includes Aeva Doppler fields. | Do not claim all LiDAR lacks velocity or all radar images contain it. No Doppler-quality, tracking or stopping-distance experiment was completed here. |
| **Why is dense geometry still insufficient?** | A returned point is neither an object recognition nor a safe-driving decision. GOOSE's ground grouping omits material and vehicle-specific traversability; its model can confuse returned obstacles with ground. | Evaluate recognition and traversability independently of sensor support. Dense LiDAR support does not establish safe off-road navigation. |
| **How can processing change the apparent ranking?** | RADIal exposes raw ADC, power spectra, point-cloud and range–azimuth processing. TruckScenes recounts demonstrate timing sensitivity; STONE demonstrates coordinate sensitivity. | Report filters, accumulation, calibration, rolling-scan correction and representation before interpreting modality differences. |

Primary sources, verified 1 October 2026:

- [Boreas official sensor/data reference](https://github.com/utiasASRL/pyboreas/blob/8e100ff82ecd4992511da61b016398dbd230f205/DATA_REFERENCE.md)
  and [Boreas Road Trip reference](https://github.com/utiasASRL/pyboreas/blob/8e100ff82ecd4992511da61b016398dbd230f205/DATA_RT_REFERENCE.md).
- [WildScenes official repository](https://github.com/csiro-robotics/WildScenes/tree/9eb4e10b4483a634159e2b371be0437e465fe218).
- [Dual-Radar official repository and sensor table](https://github.com/adept-thu/Dual-Radar/tree/9a972df36af319d3953b4a6e672e6a814ec05eb9).
- [RADIal official data and label definition](https://github.com/valeoai/RADIal/tree/02f52fc13ee41feacec82fd8e05f5b1f0bf4ce26),
  [CVPR paper](https://openaccess.thecvf.com/content/CVPR2022/html/Rebut_Raw_High-Definition_Radar_for_Multi-Task_Learning_CVPR_2022_paper.html).
- [VoD official release and access conditions](https://github.com/tudelft-iv/view-of-delft-dataset/tree/d39b519018701b221787668b182c159bbc8a848f).
- [K-Radar author repository](https://github.com/kaist-avelab/K-Radar),
  [RADIATE author documentation](https://pro.hw.ac.uk/radiate/doc/dataset/).

The Boreas data reference states CC BY 4.0. Source-code licences and dataset
terms can differ. The manifests and derived numerical tables here do not
redistribute any raw dataset. Other full-data access/terms are not treated as
approved merely because a project has a public GitHub repository.

## Reproduce the new sample and metadata analysis

Using the existing project analysis environment (NumPy/Pillow already installed):

```text
python scripts/analyse_additional_datasets.py --acquire --source-root <directory-outside-repo>
python scripts/analyse_findings_oct01.py
python scripts/render_findings_oct01.py
```

The acquisition is bounded to three radar scans, three nearest LiDAR scans,
six WildScenes split files and pinned documentation. It rejects a raw sample
above 20 MB. The analysis checks radar image layout and azimuth timestamps,
finite LiDAR values and split-ID uniqueness. Empty score populations are gaps,
not zeros. Rehash the inputs against the manifest when rerunning; raw source
changes must be investigated rather than silently labelled identical evidence.

## Relation to the client's recorded requirements

The source is the repository's [Scope of Work](../Revised%20Sprint%201%20Deliverables/1.%20Revised%20Scope%20of%20Work.md),
[acceptance criteria](../Revised%20Sprint%201%20Deliverables/3.%20Revised%20Project%20Acceptance%20Tests.md)
and [decision log](../decision-log.md), not an assumed new client instruction.

- **Keep GOOSE:** F14–F22 retain and explain its measured terrain/model findings.
- **Off-road ground/obstacles:** GOOSE and STONE answer different parts; WildScenes adds an independent terrain candidate. Physical safety and paired radar terrain accuracy remain unmeasured.
- **Beyond about 150 m:** TruckDrive provides actual 200–400 m geometric evidence. TruckScenes' recorded radar boundary and stock evaluator limits must remain visible.
- **Sensor/model comparison:** the 32 findings distinguish geometric support, model confusion and signal contrast. A matched radar-only/LiDAR-only detector accuracy comparison remains outstanding. The existing [compatibility decision](detector-compatibility-decision.md) shows why short-range checkpoint input grids cannot answer a 200–400 m question.
- **Negative results and handover:** the new experiment log, records, source hashes, code and tests preserve the results and unresolved calibration/access questions. No model training, Autoware integration or client acceptance is claimed.

The register is evidence to discuss with the client. A finding count cannot
establish P-1 acceptance, P-7 notification, or twelve weeks of work; those need
actual client communication and recorded work history.
