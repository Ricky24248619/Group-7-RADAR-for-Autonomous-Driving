# Bonn — Self-Driving Cars 2021: Perception, Parts 1 and 2

| | |
|---|---|
| Source type | Course (two recorded lectures) |
| Link | Course: https://www.ipb.uni-bonn.de/sdc-2021/index.html · [Part 1](https://www.youtube.com/watch?v=tufYlgHIGvs) (74 min, camera) · [Part 2](https://www.youtube.com/watch?v=O1VVn8ULMSU) (57 min, LiDAR) |
| Company or institution | University of Bonn, Photogrammetry & Robotics Lab (IPB). Lecturer: Jens Behley |
| Duration and date watched | 131 min total. **Worked from the auto-generated YouTube transcripts** on 29 September 2026, not from viewing, so the slides were not seen (see *How this entry was made*) |
| Notes by | Damien Zhang, drafted with Claude Code from the transcripts |
| **Depth rating** | **Medium** for LiDAR and camera · **Shallow** for radar, which gets under a minute |

Only 2 of the course's 10 lectures are about perception. The others (intro, localization,
control, MPC ×2, planning, behaviour estimation, view from practice) were skipped under
the timebox, because none of them is a perception or sensor lecture.

### How this entry was made

Every claim below comes from the auto-generated captions and carries its timestamp, so
it can be checked against the video. Two consequences:

