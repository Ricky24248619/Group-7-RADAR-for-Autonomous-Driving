"""Measure released TruckDrive same-sync geometric support, not detector accuracy.

Extract the official scene's annotations, calibrations, radar and lidar ZIPs
directly into --scene-root. No model, point filtering or temporal accumulation.
"""
import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path

import numpy as np

from compare_truckscenes_raw import write_csv
from truckscenes_paired_support import inside_box


def frame_index(folder):
    result = {}
    for path in sorted(folder.glob('*')):
        if path.suffix not in ('.bin', '.json'):
            continue
        sync, timestamp = map(int, path.stem.split('_'))
        if sync in result:
            raise ValueError(f'Duplicate sync key {sync} in {folder}')
        result[sync] = (timestamp, path)
    if not result:
        raise ValueError(f'No frames in {folder}')
    return result


def calibration_transform(records, source, target='velodyne'):
    from scipy.spatial.transform import Rotation
    graph = defaultdict(dict)
    for value in records.values():
        parent, child = value['header']['frame_id'], value['child_frame_id']
        t, q = value['transform']['translation'], value['transform']['rotation']
        matrix = np.eye(4)
        matrix[:3, :3] = Rotation.from_quat([q[k] for k in ('x','y','z','w')]).as_matrix()
        matrix[:3, 3] = [t[k] for k in ('x','y','z')]
        graph[child][parent], graph[parent][child] = matrix, np.linalg.inv(matrix)
    queue, visited = deque([(source, np.eye(4))]), set()
    while queue:
        node, matrix = queue.popleft()
        if node == target:
            return matrix
        if node in visited:
            continue
        visited.add(node)
        queue.extend((n, edge @ matrix) for n, edge in graph[node].items() if n not in visited)
    raise ValueError(f'No calibration path {source} -> {target}')


def valid_box(box):
    # Released 2D-only annotations use -1000 coordinates and negative dimensions.
    keys = ('x','y','z','l','w','h','yaw')
    try:
        values = np.array([box[k] for k in keys], dtype=float)
    except (KeyError, TypeError, ValueError):
        return False
    return bool(np.isfinite(values).all() and (values[3:6] > 0).all()
                and not (values[:3] == -1000).any())


def select_annotation_syncs(annotations, count):
    ordered=sorted(annotations,key=lambda sync:annotations[sync][0])
    if count is None or count>=len(ordered):
        return ordered
    if count<2:
        raise ValueError('Select at least two annotation frames')
    return [ordered[round(i*(len(ordered)-1)/(count-1))] for i in range(count)]


def annotation_pose_interpolator(annotations):
    """Interpolate released ego poses only; never use object trajectories."""
    from scipy.spatial.transform import Rotation, Slerp
    times, matrices = [], []
    for timestamp,path in sorted(annotations.values()):
        poses = [np.array(b['velodyne2global']) for b in json.loads(path.read_text()) if 'velodyne2global' in b]
        if not poses or not all(np.allclose(p,poses[0],atol=1e-7) for p in poses):
            raise ValueError(f'Missing/inconsistent per-frame ego poses: {path}')
        times.append(timestamp/1e9)
        matrices.append(poses[0])
    times, matrices = np.array(times),np.array(matrices)
    if not (np.diff(times)>0).all():
        raise ValueError('Ego pose timestamps must increase')
    rotations = Slerp(times,Rotation.from_matrix(matrices[:,:3,:3]))
    def pose(timestamp):
        t=timestamp/1e9
        if not times[0]<=t<=times[-1]:
            raise ValueError('No ego pose extrapolation permitted')
        matrix=np.eye(4)
        matrix[:3,:3]=rotations([t]).as_matrix()[0]
        matrix[:3,3]=[np.interp(t,times,matrices[:,i,3]) for i in range(3)]
        return matrix
    return pose


