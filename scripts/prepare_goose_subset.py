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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--per-scenario', type=int, default=3)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new subset directory; preserve earlier evidence')
    selected = []
    scenarios = sorted((args.root / 'lidar' / 'val').iterdir())
    for scenario in scenarios:
        if not scenario.is_dir():
            continue
        scans = sorted(scenario.glob('*.bin'))
        for index in interior_indices(len(scans), args.per_scenario):
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
    manifest = dict(selection='Sorted scenario filenames; index floor(k*N/(n+1)), k=1..n; selected before inference',
                    per_scenario=args.per_scenario, frames=len(selected), points=sum(e['points'] for e in selected),
                    inputs=selected)
    (args.output/'selection.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='inputs'},indent=2))


if __name__ == '__main__':
    main()
