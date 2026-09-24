"""Read raw radar range limits and test bounded LiDAR counting hypotheses.

Sector-average timing is an explicit approximation, not an exact publisher implementation.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from compare_truckscenes_raw import align_cloud, transform_points, write_csv
from truckscenes_paired_support import deskew_cloud, inside_box


def sector_mean_times(points, timestamps):
    """Use mean acquisition time in each one-degree sensor-azimuth sector."""
    points=np.asarray(points)
    times = np.asarray(timestamps).reshape(-1)
    if points.ndim!=2 or points.shape[0]<2 or points.shape[1]!=len(times) or not np.isfinite(times).all() or not np.isfinite(points).all():
        raise ValueError('Finite point coordinates and matching timestamps required')
    if not len(times):return times
    sectors = np.floor(np.degrees(np.arctan2(points[1],points[0]))).astype(int)
    _, inverse = np.unique(sectors, return_inverse=True)
    origin = times.min()
    means = np.bincount(inverse,weights=times-origin) / np.bincount(inverse)
    return origin+means[inverse]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,default=Path('docs/evidence/truckscenes/preprocessing-audit'))
    args=parser.parse_args()
    from truckscenes import TruckScenes
    from truckscenes.utils.data_classes import RadarPointCloud,LidarPointCloud
    from truckscenes.utils.geometry_utils import transform_matrix
    from pyquaternion import Quaternion
    from scipy.spatial import cKDTree
    truck=TruckScenes(version='v1.2-mini',dataroot=str(args.data_root),verbose=False)
    def matrix(r):return transform_matrix(np.array(r['translation']),Quaternion(r['rotation']))
    output=args.output_dir;output.mkdir(parents=True,exist_ok=True)
    ranges=defaultdict(list);hashes={}
    for sample in truck.sample:
        for channel,token in sample['data'].items():
            if not channel.startswith('RADAR'):continue
            sd=truck.get('sample_data',token);path=args.data_root/sd['filename']
            hashes[sd['filename']]=hashlib.sha256(path.read_bytes()).hexdigest()
            xyz=RadarPointCloud.from_file(str(path)).points[:3]
            if not np.isfinite(xyz).all():raise ValueError('Nonfinite raw radar coordinates')
            ranges[channel].append(np.linalg.norm(xyz,axis=0))
    radar_rows=[];histogram=[]
    for channel,values in sorted(ranges.items()):
        distances=np.concatenate(values)
        radar_rows.append(dict(channel=channel,keyframes=len(values),returns=len(distances),
            max_sensor_range_m=float(distances.max()),p999_sensor_range_m=float(np.quantile(distances,.999)),
            returns_ge_190=int((distances>=190).sum()),returns_ge_200=int((distances>=200).sum())))
        counts,edges=np.histogram(distances,bins=np.arange(0,211,5))
        histogram.extend(dict(channel=channel,low_m=int(low),high_m=int(high),count=int(n)) for low,high,n in zip(edges[:-1],edges[1:],counts))
    write_csv(output/'radar_sensor_ranges.csv',radar_rows)
    write_csv(output/'radar_range_histogram.csv',histogram)
    evidence=Path('docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv')
    saved={r['annotation_token']:r for r in csv.DictReader(evidence.open()) if float(r['margin_m'])==0}
    included={r['sample_token'] for r in saved.values()};scenes=defaultdict(list)
    for s in truck.sample:
        if s['token'] in included:scenes[s['scene_token']].append(s)
    selected=[]
    for scene,ss in sorted(scenes.items()):
        ss=sorted(ss,key=lambda s:s['timestamp'])
        selected.extend(ss[int(len(ss)*fraction)] for fraction in (.25,.5,.75))
    poses=sorted(truck.ego_pose,key=lambda p:p['timestamp'])
    times=np.array([p['timestamp'] for p in poses]);translations=np.array([p['translation'] for p in poses]);quats=np.array([p['rotation'] for p in poses])
    diagnostics=[]
    for index,sample in enumerate(selected,1):
        ref=matrix(truck.getclosest('ego_pose',sample['timestamp']));inverse=np.linalg.inv(ref)
        methods=defaultdict(list)
        for channel,token in sorted(sample['data'].items()):
            if not channel.startswith('LIDAR'):continue
            sd=truck.get('sample_data',token);path=args.data_root/sd['filename']
            hashes[sd['filename']]=hashlib.sha256(path.read_bytes()).hexdigest()
            cloud=LidarPointCloud.from_file(str(path));cal=matrix(truck.get('calibrated_sensor',sd['calibrated_sensor_token']))
            pose=matrix(truck.get('ego_pose',sd['ego_pose_token']))
            point=deskew_cloud(cloud.points[:3],cloud.timestamps,cal,ref,times,translations,quats)
            methods['point_all_six'].append(point)
            if channel in ('LIDAR_LEFT','LIDAR_RIGHT'):methods['point_main_two'].append(point)
            methods['rigid_all_six'].append(align_cloud(cloud.points[:3],cal,pose,ref))
            approximate=sector_mean_times(cloud.points,cloud.timestamps)
            methods['sector_mean_1deg_all_six'].append(deskew_cloud(cloud.points[:3],approximate,cal,ref,times,translations,quats))
        clouds={k:np.concatenate(v,axis=1) for k,v in methods.items()}
        trees={k:cKDTree(v.T) for k,v in clouds.items()}
        for token in sample['anns']:
            a=truck.get('sample_annotation',token);center=transform_points(np.array(a['translation'])[:,None],inverse)[:,0]
            rotation=inverse[:3,:3]@Quaternion(a['rotation']).rotation_matrix
            radius=np.linalg.norm(np.array(a['size'])/2)+1e-8
            counts={k:int(inside_box(v[:,trees[k].query_ball_point(center,radius)],center,rotation,a['size']).sum()) for k,v in clouds.items()}
            if counts['point_all_six']!=int(saved[token]['lidar_points']):raise ValueError('Point recount changed from saved baseline')
            diagnostics.append(dict(annotation_token=token,sample_token=sample['token'],range_m=float(saved[token]['range_m']),
                                    publisher=a['num_lidar_pts'],**counts))
        print(f'LiDAR hypothesis samples: {index}/{len(selected)}',flush=True)
    write_csv(output/'lidar_hypothesis_counts.csv',diagnostics)
    comparison=[]
    for scope,predicate in [('all',lambda r:True),('ge150',lambda r:r['range_m']>=150)]:
        group=[r for r in diagnostics if predicate(r)]
        for method in clouds:
            delta=np.array([r[method]-r['publisher'] for r in group])
            comparison.append(dict(scope=scope,method=method,observations=len(group),exact_matches=int((delta==0).sum()),
                mean_absolute_count_difference=float(np.abs(delta).mean()),raw_positive=int(sum(r[method]>0 for r in group)),
                publisher_positive=int(sum(r['publisher']>0 for r in group))))
    write_csv(output/'lidar_hypothesis_summary.csv',comparison)
    manifest=dict(radar_keyframes=sum(r['keyframes'] for r in radar_rows),radar_returns=sum(r['returns'] for r in radar_rows),
        radar_definition='Unfiltered Euclidean x/y/z range in each original sensor frame, all six sensors and all 400 mini samples',
        recorded_range_limit_interpretation='Observed support boundary only; does not establish hardware maximum or identify filtering/configuration cause',
        lidar_sample_selection='25%, 50%, 75% positions of timestamp-sorted accepted samples in each of the ten scenes',
        lidar_samples=[s['token'] for s in selected],lidar_observations=len(diagnostics),
        sector_method='Mean point timestamp per floor(sensor azimuth in degrees); authors confirmed 1-degree sectors but did not specify this representative-time rule',
        authors_source='https://github.com/TUMFTM/truckscenes-devkit/issues/18',
        source_raw_sha256=hashes,source_saved_counts_sha256_lf_normalized=hashlib.sha256(evidence.read_text().encode()).hexdigest())
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    plot(output)
    print(json.dumps(dict(radar=radar_rows,lidar=comparison),indent=2))


def plot(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows=list(csv.DictReader((output/'radar_range_histogram.csv').open()))
    channels=list(csv.DictReader((output/'radar_sensor_ranges.csv').open()))
    maximum=max(float(r['max_sensor_range_m']) for r in channels)
    frames=sum(int(r['keyframes']) for r in channels)
    returns=sum(int(r['returns']) for r in channels)
    beyond=sum(int(r['returns_ge_190']) for r in channels)
    totals=defaultdict(int)
    for r in rows:totals[int(r['low_m'])]+=int(r['count'])
    bins=[b for b in sorted(totals) if b>=150]
    fig,ax=plt.subplots(figsize=(10,5.5))
    ax.bar(bins,[totals[b] for b in bins],width=4.6,align='edge',color='#d49227')
    ax.axvline(maximum,color='#ae3434',linestyle='--',label=f'Largest observed sensor-frame range: {maximum:.3f} m')
    ax.set(xlim=(149,211),xlabel='Raw Euclidean range from each radar sensor (m)',ylabel='Returns in 5 m bins',
           title=f'Recorded radar support ends near {maximum:.2f} m in this mini release')
    ax.legend(loc='upper right',fontsize=9)
    ax.text(199,.45*ax.get_ylim()[1],f'{beyond:,} returns\nat or beyond 190 m',ha='center',fontsize=11)
    fig.text(.02,.02,f'All {frames:,} radar keyframes across six sensors; {returns:,} unfiltered returns.\n'
             'Observed dataset boundary, not a specification of the hardware maximum. Object-centre ego range differs.',fontsize=9)
    fig.tight_layout(rect=(0,.12,1,1));fig.savefig(output/'recorded_radar_range_boundary.png',dpi=150);plt.close(fig)


if __name__=='__main__':main()
