# TruckScenes raw-data rebuild — 21 September 2026

The official v1.2-mini release is now installed on Ricky's Windows machine at
`F:\RADAR\datasets\TruckScenes\man-truckscenes`. This resolves the local
raw-data availability blocker reported earlier on 21 September.

Source: [MAN TruckScenes on the AWS Open Data Registry](https://registry.opendata.aws/man-truckscenes/),
`release/mini/`, CC BY-NC-SA 4.0. Data remains outside the repository.

## Integrity and completeness

- Metadata archive: 13,679,356 bytes; MD5 matched
  `2d14559121bbff0011e580098d84d0d3`.
- Sensor archive: 9,625,794,846 bytes; its 8 MiB multipart MD5 ETag matched
  `31cc75c897b7e253245c7b25c2fffdaf-1148`.
- Every extracted ZIP entry passed its CRC check.
- Metadata contains 10 scenes, 400 annotated samples and 25,750 annotations.
- All 43,556 referenced sensor files are present: 6,400 keyframe files and
  37,156 non-keyframe sweeps. No missing sensor files were found.

## Rebuild result

Using Python 3.11.9, truckscenes-devkit 1.2.0, NumPy 1.26.4 and pypcd4 1.4.3,
the manifest and range-count scripts were run against the freshly extracted data.
All three outputs match the Git blobs at comparison commit `4dc33ab` byte for
byte (Git's LF bytes, rather than checkout-dependent Windows line endings).

| Output | SHA-256 | Result |
|---|---|---|
| sample-manifest.csv | `2e18de8dc506006d12c6a44c5569b1728c3f8ce44ba0ecbc2e82412fe2c01b80` | Exact match |
| sample-manifest.json | `122a76644d6993025556d8744bdae7d500ebad4ce99dc2b87ff0a2b296647c1b` | Exact match |
| range-bands.csv | `78fc8641aa13660df49c23cbd3f47ede540f97d2ad273c79bb94e73975b8f637` | Exact match |

Rebuilt files and the machine-readable verification record are in
`F:\RADAR\outputs\truckscenes-rebuild-2026-09-21`. `TRUCKSCENES_ROOT` is saved
as a Windows user environment variable; newly launched applications inherit it.
Existing shells can pass the data root explicitly:

```sh
python scripts/truckscenes_sample_manifest.py --data-root <data-root> --csv-output <output>/sample-manifest.csv --json-output <output>/sample-manifest.json
python scripts/truckscenes_range_bands.py --data-root <data-root> --manifest <output>/sample-manifest.json --csv-output <output>/range-bands.csv
```

This is an agent-run reproduction from an independently downloaded copy, not a
human reviewer signoff. It establishes that the declared raw subset reproduces
the committed counts. It does not establish representative sampling, equal
sensor geometry, completed model inference or radar/LiDAR accuracy.
The outside-pair human acceptance step remains open.
