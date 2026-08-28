# EXP-0001 — Windows GOOSE environment and smoke test

- **Date started / completed:** 27 August 2026 / 27 August 2026
- **Owner:** Ricky Yuen
- **Workstream / story:** WS2 / R1 and R1b

## Goal

Reproduce Damien's GOOSE rendering environment on a clean Windows machine, verify the
downloaded validation split, and audit the machine for an NVIDIA GPU.

## Environment

- Microsoft Windows 10 Home, 64-bit, version 10.0.19045 (build 19045)
- Native PowerShell; no WSL, Docker, or administrator shell
- Python 3.11.9 at `%USERPROFILE%\.venvs\radar\Scripts\python.exe`
- numpy 1.26.4, matplotlib 3.8.4, PyYAML 6.0.2
- NVIDIA GeForce GTX 1660, 6,144 MiB VRAM; driver 560.94; CUDA runtime reported by
  `nvidia-smi` as 12.6

This was the first setup on this machine. The pre-existing Python installations were
3.14 (64-bit) and 3.8 (32-bit), neither suitable for the documented environment.

## Dataset / data subset

GOOSE 3D validation archive from
`https://goose-dataset.de/storage/goose_3d_val.zip`.

- Downloaded archive: 3,498,402,435 bytes (about 3.26 GiB)
- Extracted to `C:\goose\goose_3d_val`, outside the repository
- Verified 961 `.bin` LiDAR scans and 961 `.label` files across eight scenario
  directories

## Steps and commands

```powershell
winget install --id Python.Python.3.11 -e --scope user `
  --accept-package-agreements --accept-source-agreements --silent

py -3.11 -m venv "$env:USERPROFILE\.venvs\radar"
$PY = "$env:USERPROFILE\.venvs\radar\Scripts\python.exe"
& $PY -m pip install pip==26.2.1
& $PY -m pip install numpy==1.26.4 matplotlib==3.8.4 PyYAML==6.0.2

New-Item -ItemType Directory -Force `
  -Path C:\goose\zips, C:\goose\goose_3d_val | Out-Null
curl.exe -# -L -o C:\goose\zips\goose_3d_val.zip `
  https://goose-dataset.de/storage/goose_3d_val.zip
tar -xf C:\goose\zips\goose_3d_val.zip -C C:\goose\goose_3d_val

(Get-ChildItem "$DATA\lidar" -Recurse -Filter *.bin).Count
(Get-ChildItem "$DATA\labels" -Recurse -Filter *.label).Count

& $PY scripts\goose_render_frame.py --root $DATA --index 0 `
  --out "$env:TEMP\goose-smoke-ricky.png"
nvidia-smi
```

## Outcome

- [x] Success — worked as intended
- [ ] Partial — describe what worked and what didn't
- [ ] Failure — did not achieve the goal

The renderer printed `Found 961 annotated frames.`, loaded the full 64-class mapping,
and wrote the PNG. Visual inspection confirmed that the bird's-eye and side-elevation
views match the structure and colours of the committed examples. The first frame had
169,883 points and no scan/label length mismatch.

The GPU audit disproves risk R-08's current premise that no team member has a discrete
NVIDIA GPU. The GTX 1660 has 6 GiB VRAM. This does **not** put Pointcept/PTv3 into the
current fortnight; model compatibility and VRAM requirements need a separate team
decision and experiment.

## Attempted fixes

None. Installation, download, extraction, and rendering all succeeded on the first
attempt.

## Decision

- [ ] Retry
- [ ] Change approach
- [x] Stop — the R1 environment setup path is complete

**Time spent:** approximately 0.6 hours

## Next action

Ricky proceeds to R2 dataset statistics and R3 traversability mapping. Report the GTX
1660 result to the team and amend risk R-08 at the next risk-register update; do not
start CUDA baselines during this fortnight.
