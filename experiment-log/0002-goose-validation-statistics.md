# EXP-0002 — GOOSE validation statistics

- **Date started / completed:** 27 August 2026 / 27 August 2026
- **Owner:** Ricky Yuen
- **Workstream / story:** WS2 / R2

## Goal

Measure class frequency, scenario composition, frame density, radial range, and
effectively absent classes over the complete downloaded GOOSE 3D validation split.

## Environment

Same Windows/Python environment as EXP-0001: Python 3.11.9, numpy 1.26.4, native
Windows 10. GPU was not used.

## Dataset / data subset

All 961 paired LiDAR/label frames in `goose_3d_val`, covering all eight validation
scenarios and 174,891,807 labelled points.

## Steps and commands

```powershell
$PY = "$env:USERPROFILE\.venvs\radar\Scripts\python.exe"
$DATA = "C:\goose\goose_3d_val"
& $PY scripts\goose_stats.py --root $DATA
```

The script streams one frame at a time, joins scans and labels through the established
renderer loading functions, and defines radial range as `sqrt(x² + y²)`.

## Outcome

- [x] Success — worked as intended
- [ ] Partial — describe what worked and what didn't
- [ ] Failure — did not achieve the goal

`GOOSE - Ricky+Damien/dataset-statistics.md` contains all five R2 outputs. Principal
findings:

- 62.90% of points are within 25 m; 1.10% are beyond 150 m.
- Forest alone is 24.37% of all labelled points.
- 22 of 64 classes are below 0.01%; six have zero validation points.
- Class sparsity confirms that every mIoU must declare its evaluated class set.

## Attempted fixes

None. All 961 scan/label pairs loaded without a length mismatch.

## Decision

- [ ] Retry
- [ ] Change approach
- [x] Stop — R2 is complete

**Time spent:** approximately 0.3 hours, including implementation and review

## Next action

Use the absent-class result in R5's segmentation definition and keep GOOSE out of the
long-range D-04 benchmark.
