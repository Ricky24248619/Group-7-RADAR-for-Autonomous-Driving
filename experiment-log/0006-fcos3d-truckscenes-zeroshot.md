# EXP-0006 — FCOS3D (nuScenes-pretrained) run zero-shot on TruckScenes, CPU-only

- **Date started / completed:** 2026-09-05 / 2026-09-05
- **Owner:** Aiden Blampain
- **Workstream / story:** None assigned yet — first real detection-model run
  against TruckScenes, following on from EXP-0004's devkit/dataset feasibility
  check. Produces `results/records/0007-fcos3d-truckscenes-zeroshot.json`.

## Goal

Get an actual detection result out of TruckScenes rather than just a devkit
walkthrough: run an existing open-source 3D detector against TruckScenes data
and evaluate it with the devkit's own scorer, per the project's stated
approach of running existing open-source models on public datasets. No GPU is
available on this machine, so the model had to be one that could plausibly
run on CPU, and one with a released pretrained checkpoint — training from
scratch was out of scope (the paper's own CenterPoint baseline took 181 GPU
hours on 2×A100).

## Environment

- Windows 11 Home 10.0.26200, AMD Ryzen 7 5700U (Radeon graphics) — **no
  NVIDIA GPU, no CUDA path**, confirmed via `nvidia-smi` absence.
- New dedicated venv, `truckscenes-devkit/detection-env`, **not** the
  `truckscenes-env` from EXP-0004 — kept separate because this stack needs
  NumPy <2 (torch 2.1.0 requires NumPy's 1.x C-API) while the tutorial venv
  already has NumPy 2.4.6 for other work.
- Python 3.11.9 (the *exact* interpreter matters — see Attempted fixes).
- numpy 1.26.4, torch 2.1.0+cpu, torchvision 0.16.0+cpu, mmengine 0.10.7,
  mmcv 2.1.0 (prebuilt CPU wheel for torch2.1.0), mmdet 3.3.0, mmdet3d 1.4.0
  (`--no-deps`, to dodge an unrelated matplotlib-downgrade conflict), numba
  0.67.0, truckscenes-devkit 1.2.0, pyquaternion, pypcd4, python-lzf,
  pydantic 2.13.5 / pydantic-core 2.46.5 (exact pairing required).
- Visual Studio 2022 Build Tools (C++ workload) installed via winget, for
  building `numpy<2` from source. Turned out to be needed only because of the
  Python-version mistake below — kept installed as it's otherwise harmless
  and unblocked a couple of small source builds (e.g. `python-lzf`) along
  the way.
- Model: FCOS3D, `fcos3d_r101-caffe-dcn_fpn_head-gn_8xb2-1x_nus-mono3d`,
  official nuScenes-pretrained checkpoint from the mmdetection3d model zoo
  (`fcos3d_r101_caffe_fpn_gn-head_dcn_2x8_1x_nus-mono3d_20210715_235813-4bed5239.pth`,
  220MB, not committed — reported baseline on nuScenes: mAP 0.298, NDS 0.377).
  Monocular camera-only detector — chosen specifically because it avoids
  `spconv` (LiDAR sparse convolution), which has no real CPU path.

## Dataset / data subset

MAN TruckScenes `v1.2-mini`, official `mini_val` split (80 samples, confirmed
via `truckscenes.utils.splits.create_splits_scenes()`), same local copy used
in EXP-0004. Only the **`CAMERA_LEFT_FRONT`** channel was used, not all 4
truck cameras — a deliberate scope cut, not a gap: at ~28s/image on CPU,
4 cameras × 80 samples (~320 images) would take roughly two hours, which
doesn't fit this session in one pass. All 80 samples' ground truth is still
scored; missing cameras only cost recall, they don't invalidate coverage.

## Steps and commands

Full command reference lives at the top of the script itself
(`scripts/truckscenes_fcos3d_infer.py`). Summary:

```bash
# environment build (detection-env), abbreviated — see script docstring
python -m venv detection-env
pip install "numpy<2"
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu
pip install mmengine
pip install mmcv==2.1.0 -f https://download.openmmlab.com/mmcv/dist/cpu/torch2.1.0/index.html
pip install mmdet
pip install mmdet3d --no-deps
pip install "numpy<2" --force-reinstall --no-deps   # mmengine's matplotlib dep silently re-upgrades numpy — reassert the pin
pip install truckscenes-devkit --no-deps pyquaternion pypcd4 python-lzf pydantic numba

# inference, chunked into 6 sequential foreground calls (see Attempted fixes)
python truckscenes_fcos3d_infer.py \
  --dataroot <man-truckscenes> --version v1.2-mini --split mini_val \
  --config <fcos3d config .py> --checkpoint <fcos3d .pth> \
  --cameras CAMERA_LEFT_FRONT --start 0 --end 15 --out results_mini_val_fcos3d.json
# ...repeated with --start/--end sliding across 15/30/45/60/75/80

# evaluation
python -m truckscenes.eval.detection.evaluate results_mini_val_fcos3d.json \
  --dataroot <man-truckscenes> --version v1.2-mini --eval_set mini_val \
  --output_dir ./metrics --plot_examples 0 --render_curves 0
```

## Outcome

- [x] Success — worked as intended

All 80 `mini_val` samples produced valid predictions (959 boxes total), and
`truckscenes.eval.detection.evaluate` ran to completion with no errors.
Result: **mAP 0.0000, NDS 0.0000** across all 12 detection classes — a real,
diagnosed zero, not a crash. Full numbers and interpretation are in
`results/records/0007-fcos3d-truckscenes-zeroshot.json`; short version: the
model's monocular depth estimates are off by 5–21m (scaling with range —
the signature of depth misestimation, not a coordinate bug), most likely
because FCOS3D's depth priors were learned from nuScenes' ~1.5m-high
car-mounted cameras and TruckScenes' cameras sit at ~2.1m with a different
pitch/FOV. Confirmed the box-conversion math itself is not the culprit by
reusing mmdet3d's own reference scoring code (`output_to_nusc_box` /
`cam_nusc_box_to_global` in `mmdet3d/evaluation/metrics/nuscenes_metric.py`)
verbatim rather than re-deriving the camera-to-global transform from scratch.

