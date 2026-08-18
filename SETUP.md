# Environment Setup — what's installed and how to use it

## Installed

| Component | Version | Location |
|---|---|---|
| Python | 3.11.15 | `/opt/homebrew/opt/python@3.11` (via Homebrew) |
| venv | — | `~/.venvs/radar` |
| truckscenes-devkit | 1.2.0 (`[all]` extras) | in venv |
| awscli | 1.45.57 | in venv |
| aria2 | 1.37.0 | `/opt/homebrew/bin/aria2c` |
| Repos | cloned | `truckscenes-devkit/`, `TruckDrive/` |

Pulled in with the `[all]` extras: numpy 2.4.6, open3d 0.19.0, opencv-python 5.0.0, matplotlib 3.11.1, jupyterlab 4.6.2, pyquaternion, pypcd4, tqdm, Pillow.

## Get the third-party repos

Neither repo is committed here — both are unmodified upstream projects, so this repo tracks only our own work. Clone them into the project root:

```bash
git clone https://github.com/TUMFTM/truckscenes-devkit.git
git clone https://github.com/torc-ai/TruckDrive.git
```

They are listed in `.gitignore`, so they will not show up as untracked changes.

## Activate

```bash
source ~/.venvs/radar/bin/activate
```

## Two setup decisions worth knowing

**1. Python 3.11, not your system Python.**
`truckscenes-devkit` declares `python_requires = ">=3.8,<3.12"`. Your system Pythons are 3.13 and 3.14, so the install would have failed. Homebrew's `python@3.11` was installed alongside them — nothing was changed about your existing Pythons. The devkit docs recommend 3.8, but 3.11 is within the supported range and installs cleanly with modern wheels.

**2. The venv lives at `~/.venvs/radar`, not in the project folder.**
The project path — `SEM 2 2026/CITS3200/RADAR Project` — contains spaces. A venv there technically works for `python`, but every console script (`aws`, `jupyter`, `pip`) breaks, because a `#!` shebang line cannot contain spaces:

```
./.venv/bin/aws: bad interpreter: /Users/damienzhang/Desktop/SEM: no such file or directory
```

I hit this, then moved the venv out. Keeping it outside the spaced path avoids the whole class of problem permanently. If you'd rather have it inside the project, everything must be run as `python -m aws`, `python -m jupyter` etc. — workable but easy to forget.

## Verified working

```
truckscenes-devkit import OK          # from truckscenes import TruckScenes
numpy 2.4.6 | open3d 0.19.0
aws-cli/1.45.57 Python/3.11.15
jupyter / ipykernel 7.3.0
aria2 version 1.37.0
```

Not yet run: the devkit's own unit tests, or the tutorial notebook. Both need the dataset on disk, which hasn't been downloaded.

## Next step — get data

Nothing has been downloaded yet. The mini split is the sensible start (~9.6 GB):

```bash
source ~/.venvs/radar/bin/activate
mkdir -p /data/man-truckscenes          # may need sudo; or pick a local path
aws s3 sync --no-sign-request --region eu-central-1 \
  s3://man-truckscenes/release/mini/ ~/datasets/man-truckscenes-zips/

cd ~/datasets/man-truckscenes-zips
unzip 'man-truckscenes_*_v1.2-mini.zip' -d /data/man-truckscenes
```

Then set the env var the devkit's tests expect and run the tutorial:

```bash
export TRUCKSCENES="/data/man-truckscenes"
jupyter lab "truckscenes-devkit/tutorials/truckscenes_tutorial.ipynb"
```

If the dataset root ends up somewhere other than `/data/man-truckscenes`, pass it explicitly:

```python
from truckscenes import TruckScenes
trucksc = TruckScenes(version='v1.0-mini', dataroot='/your/path', verbose=True)
```

### Storage warning
This machine has **~263 GB free**. Mini fits easily. **`trainval` does not** — it is ~560 GB compressed and needs roughly 1.1 TB to download and extract. Sort out external or lab storage before planning any full-split work.

### If matplotlib windows misbehave
The devkit docs suggest setting a backend in `~/.matplotlib/matplotlibrc`. Their suggested `TKAgg` is a Linux-oriented choice; on macOS use `MacOSX`, or just work inside Jupyter, where the inline backend applies and this is moot.

## TruckDrive (not installed — deliberate)

The TruckDrive repo is cloned but its tooling is not set up. Its components (`dataset_viewer`, `generate_training_data`, `mmdet_project`) have separate per-component READMEs and pull in PyQt5 and MMDetection3D. MMDetection3D in particular is a heavy, version-sensitive install that wants a CUDA GPU — worth doing deliberately in its own environment rather than mixing into this one, and only once we know we need it.

Downloading also requires accepting the licence on Hugging Face first. The mini split (24 scenes) comes via `TruckDrive/download_truckdrive.sh`; `aria2` is already installed to accelerate it.
