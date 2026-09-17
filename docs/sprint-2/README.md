# Sprint 2 deliverables

Snapshot of the team's OneDrive `Sprint 2 Deliverables/to submit` folder on
15 September 2026. These are prepared deliverables, not evidence of formal
submission, client acceptance or agreed Sprint 3 assignments.

## Main documents

- [Team project report](Group7_Sprint2_ProjectReport.docx)
- [Proposed Sprint 3 stories](New%20Stories%20for%20Sprint%203.docx)
- [Combined review and internal retrospective](Sprint%202%20Review%20and%20Internal%20Retrospective.docx)

The [supporting documents](Supporting%20documents/) contain the handbook and
revised Sprint 1 scope, risk register, acceptance tests and story ledger.
The original Sprint 1 records elsewhere in this repository are retained.
This dated package does not silently replace their Markdown sources.

## Report corrections to carry into the final team version

The current OneDrive project report is Aiden's original narrative version. It
contains older claims that need reconciling with the raw evidence and the
updated supporting documents:

- Four-camera FCOS3D has **5,247 saved boxes across 80 nonempty mini_val samples**,
  with **mAP 0.0046 and NDS 0.0038**. It is a scored camera-only transfer
  experiment, not a matched radar/LiDAR benchmark. The cause of its low score
  remains unresolved; using reference box conversion does not rule out
  calibration, geometry or preprocessing errors.
- GOOSE PTv3 remains **10/961 frames** under a modified configuration. Its
  roughly five-hour estimate extrapolates processing-loop timing and excludes
  loading; it is not a measured complete run or a proven runtime bound.
- Ground-truth traversability maps, sensor-return counts and model detection
  scores are different evidence. The stock TruckScenes evaluator's 75 m or
  150 m class limits do not provide a detection score beyond 150 m.
- Fariya's TruckDrive reproduction is documented in EXP-0009, including
  remaining dependency, empty-channel and overlay warnings. Shared TruckDrive
  survey/result integration and independent checks are still outstanding.
- The new Sprint 3 stories are proposals. Resolve the priority of Autoware and
  dashboard work against the proposed core analysis before treating either
  plan as committed.
- The four-camera experiment log is now `experiment-log/0010-fcos3d-truckscenes-4camera.md`
  and its record `results/records/0011-fcos3d-truckscenes-4camera.json`. Both were
  renumbered off an identifier collision with Fatima's EXP-0007 and the 0008 evaluator
  smoke record. The Sprint 3 stories DOCX still cites the old `0007-` path in its
  Evidence section; correct it at the next OneDrive refresh.

Evidence: [four-camera experiment](../../experiment-log/0010-fcos3d-truckscenes-4camera.md),
[raw metrics](../../scripts/fcos3d_truckscenes_metrics_summary_4cam.json),
[predictions](../../scripts/results_mini_val_fcos3d_4cam.json),
[TruckDrive reproduction](../../experiment-log/0009-fariya-truckdrive-reproduction.md).
Source code/results snapshot: `234212e5ef91ec3247ea50ad8da4dad3116651b6`.

## Maintaining this package

OneDrive remains the editable team working location. Refresh this package
deliberately when the team changes the deliverables, then update
`manifest.json`. The manifest records file sizes and SHA-256 hashes without
personal filesystem paths. Do not add personal timesheets, individual
assessment submissions, raw datasets or meeting transcripts here.

Before formal submission, confirm story ownership and actual meeting details.
The recorded absence of a demonstration is not an approved replacement for
the required demonstration/minutes.
