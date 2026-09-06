# Survey: MAN TruckScenes

## 0. Survey metadata

| | |
|---|---|
| Dataset | MAN TruckScenes (also called “MAN” in project discussions) |
| Surveyed by | Fatima Sher |
| Date surveyed | 2026-09-03 |
| Reviewed by | Not yet reviewed |
| Review date | Not yet reviewed |
| Survey status | Draft |

## 1. Identity

| Field | Value | Status | Source |
|---|---|---|---|
| Official name | MAN TruckScenes: A multimodal dataset for autonomous trucking in diverse conditions | Confirmed | [NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/71ac06f0f8450e7d49063c7bfb3257c2-Paper-Datasets_and_Benchmarks_Track.pdf) |
| Other names used | MAN; TruckScenes | Confirmed | Project Scope of Work and official paper |
| Authors / organisation | Fent et al.; MAN Truck & Bus SE and Technical University of Munich | Confirmed | [NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/71ac06f0f8450e7d49063c7bfb3257c2-Paper-Datasets_and_Benchmarks_Track.pdf) |
| Venue and year | NeurIPS 2024, Datasets and Benchmarks Track | Confirmed | [Official devkit citation](https://github.com/TUMFTM/truckscenes-devkit) |
| Paper | MAN TruckScenes | Confirmed | [NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/71ac06f0f8450e7d49063c7bfb3257c2-Paper-Datasets_and_Benchmarks_Track.pdf) |
| Project page | MAN TruckScenes | Confirmed | [MAN project page](https://www.man.eu/truckscenes) |
| Devkit repository | TUMFTM/truckscenes-devkit | Confirmed | [GitHub](https://github.com/TUMFTM/truckscenes-devkit) |
| Data host | MAN download page and AWS Open Data | Confirmed | [AWS registry](https://registry.opendata.aws/man-truckscenes/) |

## 2. Fixed checklist — mandatory

| Field | Value | Status | Source |
|---|---|---|---|
| **Domain** — on-road / off-road / both | On-road: motorways, feeder roads, city and terminal environments | Confirmed | [Official paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/71ac06f0f8450e7d49063c7bfb3257c2-Paper-Datasets_and_Benchmarks_Track.pdf) |
| **Radar present** — Yes / No | Yes, six sensors | Confirmed | Official paper, Table 2 |
| Radar type if present — 3D / 4D / N/A | 4D imaging RADAR with range, azimuth, elevation and Doppler/radial velocity | Confirmed | Official paper, §3.1 |
| LiDAR present — Yes / No | Yes, six sensors | Confirmed | Official paper, Table 2 |
| Camera present — Yes / No | Yes, four cameras | Confirmed | Official paper, Table 2 |
| **Primary task** | 3D object detection and multi-object tracking | Confirmed | Official paper, dataset and benchmark sections |
| **Annotation geometry** | Manually reviewed oriented 3D bounding boxes | Confirmed | Official paper, §3.4 |
| **Licence** | CC BY-NC-SA 4.0 | Confirmed | [AWS registry](https://registry.opendata.aws/man-truckscenes/) |
| Commercial use permitted — Yes / No | No; licence is non-commercial | Confirmed | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) |
| Share-alike obligation — Yes / No | Yes | Confirmed | CC BY-NC-SA 4.0 licence |
| Access gating — open / account / licence acceptance / request | Open through AWS without an AWS account; alternate MAN download available | Confirmed | [AWS registry](https://registry.opendata.aws/man-truckscenes/) |
| **Total download size** | Approximately 560 GB for train/validation sensor data; exact current hosted total not remeasured locally | Unverified | Project `DATASET_OVERVIEW.md`; verify against the current AWS object listing before full download |
| Smallest usable subset and its size | v1.2-mini; locally downloaded dataset is approximately 9.6 GB | Confirmed | Local download and project `.gitignore` note |
| Data format(s) | JSON metadata; PCD point clouds; image files; nuScenes-derived table structure | Confirmed | Official devkit and locally inspected files |
| **Devkit available** — Yes / No | Yes | Confirmed | [Official devkit](https://github.com/TUMFTM/truckscenes-devkit) |
| Devkit language and licence | Python; Apache-2.0 | Confirmed | [Devkit repository](https://github.com/TUMFTM/truckscenes-devkit) |
| Annotated frame count | Full dataset: 30,000 annotated samples; local mini: 400 | Confirmed | Official paper, Table 1; local v1.2-mini metadata |
| Max annotation range | More than 230 m | Confirmed | Official paper abstract and dataset analysis |

## 3. Sensor configuration

| Modality | Count | Make / model | Key specs | Status | Source |
|---|---:|---|---|---|---|
| Radar | 6 | Continental ARS 548 RDI | 76 GHz; 20 Hz; 100° × 28° field of view; 4D points | Confirmed | Official paper, Table 2 |
| LiDAR | 2 | Hesai Pandar64 | 64 layers; 10 Hz; 360° × 40°; 200 m at 10% reflectivity | Confirmed | Official paper, Table 2 |
| LiDAR | 4 | Ouster OS0 | 64 layers; 10 Hz; 360° × 90°; 35 m at 10% reflectivity | Confirmed | Official paper, Table 2 |
| Camera | 4 | Sekonix SF3324 | RGB; 10 Hz; 1928 × 1208; 120° × 73° | Confirmed | Official paper, Table 2 |
| IMU / GNSS | 2 + 1 | Xsens MTi-680G-SK; GeneSys ADMA-G-PRO+ | IMU 100 Hz, 9 DoF; GNSS 100 Hz, RTK position accuracy up to 0.01 m | Confirmed | Official paper, Table 2 |
| Other | N/A | N/A | No additional modality needed for the current survey | N/A | N/A |

**Coverage:** The six 4D RADAR sensors provide nearly 360° coverage, with occlusion from the ego truck/trailer noted by the authors. Sensors are distributed across mirrored corner modules and the vehicle body.

**Calibration / extrinsics published:** Yes. The devkit exposes calibrated-sensor records and transformations. The local mini split contains 18 calibrated sensor channels.

## 4. Annotation schema

| Field | Value | Status | Source |
|---|---|---|---|
| Annotation type | Oriented 3D object boxes with category, attributes, visibility and tracking identity | Confirmed | Official paper and local metadata |
| Class count and taxonomy | 27 object categories; local mini contains all 27 category definitions | Confirmed | Official paper and local metadata |
| Are classes grouped / regrouped? | Evaluation uses detection-class mappings; exact model-specific grouping must be recorded per experiment | Confirmed | Official devkit evaluation code |
| Attributes per object | 15 defined attributes in the full dataset; 11 attribute definitions appear in v1.2-mini metadata | Confirmed | Official paper and local metadata |
| Objects tracked across frames? | Yes, instance tokens link objects through scenes | Confirmed | Official paper and local metadata |
| Splits provided (train/val/test) | Mini, train/validation and test releases | Confirmed | [AWS registry](https://registry.opendata.aws/man-truckscenes/) |
| Annotated vs unannotated frame counts | Full dataset: 30,000 annotated samples; intermediate sweeps are distributed separately. Mini: 400 annotated samples | Confirmed | Official paper, official devkit structure and local metadata |
| Schema derived from another dataset? | Yes, based on the nuScenes database format with truck-specific extensions | Confirmed | Official paper and devkit documentation |

## 5. Access and licence

| Field | Value | Status | Source |
|---|---|---|---|
| Licence name and version | Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International | Confirmed | [AWS registry](https://registry.opendata.aws/man-truckscenes/) |
| Link to licence text | https://creativecommons.org/licenses/by-nc-sa/4.0/ | Confirmed | Creative Commons |
| Non-commercial restriction? | Yes | Confirmed | Licence text |
| Restrictions on downstream / handover use | Attribution, non-commercial use and share-alike terms apply to dataset-derived material | Confirmed | Licence text |
| Attribution required? | Yes | Confirmed | Licence text |
| Steps to obtain access | Download mini/trainval/test archives from AWS Open Data or the MAN project page; unpack without overwriting shared folders | Confirmed | Official devkit README and AWS registry |
| Time from request to access | No approval wait through AWS; download time depends on connection | Confirmed | AWS no-sign-request access; local mini download completed |
| Egress or bandwidth cost | AWS states open anonymous access; local internet/storage costs may still apply | Unverified | AWS registry; institution-specific costs not checked |

**Handover implication:** A subsequent student team can obtain the dataset and devkit from public sources, but must retain attribution and comply with the non-commercial/share-alike licence. Raw archives must not be committed to this repository.

## 6. Tooling and feasibility

| Field | Value |
|---|---|
| Devkit install attempted? | Yes |
| Install outcome | Worked |
| OS and environment used | macOS 26.3.1, Apple Silicon arm64, isolated `truckscenes-env` |
| Python / CUDA / dependency versions | Python 3.11.4; no CUDA required; truckscenes-devkit 1.2.0; NumPy 2.4.6; Matplotlib 3.11.1; pypcd4 1.4.3 |
| Errors encountered | New Matplotlib releases do not expose `matplotlib.cm.get_cmap`, which devkit 1.2.0 expects |
| Fixes attempted | Added a narrow compatibility mapping to `matplotlib.colormaps.get_cmap`; rendering then succeeded |
| Hours spent | Approximately 6 hours across download, setup, exploration, visualisation and initial documentation |
| **Single frame loaded and visualised?** | Yes; one paired RADAR/LiDAR sample from each of all 10 mini scenes |
| Evidence | `docs/evidence/truckscenes/`; `experiment-log/0004-fatima-truckscenes-setup-visualisation.md` |
| Recommended next step | Complete an independent review, then select and time-box one compatible pretrained 3D-detection baseline |

## 7. Fit for this project

**Supports the D-04 long-range question?** Conditionally. Annotations extend beyond 230 m, and the selected mini RADAR samples contain returns beyond 150 m. However, the [stock v1.2.0 detection configuration](https://github.com/TUMFTM/truckscenes-devkit/blob/v1.2.0/src/truckscenes/eval/detection/configs/detection_cvpr_2024.json) filters classes at 75 m or 150 m, so it provides no detection score beyond 150 m. Testing D-04 on TruckScenes requires an explicitly approved custom evaluator configuration and range-band protocol, reported separately from the stock benchmark. TruckDrive remains the planned long-range dataset. Point presence alone is not detection evidence.

**Supports the D-03 off-road direction?** No. TruckScenes represents on-road highway, city and logistics-terminal operation, not off-road traversability.

**Supports on-road → off-road transfer?** Potentially as an on-road source domain, but it cannot provide the off-road target domain. Any transfer claim would require a compatible task and label mapping.

**Published baselines available?** The official paper reports CenterPoint-based LiDAR, RADAR and fusion detection baselines plus tracking baselines. Their published numbers are reference context, not results produced by this project.

**Blockers:** A compatible pretrained checkpoint and its hardware requirements have not yet been selected. The mini split is for development rather than final benchmark claims. Kaya access remains relevant for compute-heavy inference.

**Verdict:** **Primary candidate for the on-road modality comparison** — it directly provides annotated 360° 4D RADAR, LiDAR and camera data for autonomous trucks. Its stock evaluator supports the within-range comparison; the beyond-150 m question needs the custom protocol described above.

## 8. Open questions and sources

**Open questions**

- [ ] Which official or third-party pretrained checkpoint can run without training a new model?
- [ ] Which detection-class mapping will the team use consistently for RADAR/LiDAR comparison?
- [ ] If D-04 is attempted here, obtain approval for a custom range configuration and keep its scores separate from the stock benchmark.
- [ ] Is the mini split acceptable for initial inference only, with the full split reserved for Kaya?
- [ ] A teammate must complete the independent review fields.

**Sources**

1. [Fent et al., MAN TruckScenes, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/71ac06f0f8450e7d49063c7bfb3257c2-Paper-Datasets_and_Benchmarks_Track.pdf)
2. [Official TruckScenes devkit](https://github.com/TUMFTM/truckscenes-devkit)
3. [MAN TruckScenes on the AWS Registry of Open Data](https://registry.opendata.aws/man-truckscenes/)
4. [CC BY-NC-SA 4.0 licence](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## Before the PR

- [x] Every mandatory checklist row has a value and status.
- [x] Confirmed external claims link to primary sources.
- [x] Sensor configuration and annotation schema are specific.
- [x] Installation compatibility issue is recorded.
- [x] Verdict and scope limitations are explicit.
- [x] Open questions remain visible rather than guessed.
- [ ] Independent review by another teammate.