def main():
    from scipy.spatial import cKDTree
    from scipy.spatial.transform import Rotation
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=Path('docs/evidence/truckdrive/paired-scene-28-1'))
    parser.add_argument('--align-ego', action='store_true',help='Sensitivity: correct each joint scan by its filename acquisition time using released annotation ego poses')
    parser.add_argument('--frame-count',type=int,help='Select evenly spaced annotation timestamps before sensor matching')
    args = parser.parse_args()
    root, output = args.scene_root, args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    calibration = json.loads((root/'calib_tf_tree_full.json').read_text())
    annotations = frame_index(root/'bounding_boxes')
    specifications = [
        ('radar', 'conti542/joint_radars/detections', 'radar_conti542_forward_left_high', '<f8', 33),
        ('lidar', 'aeva/joint_lidars/points', 'lidar_aeva_forward_center_wide', '<f8', 11),
    ]
    specifications.extend(('lidar', f'ouster/{name}/points', f'lidar_ouster_{name}', '<f4', 7)
                          for name in ('forward_center','sideward_left','sideward_right'))
    sensors = [(mode, folder, frame_index(root/folder), calibration_transform(calibration, node), dtype, columns)
               for mode, folder, node, dtype, columns in specifications]
    selected=select_annotation_syncs(annotations,args.frame_count)
    common = sorted(set(selected).intersection(*(set(s[2]) for s in sensors)))
    if not common:
        raise ValueError('No common sync keys across all sensors and annotations')
    timing_excluded = []
    pose = annotation_pose_interpolator(annotations) if args.align_ego else None
    if pose:
        low,high=min(a[0] for a in annotations.values()),max(a[0] for a in annotations.values())
        timing_excluded=[sync for sync in common if any(not low<=s[2][sync][0]<=high for s in sensors)]
        common=[sync for sync in common if sync not in timing_excluded]
    rows, frames, exclusions, hashes = [], [], [], {}
    example_saved = False
    def remember(path):
        with path.open('rb') as f:
            hashes[str(path.relative_to(root)).replace('\\','/')] = hashlib.file_digest(f,'sha256').hexdigest()
    remember(root/'calib_tf_tree_full.json')
    if pose:
        for _,path in annotations.values():
            remember(path)
    for sync in common:
        anno_time, anno_path = annotations[sync]
        remember(anno_path)
        clouds = defaultdict(list)
        for mode, folder, index, transform, dtype, columns in sensors:
            timestamp, path = index[sync]
            remember(path)
            raw = np.fromfile(path, dtype=dtype).reshape(-1, columns)[:, :3]
            if not np.isfinite(raw).all():
                raise ValueError(f'Non-finite cloud coordinates: {path}')
            xyz = raw @ transform[:3,:3].T + transform[:3,3]
            if pose:
                acquisition_to_reference = np.linalg.inv(pose(anno_time)) @ pose(timestamp)
                xyz=xyz @ acquisition_to_reference[:3,:3].T + acquisition_to_reference[:3,3]
            radius = np.linalg.norm(xyz[:,:2],axis=1)
            frames.append(dict(sync=sync, sensor=folder, modality=mode, points=len(xyz),
                timestamp_ns=timestamp, annotation_timestamp_ns=anno_time, offset_ms=(timestamp-anno_time)/1e6,
                max_planar_range_m=float(radius.max()) if len(radius) else 0,
                **{f'points_ge_{r}m':int((radius>=r).sum()) for r in (100,150,200,250,300,400)}))
            clouds[mode].append(xyz)
        clouds = {m:np.concatenate(v) for m,v in clouds.items()}
        trees = {m:cKDTree(xyz) for m,xyz in clouds.items()}
        for number, box in enumerate(json.loads(anno_path.read_text())):
            reason = 'invalid_3d' if not valid_box(box) else ('ego_vehicle' if 'EgoVehicle' in box['class-id'] else None)
            if reason:
                exclusions.append(dict(sync=sync, annotation_index=number, reason=reason))
                continue
            center = np.array([box[k] for k in ('x','y','z')])
            size = np.array([box[k] for k in ('w','l','h')])
            rotation = Rotation.from_euler('z',box['yaw']).as_matrix()
            if not example_saved and box['class-id']=='Vehicle-Passenger' and 200<=np.hypot(*center[:2])<250:
                plot_example(clouds,center,rotation,size,sync,output,args.align_ego)
                example_saved = True
            for margin in (0.0,0.5):
                counts = {}
                for mode, xyz in clouds.items():
                    indices = trees[mode].query_ball_point(center,np.linalg.norm(size/2+margin)+1e-8)
                    counts[mode+'_points'] = int(inside_box(xyz[indices].T,center,rotation,size,margin).sum())
                rows.append(dict(sample_token=str(sync),annotation_token=f'{sync}:{number}',
                    instance_token=str(box.get('id',box.get('Tracking_ID'))), scene=root.name,
                    timestamp=anno_time, category=box['class-id'],range_m=float(np.hypot(*center[:2])),
                    azimuth_deg=float(np.degrees(np.arctan2(center[1],center[0]))),
                    margin_m=margin, **counts))
        if len(frames) % 250 == 0:
            print(f'Processed {len(frames)//len(sensors)}/{len(common)} paired frames',flush=True)
    write_csv(output/'object_counts.csv',rows)
    write_csv(output/'sensor_frames.csv',frames)
    write_csv(output/'excluded_annotations.csv',exclusions)
    manifest = dict(dataset=f'TruckDrive official mini, {root.name}', paired_frames=len(common),
        available_annotation_frames=len(annotations), unmatched_annotation_syncs=sorted(set(annotations)-set(common)),
        selected_annotation_syncs=selected, missing_sensor_syncs=sorted(set(selected)-set(common)-set(timing_excluded)),
        alignment='filename acquisition-pose correction' if args.align_ego else 'static calibration',
        pose_extrapolation_excluded_syncs=timing_excluded,
        valid_object_observations=len(rows)//2, exclusions=dict((reason,sum(r['reason']==reason for r in exclusions))
            for reason in sorted({r['reason'] for r in exclusions})),
        min_range_m=min(r['range_m'] for r in rows),max_range_m=max(r['range_m'] for r in rows),
        max_abs_timestamp_offset_ms=max(abs(r['offset_ms']) for r in frames),
        transforms={folder:matrix.tolist() for _,folder,_,matrix,_,_ in sensors},input_sha256=hashes,
        source='https://github.com/torc-ai/TruckDrive/tree/a09217e877fe6bad821f9828240c4c1b64d29da1/dataset_viewer',
        method='Same sync key; all released joint radar/Aeva plus three Ouster scans; calibration to velodyne; exact oriented boxes and 0.5 m face expansion; alignment mode recorded separately',
        limitations=['One released scene, not a population benchmark','Geometric support, not detector recall or precision',
            'No additional per-point deskew, target-motion correction or temporal accumulation; acquisition correction only when --align-ego is selected',
            'Filename acquisition-pose correction is a sensitivity hypothesis; released joint-cloud internal timing/deskew is not independently reproduced',
            'Released fused point clouds; internal sensor filtering and fusion are not reproduced',
            'LiDAR-informed annotations and unmatched sensor fields of view; no inference of intrinsic sensor superiority'])
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('input_sha256','transforms')},indent=2))


