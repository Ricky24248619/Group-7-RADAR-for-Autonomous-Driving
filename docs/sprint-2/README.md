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

The OneDrive project report is Aiden's original narrative version, written before
Sprint 3. Each row below is a claim in it that the evidence no longer supports, or
supports more narrowly. **Every row has an owner** — this list previously had none,
which is how it stayed unactioned.

Reviewed against the repository on 23 September 2026.

### Corrections

| # | Claim in the report | What the evidence supports | Owner |
|---|---|---|---|
| C-1 | *"Only ~1–6% of GOOSE points sit beyond 100 m"* (§4) | That is the **per-scenario** range from `findings-damien.md`. The split-level figure is **3.84% beyond 100 m and 1.10% beyond 150 m**, which is what the acceptance tests and Scope of Work both quote. It currently reads as a split-level claim beside split-level numbers | Damien |
| C-2 | *"LiDAR samples substantially denser than paired radar in TruckScenes"* (§4) | True **for the channels compared**, and not generalisable. `LIDAR_TOP_FRONT` is a downward-tilted Ouster OS0 blind-spot unit, nominal 35 m at 10% reflectivity; the 200 m Hesai Pandar64 units are in the corner modules and were not used. Measured coverage bears this out — **165,520 of 165,588 LiDAR points fall inside 50 m**. Any range reading of this comparison is wrong | Fatima |
| C-3 | Four-camera FCOS3D: *"cause of its low score remains unresolved"* | Still true, but narrower. The audit establishes 80/80 sample coverage with no missing channels, and round-trip geometric validity, so **missing data and gross coordinate error are excluded**. Height versus scene-domain content remains unseparated and needs a controlled check | Aiden |
| C-4 | Four-camera FCOS3D result | **5,247 saved boxes across 80 mini_val samples, mAP 0.0046, NDS 0.0038.** A scored camera-only transfer experiment, not a matched radar/LiDAR benchmark | Aiden |
| C-5 | GOOSE PTv3 | **10 of 961 frames** under a modified configuration. The ~5 hour figure extrapolates processing-loop timing and **excludes loading**, so it is a lower bound, not a measured runtime or a proven bound | Ricky |
| C-6 | GOOSE validation split size | The report quotes **961 frames**; the published split is **960**. Our 961 is internally consistent — the eight scenario counts sum to it exactly — but the one-frame difference is unexplained. Needs a local-versus-published file inventory comparison, **which requires the GOOSE data** (on Ricky's machine, not Damien's) | Ricky |
| C-7 | Range reporting generally | Ground-truth traversability maps, sensor-return counts and model detection scores are **different evidence**. The stock TruckScenes evaluator filters classes at 75 m or 150 m and therefore produces **no detection score beyond 150 m** | Ricky |
| C-8 | Any combined range figure | The working coverage protocol recorded 21 September uses **0–50 / 50–100 / 100–150 / 150–400 / >=400 m** for new descriptive runs. Historical tables keep their original bins. Shared edges do **not** make different denominators or coordinate frames comparable | Ricky |
| C-9 | TruckDrive status | Fariya's reproduction is EXP-0009, with dependency, empty-channel and overlay warnings outstanding. The shared survey and result records are still not delivered. Camera and LiDAR are retained for **2 of 24 scenes** — no multimodal claim may imply full-mini coverage | Kelsey |
| C-10 | Sprint 3 scope | The new stories are proposals. The report's §6.4 says to start Autoware and the dashboard; the stories place both outside the core plan. **The two documents contradict each other** and the team has not resolved it | Ricky |

### Path changes since the snapshot

The four-camera experiment log is now
[`experiment-log/0010-fcos3d-truckscenes-4camera.md`](../../experiment-log/0010-fcos3d-truckscenes-4camera.md)
and its record `results/records/0011-fcos3d-truckscenes-4camera.json`, renumbered off
an identifier collision with Fatima's EXP-0007 and the 0008 evaluator smoke record.
**The Sprint 3 stories DOCX still cites the old `0007-` path** in its Evidence section;
correct it at the next OneDrive refresh.

### What Sprint 3 added that the report predates

Not corrections — new evidence the final version should cite rather than omit:

- Dataset suitability comparison — which question each dataset can answer, with
  denominators inline and no cross-dataset ranking. Lands at `docs/dataset-suitability.md`
  with PR #34; not linked here until it is on `main`
- TruckScenes range-band coverage with a declared sample manifest, per-sensor
  coordinate frame stated per row, and its channel caveat
- The four-camera result audit, and CI that runs both validators plus the test suite
  on every pull request

### Evidence

[Four-camera experiment](../../experiment-log/0010-fcos3d-truckscenes-4camera.md) ·
[raw metrics](../../scripts/fcos3d_truckscenes_metrics_summary_4cam.json) ·
[predictions](../../scripts/results_mini_val_fcos3d_4cam.json) ·
[TruckDrive reproduction](../../experiment-log/0009-fariya-truckdrive-reproduction.md) ·
[GOOSE statistics](../../GOOSE%20-%20Ricky+Damien/dataset-statistics.md)

Sprint 2 snapshot: `234212e5ef91ec3247ea50ad8da4dad3116651b6`.
Corrections reviewed against: `711c3f7`.

## Maintaining this package

OneDrive remains the editable team working location. Refresh this package
deliberately when the team changes the deliverables, then update
`manifest.json`. The manifest records file sizes and SHA-256 hashes without
personal filesystem paths. Do not add personal timesheets, individual
assessment submissions, raw datasets or meeting transcripts here.

Before formal submission, confirm story ownership and actual meeting details.
The recorded absence of a demonstration is not an approved replacement for
the required demonstration/minutes.
