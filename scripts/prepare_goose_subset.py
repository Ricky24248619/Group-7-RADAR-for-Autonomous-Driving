"""Create a deterministic, scenario-stratified GOOSE inference subset (symlinks).

Run in WSL with the existing Pointcept environment. Selection uses filename
order and interior quantiles, never labels, predictions, or point counts.
"""
import argparse
import hashlib
import json
from pathlib import Path


def interior_indices(length, count):
    if count < 1 or length < count:
        raise ValueError('Need at least count frames and a positive count')
    return [(i + 1) * length // (count + 1) for i in range(count)]


def neighbor_indices(scans, center):
    matches=[i for i,p in enumerate(scans) if p.name==center]
    if len(matches)!=1 or matches[0]==0 or matches[0]==len(scans)-1:
        raise ValueError('Center must uniquely match an interior frame')
    i=matches[0]
    return [i-1,i,i+1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--per-scenario', type=int, default=3)
    parser.add_argument('--center-frame',help='Diagnostic mode: this exact frame plus one validation neighbor on either side')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new subset directory; preserve earlier evidence')
    selected = []
    scenarios = sorted((args.root / 'lidar' / 'val').iterdir())
    if args.center_frame:
        matches=[p for p in (args.root/'lidar'/'val').glob('*/*.bin') if p.name==args.center_frame]
        if len(matches)!=1:raise ValueError('Center frame must uniquely identify a scan')
        scenarios=[matches[0].parent]
    for scenario in scenarios:
        if not scenario.is_dir():
            continue
        scans = sorted(scenario.glob('*.bin'))
        indices=neighbor_indices(scans,args.center_frame) if args.center_frame else interior_indices(len(scans), args.per_scenario)
        for index in indices:
            scan = scans[index]
            label_name = scan.name.replace('.bin', '.label').replace('vls128', 'goose').replace('_pcl.', '_goose.')
            paths = {'scan': scan,
                     'label': args.root / 'labels' / 'val' / scenario.name / label_name,
                     'challenge_label': args.root / 'labels_challenge' / 'val' / scenario.name / label_name}
            if not all(p.is_file() for p in paths.values()):
                raise ValueError(f'Missing paired labels: {scan.name}')
            sizes = [paths[k].stat().st_size // size for k, size in [('scan',16), ('label',4), ('challenge_label',4)]]
            if (len(set(sizes)) != 1 or sizes[0] == 0 or
                any(paths[k].stat().st_size % size for k,size in [('scan',16),('label',4),('challenge_label',4)])):
                raise ValueError(f'Point/label count mismatch: {scan.name}')
            selected.append(dict(frame=scan.name, scenario=scenario.name, index=index,
                                 scenario_frames=len(scans), points=sizes[0],
                                 paths=paths, sha256={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}))
    if not selected:
        raise ValueError('No validation scenarios')
    for entry in selected:
        for key, folder in [('scan','lidar'),('label','labels'),('challenge_label','labels_challenge')]:
            source = entry['paths'][key]
            target = args.output / folder / 'val' / entry['scenario'] / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(source.resolve())
        del entry['paths']
    policy=('Post-hoc diagnostic center plus immediately preceding/following validation scans in sorted filename order' if args.center_frame else
            'Sorted scenario filenames; index floor(k*N/(n+1)), k=1..n; selected before inference')
    manifest = dict(selection=policy,center_frame=args.center_frame,
                    per_scenario=args.per_scenario, frames=len(selected), points=sum(e['points'] for e in selected),
                    inputs=selected)
    (args.output/'selection.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='inputs'},indent=2))


if __name__ == '__main__':
    main()
