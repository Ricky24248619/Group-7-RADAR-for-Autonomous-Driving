# RADAR for Autonomous Driving — Dataset & Tooling Overview

**Project:** CITS3200 — RADAR for Autonomous Driving
**Client:** Adrian Boeing (EECE) · Multiple teams · IP: Creative Commons / open source
**Goal:** Benchmark LiDAR vs 4D RADAR performance for 3D object detection, using open-source AD frameworks (Autoware) for playback and simulation.
**Status:** Pre-client-meeting research. Scope not yet agreed.

---

## 1. MAN TruckScenes

The primary candidate dataset. Mature, well documented, permissively downloadable.

| | |
|---|---|
| Authors | MAN Truck & Bus SE + TU Munich (TUMFTM) |
| Venue | **NeurIPS 2024**, Datasets & Benchmarks Track |
| Paper | [arXiv:2407.07462](https://arxiv.org/abs/2407.07462) |
| Devkit | [github.com/TUMFTM/truckscenes-devkit](https://github.com/TUMFTM/truckscenes-devkit) |
| Landing page | [man.eu/truckscenes](https://www.man.eu/truckscenes) → redirects to [brandportal.man](https://brandportal.man/d/QSf8mPdU5Hgj) |
| Data mirror | [AWS Open Data Registry](https://registry.opendata.aws/man-truckscenes/) — no AWS account needed |
| **License** | **CC BY-NC-SA 4.0** (non-commercial, share-alike) |
| Contact | truckscenes@man.eu |

### Scale & content
- **740+ scenes**, 20 s each (~4.1 h total)
- **27 object classes** with 3D bounding boxes, **15 attributes**, **34 scene tags**
- Objects tracked across scenes (supports detection *and* tracking benchmarks)
- Annotation range **>230 m**
- Diverse environmental conditions — the paper's headline contribution alongside the radar

### Sensor suite
- **6× 4D RADAR** — full **360° coverage**. This is the key fact for us: it is the **largest radar dataset with annotated 3D bounding boxes**, and the first with 360° 4D radar.
- **6× LiDAR**
- **4× camera**
- 2× IMU, 1× high-precision GNSS

The 6-LiDAR / 6-radar pairing with shared 3D boxes is exactly what a like-for-like LiDAR-vs-RADAR detection benchmark needs — same scenes, same ground truth, two modalities.

### Truck-specific research challenges introduced
Trailer occlusion, elevated/novel sensor mounting perspectives, and terminal (depot/yard) environments — none of which appear in robotaxi datasets like nuScenes.

### Data layout
Unpack all archives into a single root without overwriting duplicate folders:

```
/data/man-truckscenes
    samples/     # sensor data at keyframes (annotated)
    sweeps/      # sensor data at intermediate frames (unannotated)
    v1.0-mini/   # JSON metadata + annotations
    v1.0-trainval/
    v1.0-test/
```

The schema is **nuScenes-derived** (see `docs/schema_truckscenes.md`), so nuScenes-based tooling and detection models often port over with modest effort. Worth confirming early — it materially affects effort estimates.

### Download sizes (verified on S3, `eu-central-1`)

| Split | Archives | Total |
|---|---|---|
| **mini** | metadata 13.7 MB + sensordata 9.63 GB | **~9.6 GB** |
| trainval | metadata 757 MB + 7 sensordata parts | **~560 GB** |
| test | metadata 167 MB + 2 sensordata parts | **~144 GB** |

```bash
# List
aws s3 ls --no-sign-request --region eu-central-1 s3://man-truckscenes/release/mini/

# Download mini (~9.6 GB)
aws s3 sync --no-sign-request --region eu-central-1 \
  s3://man-truckscenes/release/mini/ /data/man-truckscenes/
```

> ⚠️ **Disk planning:** this machine has ~263 GB free. `mini` is comfortable (~20 GB incl. extraction). **`trainval` does not fit** — it needs ~1.1 TB to download *and* extract. Plan for external/lab storage before committing to full-split training.

---

## 2. TruckDrive

The newer, larger, longer-range benchmark. Strong comparison point, heavier logistics.

| | |
|---|---|
| Authors | Torc Robotics + Princeton (Ghilotti, Palladin, Brucker, Sigal, Bijelic, **Felix Heide**) |
| Venue | **CVPR 2026** |
| Paper | [arXiv:2603.02413](https://arxiv.org/abs/2603.02413) · [Project page](http://torc-ai.github.io/TruckDrive) |
| Devkit | [github.com/torc-ai/TruckDrive](https://github.com/torc-ai/TruckDrive) |
| Full data | [Hugging Face](https://huggingface.co/datasets/Torc-Robotics/TruckDrive) (gated — must accept licence) |
| Mini data | CloudFront access portal (24 scenes) |
| **Devkit licence** | Apache 2.0 |
| **Dataset licence** | **Torc Robotics Non-Commercial License v1.0** ⚠️ see below |

### Scale & content
- **475k** synchronised multimodal samples across **3,828 sequences**
- **165k** densely annotated frames + 310k unlabelled
- Sequences 15–25 s, ~500 m ego trajectory each (highway speed)
- **85 classes regrouped into 9 categories**
- 3D boxes, lane lines, accumulated depth
- **Annotation range: 2D to 1,000 m; 3D to 400 m**
- **Total size: 28.8 TB**

### Sensor suite
- **10× Continental ARS540 4D radar** (±4° to ±20° horizontal FOV)
- **7× AEVA Aeries II long-range FMCW LiDAR** — 400 m, ~100 lines, 10 Hz, **per-point radial velocity**
- **3× Ouster OS0/OS1 short-range LiDAR** (64/128 × 2048, 20 Hz)
- **11–15× OnSemi AR0820 RCCB cameras**, 8 MP, 52.8°×28.9°, 5–10 Hz (9 short/medium + 1–3 long-focal stereo pairs)

### Published baselines (useful as our comparison targets)

| Task | Best method | Result |
|---|---|---|
| 2D detection | DINO | 37.8% mAP (**15.3%** at 250 m+) |
| 3D detection | BEVFusion | 26.45% mAP full range; 22.69% at 150–250 m |
| 3D tracking | CenterPoint | 13.0% AMOTA |
| Stereo depth | NMRF | 3.39 m MAE short; 40.88 m ultra-long |
| End-to-end planning | UniAD | 2.00 m avg L2 |

### Headline finding — highly relevant to our project
Models trained on urban datasets **degrade 31–99% on 3D perception beyond ~150 m**. Camera-only models lose 57% of 2D and up to **99%** of 3D detection performance at long range. LiDAR methods hit quadratic memory growth from dense BEV representations.

**Why this matters for a LiDAR-vs-RADAR study:** radar's relative advantage is expected to be largest exactly where LiDAR and cameras fall off — long range and adverse weather. TruckDrive is the dataset built to expose that regime. This is a strong framing for our benchmark hypothesis.

### Dataset comparison (from the TruckDrive paper)

| Dataset | LiDARs | Cameras | Manual annotations | Effective range |
|---|---|---|---|---|
| nuScenes | 1× 32-beam | 6 | 40k | ±100 m |
| Waymo | 1 mid + 4 short | 5 | 230k | ±100 m |
| MAN TruckScenes | 6 | 4 | 30k | ±226 m |
| **TruckDrive** | 7 LR + 3 SR | 11–15 | **165k** | **±400 m** |

### ⚠️ Licence risk — raise with the client
The Torc non-commercial licence permits academic research, government, and personal use, but **prohibits internal research by any entity whose primary or substantial business involves developing autonomous vehicle systems**, and any use connected to a product/service offered for sale.

Two things to confirm with Adrian Boeing:
1. Our project IP is stated as **Creative Commons / open source**. TruckDrive's licence is **not** a CC licence and is non-commercial — check this is compatible with the intended deliverable and publication route.
2. TruckScenes is **CC BY-NC-SA 4.0** — also non-commercial, and *share-alike*, which propagates to derivative works.

Neither blocks academic coursework, but both constrain what can be published and reused. Better raised at initiation than discovered at handover.

---

## 3. Assessment of the proposed approach

Your teammate's read — **TruckScenes as primary, TruckDrive as comparison** — is well judged, and the evidence supports it:

- TruckScenes is ~9.6 GB for a usable mini split vs 28.8 TB total for TruckDrive. Tractable on student hardware.
- TruckScenes has a pip-installable devkit, a Jupyter tutorial, and documented schema. TruckDrive's devkit is repo-only with per-component READMEs.
- TruckScenes downloads anonymously from S3. TruckDrive is licence-gated behind Hugging Face.
- TruckScenes' nuScenes-derived schema unlocks a large ecosystem of existing detection models.

The one point worth pushing back on: **TruckScenes' 6 LiDAR + 6 radar with shared 3D boxes makes it the better dataset for the core LiDAR-vs-RADAR comparison outright**, not merely the easier one. TruckDrive's real value to us is the **long-range regime** (>150 m) where the interesting divergence happens. Consider framing them as answering two different questions rather than primary/secondary.

### On Autoware — needs verification, currently the biggest unknown
Your teammate flagged uncertainty here, correctly. What I can confirm:

- Autoware has a documented [radar-based 3D detection reference implementation](https://autowarefoundation.github.io/autoware-documentation/main/design/autoware-architecture/perception/reference-implementations/radar-based-3d-detector/faraway-object-detection/), including a faraway-object-detection design — directly relevant.
- A ROS2 driver exists for the **Continental ARS548** ([ars548_ros](https://github.com/robotics-upo/ars548_ros)) — same ARS-series family as TruckDrive's ARS540.
- [4D-Radar-Odom](https://github.com/robotics-upo/4D-Radar-Odom) is a ROS2 Humble package for 4D radar + IMU odometry.

**What I could not find: any existing TruckScenes → ROS2/Autoware converter.** Neither dataset ships ROS2 bags. This is likely to be a genuine chunk of project work — writing a converter from the nuScenes-style JSON + sensor files into ROS2 bags with correct TF trees, timestamps, and sensor calibration. Worth scoping explicitly with the client, and worth checking whether another team is already doing it, since this is a multi-team project.

Also note: Autoware targets **Ubuntu + ROS2**, not macOS. Expect to need a Linux machine, VM, or Docker for that half of the work.

---

## 4. Open questions for the client meeting

1. **Scope of "benchmark"** — reproduce published baselines, or train our own detectors? Very different effort.
2. **Autoware's role** — visualisation/playback only, or actually running detection inference in the ROS2 pipeline?
3. **Compute & storage** — is there lab GPU access and >1 TB storage? Determines whether full splits are viable at all.
4. **Team split** — which team owns the ROS2 converter, if multiple teams need it?
5. **Licence compatibility** — CC deliverable vs NC datasets (see above).
6. **Metrics** — mAP/NDS in the dataset's own eval, or an Autoware-native evaluation?

---

## 5. Sources

- [TUMFTM/truckscenes-devkit](https://github.com/TUMFTM/truckscenes-devkit)
- [MAN TruckScenes paper — arXiv:2407.07462](https://arxiv.org/abs/2407.07462) · [OpenReview](https://openreview.net/forum?id=X8ItT6mGKF)
- [MAN TruckScenes on AWS Open Data](https://registry.opendata.aws/man-truckscenes/)
- [MAN brand portal](https://brandportal.man/d/QSf8mPdU5Hgj) *(JS single-page app — needs a browser)*
- [torc-ai/TruckDrive](https://github.com/torc-ai/TruckDrive)
- [TruckDrive paper — arXiv:2603.02413](https://arxiv.org/html/2603.02413v2)
- [TruckDrive on Hugging Face](https://huggingface.co/datasets/Torc-Robotics/TruckDrive)
- [Voxel51: TruckDrive long-range dataset in FiftyOne](https://voxel51.com/blog/truckdrive-long-range-dataset-fiftyone)
- [Autoware radar-based 3D detection docs](https://autowarefoundation.github.io/autoware-documentation/main/design/autoware-architecture/perception/reference-implementations/radar-based-3d-detector/faraway-object-detection/)
