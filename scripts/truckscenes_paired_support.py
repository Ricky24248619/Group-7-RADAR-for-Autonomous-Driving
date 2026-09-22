"""Recount all 12 sensors inside the same oriented annotations, without a detector.

Uses the existing devkit runtime (including SciPy). Raw data stays outside Git.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from compare_truckscenes_raw import (EDGES, LABELS, align_cloud, check_timing,
                                     region_counts, transform_points, write_csv)


def inside_box(points, center, rotation, size_wlh, margin=0.0):
    """Inclusive oriented box; devkit size is width, length, height, x is length."""
    points, center, rotation, size = map(np.asarray, (points, center, rotation, size_wlh))
    if (points.ndim != 2 or points.shape[0] != 3 or center.shape != (3,)
            or rotation.shape != (3, 3) or size.shape != (3,)
            or not all(np.isfinite(x).all() for x in (points, center, rotation, size))
            or (size <= 0).any() or not np.isfinite(margin) or margin < 0):
        raise ValueError("Invalid box geometry")
    local = rotation.T @ (points - center[:, None])
    half = size[[1, 0, 2]] / 2 + margin
    return np.all(np.abs(local) <= half[:, None] + 1e-9, axis=0)


def summarize(rows, threshold=1):
    lidar = np.array([r['lidar_points'] for r in rows]) >= threshold
    radar = np.array([r['radar_points'] for r in rows]) >= threshold
    return dict(observations=len(rows), instances=len({r['instance_token'] for r in rows}),
                threshold=threshold, lidar_only=int((lidar & ~radar).sum()),
                radar_only=int((radar & ~lidar).sum()), both=int((radar & lidar).sum()),
                neither=int((~radar & ~lidar).sum()))


def deskew_cloud(points, timestamps, sensor_to_ego, reference_to_global, pose_times, translations, quaternions):
    """Per-point ego correction: linear translation and quaternion SLERP between GNSS poses."""
    from scipy.spatial.transform import Rotation, Slerp
    times, inverse = np.unique(np.asarray(timestamps).reshape(-1), return_inverse=True)
    if len(inverse) != points.shape[1] or not np.isfinite(times).all():
        raise ValueError('Point timestamps must be finite and match the cloud')
    if not len(times):
        return np.empty((3, 0))
    start = int(np.searchsorted(pose_times, times[0], side='right')) - 1
    end = int(np.searchsorted(pose_times, times[-1], side='left')) + 1
    if start < 0 or end > len(pose_times):
        raise ValueError('Point times lie outside the available pose interval')
    selected_times = pose_times[start:end]
    if len(selected_times) < 2 or np.any(np.diff(selected_times) > 25_000):
        raise ValueError('Point motion interpolation would cross a pose gap >25 ms')
    seconds = (selected_times - selected_times[0]) / 1e6
    query = (times - selected_times[0]) / 1e6
    rotations = Rotation.from_quat(quaternions[start:end, [1, 2, 3, 0]])
    rotation = Slerp(seconds, rotations)(query).as_matrix()[inverse]
    translation = np.column_stack([np.interp(query, seconds, translations[start:end, axis])
                                   for axis in range(3)])[inverse]
    ego_points = transform_points(points, sensor_to_ego).T
    global_points = np.einsum('nij,nj->ni', rotation, ego_points) + translation
    return transform_points(global_points.T, np.linalg.inv(reference_to_global))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--lidar-motion', choices=('point', 'rigid'), default='point')
    args = parser.parse_args()
    from truckscenes import TruckScenes
    from truckscenes.utils.data_classes import LidarPointCloud, RadarPointCloud
    from truckscenes.utils.geometry_utils import transform_matrix
    from pyquaternion import Quaternion
    from scipy.spatial import cKDTree
    from importlib.metadata import version

    started = time.monotonic()
    truck = TruckScenes(version='v1.2-mini', dataroot=str(args.data_root), verbose=False)
    poses = sorted(truck.ego_pose, key=lambda p: p['timestamp'])
    pose_times = np.array([p['timestamp'] for p in poses], dtype=np.int64)
    if np.any(np.diff(pose_times) <= 0):
        raise ValueError('Pose timestamps must be unique and ordered')
    translations = np.array([p['translation'] for p in poses])
    quaternions = np.array([p['rotation'] for p in poses])
    channels = sorted(s['channel'] for s in truck.sensor if s['modality'] in ('lidar', 'radar'))
    if len(set(channels)) != 12 or any(sum(c.startswith(m) for c in channels) != 6 for m in ('RADAR', 'LIDAR')):
        raise ValueError('Expected six radar and six lidar channels')
    samples = sorted(truck.sample, key=lambda s: (s['scene_token'], s['timestamp']))
    if len(samples) != 400:
        raise ValueError('Expected the complete 400-sample mini release')
    excluded = []
    for sample in samples:
        reference = truck.getclosest('ego_pose', sample['timestamp'])
        for channel in channels:
            sd = truck.get('sample_data', sample['data'][channel])
            pose = truck.get('ego_pose', sd['ego_pose_token'])
            try:
                check_timing(sample['timestamp'], sd['timestamp'], pose['timestamp'], reference['timestamp'])
            except ValueError as error:
                excluded.append(dict(sample_token=sample['token'], channel=channel,
                    sensor_offset_ms=(sd['timestamp']-sample['timestamp'])/1000, reason=str(error)))
    excluded_tokens = {r['sample_token'] for r in excluded}
    samples = [s for s in samples if s['token'] not in excluded_tokens]
    print(f'Paired timing gate: {len(samples)}/400 samples; excluded {len(excluded_tokens)} whole samples', flush=True)
    def matrix(record):
        return transform_matrix(np.array(record['translation']), Quaternion(record['rotation']))
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    rows, ranges, sensor_records = [], [], []
    raw_hashes = {}
    example = None
    included_samples = []
    for index, sample in enumerate(samples, 1):
        reference = truck.getclosest('ego_pose', sample['timestamp'])
        ref = matrix(reference)
        inv = np.linalg.inv(ref)
        clouds = defaultdict(list)
        range_start, alignment_start = len(ranges), len(sensor_records)
        skipped = False
        for channel in channels:
            sd = truck.get('sample_data', sample['data'][channel])
            calibration = truck.get('calibrated_sensor', sd['calibrated_sensor_token'])
            pose = truck.get('ego_pose', sd['ego_pose_token'])
            if (sd['sample_token'] != sample['token'] or not sd['is_key_frame']
                    or truck.get('sensor', calibration['sensor_token'])['channel'] != channel):
                raise ValueError('Keyframe/calibration does not match requested sample/channel')
            check_timing(sample['timestamp'], sd['timestamp'], pose['timestamp'], reference['timestamp'])
            path = args.data_root / sd['filename']
            raw_hashes[sd['filename']] = hashlib.sha256(path.read_bytes()).hexdigest()
            modality = 'radar' if channel.startswith('RADAR') else 'lidar'
            cls = RadarPointCloud if modality == 'radar' else LidarPointCloud
            cloud = cls.from_file(str(path))
            if modality == 'lidar' and args.lidar_motion == 'point':
                try:
                    xyz = deskew_cloud(cloud.points[:3], cloud.timestamps, matrix(calibration), ref,
                                       pose_times, translations, quaternions)
                except ValueError as error:
                    if not str(error).startswith(('Point times lie outside', 'Point motion interpolation')):
                        raise
                    excluded.append(dict(sample_token=sample['token'], channel=channel, reason=str(error)))
                    skipped = True
                    break
            else:
                xyz = align_cloud(cloud.points[:3], matrix(calibration), matrix(pose), ref)
            clouds[modality].append(xyz)
            for region, counts in region_counts(xyz).items():
                for band, count in zip(LABELS, counts):
                    ranges.append(dict(sample_token=sample['token'], channel=channel, modality=modality,
                                       region=region, band_m=band, count=count))
            sensor_records.append(dict(sample_token=sample['token'], channel=channel,
                sample_data_token=sd['token'], calibration_token=calibration['token'],
                acquisition_pose_token=pose['token'], reference_pose_token=reference['token'],
                sensor_offset_ms=(sd['timestamp']-sample['timestamp'])/1000))
        if skipped:
            del ranges[range_start:]
            del sensor_records[alignment_start:]
            print(f"Excluded whole sample {sample['token']}: {excluded[-1]['reason']}", flush=True)
            continue
        included_samples.append(sample)
        clouds = {m: np.concatenate(cs, axis=1) for m, cs in clouds.items()}
        trees = {m: cKDTree(xyz.T) for m, xyz in clouds.items()}
        scene = truck.get('scene', sample['scene_token'])['name']
        for token in sample['anns']:
            annotation = truck.get('sample_annotation', token)
            center = transform_points(np.array(annotation['translation'])[:, None], inv)[:, 0]
            rotation = inv[:3, :3] @ Quaternion(annotation['rotation']).rotation_matrix
            distance = float(np.hypot(*center[:2]))
            # Sphere covers the entire box, including the 0.5 m sensitivity margin.
            radius = float(np.linalg.norm(np.array(annotation['size']) / 2 + .5)) + 1e-8
            candidates = {m: xyz[:, trees[m].query_ball_point(center, radius)] for m, xyz in clouds.items()}
            exact = None
            for margin in (0.0, 0.5):
                counts = {m: int(inside_box(xyz, center, rotation, annotation['size'], margin).sum())
                          for m, xyz in candidates.items()}
                row = dict(sample_token=sample['token'], annotation_token=token,
                    instance_token=annotation['instance_token'], scene=scene,
                    category=annotation['category_name'], range_m=distance,
                    band_m=LABELS[int(np.searchsorted(EDGES, distance, side='right') - 1)],
                    margin_m=margin, lidar_points=counts['lidar'], radar_points=counts['radar'],
                    publisher_lidar_points=annotation['num_lidar_pts'], publisher_radar_points=annotation['num_radar_pts'])
                rows.append(row)
                if margin == 0:
                    exact = row
            # Deterministic illustrative case, not selected for best-looking sensor outcome.
            if example is None and annotation['category_name'] == 'vehicle.car' and distance >= 100:
                example = dict(row=exact, center=center, rotation=rotation, size=annotation['size'],
                               candidates=candidates)
        if index % 10 == 0:
            print(f'Processed {index}/{len(samples)} paired samples ({time.monotonic()-started:.1f}s)', flush=True)
    samples = included_samples
    if not samples or len(rows) != 2 * sum(len(s['anns']) for s in samples):
        raise ValueError('Incomplete annotation coverage')
    write_csv(output / 'object_counts.csv', rows)
    write_csv(output / 'sample_channel_ranges.csv', ranges)
    write_csv(output / 'sensor_alignment.csv', sensor_records)
    summaries = []
    for fields, filename in [(('band_m',), 'range_support.csv'),
                             (('category', 'band_m'), 'class_range_support.csv'),
                             (('scene', 'band_m'), 'scene_range_support.csv')]:
        groups = defaultdict(list)
        for row in rows:
            groups[(row['margin_m'], *(row[k] for k in fields))].append(row)
        table = [dict(margin_m=key[0], **dict(zip(fields, key[1:])), **summarize(group, threshold))
                 for key, group in sorted(groups.items()) for threshold in (1, 3, 5)]
        write_csv(output / filename, table)
        if filename == 'range_support.csv':
            summaries = table
    aggregated = defaultdict(int)
    for row in ranges:
        aggregated[(row['modality'], row['region'], row['band_m'])] += row['count']
    write_csv(output / 'suite_ranges.csv', [dict(modality=m, region=r, band_m=b, count=n)
                                           for (m, r, b), n in sorted(aggregated.items())])
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((args.data_root / 'v1.2-mini').glob('*.json'))}
    exact_rows = [r for r in rows if r['margin_m'] == 0]
    manifest = dict(dataset='MAN TruckScenes v1.2-mini', samples=len(samples),
        scenes=len(truck.scene), channels=channels, annotation_observations=len(exact_rows),
        excluded_samples=excluded, total_available_samples=400,
        unique_instances=len({r['instance_token'] for r in exact_rows}),
        elapsed_seconds=time.monotonic()-started,
        definition='All six current keyframes per modality, aligned to sample-time ego; points inside oriented 3D boxes; inclusive boundaries; no radar quality filtering',
        lidar_motion=args.lidar_motion,
        point_motion_method='Linear translation and quaternion SLERP between recorded ego poses; maximum pose gap 25 ms' if args.lidar_motion == 'point' else 'One acquisition pose per scan',
        margins_m=[0, .5], thresholds_points=[1, 3, 5],
        limitations=['Annotation-conditioned geometric support, not detection recall or mAP',
            'LiDAR-supported annotation selection; cannot infer unseen radar-only objects',
            'No moving-object correction or additional cabin articulation correction; see lidar_motion for ego correction',
            'Overlapping sensors/boxes can count the same surface more than once; points are not unique objects',
            'Expanded boxes can include background; sensitivity check only',
            'Repeated observations across ten scenes are not independent trials'],
        metadata_sha256=hashes, raw_file_sha256=raw_hashes,
        packages={p: version(p) for p in ('truckscenes-devkit', 'numpy', 'scipy', 'pypcd4', 'pyquaternion')},
        summary=summarize(exact_rows),
        publisher_recount=dict(lidar_equal=sum(r['lidar_points']==r['publisher_lidar_points'] for r in exact_rows),
                               radar_equal=sum(r['radar_points']==r['publisher_radar_points'] for r in exact_rows)),
        scene_descriptions={s['name']: s['description'] for s in truck.scene})
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    make_plots(output, summaries, example, len(samples), args.lidar_motion)
    print(json.dumps({k: manifest[k] for k in ('elapsed_seconds', 'summary', 'publisher_recount')}, indent=2))


def make_plots(output, summaries, example, sample_count, lidar_motion='rigid'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    selected = {r['band_m']: r for r in summaries if r['margin_m'] == 0 and r['threshold'] == 1}
    bands = [b for b in LABELS if b in selected]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    bottom = np.zeros(len(bands))
    for key, label, color in [('both', 'Both suites', '#588ba8'), ('lidar_only', 'LiDAR only', '#e1a340'),
                              ('radar_only', 'Radar only', '#7358a8'), ('neither', 'Neither', '#b5b5b5')]:
        shares = [100*selected[b][key]/selected[b]['observations'] for b in bands]
        ax.bar(bands, shares, bottom=bottom, label=label, color=color)
        bottom += shares
    ax.set(ylim=(0, 104), ylabel='Share of labelled box observations (%)', xlabel='Object-centre distance (m)',
           title='Which sensor suites put at least one return inside the same object box?')
    for i, b in enumerate(bands):
        ax.text(i, 101, f"n={selected[b]['observations']:,}", ha='center', fontsize=9)
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.14), ncol=4)
    motion_label = 'Per-point ego correction' if lidar_motion == 'point' else 'One ego pose per scan'
    fig.text(.02, .02, f'TruckScenes mini: {sample_count} paired samples, all six radar + six LiDAR sensors; exact 3D boxes.\n'
             f'{motion_label}. Geometric support, not detector accuracy. LiDAR-based labels.', fontsize=9)
    fig.tight_layout(rect=(0, .12, 1, 1))
    fig.savefig(output/'paired_object_support.png', dpi=150)
    plt.close(fig)
    if example:
        fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharex=True, sharey=True)
        size = np.array(example['size'])[[1, 0, 2]] / 2
        for ax, modality in zip(axes, ('lidar', 'radar')):
            local = example['rotation'].T @ (example['candidates'][modality] - example['center'][:, None])
            mask = inside_box(example['candidates'][modality], example['center'], example['rotation'], example['size'])
            ax.scatter(local[0, ~mask], local[1, ~mask], s=3, color='#bbb', label='Outside 3D box')
            ax.scatter(local[0, mask], local[1, mask], s=10, color='#3168ba', label='Inside 3D box')
            ax.add_patch(plt.Rectangle((-size[0], -size[1]), 2*size[0], 2*size[1], fill=False, color='#b84630'))
            ax.set(title=f"{modality.upper()}: {mask.sum()} in-box returns", xlabel='Box-local longitudinal (m)', aspect='equal')
            ax.legend(fontsize=8)
        axes[0].set_ylabel('Box-local lateral (m)')
        fig.suptitle(f"Paired car example at {example['row']['range_m']:.1f} m - top view")
        fig.text(.02, .015, 'First car at >=100 m in sorted scene/time/annotation order; not a representative average.\n'
                 'Same labelled box and sample. Grey context points can be outside the box height.', fontsize=9)
        fig.tight_layout(rect=(0, .12, 1, .94))
        fig.savefig(output/'paired_car_example.png', dpi=150)
        plt.close(fig)
        (output/'example.json').write_text(json.dumps(example['row'], indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
