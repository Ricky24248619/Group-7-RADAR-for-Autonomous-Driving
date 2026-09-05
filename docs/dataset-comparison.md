# Dataset comparison and next experiment

**Prepared by Ricky Yuen, 5 September 2026.** This compares dataset suitability and
records a proposed next experiment. It is not a model leaderboard or an approved change
to the team's scope. Pair ownership stays with Damien/Ricky (GOOSE), Aiden/Fatima
(TruckScenes), and Kelsey/Fariya (TruckDrive).

## What the evidence supports

| Question | GOOSE | MAN TruckScenes | TruckDrive |
|---|---|---|---|
| Main task | Per-point terrain segmentation | 3D object detection | 3D object detection, including long range |
| Useful project role | Off-road material/traversability interpretation | Proposed first radar/LiDAR comparison | Planned long-range comparison |
| Shared labelled radar/LiDAR experiment | Not supported by the released assets available to us | Shared scenes and common box annotations | Shared scenes and common box annotations |
| Work already evidenced | 961-frame statistics, human-label mapping, figures, partial PTv3 inference | Mini metadata, selected sensor measurements and visualisations | 24-scene radar/annotation statistics and selected multimodal loading |
| Model result from the team | 10/961 validation frames; no full score | None in the reviewed evidence | None in the reviewed evidence |
| Immediate limitation | No paired labelled radar; full PTv3 protocol/compute unresolved | Compatible detector code and checkpoint not verified | Full multimodal mini data not retained; detector not selected |
| Metric boundary | Segmentation mIoU, with named taxonomy/class set | Stock mAP/NDS; class ranges end at 75 or 150 m | Pin the official evaluator and range protocol before scoring |

GOOSE's 174,891,807 labelled points cover all 961 validation frames. Fatima's TruckScenes
point totals use one selected radar and one selected LiDAR channel on one sample per
scene. Kelsey's 6,746 long-range TruckDrive returns cover one radar frame in each of 24
scenes. Those sampling rules differ: the counts are descriptions of those samples, not
a sensor-density ranking or evidence of detection accuracy. The mini sets are suitable
for development, not claims about the full datasets.

Repository evidence:

- [GOOSE measurements](../GOOSE%20-%20Ricky+Damien/dataset-statistics.md) and
  [partial model run](../experiment-log/0004-goose-ptv3-partial-validation.md).
- [TruckScenes measurements in PR #21](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/blob/35d78ec664a4b9d01d80ecc936d73d06973099ed/TruckScenes%20-%20Fatima/dataset-statistics.md).
  This work is reviewed on its branch and is not yet on `main`.
- [TruckDrive summary](../TruckDrive%20-%20Kelsey/SUMMARY.md) and
  [recorded setup](../experiment-log/experiment-log/0005-kelsey-truckdrive-setup-statistics.md).
- [Comparison rules and evaluator definition](metrics-definitions.md).

## TruckScenes checkpoint check

**Outcome on 5 September: no compatible, downloadable TruckScenes 3D-detector checkpoint
was verified in the sources below.** This is a bounded source check, not proof that none
exists. Installing a detector framework or obtaining more compute does not fill this gap.

| Candidate | Verified source | Decision for this pilot |
|---|---|---|
| Published TruckScenes baselines | Maintainer [issue #11](https://github.com/TUMFTM/truckscenes-devkit/issues/11#issuecomment-2721049514) announced a future code release; [issue #24](https://github.com/TUMFTM/truckscenes-devkit/issues/24#issuecomment-3341553328) supplies a PETR configuration referencing a local `epoch_24.pth`, not a downloadable checkpoint | Preferred lead if matching code, weights and preprocessing can be obtained; not ready to run |
| Upstream CenterPoint | [Official repository](https://github.com/tianweiy/CenterPoint) provides nuScenes/Waymo configurations and models | Not a verified TruckScenes checkpoint; data features, coordinates and classes require explicit adaptation |
| HyperDet | [Author paper, v1](https://arxiv.org/html/2602.11554v1) reports TruckScenes detection and says code/models will be released | No release verified in this check; training uses LiDAR supervision, which must be disclosed in any radar comparison |
| RadarGen | [Author repository](https://github.com/tomerborreda/RadarGen) releases TruckScenes weights for generating radar point clouds from camera input | Different task and input modality; does not fill the radar-only detector requirement |

No model weights were downloaded and no inference was started for this check. Before
choosing a checkpoint, record its URL/hash, code commit, dataset release, training split,
class ordering, sensor/features, preprocessing, temporal history and licence. A matching
configuration file alone does not establish compatible weights or complete loader code.

## Smallest useful pilot

This is a proposal for Aiden/Fatima and the team reviewer, not an instruction to change
their existing work or start a large run.

1. **Use existing data and code.** Review/merge PR #21 and use its path-configurable
   loaders. The TruckScenes mini data is on the pair's machine; it was not found in
   Ricky's known dataset locations during this check. Avoid downloading it again merely
   to duplicate their exploration.
2. **Resolve the checkpoint gate.** Obtain one verified TruckScenes detector and its
   preprocessing instructions. If none is available, record that blocker and ask the
   team/client whether a clearly labelled transfer experiment is worthwhile. Do not
   silently substitute a nuScenes score or begin training from scratch.
3. **Fix the sample selection before looking at predictions.** Use the official v1.2.0
   `mini_val` scene list. For a first-frame feasibility check, sort those scene names and
   select the first sample of the first scene; record the exact scene/sample tokens and
   sensor files. This single-frame check establishes loading/inference only.
4. **Verify one prediction end to end on approved compute.** Check coordinate frame,
   box size/order, units, taxonomy, confidence and timestamps. Keep empty predictions
   as explicit empty lists. Record elapsed wall time and peak memory; a modified model
   configuration becomes part of the result identity.
5. **Score only the complete named subset.** If the first frame works, plan the full
   official `mini_val` subset with the unchanged v1.2.0 stock evaluator. Supply every
   required sample token, including empty lists. Do not present a one-frame result as
   stock `mini_val` mAP/NDS. Full-dataset evaluation is a later compute decision.
6. **Add the second modality under the same contract.** Match scenes, ground truth,
   evaluation, temporal horizon and training/reporting conditions. Different model
   families or training regimes produce a model-plus-modality comparison, not evidence
   that the sensor alone caused the difference. Keep any >150 m custom evaluation
   separate and pending approval.

The runnable [CPU evaluator smoke check](../scripts/truckscenes_eval_smoke.py) exercises
synthetic box matching and AP only. It does not verify real dataset loading, coordinate
transforms, inference or the full `DetectionEval` pipeline. Its outputs must not enter a
model results table.

## Actions that still need people

- **Team reviewer:** reconcile the final GOOSE proposal (#26), survey correction (#25)
  and earlier draft (#18); complete the cold read or record acceptance of its omission.
  An omitted acceptance check is not a pass. Keep one agreed client note.
- **Damien and the team:** agree the revised scope against completed evidence and
  realistic next experiments. The repository draft does not establish client approval.
- **Aiden/Fatima, supported by Ricky:** confirm checkpoint availability and own the
  TruckScenes pilot; keep its result/log in the shared format.
- **Kelsey/Fariya:** finish the TruckDrive survey and representative visualisations;
  distinguish long-range returns from model detections.
- **Client/technical mentor:** confirm the dataset focus, primary detection metric,
  long-range protocol and available compute. No message was sent by this review.

For the next team discussion, choose the experiment and its owner first. A framework
installation, full dataset download or further GOOSE inference should follow a specific
evidence need, not replace that decision.
