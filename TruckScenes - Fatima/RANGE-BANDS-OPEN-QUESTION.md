# Open question: which distance bands does the TruckScenes range analysis use?

**Raised by:** Fatima Sher · **Story:** FA-S3-1 · **Decision owner:** Ricky Yuen
(RY-S3-1 covers distance bands in the comparison protocol) · **Needs:** Fabian's
confirmation, per open question 3 in [`docs/metrics-definitions.md`](../docs/metrics-definitions.md)

## The problem

Three different sets of band edges are currently in use or proposed across this
repository. They produce different numbers from the same point cloud, so a
figure cannot be read without knowing which set produced it.

| Source | Band edges |
|---|---|
| `scripts/truckscenes_stats.py` (Sprint 2, in `main`) | 0–25 / 25–50 / 50–80 / 80–100 / 100–150 / 150 m+ |
| `docs/metrics-definitions.md`, open question 3 | 0–50 / 50–100 / 100–150 / 150–400 m |
| D-04 reporting requirement | "results by range band", edges unspecified |

The metrics document records its four-band set as a **proposal pending
confirmation**, not an agreed standard. The Sprint 2 script predates it.

## Why it blocks the Sprint 3 analysis

FA-S3-1 asks for "counts/proportions by documented distance bands". The word
that matters is *documented* — a band count with undeclared edges cannot be
compared with anyone else's, and `docs/metrics-definitions.md` requires every
reported number to carry its range band.

There is also a hard limit worth restating, since it constrains what the top
band can ever mean:

- The stock TruckScenes v1.2.0 detection configuration filters classes at
  **75 m or 150 m** depending on class, so it produces **no detection metric
  beyond 150 m**. Testing D-04's beyond-150 m question on TruckScenes needs an
  explicitly approved custom evaluator configuration, reported separately.
- The range analysis under FA-S3-1 counts **sensor returns**, which is
  **coverage**, not detection. A populated `>150 m` band shows that returns
  exist at that distance. It is not evidence that anything can be detected
  there.

## Proposal

1. **Make the band edges a parameter of the analysis script**, not a constant.
   The decision is not ours to make and has not been made; hard-coding either
   set would have to be undone.
2. **Default to the four edges in `docs/metrics-definitions.md`**
   (0–50 / 50–100 / 100–150 / 150–400 m), as the most recently proposed set,
   and record the edges used in the output alongside the counts.
3. **Also record the maximum observed range per sensor per sample.** A band
   count says returns exist beyond 150 m; it does not say whether they stop at
   160 m or reach 250 m. The maximum answers that directly and does not depend
   on which edges are agreed.
4. **An empty band reads `no data`, never `0`** — required by both
   `docs/metrics-definitions.md` and D-04.
5. **Do not retrofit `scripts/truckscenes_stats.py`.** Its six-band output is
   already cited by result record `0009-truckscenes-mini-characterisation` and
   `TruckScenes - Fatima/dataset-statistics.md`. Changing its edges would
   silently alter numbers already recorded. If the team wants one band set
   everywhere, that is a separate, deliberate change with its own record.

## What is not blocked

The sample subset, channels and coordinate frame are settled and committed —
see [`SAMPLE-MANIFEST.md`](SAMPLE-MANIFEST.md). Band edges affect how the
counts are grouped, not which samples are measured, so the analysis can be
built and run before the decision lands.

## Status

Open. To be raised with Ricky, and through him with Fabian alongside the D-01 /
D-04 confirmations already listed in `docs/metrics-definitions.md`. This file
records the conflict; it does not resolve it, and nothing here should be read
as an agreed team decision.
