# EXP-0003 — GOOSE traversability rendering and projection check

- **Date started / completed:** 31 August 2026 / 31 August 2026
- **Owner:** Ricky Yuen
- **Workstream / story:** WS2 / R3–R5 and R6

## Goal

Re-run the four-class traversability renderer from the restored Windows environment,
verify that all eight validation scenarios still produce a coherent drivable region,
and record Damien's D4 finding about projection choice as a metric boundary. This is
the third experiment-log entry required by R4/R6.

## Environment

- Microsoft Windows 11, native PowerShell
- Python 3.11.9 at `%USERPROFILE%\.venvs\radar\Scripts\python.exe`
- numpy 1.26.4, matplotlib 3.8.4, PyYAML 6.0.2
- NVIDIA GeForce GTX 1660, 6,144 MiB VRAM; GPU not used by this renderer
- Team repository commit `0de5057`

## Dataset / data subset

The restored GOOSE 3D validation archive contains all 961 paired LiDAR/label frames
under `F:\RADAR\datasets\GOOSE\extracted\goose_3d_val`. The renderer selected the
midpoint frame from each of the eight scenarios, so this run rendered eight
representative frames rather than measuring all 961. It uses the original 64-class
labels and the committed four-class `traversability_map.csv`; it does not use model
predictions or the separate challenge labels.

## Steps and commands

```powershell
$PY = "$env:USERPROFILE\.venvs\radar\Scripts\python.exe"
$DATA = "F:\RADAR\datasets\GOOSE\extracted\goose_3d_val"
$OUT = "F:\RADAR\outputs\ricky_r6"

& $PY scripts\validate_traversability_map.py `
  --dataset-root $DATA

& $PY scripts\goose_traversability.py `
  --root $DATA `
  --map "GOOSE - Ricky+Damien\traversability_map.csv" `
  --out-dir $OUT `
  --tag post-reinstall
```

The generated sheet is
`F:\RADAR\outputs\ricky_r6\goose_traversability_sheet_post-reinstall.png`. The
repository evidence remains
[`docs/evidence/goose_traversability_sheet.png`](../docs/evidence/goose_traversability_sheet.png).

## Outcome

- [x] Success — worked as intended
- [ ] Partial — describe what worked and what didn't
- [ ] Failure — did not achieve the goal

All eight representative scenario frames rendered successfully. Visual inspection
shows a connected blue Traversable region in every panel. The representative-frame
raw all-return shares reproduced the expected scenario pattern: open field tracks
were 82.1% Traversable, while the two woodland `aying` frames were dominated by
Non-Traversable returns. These eight percentages describe the selected frames, not
the complete 961-frame split.

Damien's D4 ground-selection experiment explains why the raw bird's-eye shares are not
the final word. Selecting the lowest return per grid cell reduced apparent
Non-Traversable share in every inspected scenario; `aying_mangfall_2` changed from 92%
to 58%. Traversable share was not monotonic (`garching_uebungsplatz_2` changed from
31% to 26%), so the projection must be reported as part of the metric method rather
than treated as a universal correction factor. The boundary is now recorded in
`docs/metrics-definitions.md`.

## Attempted fixes

None. Mapping validation, frame pairing, and rendering succeeded on the first
post-reinstall run.

## Decision

- [ ] Retry
- [ ] Change approach
- [x] Stop — the missing R4/R6 experiment log and projection caveat are complete

**Time spent:** approximately 0.3 hours for the verified re-run, inspection, and record

## Next action

Proceed to R7: run the pretrained PTv3 baseline against the official GOOSE challenge
labels. Start with one validation frame or batch, and record either the first model
result or the exact dated environment/VRAM failure.
