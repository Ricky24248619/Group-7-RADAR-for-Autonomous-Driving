"""Plot RADAR vs LiDAR range-band coverage from the committed range-bands CSV.

FA-S3-1. This script reads `TruckScenes - Fatima/range-bands.csv` and plots
what is already in it. It never opens the dataset and never recomputes a
count, so a figure can always be traced back to a committed number.

Two figures, because the two questions need different scales:

  1. Share of each modality's returns per band. Both modalities share one
     0-100% axis, which is the only fair common scale for a paired
     comparison here -- the two sensors produce very different numbers of
     returns, so raw counts on one linear axis would flatten the smaller
     series into the baseline.

  2. Absolute counts per band, on a shared logarithmic axis. Drawn as
     markers rather than bars: a bar encodes magnitude by length from zero,
     and a log axis has no meaningful zero, so log bars would misstate every
     value. Markers only encode position, which a log axis supports.

WHAT THE FIGURES SHOW: how many sensor returns fall in each distance band.
That is coverage. It is not object-detection accuracy, and the denser
modality is not the better one. No detection model has been run.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "TruckScenes - Fatima" / "range-bands.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "evidence" / "truckscenes"

SHARE_FIGURE = "range_bands_share.png"
COUNT_FIGURE = "range_bands_counts.png"

NO_DATA = "no data"

# Validated two-colour categorical pair: adjacent-pair CVD separation 28.3
# (protan) and 33.5 for normal vision, both well above the required floors.
# Assigned to a fixed modality, never cycled.
MODALITY_COLOURS = {"radar": "#3B6FD6", "lidar": "#D97706"}
MODALITY_LABELS = {"radar": "RADAR", "lidar": "LiDAR"}
PLOT_ORDER = ["radar", "lidar"]

INK = "#22201d"
MUTED_INK = "#6b6660"
GRID = "#dcd9d4"
SURFACE = "#fcfcfb"

# Matplotlib stamps the current date into a PNG by default, which would make
# every regeneration a different file. Stripping it keeps the figures
# reproducible, the same way the CSVs are.
PNG_METADATA = {"Software": None, "Date": None}


class PlotError(Exception):
    """Raised when the CSV cannot be plotted as it stands."""


def read_rows(path):
    if not path.exists():
        raise PlotError(
            f"{path} not found. Run scripts/truckscenes_range_bands.py first."
        )
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def aggregate_series(rows, modality):
    """Pull one modality's aggregate rows out of the CSV, in CSV band order.

    Returns the band labels, the counts, the shares, the denominator and the
    number of samples behind them -- everything a figure has to state.

    Bands whose count reads "no data" are kept in the band list with a value
    of None, so a gap stays a visible gap rather than being drawn as zero.
    """
    selected = [
        row
        for row in rows
        if row["scope"] == "aggregate" and row["modality"] == modality
    ]
    if not selected:
        raise PlotError(f"No aggregate rows for modality '{modality}' in the CSV.")

    labels = [row["band_label"] for row in selected]
    counts = [None if row["point_count"] == NO_DATA else int(row["point_count"]) for row in selected]
    shares = [
        None
        if row["proportion_of_denominator"] == NO_DATA
        else float(row["proportion_of_denominator"]) * 100.0
        for row in selected
    ]

    denominators = {row["denominator_points"] for row in selected}
    sample_counts = {row["sample_count"] for row in selected}
    if len(denominators) != 1 or len(sample_counts) != 1:
        raise PlotError(
            f"Aggregate rows for '{modality}' disagree on denominator or sample count."
        )

    denominator = denominators.pop()
    return {
        "labels": labels,
        "counts": counts,
        "shares": shares,
        "denominator": None if denominator == NO_DATA else int(denominator),
        "sample_count": int(sample_counts.pop()),
        "channel": selected[0]["channel"],
    }


def check_bands_match(series_by_modality):
    """Two series can only share an axis if they use the same bands."""
    band_sets = {tuple(series["labels"]) for series in series_by_modality.values()}
    if len(band_sets) != 1:
        raise PlotError("Modalities use different band labels; they cannot share an axis.")


def subtitle_for(series_by_modality):
    """One line naming the sample count, channels and denominators."""
    parts = []
    for modality in PLOT_ORDER:
        series = series_by_modality[modality]
        denominator = "no data" if series["denominator"] is None else f"{series['denominator']:,}"
        # The channel name already says which modality it is, so naming both
        # would read "RADAR RADAR_LEFT_FRONT".
        parts.append(f"{series['channel']}: {denominator} returns")
    samples = series_by_modality[PLOT_ORDER[0]]["sample_count"]
    return f"{samples} matched samples  ·  " + "  ·  ".join(parts)


FOOTER = (
    "Counts are sensor returns per distance band — coverage, not detection accuracy. "
    "No detection model has been run.\n"
    "Range is measured in each sensor's own frame, so the two modalities are measured "
    "from different positions on the truck.\n"
    "One radar channel and one LiDAR channel out of six each; see RANGE-BANDS.md for limits."
)


def style_axes(ax):
    """Recessive grid and axes so the data is the loudest thing on the figure."""
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(GRID)
    ax.tick_params(colors=MUTED_INK, labelsize=9)


def plot_shares(series_by_modality, path):
    """Grouped bars: what share of each modality's returns sits in each band."""
    labels = series_by_modality[PLOT_ORDER[0]]["labels"]
    positions = range(len(labels))
    width = 0.38

    figure, ax = plt.subplots(figsize=(9, 5.2))
    style_axes(ax)

    for index, modality in enumerate(PLOT_ORDER):
        series = series_by_modality[modality]
        offsets = [position + (index - 0.5) * width for position in positions]
        values = [0.0 if share is None else share for share in series["shares"]]
        ax.bar(
            offsets,
            values,
            width=width - 0.02,  # 2px-equivalent gap between adjacent fills
            color=MODALITY_COLOURS[modality],
            label=series["channel"],
            zorder=3,
        )
        for offset, share in zip(offsets, series["shares"]):
            text = "no data" if share is None else f"{share:.2f}%"
            ax.annotate(
                text,
                (offset, 0.0 if share is None else share),
                textcoords="offset points",
                xytext=(0, 4),
                ha="center",
                fontsize=8,
                color=MUTED_INK,  # text wears ink, never the series colour
            )

    ax.set_xticks(list(positions))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Share of that modality's returns (%)", color=INK, fontsize=10)
    ax.set_xlabel("Distance band (range in sensor frame)", color=INK, fontsize=10)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc="upper right")

    finish(figure, ax, "Where each sensor's returns fall, by distance band",
           subtitle_for(series_by_modality), path)


