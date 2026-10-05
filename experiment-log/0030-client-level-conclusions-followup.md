# EXP-0030 — New clip coverage, unseen terrain frames and client-level conclusions

- Date: 2026-10-01
- Owner: Ricky Yuen
- Results: 0036, 0037
- Status: two bounded follow-up studies complete; recognition comparison still lacks compatible long-range model weights.

Created a local question/conclusion register before scoring the follow-ups. It contains twenty open or qualified decision questions rather than twenty prewritten answers. The planning register and theoretical client report are outside Git; this commit contains completed findings and their reproducible evidence.

## Distance / object types

All cached TruckDrive clip timestamps had already been examined. Acquired previously unexamined clips 28_3 and 28_15, eight evenly spaced annotation timestamps per clip fixed before sensor scoring. Downloaded all annotation/calibration ZIP members and only matching sensor members using verified HTTP ranges, ZIP CRCs and SHA-256. Raw assets remain on F:. The initial 200 MiB cap stopped before the second LiDAR sample; ZIP sizes established the cost of keeping the fixed selection, so the bound increased to 400 MiB before outcome inspection. Completed compressed members total 298,289,104 bytes; no full sensor ZIP was downloaded.

The existing paired-support analyzer scored static and acquisition-aligned assumptions. Alignment forbids ego-pose extrapolation, excluding two endpoint frames per clip; all comparisons use the same remaining twelve frames and 115 valid object observations. At 200–400 m there are 36 vehicle observations from 18 scene-qualified tracks: aligned LiDAR support 86.11%, radar 33.33%, union 88.89%. Static support is 80.56% versus 36.11%. LiDAR leads in both clips and in expanded-box sensitivities. This independently checks new clips within the same released platform, not a new sensor population or detector recall.

Expanded TruckScenes class, equal-track, camera-visibility and weather summaries using its existing complete eligible pointwise-corrected recount. Joined raw metadata only after hashes and annotation/sample/track identities matched. Nearby coverage differences remain across bicycles and road signs, in addition to the earlier pedestrian/cone results. Weather rows are descriptive across different scenes; no causal rain/snow penalty is inferred.

## Terrain configuration

Selected one unseen interior-third frame from each of seven base validation recordings; excluded the January tuning recording and every previously evaluated frame ID. Selection used filenames, before inference or label-outcome inspection. Total 1,186,454 points. These are unseen frames in existing recordings, not an external held-out dataset.

Ran unchanged published checkpoint, seed 20260831, FP32, FlashAttention off, one augmentation: patch 64, fresh patch-64 repeat, patch 128. All completed and exited zero; saved configs differ only in patch sizes and output paths. Every repeated baseline prediction is identical. The three bounded runs took 127.85, 122.80 and 154.09 seconds. Sampled total GPU memory peaks were 4,747, 4,966 and 5,953 MiB, with temperatures 71, 75 and 73 C respectively. These readings include desktop workloads and are sampled system totals, not isolated model allocation peaks. Patch 128 is near the device memory ceiling, so it is not adopted as the default. No package installation, training or full-split inference.

Patch 128 improves six of seven frame scores, with pooled eight-class point correctness 89.54% to 90.81%; the flight frame worsens 86.37% to 83.69%. Fine-label diagnostics add high-grass ground confusion, pole improvement, broad-ground/material disagreement, wall and bicycle case weaknesses, and class/recording concentration. Rock has zero points in this new cohort, so its generalisation is explicitly unresolved.

## Plain-language conclusions and feasibility

The [twenty-conclusion register](../docs/client-level-conclusions-oct01.md) links every headline, client implication and boundary to source measurements. It consolidates earlier evidence and adds new inference/reanalysis; it does not claim twenty new independent experiments or twelve weeks of labour. Case findings and the suggestive fog pilot are marked explicitly.

Refreshed official TruckDrive, L-RadSet and Dual-Radar release documentation; all heads remain at the previously inspected revisions. The already-audited approximately 70 m pretrained pair remains unsuitable for 200–400 m recognition. No author message, client notification, full detector benchmark or client acceptance is claimed.

## Reproduction

```text
python scripts/acquire_truckdrive_followup.py --root <TruckDrive-root-outside-git> --output results/evidence/sprint-followup-oct01/truckdrive
python scripts/truckdrive_paired_support.py --scene-root <TruckDrive-root>/<scene> --frame-count 8 --output-dir results/evidence/sprint-followup-oct01/truckdrive/<scene>/static
python scripts/truckdrive_paired_support.py --scene-root <TruckDrive-root>/<scene> --frame-count 8 --align-ego --output-dir results/evidence/sprint-followup-oct01/truckdrive/<scene>/aligned
python scripts/analyse_sprint_followup.py sensors --truckscenes-root <TruckScenes-root>
python scripts/prepare_goose_followup.py --root <GOOSE-root> --subset <fresh-WSL-subset> --output results/evidence/sprint-followup-oct01/terrain
```

For terrain inference, reuse the EXP-0027 Pointcept command with the frozen subset, fresh save paths, patches 64/repeated64/128 and unchanged remaining settings. The exact three commands and sampled resource observations are saved in `results/evidence/sprint-followup-oct01/terrain/execution.json`. Then:

```text
python scripts/analyse_sprint_followup.py terrain --goose-root <GOOSE-root> --runs <new-runs-root> --mapping <challenge-mapping.csv> --checkpoint <challenge_ptv3.pth> --execution <execution.json>
python scripts/plot_sprint_followup.py
python scripts/render_client_conclusions.py
```

Generated CSVs have empty values for absent classes, not zero accuracy. Rerunning must preserve source hashes and exact selected cohorts. Model resources/predictions remain outside Git. Data/implementation credit: TruckScenes/MAN, TruckDrive/Torc, GOOSE authors (CC BY-SA 4.0), Pointcept/PTv3 challenge checkpoint. The local report is a theoretical review draft, not a sent or accepted client deliverable.

## Verification

All 246 repository tests passed, with eleven optional-runtime skips. The seven focused follow-up regressions also passed in the raw-data environment. All 36 result records and experiment-log numbering validate; two existing records retain warnings for missing metrics. An independent full-cloud implementation reproduced 224 selected TruckDrive box counts across both new clips, timing variants, margins and modalities; 482 raw source files were rehashed. This independently checks counting, while sharing the calibration and pose interpolation with the producer.

Repository text hashes use UTF-8 with LF line endings to survive Git's Windows/Linux conversion; external raw data hashes cover exact bytes. Canonicalising metadata hashes does not change the frozen sample identities or inference outputs. Every conclusion has a linked source and an explicit evidence boundary.