"Success" here means the run completed and produced a trustworthy
measurement — it says nothing about whether the model detected well. The
zero mAP *is* the result.

## Attempted fixes

Several real obstacles, each recorded because the next person will hit them
too:

1. **NumPy 2 / torch 2.1.0 ABI break.** `torch.from_numpy()` raised
   `RuntimeError: Numpy is not available` under NumPy 2.4.6 — not cosmetic,
   fully fatal for mmdet3d's data pipeline. Fix: a separate venv pinned to
   `numpy<2`.
2. **First `numpy<2` install attempt failed** with "no version satisfies
   numpy==1.26.4" even via `--only-binary`. Root cause misdiagnosed at first
   as a missing PyPI mirror wheel; actual cause was that the venv had been
   created with **Python 3.13** (whatever `python` resolved to on PATH),
   and numpy 1.26.4 predates Python 3.13 entirely — no wheel could ever
   exist. Fix: recreate the venv explicitly with the same Python 3.11.9
   interpreter used by `truckscenes-env`. After that, `numpy<2` installed as
   a prebuilt wheel in 5 seconds, no compiler needed.
3. Installed Visual Studio 2022 Build Tools (winget) to unblock the above
   before the real cause was found — turned out to be unnecessary once the
   Python-version bug was fixed, but not wasted: it separately let
   `python-lzf` (a `pypcd4` dependency) build from source without further
   fuss.
4. **`mmengine` silently re-upgraded numpy to 2.4.6** as a side effect of
   pulling in `matplotlib` with no upper bound. Not caught until the next
   import test failed the same way as (1). Fix: reassert `numpy<2` with
   `--force-reinstall --no-deps` as the last install step, every time.
5. **`pypcd4` needed `lzf` and `pydantic`**, neither pinned in the devkit's
   own `requirements_base.txt` — installed both directly. A `pydantic`/
   `pydantic-core` version mismatch from piecemeal `--no-deps` installs
   raised `SystemError: ... incompatible with the current pydantic version`;
   fixed by installing the matching pair together.
6. **`inference_mono_3d_detector` returns a bare result, not a tuple**, for
   a single non-batch image — `result, _ = inference_mono_3d_detector(...)`
   raised `TypeError: cannot unpack non-iterable Det3DDataSample object`.
   One-line fix.
7. **Results JSON schema gap**: the eval/detection/README's documented
   `sample_result` schema doesn't mention it, but `DetectionBox.deserialize`
   requires `sample_token` inside *each* box dict, not just as the outer
   dict key — `KeyError: 'sample_token'` on first evaluate attempt. Patched
   the already-computed results file in place (no need to redo 80 samples
   of inference) and fixed the script for future runs.
8. **Background execution (`run_in_background` + a scheduled wakeup) was
   unreliable**: two consecutive background inference runs were killed
   before completing even one checkpoint interval, despite a generous
   timeout. Switched to sequential **foreground** calls with the sample
   range chunked (`--start`/`--end`) to fit the ~10-minute per-call ceiling,
   and added periodic mid-chunk checkpointing to disk so a killed chunk
   wouldn't lose progress. This is a tooling note for whoever runs long CPU
   jobs next, not a finding about the model.

## Decision

- [ ] Retry
- [x] Change approach — the zero-shot camera path is now proven end-to-end;
      the sensible next step is either (a) extend camera coverage to all 4
      truck cameras once more CPU time (or a GPU) is available, or (b) try
      the LiDAR path (CenterPoint) on a machine with an NVIDIA GPU, since
      that was the paper's strongest baseline and doesn't share FCOS3D's
      depth-estimation domain-gap failure mode.
- [ ] Stop

**Time spent:** approximately 4 hours, most of it environment/dependency
debugging (items 1–7 above) rather than the actual inference or evaluation.

## Next action

Bring the mATE/domain-gap finding to the team as evidence for the D-04
range-degradation question, and decide who picks up the GPU-based LiDAR path
(CenterPoint) next, since a NuScenes-pretrained checkpoint for it also
exists and this machine cannot run it.
