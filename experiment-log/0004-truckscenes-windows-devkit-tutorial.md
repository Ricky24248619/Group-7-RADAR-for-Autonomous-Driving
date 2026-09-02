# Experiment Log — Entry Template

One file per experiment attempt in `experiment-log/`, numbered sequentially
(`0001-short-name.md`). Successes AND failures both get entries — the client
has said negative results count as results, and an unlogged failure gets
repeated by someone else.

---

## EXP-0004 — TruckScenes devkit install and tutorial run (Windows)

- **Date started / completed:** 2026-08-21 / 2026-08-21
- **Owner:** Aiden Blampain
- **Workstream / story:** None assigned yet — general devkit/dataset feasibility
  check on Windows, done ahead of Epic E work. Overlaps with Epic D (dataset
  exploration); flagging for Kelsey rather than claiming that ground.

### Goal

Confirm that the TruckScenes devkit and the `v1.2-mini` dataset can be
installed independently of each other on Windows, wired together correctly,
and that the official tutorial notebook runs end-to-end — as a baseline before
any deeper dataset exploration or benchmarking work.

### Environment

- Windows 11 Home 10.0.26200
- Python 3.11.9 (`python -m venv`)
- venv at `truckscenes-devkit/truckscenes-env` (project-local, not `~/.venvs` —
  no spaces issue hit since venv itself has no space in its own path)
- `truckscenes-devkit` installed via `pip install "truckscenes-devkit[all]"`
  (regular install, **not** editable — confirmed via dist-info, no
  `direct_url.json`), version `1.2.0`
- Key packages pulled in by `[all]`: numpy 2.4.6, open3d 0.19.0,
  opencv-python 5.0.0.93, matplotlib 3.8.4, pyquaternion 0.9.9, pypcd4 1.4.3,
  jupyterlab 4.6.3
- Notebook run inside VS Code's Jupyter integration, kernel set to
  `truckscenes-env`

### Dataset / data subset

MAN TruckScenes **v1.2-mini**, downloaded separately from the devkit (per
SETUP.md convention — dataset and devkit are independent installs) and placed
at a sibling folder outside both this repo and the devkit clone:
`.../Rep/man-truckscenes/`.

Structure present:
- `samples/` — 16 sensor folders (4 camera: `CAMERA_LEFT/RIGHT_BACK/FRONT`;
  6 lidar: `LIDAR_LEFT`, `LIDAR_REAR`, `LIDAR_RIGHT`, `LIDAR_TOP_FRONT/LEFT/RIGHT`;
  6 radar: `RADAR_LEFT/RIGHT_BACK/FRONT/SIDE`)
- `v1.2-mini/` — all 14 JSON metadata tables the devkit expects

**`sweeps/` is not present** — this mini archive ships keyframes only, no
intermediate-frame sensor data.

Table counts on load (`verbose=True`): 400 `sample`, 10 `scene`, 1094
`instance`, 25750 `sample_annotation`, 43556 `sample_data`, 20116 `ego_pose`,
20090 `ego_motion_cabin`, 20089 `ego_motion_chassis`, 18 `sensor`, 18
`calibrated_sensor`, 27 `category`, 11 `attribute`, 4 `visibility`, 10
`weather_annotation`.

### Steps and commands

```bash
# from truckscenes-devkit/
python -m venv truckscenes-env
truckscenes-env\Scripts\activate
pip install "truckscenes-devkit[all]"

# dataset acquired separately, extracted to a sibling folder:
# .../Rep/man-truckscenes/{samples,v1.2-mini}
```

In `tutorials/truckscenes_tutorial.ipynb` (VS Code, kernel = `truckscenes-env`):

```python
from truckscenes import TruckScenes

trucksc = TruckScenes(
    dataroot=r"path",
    version="v1.2-mini"
)
```

Then ran every cell in the notebook top to bottom.

### Outcome

- [x] Success — worked as intended

All 14 tables loaded with no errors ("Done loading in 1.841 seconds"), reverse
indexes built, and the visualization explorer initialized correctly (the
`[all]` extras were installed, so no missing-dependency warning). Every cell
in the tutorial notebook executed with zero error outputs.

### Attempted fixes

None needed — clean run on the first attempt.

### Decision

- [x] Retry — no
- [ ] Change approach
- [ ] Stop

This establishes a working Windows baseline for TruckScenes. Next step is
deciding whether follow-on dataset exploration belongs under Epic D (Kelsey)
or feeds directly into Epic E's industry/technology review.

**Time spent:** 0.2 hours

### Next action

Check whether `docs/dataset-surveys/truckscenes.md` is
already in progress before starting one; if not, write it from this entry's
environment and table-count findings. Do not begin deeper visualisation or
benchmarking on TruckScenes until that overlap is resolved.
