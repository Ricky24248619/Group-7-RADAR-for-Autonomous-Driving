# Sensor identity check — 21 September 2026

The [MAN TruckScenes paper, section 3.1, Table 2 and Figure 2](https://arxiv.org/html/2407.07462v2#S3.SS1)
places the Top Front LiDAR on the roof and identifies the three roof units as
downward-tilted Ouster OS0 sensors for blind-spot coverage. The side corner
modules contain the Hesai Pandar64 units. Table 2 gives nominal ranges of
35 m and 200 m respectively at 10% reflectivity; these are specifications,
not hard cutoffs or measured object-detection ranges.

Consequently, `LIDAR_TOP_FRONT` versus `RADAR_LEFT_FRONT` is a comparison
of these two selected channels. It must not be used to conclude that LiDAR
generally cannot reach the radar's measured distances. Different mounting
positions, tilts, fields of view and own-frame distance planes remain confounders.
Confirm calibration/token joins against the local release before constructing
a new common-frame or corner-module analysis.

This check used the source paper and its labelled sensor-placement figure;
it did not inspect a locally installed TruckScenes dataset.
