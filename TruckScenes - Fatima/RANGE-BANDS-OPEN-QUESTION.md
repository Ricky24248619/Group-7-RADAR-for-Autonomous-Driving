# Distance-band decision status — 21 September 2026

The working descriptive coverage protocol is recorded in
[`docs/metrics-definitions.md`](../docs/metrics-definitions.md#sprint-3-working-coverage-protocol--21-september-2026).
Use [0,50), [50,100), [100,150), [150,400) and >=400 m. Keep the existing
sensor-frame planar-distance definition explicit. Measured zero counts are 0;
missing measurements and undefined ratios are `no data`.

This resolves the implementation choice for coverage reporting under RY-S3-1.
It does not record client approval. Fabian's approval of a custom detection
evaluation beyond stock class ranges remains open. Coverage does not measure
accuracy and cannot answer that question by itself.

Sprint 2's six-band outputs remain historical results and must not be silently
rewritten. Alternative edges can be supplied explicitly and recorded with new
outputs. The maximum observed range also remains in the CSV.
