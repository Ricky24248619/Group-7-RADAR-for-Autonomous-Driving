"""Freeze unseen GOOSE frames before a bounded attention-context follow-up.

One interior-third frame per recording, excluding the January tuning recording.
Run in WSL; raw data and fresh inference directories remain outside Git.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TUNING = "2023-01-20_aying_mangfall_2"


def unseen_index(length, excluded_indices):
    if length < 3:
        raise ValueError("Need an interior frame")
    index = length // 3
    while index in excluded_indices and index < length - 1:
        index += 1
    if index >= length - 1:
        raise ValueError("No unseen interior frame after the first third")
    return index


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--subset", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.subset.exists():
        raise ValueError("Use a fresh subset directory")
    earlier = [ROOT / "docs/evidence/goose-stratified/selection.json",
               ROOT / "docs/evidence/goose-failure-causes/selection.json",
               ROOT / "docs/evidence/missing-support/goose-saved/manifest.json"]
    used = set()
    sources = {}
    for path in earlier:
        sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        used.update(row["frame"] for row in json.loads(path.read_text())["inputs"])
    selected = []
    for scenario in sorted((args.root / "lidar/val").iterdir()):
        if not scenario.is_dir() or scenario.name == TUNING:
            continue
        scans = sorted(scenario.glob("*.bin"))
        index = unseen_index(len(scans), {i for i, p in enumerate(scans) if p.name in used})
        scan = scans[index]
        label_name = scan.name.replace("_vls128.bin", "_goose.label")
        paths = {"scan": scan, "label": args.root / "labels/val" / scenario.name / label_name,
                 "challenge_label": args.root / "labels_challenge/val" / scenario.name / label_name}
        sizes = [paths[key].stat().st_size // width for key, width in
                 (("scan", 16), ("label", 4), ("challenge_label", 4))]
        if len(set(sizes)) != 1 or sizes[0] <= 0 or any(paths[k].stat().st_size % w for k, w in
                 (("scan", 16), ("label", 4), ("challenge_label", 4))):
            raise ValueError("Mismatched selected scan/labels")
        row = dict(frame=scan.name, scenario=scenario.name, index=index,
                   scenario_frames=len(scans), points=sizes[0],
                   sha256={key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()})
        selected.append(row)
        for key, folder in (("scan", "lidar"), ("label", "labels"), ("challenge_label", "labels_challenge")):
            target = args.subset / folder / "val" / scenario.name / paths[key].name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(paths[key].resolve())
    if len(selected) != 7 or any(row["frame"] in used for row in selected):
        raise ValueError("Expected seven unseen frames, excluding the tuning recording")
    record = dict(selection="Sorted filenames: floor(N/3), advance only past previously evaluated IDs; no outcome-based selection",
                  excluded_tuning_recording=TUNING, excluded_previously_evaluated_frames=len(used),
                  frames=len(selected), points=sum(row["points"] for row in selected), inputs=selected,
                  earlier_manifest_sha256=sources,
                  earlier_manifest_hash_definition="Repository UTF-8 text with LF endings",
                  scope="Unseen frames in seven existing validation recordings; recordings are not independent of earlier characterization. Not full validation.")
    args.output.mkdir(parents=True, exist_ok=True)
    for destination in (args.subset / "selection.json", args.output / "selection.json"):
        destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: record[k] for k in ("frames", "points", "scope")}, indent=2))


if __name__ == "__main__":
    main()
