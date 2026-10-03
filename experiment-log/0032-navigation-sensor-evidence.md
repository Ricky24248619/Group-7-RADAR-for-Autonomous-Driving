# EXP-0032 Terrain maps and modality-specific evidence

3 October 2026 · Ricky Yuen · result 0039 · bounded CPU characterisation

Reused 31 hash-verified GOOSE scans and saved predictions; all 25,117 corrected
TruckScenes observations; and all 17 eligible RADIATE fog frames. No GPU run,
training, raw acquisition, new camera model or autonomy implementation.

The analysis records unobserved map cells, nearby ground-reference availability,
raw relative vertical position, orthogonal plane shape, conservative square map
footprints, panoramic-camera visibility versus sensor return presence, and radar
contrast/persistence in labelled and unlabelled footprints. The author RELLIS-3D
release was audited at a pinned commit as additional follow-up data; no project
performance result is claimed for it.

All eight analysis output files matched a fresh-directory reproduction. Independent
scalar algorithms matched footprint and plane counts on all 31 frames; 1,160
sampled nearest-ground queries matched brute-force minima; 390 visibility strata
matched direct metadata/table recounts. This is independent algorithm checking by
the same analyst, not independent human or client approval.

The final synthesis contains 20 different decision questions and preserves the
earlier sources. D11 is retained as support; D07/D17 and D14/D16 are consolidated.
Repeated ranges, classes, frames and settings do not create extra headlines.

Limits: semantic candidate ground is not physical passability; raw delta-z is not
validated object height; map footprints are not routes or actual vehicle geometry;
plane RMS is not grip or grade. Camera visibility is not sensor-specific
visibility. Fog comparison regions are unlabelled, not verified empty. Sensor
return presence and radar contrast are not recognition or safety metrics.

Reproduction command and exact source/output hashes are in
`results/evidence/p5-oct03/manifest.json` and result 0039. Numerical evidence and
plain findings are public; reports, planning and raw data remain local.
