"""Plot measured support within each dataset; reanalyse saved TruckDrive tables.

TruckDrive raw data is not read by this script. No cross-dataset score ranking.
"""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from compare_truckscenes_raw import LABELS, write_csv

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def markdown_counts(text, heading):
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) == 2 and cells[1].replace(",", "").isdigit():
            rows.append((cells[0], int(cells[1].replace(",", ""))))
    if not rows or len({name for name, _ in rows}) != len(rows):
        raise ValueError("Missing or duplicate source table rows")
    return rows


def save(fig, path):
    fig.tight_layout(rect=(0, .13, 1, 1))
    fig.savefig(path, dpi=150, metadata={"Software": None})
    plt.close(fig)


def main():
    out = EVIDENCE / "truckscenes/object-support"
    rows = read_csv(out / "range_support.csv")
    lookup = {r["band_m"]: r for r in rows}
    bands = [band for band in LABELS if band in lookup]
    fig, ax = plt.subplots(figsize=(9, 5))
    values = [float(lookup[band]["radar_support_percent"]) for band in bands]
    ax.bar(bands, values, color="#326ab4")
    for i, band in enumerate(bands):
        ax.text(i, values[i] + 1, f'{values[i]:.1f}%\nn={int(lookup[band]["box_observations"]):,}', ha="center")
    ax.set(xlabel="Box-centre ego planar range (m)", ylabel="Released boxes with >=1 radar point (%)", ylim=(0, 100),
           title="TruckScenes: radar support of LiDAR-supported annotations")
    fig.text(.02, .025, "25,750 box observations / 400 samples / 10 scenes. Publisher point counts, not detection recall.\n"
             "All released boxes have LiDAR support; repeated instances and annotation selection limit interpretation.", fontsize=9)
    save(fig, out / "radar_object_support.png")

    rows = read_csv(out / "scene_range_support.csv")
    scenes = sorted({r["scene"] for r in rows})
    descriptions = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["scene_descriptions"]
    scene_labels = [f"S{i:02d}: " + ", ".join(tag.split(".", 1)[1] for tag in descriptions[s].split(";")[:2])
                    for i, s in enumerate(scenes, 1)]
    write_csv(out / "scene_legend.csv", [{"label": label, "scene": scene, "description": descriptions[scene]}
                                        for label, scene in zip(scene_labels, scenes)])
    grid = np.full((len(scenes), len(bands)), np.nan)
    for row in rows:
        grid[scenes.index(row["scene"]), bands.index(row["band_m"])] = float(row["radar_support_percent"])
    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(grid, vmin=0, vmax=100, cmap="Blues", aspect="auto")
    for row in rows:
        i, j = scenes.index(row["scene"]), bands.index(row["band_m"])
        ax.text(j, i, f'{float(row["radar_support_percent"]):.1f}% / n={row["box_observations"]}',
                ha="center", va="center", fontsize=8, color="white" if grid[i,j] > 65 else "black")
    ax.set(xticks=range(len(bands)), xticklabels=bands, yticks=range(len(scenes)), yticklabels=scene_labels,
           xlabel="Box-centre ego planar range (m)", title="TruckScenes: radar-supported annotation share by scene and range")
    fig.colorbar(im, ax=ax, label="Released boxes with radar support (%)")
    fig.text(.02, .03, "Each cell shows share / box-observation denominator. Blank means no annotations.\n"
             "Scene, weather, road and class composition are confounded; this is not a weather-robustness test.", fontsize=9)
    save(fig, out / "scene_support.png")

    out = EVIDENCE / "goose/range-support"
    rows = [r for r in read_csv(out / "traversability_ranges.csv") if r["scenario"] == "ALL"]
    groups = sorted({r["group"] for r in rows})
    fig, ax = plt.subplots(figsize=(11, 5))
    bottom = np.zeros(len(LABELS))
    for group, color in zip(groups, ["#888888", "#d95f02", "#7570b3", "#1b9e77"]):
        by_band = {r["band_m"]: r for r in rows if r["group"] == group}
        counts = np.array([int(by_band[b]["points"]) for b in LABELS])
        denominators = np.array([int(by_band[b]["all_points_in_band"]) for b in LABELS])
        values = np.divide(100.0 * counts, denominators, out=np.zeros(len(LABELS)), where=denominators > 0)
        ax.bar(LABELS, values, bottom=bottom, label=group, color=color)
        bottom += values
    ax.set(xlabel="Released LiDAR planar range (m); >=400 m has no points", ylabel="Share of labelled points in each range band (%)",
           title="GOOSE: semantic labels grouped by the project's traversability map", ylim=(0, 105))
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    fig.text(.02, .025, "961 frames / 8 scenarios / 174,891,807 points. Each band uses its own point denominator.\n"
             "Ground-truth remap, not model accuracy or verified driveability. No paired radar analysis.", fontsize=9)
    save(fig, out / "traversability_by_range.png")

    source = ROOT / "TruckDrive - Kelsey/dataset-statistics.md"
    text = source.read_text(encoding="utf-8")
    bands = markdown_counts(text, "## 4. Radar range distribution")
    classes = markdown_counts(text, "## 2. Object class distribution")
    if sum(n for _, n in bands) != 71206 or sum(n for _, n in classes) != 526148:
        raise ValueError("TruckDrive source denominators changed; review before comparing")
    out = EVIDENCE / "truckdrive_/saved-comparison"
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "radar_ranges.csv", [{"band_m": b, "returns": n, "denominator": 71206,
               "percent": 100*n/71206, "selected_frames": 24, "source": source.relative_to(ROOT).as_posix()} for b,n in bands])
    write_csv(out / "class_counts.csv", [{"class": b, "box_observations": n, "denominator": 526148,
               "percent": 100*n/526148, "annotated_frames": 4800} for b,n in classes])
    manifest = {"input": source.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "status": "Reanalysis of committed teammate tables; raw data not reproduced on this machine",
                "raw_download_status": "Hugging Face account access confirmed; Chrome blocked file host with ERR_BLOCKED_BY_CLIENT",
                "sampling": "First shared radar/annotation sync ID in each of 24 scenes; not all 12502 radar frames",
                "coordinate_frame": "Original joint-radar frame from source script; not common ego aligned",
                "paired_lidar_ranges": "Unavailable in the committed evidence",
                "selection_bias": "scene_28_22 was selected after observing the highest distant-return count"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([b for b,n in bands], [100*n/71206 for b,n in bands], color="#326ab4")
    ax.set(xlabel="Planar range in source joint-radar frame", ylabel="Share of 71,206 selected-frame returns (%)",
           title="TruckDrive: committed 24-frame radar evidence")
    fig.text(.02, .025, "One first annotated radar frame per scene. Source: Kelsey's committed statistics, reaggregated here.\n"
             "Raw data not reproduced locally; no matching LiDAR range table or detection model scores.", fontsize=9)
    save(fig, out / "radar_ranges.png")


if __name__ == "__main__":
    main()