def plot_example(clouds,center,rotation,size,sync,output,align_ego=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig,axes=plt.subplots(2,2,figsize=(10,7))
    extent=size[[1,0,2]]
    for column,(mode,xyz) in enumerate(clouds.items()):
        local=(xyz-center) @ rotation
        keep=np.all(np.abs(local)<=extent/2+3,axis=1)
        points=local[keep]
        for row,(a,b) in enumerate([(0,1),(0,2)]):
            ax=axes[row,column]
            ax.scatter(points[:,a],points[:,b],s=5,color='#247b91' if mode=='lidar' else '#ce8425')
            ax.add_patch(Rectangle((-extent[a]/2,-extent[b]/2),extent[a],extent[b],fill=False,color='black'))
            ax.set(xlim=(-extent[a]/2-3,extent[a]/2+3),ylim=(-extent[b]/2-3,extent[b]/2+3),
                   xlabel='Object-local length axis (m)',ylabel=('Width' if b==1 else 'Height')+' axis (m)',
                   title=mode.title()+(' top view' if b==1 else ' side view'))
            ax.set_aspect('equal');ax.grid(alpha=.2)
    fig.suptitle(f'First passenger-car box at 200-250 m: sync {sync}, range {np.hypot(*center[:2]):.1f} m')
    alignment = 'acquisition-pose correction hypothesis' if align_ego else 'static calibration'
    fig.text(.015,.02,f'Black rectangle: released annotation. Points: released scans, {alignment}.\n'
             'Deterministic example, not representative accuracy; nearby returns may belong to background.',fontsize=10)
    fig.tight_layout(rect=(0,.085,1,.95));fig.savefig(output/'example_car_200_250m.png',dpi=150);plt.close(fig)


if __name__ == '__main__':
    main()
