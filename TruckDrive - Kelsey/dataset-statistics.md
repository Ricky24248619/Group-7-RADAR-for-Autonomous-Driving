# TruckDrive mini dataset statistics

These measurements come from the local TruckDrive mini split prepared for this project.

The current local setup contains all 24 mini scenes. Radar, annotations, calibrations
and poses are available for all scenes. `scene_28_1` and `scene_28_22` also contain
Camera and LiDAR data for synchronized multimodal checks.

The statistics below were generated using:

`scripts/truckdrive_stats.py`

---

## 1. Dataset coverage

| Item | Measured value |
|---|---:|
| Mini scenes | 24 |
| Radar frames | 12,502 |
| Bounding-box annotation frames | 4,800 |
| Lane-line annotation frames | 480 |
| 3D bounding boxes | 526,148 |
| Object classes | 27 |

Each scene contains approximately 520 Radar frames, 200 bounding-box annotation frames
and 20 lane-line annotation frames.

All 4,800 bounding-box annotation frames have a matching Radar frame based on the
TruckDrive synchronization ID.

---

## 2. Object class distribution

The following counts were measured directly from the bounding-box annotation JSON
files across all 24 mini scenes.

| Class | Bounding boxes |
|---|---:|
| Vehicle | 313,408 |
| TrafficSign | 81,450 |
| RoadDebris | 30,664 |
| Vehicle-Passenger | 29,920 |
| Vehicle-SemiTruck-Trailer | 13,803 |
| Vehicle-SemiTruck-Cab | 11,165 |
| RoadObstruction-Barrel | 10,207 |
| Person | 7,446 |
| RoadObstruction | 5,793 |
| Vehicle-EgoVehicle-Cab | 4,817 |
| Vehicle-EgoVehicle-Trailer | 4,402 |
| Vehicle-Trailer | 3,397 |
| Vehicle-SingleUnitTruck | 2,310 |
| RoadObstruction-Delineator | 1,981 |
| RoadObstruction-Cone | 1,208 |
| Vehicle-Equipment | 864 |
| TrafficSignal | 624 |
| Vehicle-RV | 554 |
| Person-Pedestrian | 456 |
| DynamicTrafficSign | 374 |
| Vehicle-Other | 342 |
| VRUvehicle-Motorcycle | 305 |
| VRUvehicle | 289 |
| Person-Rider | 198 |
| Vehicle-Bus | 129 |
| RoadObstruction-Barricade | 35 |
| Vehicle-SchoolBus | 7 |

The class counts sum to 526,148 bounding boxes.

---

## 3. Selected Radar sample measurements

To obtain a consistent small sample across the whole mini split, one synchronized
annotated Radar frame was selected from each of the 24 scenes.

For each scene, the first synchronization ID shared by Radar and bounding-box
annotations was used.

Across these 24 selected frames:

| Measurement | Value |
|---|---:|
| Selected scenes | 24 |
| Selected Radar frames | 24 |
| Radar detections | 71,206 |
| Detections at 150 m or greater | 6,746 |
| Share at 150 m or greater | 9.47% |

---

## 4. Radar range distribution

Range is calculated in the Radar frame using:

`sqrt(x² + y²)`

The following counts are summed across the 24 selected annotated Radar frames.

| Range band | Radar detections |
|---|---:|
| 0–25 m | 13,717 |
| 25–50 m | 22,264 |
| 50–80 m | 16,396 |
| 80–100 m | 5,356 |
| 100–150 m | 6,727 |
| 150 m+ | 6,746 |
| **Total** | **71,206** |

The selected samples therefore contain Radar returns beyond 150 m. This confirms that
long-range Radar data is present in the mini split.

This does not demonstrate object-detection accuracy at long range. No detection model
was evaluated in this work.

---

## 5. Representative scenes

The first complete scene used for setup and feasibility testing was:

### `scene_28_1`

This scene was used to verify:

- the official TruckDrive dataset viewer
- Camera loading
- Aeva LiDAR loading
- Continental Radar loading
- projected Camera bounding boxes
- direct synchronized Camera, LiDAR and Radar access using Python

The synchronized sensor-check script found 258 Camera/LiDAR/Radar common frames in
this scene.

---

### `scene_28_22`

This scene was selected as an additional long-range representative scene after the
24-scene Radar survey.

For the selected annotated frame:

- total Radar detections: 4,377
- detections between 100–150 m: 640
- detections at 150 m or greater: 708

This was the highest 150 m+ count among the 24 selected scene samples.

Camera and LiDAR data were therefore added locally for this scene so that it can be
used for later multimodal visualisation.

The synchronized sensor-check script found 259 Camera/LiDAR/Radar common frames in
this scene.

---

## 6. Synchronized sensor access

`scripts/truckdrive_sensor_check.py` was tested successfully on both complete scenes.

### `scene_28_1`

- Camera: 3848 × 2168 RGB
- LiDAR: 217,519 points in the selected frame
- LiDAR fields per point: 11
- Radar: 2,672 detections in the selected frame
- Radar fields per detection: 33

### `scene_28_22`

- Camera: 3848 × 2168 RGB
- LiDAR: 451,201 points in the selected frame
- LiDAR fields per point: 11
- Radar: 3,038 detections in the selected frame
- Radar fields per detection: 33

These checks demonstrate that synchronized Camera, LiDAR and Radar files can be read
directly without relying only on the official graphical viewer.

---

## 7. Interpretation and limits

- The complete 24-scene mini split was not downloaded with every modality because the
  full mini download is approximately 282.71 GB.
- Radar, annotations, calibrations and poses were retained across all 24 scenes because
  these components are much smaller and support dataset-wide characterisation.
- Camera and LiDAR were retained for selected representative scenes because they require
  substantially more local storage.
- The 150 m+ distribution is based on one selected annotated Radar frame per scene,
  not all 12,502 Radar frames.
- Radar return counts describe sensor measurements, not object-detection performance.
- No model inference, precision, recall or mAP measurements were produced during this
  stage.