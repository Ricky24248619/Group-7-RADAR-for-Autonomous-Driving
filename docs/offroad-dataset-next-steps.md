# Additional datasets for useful radar/LiDAR comparisons

Primary sources checked 26 September 2026. “Candidate” is not a downloaded or
validated benchmark. We prioritize references that answer a distinct question,
rather than adding large downloads with no matching labels.

| Dataset | Useful question | Verified resource | Status / limitation |
|---|---|---|---|
| **STONE** | Ground patches versus protruding geometry, 2–40 m | Three 4D radar streams, 128-channel LiDAR, 3D traversability voxels | **20 paired frames processed**; [actual results](stone-paired-terrain-pilot.md). Physical radar translations and visibility unresolved. |
| **CORD — Clemson Off-Road Dataset** | Independent off-road comparison, potentially farther range | Official catalog lists LiDAR, long-range radar, >1,500 annotated LiDAR clouds and four environment types | **Promising next independent source**, 1.57 TB full size. Controlled public access via Globus/request form; no download or request sent. Need annotation distances, radar elevation, calibration and a subset manifest before claiming suitability. |
| **Great Outdoors** | Off-road radar range/azimuth evidence and vegetation/weather context | Official project provides LiDAR, Navtech radar, bags and image/thermal segmentation resources | 2D scanning radar cannot directly be scored as the same height-resolved point-cloud task. Inspect a small sequence and label availability before designing a BEV comparison. No new analysis completed here. |
| **RADIATE** | Whether radar retains useful object evidence when LiDAR degrades in fog, rain or snow | Paired radar/LiDAR, calibration, SDK, eight object classes; radar configured to 100 m | Strong weather follow-up, **not** ground/height or >150 m benchmark. Radar images are 2D and this release has no Doppler. No new download or results here. |
| **GOOSE** | Surface/material and ground-versus-obstacle model errors | Existing local labelled LiDAR and saved predictions | Existing completed LiDAR diagnostic; local files do not supply paired radar terrain scores. |

Sources: [STONE](https://github.com/konyul/STONE),
[Clemson official catalog](https://www.clemson.edu/cecas/vipr-gs/research/data-catalog.html),
[Great Outdoors project](https://www.unmannedlab.org/the-great-outdoors-dataset/),
[Great Outdoors downloads](https://www.unmannedlab.org/the-great-outdoors-dataset/download/),
[RADIATE documentation](https://pro.hw.ac.uk/radiate/doc/dataset/),
[GOOSE](https://goose-dataset.de/).

**Recommended sequence:** first fix the STONE calibration ambiguity exposed by
the measured sensitivity; then sample another STONE environment. Investigate a
small CORD subset for independent off-road evidence once access is available.
Use RADIATE as a separate weather experiment rather than mixing weather/object
scores into terrain coverage. The large F: allowance removes a storage barrier,
but it does not supply missing calibration, labels or compute-efficient subsets.

RaDelft and the ROSS paper were also checked. [RaDelft](https://github.com/RaDelft/RaDelft-Dataset)
is useful for urban imaging-radar research but is less direct for this off-road
question. [ROSS](https://arxiv.org/abs/2310.13551) describes off-road radar semantic
segmentation using LiDAR-derived labels; a runnable public data/code release was
not verified, so no model result is promised from it.
