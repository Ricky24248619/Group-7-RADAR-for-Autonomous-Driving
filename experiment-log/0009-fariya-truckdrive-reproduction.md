# EXP-0009 — TruckDrive reproduction and viewer verification

> Review update, 11 September: integrated Fariya's 6 September branch, corrected
> Markdown/copyable commands and moved the log to the next free number. The
> observations below are Fariya's report; this review did not run her environment
> or download the dataset. The NumPy/SciPy warning and empty camera channels remain
> unresolved. The 87-box observation has no recorded frame scope and must not be
> treated as a scene total or detection score.

- **Date started / completed:** 2026-09-05 / 2026-09-06
- **Owner:** Fariya
- **Workstream / story:** TruckDrive dataset exploration (reproducing Kelsey's setup) → TruckDrive visualisation and documentation (Epic A / WS5)

## Goal

Reproduce Kelsey's TruckDrive setup on a second machine to confirm it's repeatable,
then move into the visualisation and documentation stage she handed off.

## Environment

- Windows
- Python 3.12.4 (note: differs from Kelsey's 3.11.11 — no issues encountered so far)
- Python venv: `truckdrive_visualizer` (used venv instead of conda, not installed locally)
- NumPy 1.26.4
- Open3D 0.19.0
- PyQt5 5.15.11
- Pillow, matplotlib, imageio, pyquaternion, scipy (additional deps required by
  `dataset_viewer/pyproject.toml`, not listed in Kelsey's original environment notes)
- Data source: TruckDrive Hugging Face repo (`Torc-Robotics/TruckDrive`), downloaded via
  `download_truckdrive.py` after accepting the Torc non-commercial license and
  authenticating via `hf auth login`
- Raw data stored outside the Git repo, on a separate local drive (G:)

## Dataset / data subset

- `scene_28_1`, full multimodal download (camera, LiDAR, radar, poses, calibrations,
  annotations) — 7.86 GB downloaded, ~10.2 GB raw before compression

## Steps and commands

```powershell
python download_truckdrive.py --out "G:\TruckDrive-data\TruckDrive" --scene scene_28_1 --all-modalities
python entrypoint.py --root-dir "G:\TruckDrive-data\TruckDrive\TruckDrive" --recording scene_28_1
```

## Outcome

- [x] Success — worked as intended, with one setup fix required (see below)

Reported sensor and annotation counts:
- 260 Aeva LiDAR frames, 258–260 Ouster frames (×3 orientations)
- 521 Radar frames
- 259–260 images per populated camera angle; some angles show 0 frames. Whether
  this reflects missing downloads, folder layout or the capture is not yet confirmed.
- 87 bounding boxes loaded from JSON
- 20 lane-line JSON files loaded
- Fused `all_3d` point cloud rendered successfully: 545,829 points across LiDAR + radar
- 2D camera view with bounding-box overlay rendered. A box triggered
  `x1 must be greater than or equal to x0` in the 2D draw call; rendering continued,
  but the effect on the affected box overlay has not been verified.

## Attempted fixes

1. **Folder structure mismatch (main issue).** `download_truckdrive.py --all-modalities`
   with manual `Expand-Archive` extracts each modality's contents directly into the
   scene folder (e.g. `scene_28_1/aeva`, `scene_28_1/bounding_boxes`) rather than nesting
   them under the wrapper folders (`lidar/`, `radar/`, `camera/`, `annotations/`) that
   `entrypoint.py` expects. Fixed by manually creating the wrapper folders and moving each
   modality folder into place:
   - `aeva`, `ouster` → `lidar/`
   - `conti542` → `radar/`
   - `leopard` → `camera/`
   - `bounding_boxes`, `lane_lines` → `annotations/`

   **This will affect anyone downloading TruckDrive fresh via the Hugging Face script and
   should be flagged to the team / added to setup docs.**

2. Hugging Face authentication was required before download would run
   (`huggingface_hub.errors.LocalTokenNotFoundError`). Resolved via `hf auth login`
   (browser OAuth flow) after creating a free HF account and accepting Torc Robotics'
   TruckDrive Non-Commercial License Agreement on the dataset page.

3. `dataset_viewer/pyproject.toml` requires `imageio`, `matplotlib`, `pyquaternion`,
   `scipy` in addition to the packages Kelsey listed. Installing `imageio`/`scipy`
   silently upgraded numpy from 1.26.4 → 2.5.2; downgraded back to 1.26.4 to match
   Kelsey's environment, which now leaves a `scipy` version conflict warning
   (`scipy 1.18.1 requires numpy>=2.0.0`). Not yet confirmed if this causes runtime
   issues — noted as a follow-up.

4. One network interruption during download (`Xet CAS Client Error: I/O error:
   error decoding response body`) at 86% progress — resolved by simply re-running the
   same download command, which resumed/completed without re-downloading from scratch.

5. Video export feature (`Generate Video (Camera)`) failed — requires the optional
   `imageio[ffmpeg]` dependency, not installed by default. Not required for the
   current visualisation/documentation task; noted for later if video export is needed.

## Decision

- [x] Change approach — document the folder-restructuring step so future setups
  (including the remaining 22-scene lightweight download) go faster
- [ ] Retry
- [ ] Stop

**Time spent:** ~2.5 hours across environment setup, HF auth, download, and viewer
troubleshooting (2026-09-06).

## Next action

Viewer reproduction was reported successful; environment compatibility and empty camera channels still need verification. Next is the visualisation and documentation stage
per Kelsey's handover:
1. Capture representative Camera/LiDAR/Radar visualisation evidence from `scene_28_1`
   (and `scene_28_22` once downloaded).
2. Complete `docs/dataset-surveys/truckdrive.md` using Kelsey's `dataset-statistics.md`
   as the primary data source.
3. In the same activated environment, capture `python -m pip check` and
   `python -m pip show numpy scipy`. Resolve the reported conflict using the actual
   installed requirements, then record the working versions and rerun the viewer.
   No replacement version pin or successful repair is claimed by this review.
4. Flag the folder-structure fix to Kelsey/the team so it's documented for anyone else
   downloading TruckDrive fresh.
