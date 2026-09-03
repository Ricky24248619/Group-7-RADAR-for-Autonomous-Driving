# MAN TruckScenes context

MAN TruckScenes is a multimodal autonomous-trucking dataset recorded in motorway, feeder-road, city and logistics-terminal environments. It provides synchronized 4D RADAR, LiDAR, camera and positioning data together with reviewed 3D object annotations.

The dataset is relevant to this project because it supports on-road investigation of how RADAR, LiDAR and camera sensing differ under varied traffic, lighting and weather conditions. Its six 4D RADAR sensors also make it useful for studying long-range returns, although sensor returns alone do not demonstrate successful object detection.

TruckScenes complements the other selected datasets. GOOSE focuses on off-road terrain and traversability, while TruckDrive provides a separate on-road dataset. Results from these datasets should be documented within their own settings before any cross-dataset comparison is attempted.

This work uses the `v1.2-mini` split. It contains 10 scenes and 400 annotated samples and is intended for setup, development and small feasibility checks. It is not a substitute for full-dataset training or benchmark evaluation.

Official sources:

- [MAN TruckScenes paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/71ac06f0f8450e7d49063c7bfb3257c2-Paper-Datasets_and_Benchmarks_Track.pdf)
- [Official TruckScenes devkit](https://github.com/TUMFTM/truckscenes-devkit)
- [AWS Registry of Open Data](https://registry.opendata.aws/man-truckscenes/)

