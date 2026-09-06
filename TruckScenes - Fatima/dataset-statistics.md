# MAN TruckScenes v1.2-mini statistics

These measurements come from the local `v1.2-mini` metadata and the first annotated sample from each of its 10 scenes. They are not full-dataset benchmark results.

## Dataset inventory

| Item | Measured value |
|---|---:|
| Scenes | 10 |
| Annotated samples | 400 |
| Sample annotations | 25,750 |
| Tracked instances | 1,094 |
| Categories | 27 |
| Sample-data records | 43,556 |
| Calibrated sensor channels | 18 |

## Sensor configuration

| Modality | Channels |
|---|---:|
| 4D RADAR | 6 |
| LiDAR | 6 |
| Camera | 4 |
| IMU | 2 |

The six RADAR sensors are Continental ARS 548 RDI units. The LiDAR setup contains two Hesai Pandar64 and four Ouster OS0 sensors.

## Selected paired samples

The point measurements use `RADAR_LEFT_FRONT` and `LIDAR_TOP_FRONT` for the first annotated sample in each scene.

| Measurement | Value |
|---|---:|
| Selected scenes | 10 |
| RADAR points | 4,571 |
| LiDAR points | 165,588 |
| LiDAR/RADAR point-count ratio | 36.2× |
| RADAR points at 150 m or greater | 305 |
| Share of selected RADAR points at 150 m or greater | 6.67% |

These point counts describe this fixed sample set only. They do not compare detector performance and do not establish precision, recall or mAP.
