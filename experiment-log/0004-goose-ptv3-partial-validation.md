# EXP-0004 — GOOSE PTv3 bounded gates and partial validation

- **Date started / completed:** 31 August 2026
- **Owner:** Ricky Yuen
- **Workstream / story:** GOOSE / R7–R8

### Goal

Test whether the published GOOSE Pointcept/PTv3 checkpoint can execute bounded FP32
inference on the available GTX 1660, then start a validation reproduction after both the smallest
and largest frames pass. The full validation was not required to continue once the
user set a stricter limit on sustained GPU load.

### Environment

- Windows host with Ubuntu 22.04.5 under WSL 2.7.12.0, kernel
  `6.18.33.2-microsoft-standard-WSL2`
- NVIDIA GeForce GTX 1660, 6,144 MiB, compute capability 7.5, driver 591.86
- Python 3.10.12; PyTorch 2.0.1+cu117; torchvision 0.15.2+cu117;
  torch-scatter 2.1.2+pt20cu117; spconv-cu117 2.3.6; NumPy 1.26.4
- Fraunhofer Pointcept fork commit
  `92f91ccedba88bda72d1727d6f5212efd0351414`
- Local GOOSE-only runtime patch: [`pointcept-goose-runtime.patch`](pointcept-goose-runtime.patch),
  8 additions and 43 deletions across
  `pointcept/datasets/__init__.py`, `pointcept/datasets/defaults.py`,
  `pointcept/engines/test.py`, and `pointcept/models/__init__.py`. A SHA-256 of the text
  patch is not used as an identifier because Git may check it out with platform line
  endings; the committed patch blob is the source of truth.
  It avoids importing unrelated optional model/dataset families, lazily imports
  SharedArray caching, loads the checkpoint through CPU memory, and makes test-time
  autocast respect `enable_amp`.
- Checkpoint `challenge_ptv3.pth`, 554,559,017 bytes, epoch 33, SHA-256
  `314B6402AE7738248136EF0F2A5D49C10CF71A63E94F0CD75FB39B285D6F565E`;
  the model reported 46,158,792 parameters.

No training, FlashAttention, PointOps, Open3D, ROS, Autoware, or STONE data was used.

### Dataset / data subset

GOOSE 3D base validation split with the official version 1.1 challenge labels:
961 matching LiDAR/label pairs and 174,891,807 points. The validation portion of the
challenge-label download contains 1,368 labels: 961 match base GOOSE and the other 407
are GOOSE-Ex labels that were not part of this run.

Bounded gates used:

- smallest frame: `2023-05-17_neubiberg_sunny__0409_1684329849670608600`,
  30,263 points
- largest frame: `2023-05-17_neubiberg_sunny__0440_1684329957111926151`,
  270,720 points

The full-run attempt completed the first 10 of 961 frames, covering 1,785,024 points,
before intentional termination.

### Steps and commands

All four invocations used seed `20260831`, `enable_flash=false`, encoder/decoder patch
sizes 64, one test augmentation, and a fresh output directory. The generated config
files and test logs remain under `F:\RADAR\outputs\pointcept\`; they are deliberately
not committed because outputs and model assets stay off Git.

The full partial run used these commands. `TEAM_REPO` is the path to this repository as
seen from WSL:

```bash
TEAM_REPO='/mnt/c/Users/aaa55/Documents/Codex Uni Sem 2/Group-7-RADAR-for-Autonomous-Driving'
source /home/ricky/.venvs/pointcept-goose/bin/activate
cd /home/ricky/src/Pointcept-goose
git switch --detach 92f91ccedba88bda72d1727d6f5212efd0351414
git -C "$TEAM_REPO" show HEAD:experiment-log/pointcept-goose-runtime.patch | git apply --unidiff-zero --check -
git -C "$TEAM_REPO" show HEAD:experiment-log/pointcept-goose-runtime.patch | git apply --unidiff-zero -
python tools/test.py \
  --config-file configs/goose/semseg-pt-v3m1-0-base.py \
  --num-gpus 1 \
  --options \
    weight=/mnt/f/RADAR/models/GOOSE/challenge_ptv3.pth \
    seed=20260831 \
    model.backbone.enable_flash=false \
    model.backbone.enc_patch_size='[64,64,64,64,64]' \
    model.backbone.dec_patch_size='[64,64,64,64]' \
    data.test.split=val \
    data.test.test_cfg.aug_transform='[[]]' \
    enable_amp=false \
    data.test.data_root=/mnt/f/RADAR/datasets/GOOSE/extracted/goose_3d_val \
    save_path=/mnt/f/RADAR/outputs/pointcept/ptv3_val961_p64_fp32_20260831_133507
```

The two one-frame gates used temporary symlinked roots containing only the named
scan/label pair. The initial smallest-frame attempt used `enable_amp=true`; the three
successful/partial FP32 attempts used `enable_amp=false`.

### Outcome

- [ ] Success — worked as intended
- [x] Partial — bounded FP32 inference succeeded; full validation intentionally stopped
- [ ] Failure — did not achieve the goal

The AMP smallest-frame gate failed before evaluation. The preserved `test.log` ends at
`Start Evaluation`; the exact error observed in the terminal was:

```text
!all_profile_res.empty() assert faild. can't find suitable algorithm for 0
```

This was not an out-of-memory error. Disabling AMP was the minimal fix for spconv on
this Turing card:

| Attempt | Outcome |
|---|---|
| Smallest frame, FP32 | complete; 30,263 points; 3 fragments; 8.613 s; `End Evaluation` present |
| Largest frame, FP32 | complete; 270,720 points; 8 fragments; 35.381 s; `End Evaluation` present |
| 961-frame validation, FP32 | 10 predictions; 1,785,024 points; Pointcept loop-body `Batch` mean 18.940 s/frame; no traceback, OOM, or `End Evaluation` |

The one-frame scores and the rolling 10-frame values are diagnostics only. They are not
reported as benchmark metrics: neither covers the complete 961-frame split, and
Pointcept's zero-union averaging differs from this repository's mIoU definition.

The exact full-run stop reason was the user's instruction: *“dont overload my gpu i
dont want to break it.”* At the first stop checkpoint the card was at 99% utilisation,
3,184/6,144 MiB and 66°C. After termination no Pointcept process remained; the card was
at 1%, 792 MiB and 63°C. The ten completed predictions and logs were preserved.

### Attempted fixes

1. Tried the documented AMP path on the smallest frame; spconv could not select a
   suitable FP16 convolution algorithm.
2. Disabled AMP while keeping FlashAttention off and patch sizes at 64; the smallest
   frame completed.
3. Ran the largest frame under the same FP32 settings; it completed without OOM.
4. Started the full 961-frame validation only after both gates passed; stopped it
   promptly when the user limited sustained GPU use.

### Decision

- [ ] Retry now
- [x] Change approach — preserve this as a partial result and use lower-load or remote
  compute only after explicit approval
- [ ] Stop — this path is closed

**Time spent:** not reliably captured; omitted from the result record rather than
invented.

### Next action

Do not restart the full GTX 1660 run without Ricky's explicit approval. If a complete
benchmark is still required, first choose a lower-load schedule or another CUDA machine,
then run all 961 frames with one fixed, fully documented protocol and recompute metrics
under the repository definition.
