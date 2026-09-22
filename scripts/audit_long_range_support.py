"""Stress-test saved paired support without treating repeated boxes as independent trials."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from compare_truckscenes_raw import write_csv


def describe(rows, threshold=1):
    if not rows:
        raise ValueError('Cannot describe an empty cohort')
    lidar = np.array([r['lidar_points'] for r in rows]) >= threshold
    radar = np.array([r['radar_points'] for r in rows]) >= threshold
    return dict(observations=len(rows), instances=len({r['instance_token'] for r in rows}),
        scenes=len({r['scene'] for r in rows}), lidar_supported=int(lidar.sum()),
        radar_supported=int(radar.sum()), both=int((lidar & radar).sum()),
        lidar_only=int((lidar & ~radar).sum()), radar_only=int((radar & ~lidar).sum()),
        neither=int((~lidar & ~radar).sum()), lidar_percent=float(100*lidar.mean()),
        radar_percent=float(100*radar.mean()), difference_pp=float(100*(lidar.mean()-radar.mean())),
        min_range_m=min(r['range_m'] for r in rows), max_range_m=max(r['range_m'] for r in rows))


def one_per_instance(rows):
    """First qualifying observation by timestamp, then token; independent of sensor outcome."""
    selected = {}
    for row in sorted(rows, key=lambda r: (r['timestamp'], r['annotation_token'])):
        selected.setdefault(row['instance_token'], row)
    return list(selected.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, default=Path('docs/evidence/truckscenes/paired-point-motion-support'))
    parser.add_argument('--output-dir', type=Path, default=Path('docs/evidence/truckscenes/long-range-audit'))
    args = parser.parse_args()
    from pyquaternion import Quaternion
    from truckscenes.utils.splits import create_splits_scenes
    metadata = args.data_root/'v1.2-mini'
    samples = {s['token']:s for s in json.loads((metadata/'sample.json').read_text())}
    annotations = {a['token']:a for a in json.loads((metadata/'sample_annotation.json').read_text())}
    poses = {p['token']:p for p in json.loads((metadata/'ego_pose.json').read_text())}
    attrs = {a['token']:a['name'] for a in json.loads((metadata/'attribute.json').read_text())}
    alignment = list(csv.DictReader((args.evidence/'sensor_alignment.csv').open()))
    reference = {r['sample_token']:poses[r['reference_pose_token']] for r in alignment}
    validation = set(create_splits_scenes()['mini_val'])
    rows = []
    for row in csv.DictReader((args.evidence/'object_counts.csv').open()):
        for key in ('lidar_points','radar_points','publisher_lidar_points','publisher_radar_points'):
            row[key] = int(row[key])
        row['range_m'], row['margin_m'] = float(row['range_m']), float(row['margin_m'])
        ann, pose = annotations[row['annotation_token']], reference[row['sample_token']]
        xyz = Quaternion(pose['rotation']).rotation_matrix.T @ (np.array(ann['translation'])-pose['translation'])
        if not np.isclose(np.hypot(*xyz[:2]), row['range_m'], atol=1e-7):
            raise ValueError('Saved range disagrees with annotation/reference geometry')
        row['azimuth_deg'] = float(np.degrees(np.arctan2(xyz[1],xyz[0])))
        row['timestamp'] = samples[row['sample_token']]['timestamp']
        row['attributes'] = ';'.join(sorted(attrs[t] for t in ann['attribute_tokens']))
        rows.append(row)
    long = [r for r in rows if r['range_m'] >= 150]
    exact = [r for r in long if r['margin_m'] == 0]
    if len({r['annotation_token'] for r in exact}) != len(exact):
        raise ValueError('Duplicate annotation observations')
    predicates = dict(all=lambda r:True,
        vehicles=lambda r:r['category'].startswith('vehicle.') and r['category']!='vehicle.ego_trailer',
        cars=lambda r:r['category']=='vehicle.car', trucks=lambda r:r['category']=='vehicle.truck',
        forward_30deg=lambda r:abs(r['azimuth_deg'])<=30,
        front_180deg=lambda r:abs(r['azimuth_deg'])<=90,
        rear_180deg=lambda r:abs(r['azimuth_deg'])>90,
        within_150_180=lambda r:r['range_m']<180,
        forward_30deg_150_180=lambda r:r['range_m']<180 and abs(r['azimuth_deg'])<=30,
        official_mini_val=lambda r:r['scene'] in validation)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    sensitivity = []
    for margin in (0, .5):
        for name, predicate in predicates.items():
            group = [r for r in long if r['margin_m']==margin and predicate(r)]
            if group:
                for threshold in (1,3,5):
                    sensitivity.append(dict(cohort=name,margin_m=margin,threshold=threshold,**describe(group,threshold)))
    write_csv(output/'sensitivity.csv', sensitivity)
    for field,filename in [('scene','by_scene.csv'),('category','by_class.csv'),('attributes','by_activity.csv')]:
        groups = defaultdict(list)
        for r in exact:groups[r[field]].append(r)
        write_csv(output/filename,[dict(group=k,**describe(v)) for k,v in sorted(groups.items())])
    fine = []
    for low,high in [(150,175),(175,200),(200,225),(225,250)]:
        group = [r for r in exact if low <= r['range_m'] < high]
        if group:fine.append(dict(band_m=f'{low}-{high}',**describe(group)))
    write_csv(output/'fine_ranges.csv',fine)
    instances = defaultdict(list)
    for r in exact:instances[r['instance_token']].append(r)
    track_rows = [dict(instance_token=k,category=v[0]['category'],scene=v[0]['scene'],**{a:b for a,b in describe(v).items() if a!='scenes'}) for k,v in sorted(instances.items())]
    write_csv(output/'track_support.csv',track_rows)
    exclusions = [dict(excluded_scene=scene,**describe([r for r in exact if r['scene'] != scene])) for scene in sorted({r['scene'] for r in exact})]
    write_csv(output/'leave_one_scene_out.csv',exclusions)
    manifest = json.loads((args.evidence/'manifest.json').read_text())
    mismatch = {}
    for name,group in [('all',[r for r in rows if r['margin_m']==0]),('long_range',exact)]:
        mismatch[name] = dict(n=len(group),lidar_equal=sum(r['lidar_points']==r['publisher_lidar_points'] for r in group),
            radar_equal=sum(r['radar_points']==r['publisher_radar_points'] for r in group),
            lidar_publisher_positive_raw_zero=sum(r['publisher_lidar_points']>0 and r['lidar_points']==0 for r in group),
            lidar_raw_greater=sum(r['lidar_points']>r['publisher_lidar_points'] for r in group),
            lidar_raw_less=sum(r['lidar_points']<r['publisher_lidar_points'] for r in group))
    result = dict(definition='At least 150 m planar object-centre range; same saved paired observations; no inference',
        summary=describe(exact), first_observation_per_instance=describe(one_per_instance(exact)),
        equal_instance_weight=dict(instances=len(track_rows),lidar_percent=float(np.mean([r['lidar_percent'] for r in track_rows])),
                                  radar_percent=float(np.mean([r['radar_percent'] for r in track_rows]))),
        leave_one_scene_out_difference_pp=[min(r['difference_pp'] for r in exclusions),max(r['difference_pp'] for r in exclusions)],
        publisher_reconciliation=mismatch,scene_descriptions=manifest['scene_descriptions'],
        absent_ranges='No observations at >=250 m; 150-400 was a storage bin, not demonstrated coverage to 400 m',
        limitations=['Descriptive sensitivity, no population confidence interval or causal sensor claim',
            'LiDAR-based annotations exclude unlabelled objects; resampling cannot remove that selection bias',
            'First-per-track and equal-track weighting reduce duration bias but tracks in one scene remain correlated',
            'Mini-val has only two scenes; no detector predictions are evaluated'],
        input_sha256_lf_normalized={str(p).replace('\\','/'):hashlib.sha256(p.read_text().encode()).hexdigest()
            for p in [args.evidence/'object_counts.csv',args.evidence/'sensor_alignment.csv',metadata/'sample.json',metadata/'sample_annotation.json',metadata/'ego_pose.json',metadata/'attribute.json']})
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    plot(output)
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256_lf_normalized','scene_descriptions')},indent=2))


def plot(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = list(csv.DictReader((output/'by_scene.csv').open()))
    fig,ax = plt.subplots(figsize=(10,6))
    y=np.arange(len(rows))
    ax.barh(y-.16,[float(r['lidar_percent']) for r in rows],height=.3,label='LiDAR',color='#297b91')
    ax.barh(y+.16,[float(r['radar_percent']) for r in rows],height=.3,label='Radar',color='#d49227')
    ax.set(yticks=y,yticklabels=[f"{r['group'][-8:]}  (n={r['observations']})" for r in rows],
        xlim=(0,105),xlabel='Labelled long-range observations with an in-box return (%)',
        title='Does the long-range support difference persist across scenes?')
    ax.legend(loc='lower right');ax.invert_yaxis()
    fig.text(.02,.02,'All observed box centres >=150 m (maximum 229.4 m). Exact boxes; per-point LiDAR ego correction.\n'
             'Scene suffixes identify saved cohorts. LiDAR-based labels; geometric support, not detector recall.',fontsize=9)
    fig.tight_layout(rect=(0,.10,1,1));fig.savefig(output/'long_range_by_scene.png',dpi=150);plt.close(fig)


if __name__=='__main__':main()