- **The slides were not seen.** Where the lecturer points at a figure ("as you can see
  here"), only the spoken part is recorded. Numbers read off slides are the most likely
  place for an error.
- **The captions mis-hear terms.** "lighter" means LiDAR throughout, "Vine"/"valine"
  means Velodyne, and "KP conv"/"CAPIC conv" means KPConv. One number is ambiguous and
  is flagged where it appears.

## A. What they actually said

- **No single sensor is enough; fusion is "the essential part" and "really hard", and
  the course then does not cover it** (P1 8:30–9:14). The course is camera- and
  LiDAR-centred by design.
- **LiDAR density falls with distance, and this is the first challenge he names for
  LiDAR perception.** A pedestrian or cyclist moving away from an HDL-64 soon becomes
  unrecognisable, and "could also be maybe a pole" (P2 24:26). The distance is captioned
  as "15 m". *Doubtful: it could be a mis-hearing of "50 m". Check the video before
  citing the number.*
- **LiDAR fails on very dark objects (absorption), very reflective ones (detector
  overload, range error), and glass (mirror reflections that create phantom objects)**
  (P2 25:20–28:01). A reflected car can look like a car approaching.
- **A LiDAR model trained on one sensor and mounting does not transfer to another.** A
  network trained on 64-beam KITTI scans, applied to a 32-beam sensor, labels pedestrians
  as cars and drivable road as terrain. *Moving the sensor's mounting changes the
  sampling and affects results too* (P2 52:21–54:14). **This is directly relevant to
  PR #63.** It is a lecture-level statement of why a checkpoint's expected sensor
  geometry matters.
- **PointPillars is taught as the canonical LiDAR detector.** Points are grouped into
  vertical pillars on an XY grid, encoded with a PointNet, then run through a 2D CNN on
  a bird's-eye-view pseudo-image. Boxes are yaw-only around Z (P2 44:18–47:52). This is
  the detector AD-S3-1 found runnable on TruckScenes.
- **Open problems for Level 5 include adverse weather.** He says current datasets are
  "mainly … very sunny or very good weather", alongside rare events, open-set objects and
  adversarial attacks (P1 71:41–73:16).

## B. Company profile → feeds Aiden's AD-3

*Skipped: this is a course, not a company.*

## C. Sensor content

| Modality | What they said about strengths | Weaknesses / failure modes | Covered? |
|---|---|---|---|
| Radar | Measures velocity as well as position; mature technology already fitted in cars (P1 6:52) | Very low resolution, sparse, "sometimes a little bit noisy" (P1 6:52–7:42) | ⚠️ Mentioned only, under a minute. No radar perception method is taught |
| LiDAR | Active, so it works day and night and cannot be blinded; direct, accurate 3D (P2 3:33–5:27). Remission/intensity is usable too (P2 7:16) | Sparsity grows with range (P2 24:26). Dark, shiny and glass surfaces (P2 25:20–28:01). Cost: HDL-64E $75,000 in 2007, Ouster OS1-128 about €18,000 in 2019 (P2 14:56–17:01). Mechanical wear motivates solid-state (P2 17:01). Poor cross-sensor transfer (P2 52:21) | ✅ Deep: the whole of Part 2 |
| Camera | Cheap, high resolution, colour for lights and signs (P1 4:37; P2 1:42) | Passive, so it depends on illumination and can be blinded by the sun (P1 5:22; P2 2:32) | ✅ Deep: the whole of Part 1 |
| Fusion | Called essential because sensors complement each other (P1 8:30) | "Really hard"; explicitly **not covered** (P1 9:14) | ❌ Not covered |

**Anything on 4D radar specifically?** **No.** 4D or imaging radar is not mentioned in
either lecture. Radar gets one slide's worth of speech in 131 minutes. For a 2021
university perception course, that silence fits the domain-study template's expectation
that 4D radar is too new to have reached teaching material.

**Anything on off-road or unstructured environments?** Only historically. Stanford's
Stanley won the 2005 DARPA Grand Challenge in the desert using several tilted 2D LiDARs
swept forward by the car's motion to detect uneven ground and obstacles (P2 10:53–11:49).
The semantic segmentation examples include vegetation and terrain classes (P2 49:37),
and the transfer example shows road mislabelled as terrain (P2 53:20). Nothing on
traversability as a task.

## D. Relevance to our decisions

- **D-04 (long-range):** **No range limits or degradation figures past ~150 m.** The
  only range statement is qualitative: LiDAR density falls with distance (P2 24:26).
  Point clouds "in the distance [look] very sparse" (P2 21:42). No radar range claim at
  all.
- **D-03 (off-road):** Weak. The Stanley example (above) and terrain/vegetation as
  segmentation classes. No ground-vs-not-ground method is taught beyond segmentation in
  general.
- **R-21 (no radar-first baseline):** **No radar-first detection model is named.** Every
  detector taught is camera-based (Faster R-CNN, YOLO, CornerNet) or LiDAR-based
  (PointPillars, with KPConv, PointNet and sparse convolutions as backbones).
- **PR #63 / G-12 (not a decision, but live):** P2 53:20–54:14 is a citable teaching
  source for the claim that a checkpoint is tied to its training sensor's sampling and
  mounting. That supports rotating TruckScenes' tilted LiDAR into the upright frame
  PointPillars expects, rather than treating the zero score as a model finding.

## E. Terms I did not understand

- **Remission / intensity:** the strength of the returned laser signal, a proxy for
  surface reflectivity (P2 7:16)
- **Range image:** the sensor-native 2D layout, one row per beam and one column per
  rotation angle, convertible to a point cloud (P2 13:55, 19:47)
- **Sparse convolution:** convolution evaluated only on occupied voxels (P2 34:47).
  This is what `spconv` implements, the dependency that blocked CenterPoint on Windows
  in EXP-0019
- **Pillars / pseudo-image:** see PointPillars above
- **KPConv (kernel point convolution):** convolution defined directly on points via
  fixed kernel points in space (P2 42:30)
- **Panoptic segmentation, stuff vs things:** semantic plus instance; "stuff" is
  uncountable (road, sky), "things" are countable objects (P1 52:50)
- **4D panoptic LiDAR segmentation:** panoptic segmentation with instance IDs kept
  consistent over time (P2 55:54). *"4D" here means 3D plus time, not 4D radar's
  range–azimuth–elevation–Doppler.* That's worth a glossary note, because the same word
  means different things in the two literatures
- **Open-set perception / OpenGAN:** detecting that an object belongs to no known class
  (P1 67:08–71:41)
- **Unsupervised domain adaptation, self-supervised pre-training:** ways to move a model
  to a new sensor with few new labels (P2 55:06)

## F. Worth escalating to Fabian

- The **"15 m"** sparsity figure (P2 24:26) is probably mis-captioned and should be
  checked in the video before anyone quotes it.
- Is there a comparable **radar** transfer result? The lecture shows LiDAR models failing
  across beam counts and mountings. Whether radar detectors transfer across radar
  models or mountings would bear directly on R-21 and on reusing any published radar
  checkpoint (EXP-0018, EXP-0020). This source is silent on it.
