# EXP-0029 — TruckScenes matched radar and LiDAR range-band coverage

- Date: 29 September 2026.
- Owner: Fatima Sher; reviewer Kelsey Chen. Story FA-S3-1, Epic C.
- Question: across a declared subset, where do RADAR_LEFT_FRONT and LIDAR_TOP_FRONT returns actually land by distance?
- Method: the first annotated sample of each of the 10 mini scenes, declared in `sample-manifest.csv` before any measurement was taken. Range is `sqrt(x^2 + y^2)` in each sensor's own frame; no ego or global transform is applied. Bands 0 / 50 / 100 / 150 / 400 m with an open band above the highest edge, lower edges inclusive and upper edges exclusive, per the 21 September working coverage protocol in `docs/metrics-definitions.md`.
- Result record: 0034. [Range-band report and figures](../TruckScenes%20-%20Fatima/RANGE-BANDS.md).
- Measured: radar 4,571 returns spread 1,655 / 1,670 / 941 / 305 / 0 across the five bands, furthest return 189.46 m. LiDAR 165,588 returns at 165,520 / 53 / 15 / 0 / 0, furthest return 140.25 m. Every band sums to its stated denominator and every share matches its own count.
- Reproducibility: the CSV and manifest carry no timestamp or machine detail and are written with LF endings, so regeneration is byte-identical and `git status` stays empty. The figures read the committed CSV and never open the dataset, so every plotted value traces to a committed number. Figures are reproducible against themselves on one machine but not byte-identical across operating systems, because text is rendered with the host's own fonts.
- Limitations: coverage, not detection — no model is run and no annotation is read, so a populated far band is not evidence of detection at that distance. Point density is not a quality measure. One radar of six against one LiDAR of six, with differing fields of view not accounted for. Ten of 400 annotated samples. No shared coordinate frame between the two modalities. Weather is not analysed.
- Principal confound: `LIDAR_TOP_FRONT` is a roof Ouster OS0 rated 35 m at 10% reflectivity, angled down for blind-spot coverage, confirmed from mounting heights in the dataset's own `calibrated_sensor` table rather than from the paper alone (`sensor-inventory.csv`). Its returns concentrating below 50 m is that sensor working as designed, not a LiDAR range finding. This comparison is channel-specific and is not a modality-level result.
- Next step: repeat on `LIDAR_LEFT`, the corner-module Hesai Pandar64 rated 200 m, which is the like-for-like channel against `RADAR_LEFT_FRONT`. Until that is done, no radar-versus-LiDAR range claim should be drawn from this subset.
- Validation: the full dependency-light unittest suite plus both existing validators. Cross-artefact acceptance checks A-1 to A-5 and A-7 run in CI; A-6 (regeneration against the dataset) needs a person with the 9.6 GB release and has not yet been performed by anyone outside the pair.

This log records an agent-assisted analysis, not a completed human acceptance review.
