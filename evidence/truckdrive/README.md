# TruckDrive Evidence

This folder collates the TruckDrive dataset results and analysis used by the team during Sprint 3. It brings together the dataset statistics, long-range Radar analysis, paired Radar/LiDAR evidence, multi-scene analysis, class/range analysis, and shared result records in one location.

The evidence in this folder is intended for dataset characterisation. Unless explicitly stated otherwise, the results should not be interpreted as detector accuracy, precision/recall, or proof that one sensor modality is universally better than another.

## 1. Dataset coverage

The local TruckDrive mini setup contains 24 scenes.

The retained dataset includes:

- 12,502 Radar frames
- 4,800 bounding-box annotation frames
- 480 lane-line annotation frames
- 526,148 3D bounding boxes
- 27 annotation classes

Radar, annotations, calibrations and poses are available across the 24 mini scenes. Camera and LiDAR data were retained only for selected representative scenes, so the local dataset should not be interpreted as having complete multimodal coverage for every scene.

Detailed dataset statistics are available in:

`dataset-statistics.md`

## 2. Selected-frame Radar range analysis

A lightweight Radar subset was used to characterise the range distribution across the 24 mini scenes.

For each scene, the first synchronization ID shared by the joint-Radar detections and bounding-box annotations was selected.

Across the 24 selected Radar frames:

- Total Radar returns: 71,206
- Radar returns at or beyond 150 m: 6,746
- Share at or beyond 150 m: 9.47%

The 6,746 value therefore refers specifically to Radar returns in these 24 selected frames. It does not refer to all 12,502 Radar frames in the local mini dataset.

Planar range was calculated as:

`range = sqrt(x^2 + y^2)`

where `x` and `y` are the Radar return coordinates in the relevant sensor frame.

The supporting files are stored in:

`saved-comparison/`

This folder contains the saved Radar range distribution, class-count table, plot and analysis manifest.

The shared result record is:

`records/0015-truckdrive-saved-evidence-reanalysis.json`

## 3. Paired Radar/LiDAR evidence

Paired Radar/LiDAR evidence is available for `scene_28_1`.

The static paired analysis contains:

- 200 paired frames
- 8,113 valid non-ego paired object observations
- Maximum labelled planar centre range: approximately 399.03 m
- 2,828 Radar returns at or beyond 300 m

The Radar-return count at long range represents calibrated geometric sensor returns. It is not a count of verified object detections or true positives.

The paired evidence files are stored in:

`paired-scene-28-1/`

This folder includes:

- `manifest.json` - analysis metadata and configuration
- `download_manifest.json` - source/download information
- `sensor_frames.csv` - paired sensor-frame information
- `object_counts.csv` - object-level geometric support measurements
- `excluded_annotations.csv` - annotations excluded from the analysis
- `example_car_200_250m.png` - a representative long-range paired example

The corresponding shared result record is:

`records/0018-truckdrive-long-range-paired-support.json`

## 4. Multi-scene long-range support analysis

A wider shared analysis used five TruckDrive mini scenes:

- `scene_28_1`
- `scene_28_6`
- `scene_28_12`
- `scene_28_18`
- `scene_28_24`

The protocol sampled 40 timestamp-spaced frames per scene, with 190 frames used in the matched timing comparison.

For vehicle observations between 200 m and 400 m:

- Matched vehicle observations: 504
- Static LiDAR geometric support: approximately 80.36%
- Static Radar geometric support: 37.5%

Geometric support was defined using the presence of sensor returns within the relevant annotated box. These values are not detector accuracy measurements.

The analysis also retained timing, box-margin and track sensitivities. The results therefore should not be used to claim universal LiDAR or Radar superiority.

The final summary evidence is stored in:

`multiscene-summary/`

This folder contains the overall summary, per-scene and per-class results, first-per-track results, scene manifest, verification information and a visualisation of scene differences.

The corresponding shared result record is:

`records/0020-truckdrive-multiscene-long-range-support.json`

## 5. Class and range support analysis

The same five-scene subset was also analysed by native object class and distance.

The analysis contains:

- 190 matched sampled frames
- 4,306 object observations

These observations include repeated tracks and therefore should not be treated as independent trials.

Support was defined as at least one sensor return within an annotated 3D box, with exact-box and expanded-box sensitivity retained in the analysis.

The results are descriptive dataset characterisation rather than detector accuracy. Class-specific counterexamples also mean that the results do not support a universal claim that one modality is always superior.

The final TruckDrive class/range evidence is stored in:

`class-range-support/`

This folder contains class-level support results, scene/class results, matched-track summaries, overall results, verification information and the TruckDrive missing-support visualisation.

The corresponding shared result record is:

`records/0025-truckdrive-class-range-support.json`

## 6. Evidence structure

```text
evidence/truckdrive/
|-- README.md
|-- dataset-statistics.md
|
|-- saved-comparison/
|   |-- class_counts.csv
|   |-- manifest.json
|   |-- radar_ranges.csv
|   `-- radar_ranges.png
|
|-- paired-scene-28-1/
|   |-- download_manifest.json
|   |-- example_car_200_250m.png
|   |-- excluded_annotations.csv
|   |-- manifest.json
|   |-- object_counts.csv
|   `-- sensor_frames.csv
|
|-- multiscene-summary/
|   |-- by_class.csv
|   |-- by_scene.csv
|   |-- calibration_verification.json
|   |-- first_per_track.csv
|   |-- manifest.json
|   |-- scene_differences.png
|   |-- scene_manifest.csv
|   |-- summary.csv
|   `-- verification.json
|
|-- class-range-support/
|   |-- class_support.csv
|   |-- manifest.json
|   |-- matched_track_summary.csv
|   |-- overall.csv
|   |-- scene_class_support.csv
|   |-- truckdrive_missing_by_class.png
|   `-- verification.json
|
`-- records/
    |-- 0015-truckdrive-saved-evidence-reanalysis.json
    |-- 0018-truckdrive-long-range-paired-support.json
    |-- 0020-truckdrive-multiscene-long-range-support.json
    `-- 0025-truckdrive-class-range-support.json
```

The evidence is organised by analysis purpose:

- `saved-comparison/` contains the committed 24-frame Radar range and class-count reanalysis.
- `paired-scene-28-1/` contains detailed paired Radar/LiDAR evidence for one representative scene.
- `multiscene-summary/` contains the final summary outputs from the five-scene long-range support analysis.
- `class-range-support/` contains the final TruckDrive class and distance support analysis.
- `records/` preserves the schema-valid shared result records and their original provenance.

## 7. Interpretation and limitations

The TruckDrive evidence supports the following conclusions:

- The retained mini dataset provides substantial Radar and annotation coverage across 24 scenes.
- The selected 24-frame Radar subset contains measurable long-range returns, including 6,746 returns at or beyond 150 m.
- Paired Radar/LiDAR data is available for selected scenes and can be used for geometric support analysis.
- The shared five-scene analysis provides additional evidence about sensor support at long range and across object classes.

Important limitations are:

- The 24-frame Radar range subset is a sampled subset and does not represent every Radar frame.
- Camera and LiDAR are not retained locally for every mini scene.
- A sensor return inside an annotated box is geometric support, not a verified detection.
- Repeated object tracks mean that object observations are not all independent trials.
- Timing alignment, annotation choice, box margins and scene selection can affect comparisons.
- The current evidence does not establish universal superiority of Radar or LiDAR.

## 8. Provenance

This folder collates existing TruckDrive results produced and used by the project team. Individual shared result records retain their original owner, environment, commands, measurements and notes so that authorship and provenance are not lost when the evidence is collected into this common folder.