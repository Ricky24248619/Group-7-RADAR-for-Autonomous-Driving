# GOOSE results log

Every GOOSE result record, in date order. Status is the record's own `status` field. Owner as recorded.

| Date | Record | Status | Owner | Result | Experiment log |
|---|---|---|---|---|---|
| 2026-08-22 | [0003](../../results/records/0003-goose-macos-devkit-feasibility.json) | success | Damien Zhang | GOOSE devkit installed and frames rendered on macOS Apple Silicon | — |
| 2026-08-27 | [0001](../../results/records/0001-goose-val-characterisation.json) | success | Ricky Yuen | GOOSE 3D validation split measured in full — 961 frames, 174.9M labelled points | [0002](../../experiment-log/0002-goose-validation-statistics.md) |
| 2026-08-27 | [0002](../../results/records/0002-goose-windows-environment.json) | success | Ricky Yuen | GOOSE environment reproduced on Windows from a clean machine | [0001](../../experiment-log/0001-ricky-windows-goose-setup.md) |
| 2026-08-28 | [0004](../../results/records/0004-goose-traversability-mapping.json) | success | Damien Zhang | Four-class traversability mapping applied across all 8 GOOSE scenarios | [0003](../../experiment-log/0003-goose-traversability-rendering.md) |
| 2026-08-30 | [0005](../../results/records/0005-ptv3-baseline-apple-silicon.json) | failure | Damien Zhang | Pointcept/PTv3 GOOSE baseline cannot start on Apple Silicon — no CUDA path exists | — |
| 2026-08-31 | [0006](../../results/records/0006-goose-ptv3-gtx1660-partial.json) | partial | Ricky Yuen | GOOSE PTv3 runs in FP32 on GTX 1660; full validation stopped after 10 frames | [0004](../../experiment-log/0004-goose-ptv3-partial-validation.md) |
| 2026-09-22 | [0014](../../results/records/0014-goose-range-semantic-support.json) | success | Ricky Yuen | GOOSE full validation class and traversability composition by range | [0012](../../experiment-log/0012-dataset-range-and-support-comparison.md) |
| 2026-09-26 | [0026](../../results/records/0026-goose-saved-range-errors.json) | success | Ricky Yuen | GOOSE saved PTv3 predictions: class and range error diagnostic | [0021](../../experiment-log/0021-what-sensors-miss-by-range.md) |
| 2026-09-26 | [0027](../../results/records/0027-offroad-ground-obstacle-diagnostic.json) | success | Ricky Yuen | GOOSE ground-surface and obstacle-candidate diagnostic; STONE metadata feasibility | [0022](../../experiment-log/0022-offroad-ground-obstacles.md) |
| 2026-09-28 | [0032](../../results/records/0032-goose-multiscenario-terrain.json) | success | Ricky Yuen | GOOSE ground-category errors across eight scenarios: fresh 24-frame PTv3 subset | [0027](../../experiment-log/0027-goose-multiscenario-terrain.md) |
| 2026-09-28 | [0033](../../results/records/0033-goose-attention-context-diagnostic.json) | success | Ricky Yuen | GOOSE failure causes: attention context intervention and low-rock geometry association | [0028](../../experiment-log/0028-goose-failure-causes.md) |

Validators (`scripts/validate_result.py`, `scripts/validate_experiment_logs.py`) pass on `main` for all of the above.
