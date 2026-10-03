"""Observed terrain geometry and sensor evidence; no autonomy or safety score.

Uses saved GOOSE predictions and existing paired sensor tables. Relative z,
semantic candidate ground, and observed-map footprints are diagnostics only.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from analyse_p3_p4_road import episodes
from analyse_p3_p4_terrain import policy_groups
from compare_truckscenes_raw import write_csv
from goose_render_frame import find_frames, load_frame

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def text_sha(path):
    return hashlib.sha256(path.read_text(encoding='utf-8').encode()).hexdigest()


def surface_planes(xyz, candidate, size):
    """Batched covariance planes; insufficient/line-like references stay unknown."""
    xyz = np.asarray(xyz, dtype=float)
    candidate = np.asarray(candidate, dtype=bool)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or len(candidate) != len(xyz) or size <= 0 or not np.isfinite(xyz).all():
        raise ValueError('Invalid surface points')
    cells, inverse = np.unique(np.floor(xyz[candidate, :2]/size).astype(np.int64), axis=0, return_inverse=True)
    if len(cells) == 0:
        return dict(candidate_cells=0, sparse_cells=0, line_like_cells=0, eligible_cells=0,
                    rms_le_002=0, rms_002_005=0, rms_gt_005=0, rms_max_m=None)
    points = xyz[candidate]
    count = np.bincount(inverse)
    mean = np.column_stack([np.bincount(inverse, weights=points[:, k])/count for k in range(3)])
    delta = points-mean[inverse]
    covariance = np.empty((len(count), 3, 3))
    for j in range(3):
        for k in range(3):
            covariance[:, j, k] = np.bincount(inverse, weights=delta[:, j]*delta[:, k])/count
    eigenvalues = np.maximum(np.linalg.eigvalsh(covariance), 0)
    eligible = (count >= 5) & (eigenvalues[:, 1] >= .0025)
    rms = np.sqrt(eigenvalues[eligible, 0])
    return dict(candidate_cells=len(cells), sparse_cells=int((count < 5).sum()),
                line_like_cells=int(((count >= 5)&(eigenvalues[:, 1] < .0025)).sum()),
                eligible_cells=int(eligible.sum()), rms_le_002=int((rms <= .02).sum()),
                rms_002_005=int(((rms > .02)&(rms <= .05)).sum()), rms_gt_005=int((rms > .05).sum()),
                rms_max_m=float(rms.max()) if len(rms) else None)


def footprint_counts(candidate, hazard, radius_cells):
    """Count all touched square cells; missing map support is never treated free."""
    candidate = np.asarray(candidate, dtype=bool)
    hazard = np.asarray(hazard, dtype=bool)
    if candidate.shape != hazard.shape or candidate.ndim != 2 or radius_cells < 0 or not isinstance(radius_cells, int):
        raise ValueError('Invalid footprint maps')
    clear = candidate & ~hazard
    retained = np.ones_like(clear)
    touched_hazard = np.zeros_like(clear)
    pad = radius_cells
    padded_clear = np.pad(clear, pad, constant_values=False)
    padded_hazard = np.pad(hazard, pad, constant_values=False)
    nx, ny = clear.shape
    for dx in range(2*pad+1):
        for dy in range(2*pad+1):
            retained &= padded_clear[dx:dx+nx, dy:dy+ny]
            touched_hazard |= padded_hazard[dx:dx+nx, dy:dy+ny]
    retained &= clear
    lost_hazard = clear & touched_hazard
    lost_support = clear & ~retained & ~touched_hazard
    return dict(candidate_centres=int(clear.sum()), retained_footprints=int(retained.sum()),
                lost_to_hazard=int(lost_hazard.sum()), lost_to_missing_or_uncertain_support=int(lost_support.sum()))


def map_counts(xyz, groups, size, radius=25):
    limit = int(np.ceil(radius/size))
    dimension = 2*limit+1
    axis = (np.arange(-limit, limit+1)+.5)*size
    roi = np.hypot(axis[:, None], axis[None, :]) <= radius
    candidate = np.zeros((dimension, dimension), dtype=bool)
    hazard = np.zeros_like(candidate)
    observed = np.zeros_like(candidate)
    cells = np.floor(xyz[:, :2]/size).astype(np.int64)+limit
    keep = np.all((cells >= 0)&(cells < dimension), axis=1)
    ix, iy = cells[keep].T
    observed[ix, iy] = True
    selected = np.asarray(groups)[keep]
    candidate[ix[selected == 1], iy[selected == 1]] = True
    hazardous = np.isin(selected, (3, 5))
    hazard[ix[hazardous], iy[hazardous]] = True
    candidate &= roi
    hazard &= roi
    rows = []
    for width in (.5, 1.5, 2.5):
        # Conservative cell-centred square footprint includes boundary cells.
        r = max(0, int(np.ceil((width/size-1)/2)))
        rows.append(dict(requested_width_m=width, radius_cells=r, effective_width_m=(2*r+1)*size,
                         roi_cells=int(roi.sum()), observed_roi_cells=int((observed&roi).sum()),
                         unknown_roi_cells=int((~observed&roi).sum()), **footprint_counts(candidate, hazard, r)))
    return rows


def terrain(args):
    from scipy.spatial import cKDTree
    manifest_path = ROOT/'results/evidence/p3-p4-oct03/terrain_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    mapping = list(csv.DictReader((ROOT/'GOOSE - Ricky+Damien/traversability_map.csv').open(encoding='utf-8-sig')))
    lut = policy_groups(mapping)
    scans = {s.name:(s, l) for s, l in find_frames(args.goose_root)}
    inputs, references, heights, columns, shapes, footprints = [], [], [], [], [], []
    seen = set()
    for entry in manifest['goose_inputs']:
        if entry['kind'] != 'paired_frame' or entry['variant'] not in ('stratified24', 'p64'):
            continue
        frame = entry['frame']
        if frame in seen:
            raise ValueError('Repeated source frame needs an explicit cohort decision')
        seen.add(frame)
        scan, label = scans[frame]
        pred_path = (args.original_predictions if entry['variant']=='stratified24' else args.followup_predictions/'p64/result')/(frame+'_pred.npy')
        for kind, path in [('scan', scan), ('label', label), ('prediction', pred_path)]:
            if sha(path) != entry['sha256'][kind]:
                raise ValueError('Changed source: '+frame+'/'+kind)
        points, raw = load_frame(scan, label)
        xyz = points[:, :3].astype(float)
        pred = np.load(pred_path, allow_pickle=False)
        if not np.isfinite(xyz).all() or not np.isin(raw, range(64)).all() or len(pred) != len(raw):
            raise ValueError('Invalid source points or predictions')
        groups = lut[raw]
        in_range = np.hypot(xyz[:, 0], xyz[:, 1]) <= 25
        target = np.flatnonzero(in_range & np.isin(groups, (3, 5)))
        ground = np.flatnonzero(groups == 1)
        distance = np.full(len(target), np.inf)
        delta = np.full(len(target), np.nan)
        if len(ground):
            distance, nearest = cKDTree(xyz[ground, :2]).query(xyz[target, :2], k=1)
            delta = xyz[target, 2]-xyz[ground[nearest], 2]
        base = dict(frame=frame, recording=scan.parent.name, source_variant=entry['variant'])
        for kind, ids in [('rigid', groups[target]==3), ('vegetation', groups[target]==5)]:
            for cutoff in (1, 2):
                valid = ids & (distance <= cutoff)
                cell_ids = np.floor(xyz[target, :2]/.5).astype(np.int64)
                def cell_set(mask):
                    return set(map(tuple, cell_ids[mask].tolist()))
                all_columns = cell_set(ids)
                resolved_columns = cell_set(valid)
                for ceiling in (2, 3):
                    body_columns = cell_set(valid & (delta >= .2) & (delta < ceiling))
                    high_columns = cell_set(valid & (delta >= ceiling))
                    unresolved_columns = cell_set(ids & ~valid)
                    columns.append(dict(**base, kind=kind, cutoff_m=cutoff, diagnostic_ceiling_m=ceiling,
                        any_height_columns=len(all_columns), resolved_reference_columns=len(resolved_columns),
                        body_window_columns=len(body_columns), high_columns=len(high_columns),
                        high_without_body_columns=len(high_columns-body_columns),
                        unresolved_reference_columns=len(unresolved_columns),
                        high_without_body_or_unresolved_columns=len(high_columns-body_columns-unresolved_columns)))
                references.append(dict(**base, kind=kind, cutoff_m=cutoff, hazard_points=int(ids.sum()),
                                       resolved_points=int(valid.sum()), unresolved_points=int((ids&~valid).sum())))
                bands = ((-np.inf,-.2,'below_reference'),(-.2,.2,'near_reference'),(.2,.5,'0.2-0.5'),
                         (.5,1,'0.5-1'),(1,2,'1-2'),(2,3,'2-3'),(3,np.inf,'above_3'))
                for lo, hi, name in bands:
                    selected = valid & (delta >= lo) & (delta < hi)
                    heights.append(dict(**base, kind=kind, cutoff_m=cutoff, delta_z_band_m=name,
                                        points=int(selected.sum()), called_ground=int(np.isin(pred[target[selected]],(2,3)).sum()),
                                        xy_columns_05m=len(np.unique(np.floor(xyz[target[selected],:2]/.5).astype(int),axis=0))))
        for size in (.5, 1):
            shapes.append(dict(**base, cell_size_m=size, **surface_planes(xyz[in_range],groups[in_range]==1,size)))
            for row in map_counts(xyz,groups,size):
                footprints.append(dict(**base,cell_size_m=size,**row))
        inputs.append(dict(**base,sha256=entry['sha256']))
        print('P5 terrain',len(seen),frame,flush=True)
    return (
        {'ground_reference.csv': references, 'relative_height.csv': heights, 'height_columns.csv': columns, 'surface_shape.csv': shapes,
         'vehicle_footprint.csv': footprints}, dict(prior_terrain_manifest_sha256_lf=text_sha(manifest_path),frames=inputs))


def sensors(args):
    source = ROOT/'docs/evidence/truckscenes/paired-point-motion-support'
    manifest = json.loads((source/'manifest.json').read_text())
    sources = {}
    metadata = {}
    for name in ('sample_annotation','visibility'):
        path = args.truckscenes_root/'v1.2-mini'/(name+'.json')
        if sha(path) != manifest['metadata_sha256'][name+'.json']:
            raise ValueError('Changed metadata: '+name)
        sources['external:'+name+'.json'] = sha(path)
        metadata[name] = {r['token']:r for r in json.loads(path.read_text())}
    rows = list(csv.DictReader((source/'object_counts.csv').open(encoding='utf-8-sig')))
    old = json.loads((ROOT/'results/evidence/p3-p4-oct03/road_manifest.json').read_text())
    key = str((source/'object_counts.csv').relative_to(ROOT)).replace('\\','/')
    if text_sha(source/'object_counts.csv') != old['source_sha256'][key]:
        raise ValueError('Changed paired counts')
    sources[key] = text_sha(source/'object_counts.csv')
    grouped = defaultdict(list)
    for row in rows:
        if float(row['margin_m']) != 0:
            continue
        ann = metadata['sample_annotation'][row['annotation_token']]
        if ann['sample_token'] != row['sample_token'] or ann['instance_token'] != row['instance_token']:
            raise ValueError('Annotation identity mismatch')
        level = metadata['visibility'][ann['visibility_token']]['level']
        distance = float(row['range_m'])
        band = '0-25' if distance < 25 else '25-50' if distance < 50 else '50-100' if distance < 100 else '100+'
        grouped[row['category'], band, level].append(row)
    visibility = []
    for (category,band,level),group in sorted(grouped.items()):
        for threshold in (1,3):
            visibility.append(dict(category=category,band_m=band,camera_visibility_level=level,threshold=threshold,
                 observations=len(group),tracks=len({(r['scene'],r['instance_token']) for r in group}),
                 recordings=len({r['scene'] for r in group}),
                 lidar=sum(int(r['lidar_points'])>=threshold for r in group),
                 radar=sum(int(r['radar_points'])>=threshold for r in group),
                 neither=sum(int(r['lidar_points'])<threshold and int(r['radar_points'])<threshold for r in group)))
    fog = []
    for kind,filename in [('target','observations.csv'),('unlabelled_control','unlabelled_controls.csv')]:
        path=ROOT/'docs/evidence/radiate-fog'/filename
        sources[str(path.relative_to(ROOT)).replace('\\','/')] = text_sha(path)
        data=list(csv.DictReader(path.open(encoding='utf-8-sig')))
        if kind=='target': data=[r for r in data if float(r['margin_m'])==0]
        groups=defaultdict(list)
        for row in data:
            frame=int(row['frame'])
            if not 1<=frame<=17:raise ValueError('Unexpected fog frame')
            row.update(position=frame,time_s=frame)
            groups[row['track'] if kind=='target' else (row['parent_track'],row['angle_deg'])].append(row)
        for group,data in sorted(groups.items()):
            for gap,field in [(0,'radar_contrast_pass'),(10,'radar_contrast_gap10'),(20,'radar_contrast_gap20')]:
                runs=episodes(data,lambda r:int(r[field])==1,1)
                fog.append(dict(kind=kind,footprint=str(group),gap=gap,observations=len(data),
                                positive=sum(int(r[field]) for r in data),persistent_runs=sum(len(r)>=3 for r in runs),
                                maximum_run=max(map(len,runs),default=0)))
    return {'camera_visibility.csv':visibility,'fog_background.csv':fog},sources


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--goose-root',type=Path,required=True)
    parser.add_argument('--original-predictions',type=Path,required=True)
    parser.add_argument('--followup-predictions',type=Path,required=True)
    parser.add_argument('--truckscenes-root',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    output,terrain_sources=terrain(args)
    sensor_output,sensor_sources=sensors(args)
    output.update(sensor_output)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,rows in output.items():write_csv(args.output_dir/name,rows)
    manifest=dict(terrain_sources=terrain_sources,sensor_sources_sha256=sensor_sources,
                  output_sha256_lf={name:text_sha(args.output_dir/name) for name in output},new_gpu_runs=0,
                  method='Fixed <=25m terrain point cohort; ground-reference cutoffs 1/2m; map/plane cells 0.5/1m; frozen footprint widths 0.5/1.5/2.5m.',
                  limits=['31 selected frames from eight recordings, not a full benchmark',
                          'Candidate ground is provisional semantic policy; no physical passability truth',
                          'Raw sensor-frame delta-z is not gravity-aligned object height or clearance',
                          'Orthogonal plane RMS is measured local shape, not grip, grade or traversability',
                          'Footprints use all touched square map cells, no vehicle kinematics or route',
                          'Unobserved/uncertain map support never counted free',
                          'Camera visibility metadata does not measure sensor-specific visibility',
                          'Fog controls are unlabelled, not confirmed empty; no recognition score'])
    (args.output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__': main()
