# Sprint 3 review and next steps — 21 September 2026

## What the project now establishes

The project has working dataset exploration and bounded feasibility evidence.
It does not yet have a matched radar-versus-LiDAR object-detection benchmark.

| Strand | Evidence we have | What remains |
|---|---|---|
| GOOSE | Full validation-set characterisation, human-label traversability figures, a partial 10-frame PTv3 feasibility run | Explain the mapping and projection limits to an outside-pair reader; no new full inference run is required for this handover |
| TruckScenes | CPU camera-model experiment, dataset survey, a ten-sample radar/LiDAR return-coverage workflow | Raw-data rebuild on another machine, fairer sensor/channel selection if extending the comparison, conditional detector feasibility |
| TruckDrive | Long-range radar returns in a 24-frame sample, retained multimodal data for two scenes, setup/reproduction notes | Finish the template survey, resolve second-machine warnings and define an evaluator before proposing detection scores |

## Work completed in this review

- Inspected PRs #39–42 and the committed manifest, range CSV, plotting and
  acceptance-check code. Reproduced a Windows JSON line-ending failure and
  fixed it. Added Windows to the CI matrix.
- Rejected non-finite/non-zero-start range edges and non-finite point coordinates,
  preventing silent loss from counts. Corrected the open-band label to >=400 m
  and tested a return exactly at 400 m. Existing measured counts are unchanged.
- Corrected plot captions to report each modality's sample count rather than
  claiming that equal or unequal counts prove matched sample identity.
- Regenerated both figures from the committed CSV and inspected them. This
  reproduces the plotting stage, not measurements from raw sensor files.
- Verified the Top Front LiDAR identity against the source paper; see
  [sensor check](../TruckScenes%20-%20Fatima/SENSOR-CHECK.md). It is a tilted
  blind-spot Ouster, so the plots cannot establish a general LiDAR range limit.
- Recorded the working descriptive coverage protocol in
  [metrics definitions](metrics-definitions.md). Custom detection metrics or
  evaluator changes still require their separate approval.

## Reproduction evidence and limits

The review used an isolated Windows Python 3.11 environment with the repository's
four pinned CI dependencies. All 118 tests in the TruckScenes branch passed after
the fixes; both record/log validators passed. The baseline had 114 tests and
failed the existing Windows JSON newline check. New regressions cover invalid
edges, non-finite coordinates, the exact upper boundary and unequal sample captions.

No TruckScenes raw dataset was found in the checked project, Documents, Downloads,
OneDrive or F:\RADAR locations. F:\RADAR\datasets contains GOOSE and STONE.
No TruckScenes root was configured in the environment. This is not proof that
another teammate lacks the dataset; the dataset-holder path is still needed.

**A-6 remains open.** A fresh raw-data rebuild was not run. An agent-run check
also does not stand in for an outside-team human reproduction or cold read.
Use [ACCEPTANCE-CHECK.md](../TruckScenes%20-%20Fatima/ACCEPTANCE-CHECK.md) once a
teammate with the mini dataset can run the three commands and record the result.

## Next actions and proposed ownership

The following follows the story roles; it does not claim a new team agreement.

| Who | Next concrete output | Done when |
|---|---|---|
| Ricky | Explain and review the coverage protocol with the team; collect any client response on custom detection evaluation | Bands, frame, denominators and zero/missing rules are understood; external decisions are recorded as received |
| Fatima + Kelsey | Raw-data rebuild of the declared TruckScenes subset on another machine | Manifest and CSV match, or differences are recorded and investigated; actual reviewer/date/environment are supplied |
| Aiden + Fatima | Time-boxed radar/LiDAR detector feasibility check | Released code/checkpoint, licence, preprocessing, taxonomy, evaluator and memory needs are checked; run or no-go decision has evidence |
| Damien + Fariya | Cold read of the dataset comparison and GOOSE figures | Reader explains what is measured and what is not; their actual feedback and resulting corrections are recorded |
| Kelsey + Fariya | TruckDrive survey and reproducibility closeout | Retained subset and unresolved warnings are clear; any multimodal claim is limited to verified overlap |
| Whole team | Integrated findings and handover | Each conclusion links to an output, every limitation remains visible, and someone outside the author pair can follow the workflow |

The next experiment should be a better-controlled coverage comparison only if
the relevant channels and calibration can be loaded. A model benchmark stays
conditional. More compute alone does not fix mismatched geometry, labels or
evaluation rules. Do not start another large download or GPU run merely to
increase activity: first state the question and the evidence the run would add.
