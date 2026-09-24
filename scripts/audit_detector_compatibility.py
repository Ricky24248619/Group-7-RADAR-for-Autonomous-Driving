"""Audit downloaded checkpoint configs and input-ROI coverage, without inference.

Checkpoint pickle strings are inspected with pickletools, never unpickled or
executed. ROI coverage is a compatibility diagnostic, not detector recall.
"""
import argparse
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import pickletools
import subprocess
import zipfile


def sha256(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def input_range(config):
    tree = ast.parse(config)
    ranges = [ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign) and any(
                  isinstance(t, ast.Name) and t.id == 'point_cloud_range'
                  for t in node.targets)]
    if len(ranges) != 1:
        raise ValueError('Expected one literal top-level point_cloud_range')
    bounds = ranges[0]
    if (len(bounds) != 6 or not all(math.isfinite(x) for x in bounds)
            or any(bounds[i] >= bounds[i+3] for i in range(3))):
        raise ValueError('Invalid input bounds')
    return bounds


def checkpoint_configs(path):
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f'Checkpoint ZIP CRC failure: {bad}')
        members = [n for n in archive.namelist() if n.endswith('/data.pkl')]
        if len(members) != 1:
            raise ValueError('Expected one checkpoint data.pkl')
        return sorted(set(arg for op, arg, _ in pickletools.genops(archive.read(members[0]))
                          if op.name in ('BINUNICODE', 'SHORT_BINUNICODE')
                          and 'model = dict(' in arg and 'point_cloud_range' in arg))


def in_input_roi(center, bounds, dimensions=2):
    return all(bounds[i] <= center[i] < bounds[i+3] for i in range(dimensions))


def source_revision(root):
    return subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-root', type=Path, required=True)
    parser.add_argument('--dataset-root', type=Path, required=True)
    parser.add_argument('--truckdrive-source', type=Path, required=True)
    parser.add_argument('--lradset-source', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, default=Path('docs/evidence/truckdrive-multiscene'))
    parser.add_argument('--output-dir', type=Path, default=Path('docs/evidence/detector-compatibility'))
    args = parser.parse_args()
    models = []
    for modality, file_id in [('lidar', '1ztdeQNoOcIXPHRganyAexk_hx_MrJyrf'),
                              ('radar', '1RNWtkgWlBwpsqYPpECd0xins4k-tDLnL')]:
        path = args.model_root / f'pp_{modality}.pth'
        configs = checkpoint_configs(path)
        if not configs:
            raise ValueError('Checkpoint has no readable config')
        bounds = [input_range(c) for c in configs]
        if any(b != bounds[0] for b in bounds):
            raise ValueError('Embedded checkpoint configs disagree')
        models.append(dict(name=f'lradset_pointpillars_{modality}_checkpoint',
            kind='downloaded_checkpoint', point_cloud_range=bounds[0],
            sha256=sha256(path), bytes=path.stat().st_size, archive_crc_verified=True,
            source=f'https://drive.google.com/file/d/{file_id}/view',
            unique_embedded_configs=len(configs),
            config_sha256=[hashlib.sha256(c.encode()).hexdigest() for c in configs]))
    configs = [
        ('lradset_lidar_long_config', args.lradset_source,
         'configs/pointpillars/pointpillars_hv_fpn_8xb6_l-radset-long.py', 'crrasjtu/L-RadSet'),
        ('lradset_radar_long_config', args.lradset_source,
         'configs/pointpillars/pointpillars_hv_fpn_8xb6_radset-long-range.py', 'crrasjtu/L-RadSet'),
        ('truckdrive_lidar_fullrange_config', args.truckdrive_source,
         'mmdet_project/TruckDrive/configs/bevfusion_lidar_voxel0075_second_secfpn_8xb4-cyclic-20e_truckdrive-3d_fullrange.py', 'torc-ai/TruckDrive')]
    for name, root, relative, repository in configs:
        path = root / relative
        models.append(dict(name=name, kind='source_config_only', point_cloud_range=input_range(path.read_text()),
            sha256=sha256(path), source=f'https://github.com/{repository}/blob/{source_revision(root)}/{relative}'))

    scenes = json.loads((args.evidence_root/'summary/manifest.json').read_text())['scenes']
    observations = []
    source_hashes = {}
    for scene in scenes:
        folder = args.evidence_root/scene/'aligned'
        run = json.loads((folder/'manifest.json').read_text())
        path = folder/'object_counts.csv'
        source_hashes[f'{scene}/aligned/object_counts.csv'] = sha256(path)
        with path.open(newline='') as handle:
            rows = [r for r in csv.DictReader(handle) if float(r['margin_m']) == 0 and r['category'].startswith('Vehicle')]
        annotations = {}
        for row in rows:
            sync, index = map(int, row['annotation_token'].split(':'))
            if sync not in annotations:
                matches = list((args.dataset_root/scene/'bounding_boxes').glob(f'{sync:04d}_*.json'))
                if len(matches) != 1:
                    raise ValueError('Ambiguous annotation source')
                source = matches[0]
                relative = source.relative_to(args.dataset_root/scene).as_posix()
                digest = sha256(source)
                if digest != run['input_sha256'][relative]:
                    raise ValueError('Annotation hash differs from paired evidence')
                source_hashes[f'{scene}/{relative}'] = digest
                annotations[sync] = json.loads(source.read_text())
            box = annotations[sync][index]
            center = [box[k] for k in ('x', 'y', 'z')]
            if box['class-id'] != row['category'] or not math.isclose(math.hypot(*center[:2]), float(row['range_m'])):
                raise ValueError('Annotation identity/geometry mismatch')
            observations.append(dict(scene=scene, track=scene+':'+row['instance_token'],
                sample=scene+':'+str(sync), center=center, range_m=float(row['range_m'])))
    coverage = []
    for model in models:
        for low, high in [(0,50),(50,100),(100,150),(150,200),(200,250),(250,300),(300,400),(200,400)]:
            rows = [r for r in observations if low <= r['range_m'] < high]
            coverage.append(dict(model=model['name'], band_m=f'{low}-{high}', observations=len(rows),
                tracks=len({r['track'] for r in rows}), scenes=len({r['scene'] for r in rows}),
                centers_inside_xy=sum(in_input_roi(r['center'],model['point_cloud_range']) for r in rows),
                centers_inside_xyz=sum(in_input_roi(r['center'],model['point_cloud_range'],3) for r in rows)))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir/'input_roi_coverage.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=list(coverage[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(coverage)
    result = dict(models=models, source_sha256=source_hashes, scenes=scenes,
        comparison='Released TruckDrive annotation centers, with no learned-model input conversion or inference.',
        boundary='Lower inclusive, upper exclusive; input-ROI coverage is not a bound on regressed prediction centers or detector recall.',
        decision='No verified compatible pretrained radar/LiDAR pair for 200-400 m found in these releases. Do not score short-range checkpoints as long-range detectors.')
    (args.output_dir/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    for row in coverage:
        if row['band_m'] == '200-400': print(row)


if __name__ == '__main__':
    main()
