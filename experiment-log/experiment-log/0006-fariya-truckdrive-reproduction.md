\# EXP-0006 — TruckDrive reproduction and viewer verification



\- \*\*Date started / completed:\*\* 2026-09-05 / 2026-09-06

\- \*\*Owner:\*\* Fariya

\- \*\*Workstream / story:\*\* TruckDrive dataset exploration (reproducing Kelsey's setup) → TruckDrive visualisation and documentation (Epic A / WS5)



\## Goal



Reproduce Kelsey's TruckDrive setup on a second machine to confirm it's repeatable,

then move into the visualisation and documentation stage she handed off.



\## Environment



\- Windows

\- Python 3.12.4 (note: differs from Kelsey's 3.11.11 — no issues encountered so far)

\- Python venv: `truckdrive\_visualizer` (used venv instead of conda, not installed locally)

\- NumPy 1.26.4

\- Open3D 0.19.0

\- PyQt5 5.15.11

\- Pillow, matplotlib, imageio, pyquaternion, scipy (additional deps required by

&#x20; `dataset\_viewer/pyproject.toml`, not listed in Kelsey's original environment notes)

\- Data source: TruckDrive Hugging Face repo (`Torc-Robotics/TruckDrive`), downloaded via

&#x20; `download\_truckdrive.py` after accepting the Torc non-commercial license and

&#x20; authenticating via `hf auth login`

\- Raw data stored outside the Git repo, on a separate local drive (G:)



\## Dataset / data subset



\- `scene\_28\_1`, full multimodal download (camera, LiDAR, radar, poses, calibrations,

&#x20; annotations) — 7.86 GB downloaded, \~10.2 GB raw before compression



\## Steps and commands



```powershell

python download\_truckdrive.py --out "G:\\TruckDrive-data\\TruckDrive" --scene scene\_28\_1 --all-modalities

python entrypoint.py --root-dir "G:\\TruckDrive-data\\TruckDrive\\TruckDrive" --recording scene\_28\_1

```



\## Outcome



\- \[x] Success — worked as intended, with one setup fix required (see below)



All sensors loaded with correct frame counts:

\- 260 Aeva LiDAR frames, 258–260 Ouster frames (×3 orientations)

\- 521 Radar frames

\- 259–260 images per camera angle (some angles show 0 frames — appears to be a gap

&#x20; in this scene's capture, not a setup error; not yet confirmed against Kelsey's data)

\- 87 bounding boxes loaded from JSON

\- 20 lane-line JSON files loaded

\- Fused `all\_3d` point cloud rendered successfully: 545,829 points across LiDAR + radar

\- 2D camera view with bounding-box overlay rendered (one harmless warning: an edge-case

&#x20; box triggered `x1 must be greater than or equal to x0` in the 2D draw call — did not

&#x20; block rendering)



\## Attempted fixes



1\. \*\*Folder structure mismatch (main issue).\*\* `download\_truckdrive.py --all-modalities`

&#x20;  with manual `Expand-Archive` extracts each modality's contents directly into the

&#x20;  scene folder (e.g. `scene\_28\_1/aeva`, `scene\_28\_1/bounding\_boxes`) rather than nesting

&#x20;  them under the wrapper folders (`lidar/`, `radar/`, `camera/`, `annotations/`) that

&#x20;  `entrypoint.py` expects. Fixed by manually creating the wrapper folders and moving each

&#x20;  modality folder into place:

&#x20;  - `aeva`, `ouster` → `lidar/`

&#x20;  - `conti542` → `radar/`

&#x20;  - `leopard` → `camera/`

&#x20;  - `bounding\_boxes`, `lane\_lines` → `annotations/`



&#x20;  \*\*This will affect anyone downloading TruckDrive fresh via the Hugging Face script and

&#x20;  should be flagged to the team / added to setup docs.\*\*



2\. Hugging Face authentication was required before download would run

&#x20;  (`huggingface\_hub.errors.LocalTokenNotFoundError`). Resolved via `hf auth login`

&#x20;  (browser OAuth flow) after creating a free HF account and accepting Torc Robotics'

&#x20;  TruckDrive Non-Commercial License Agreement on the dataset page.



3\. `dataset\_viewer/pyproject.toml` requires `imageio`, `matplotlib`, `pyquaternion`,

&#x20;  `scipy` in addition to the packages Kelsey listed. Installing `imageio`/`scipy`

&#x20;  silently upgraded numpy from 1.26.4 → 2.5.2; downgraded back to 1.26.4 to match

&#x20;  Kelsey's environment, which now leaves a `scipy` version conflict warning

&#x20;  (`scipy 1.18.1 requires numpy>=2.0.0`). Not yet confirmed if this causes runtime

&#x20;  issues — noted as a follow-up.



4\. One network interruption during download (`Xet CAS Client Error: I/O error:

&#x20;  error decoding response body`) at 86% progress — resolved by simply re-running the

&#x20;  same download command, which resumed/completed without re-downloading from scratch.



5\. Video export feature (`Generate Video (Camera)`) failed — requires the optional

&#x20;  `imageio\[ffmpeg]` dependency, not installed by default. Not required for the

&#x20;  current visualisation/documentation task; noted for later if video export is needed.



\## Decision



\- \[x] Change approach — document the folder-restructuring step so future setups

&#x20; (including the remaining 22-scene lightweight download) go faster

\- \[ ] Retry

\- \[ ] Stop



\*\*Time spent:\*\* \~2.5 hours across environment setup, HF auth, download, and viewer

troubleshooting (2026-09-06).



\## Next action



Reproduction confirmed successful. Moving to the visualisation and documentation stage

per Kelsey's handover:

1\. Capture representative Camera/LiDAR/Radar visualisation evidence from `scene\_28\_1`

&#x20;  (and `scene\_28\_22` once downloaded).

2\. Complete `docs/dataset-surveys/truckdrive.md` using Kelsey's `dataset-statistics.md`

&#x20;  as the primary data source.

3\. Resolve the numpy/scipy version conflict before it causes issues in later stats work.

4\. Flag the folder-structure fix to Kelsey/the team so it's documented for anyone else

&#x20;  downloading TruckDrive fresh.