def plot_counts(series_by_modality, path):
    """Markers on a shared log axis: how many returns, not what share."""
    labels = series_by_modality[PLOT_ORDER[0]]["labels"]
    positions = list(range(len(labels)))

    figure, ax = plt.subplots(figsize=(9, 5.2))
    style_axes(ax)

    for index, modality in enumerate(PLOT_ORDER):
        series = series_by_modality[modality]
        offsets = [position + (index - 0.5) * 0.18 for position in positions]
        drawn_y, drawn_x = [], []
        for offset, count in zip(offsets, series["counts"]):
            if count is None or count == 0:
                # A hollow mark in the series colour carries identity; the
                # label stays in ink. Without it, a bare "0" at the axis
                # cannot be attributed to either sensor.
                ax.scatter(
                    [0.62],
                    [offset],
                    s=64,
                    facecolors="none",
                    edgecolors=MODALITY_COLOURS[modality],
                    linewidths=1.6,
                    zorder=3,
                )
                ax.annotate(
                    "no data" if count is None else "0",
                    (0.62, offset),
                    textcoords="offset points",
                    xytext=(9, 0),
                    ha="left",
                    va="center",
                    fontsize=8,
                    color=MUTED_INK,
                )
                continue
            drawn_y.append(offset)
            drawn_x.append(count)
            ax.annotate(
                f"{count:,}",
                (count, offset),
                textcoords="offset points",
                xytext=(9, 0),
                va="center",
                fontsize=8,
                color=MUTED_INK,
            )
        ax.scatter(
            drawn_x,
            drawn_y,
            s=64,
            color=MODALITY_COLOURS[modality],
            label=series["channel"],
            zorder=3,
            edgecolors=SURFACE,
            linewidths=1.5,  # surface ring, so overlapping marks stay readable
        )

    ax.set_yticks(positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlim(0.5, 10 ** 6)
    ax.set_xlabel("Returns in band (log scale; bands with none are labelled)", color=INK, fontsize=10)
    ax.set_ylabel("Distance band (range in sensor frame)", color=INK, fontsize=10)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc="lower right")

    finish(figure, ax, "How many returns each sensor produced, by distance band",
           subtitle_for(series_by_modality), path)


def finish(figure, ax, title, subtitle, path):
    """Title, subtitle, footer and a reproducible save."""
    ax.set_title(title, color=INK, fontsize=13, loc="left", pad=26, fontweight="bold")
    ax.annotate(
        subtitle,
        (0, 1),
        xycoords="axes fraction",
        textcoords="offset points",
        xytext=(0, 8),
        fontsize=9,
        color=MUTED_INK,
    )
    figure.text(0.01, 0.01, FOOTER, fontsize=7.5, color=MUTED_INK, va="bottom")
    figure.tight_layout(rect=(0, 0.12, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=200, facecolor=SURFACE, metadata=PNG_METADATA)
    plt.close(figure)


def build_figures(rows, output_dir):
    series_by_modality = {
        modality: aggregate_series(rows, modality) for modality in PLOT_ORDER
    }
    check_bands_match(series_by_modality)

    share_path = output_dir / SHARE_FIGURE
    count_path = output_dir / COUNT_FIGURE
    plot_shares(series_by_modality, share_path)
    plot_counts(series_by_modality, count_path)
    return series_by_modality, [share_path, count_path]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        rows = read_rows(args.csv)
        series_by_modality, paths = build_figures(rows, args.output_dir)
    except PlotError as error:
        raise SystemExit(str(error))

    samples = series_by_modality[PLOT_ORDER[0]]["sample_count"]
    print(f"plotted {len(rows)} CSV row(s) from {args.csv.name}")
    print(f"{samples} matched sample(s); no dataset was read")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
