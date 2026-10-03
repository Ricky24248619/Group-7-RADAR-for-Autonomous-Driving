# EXP-0031 — Temporal sensing and consequential terrain evidence

- **Date started / completed:** 3 October 2026 / 3 October 2026.
- **Owner:** Ricky Yuen; analyses implemented and executed with Codex assistance.
- **Workstream / story:** RADAR dataset analysis and reproducible findings.

## Goal

Measure persistence of paired object support, directional terrain errors, information lost during map aggregation, descriptive weather controls and eligibility of independent terrain inputs.

## Environment

Existing native Windows RADAR Python 3.11 environment with NumPy/Pillow/Matplotlib. CPU only for this attempt. All AI outputs and GPU timings are reused from the saved earlier runs; no new model run or dependency installation.

## Dataset / data subset

Seven fixed TruckDrive clips (scene_28_1/6/12/18/24 and follow-up 3/15), restricted to common static/aligned keys. TruckScenes v1.2-mini all 25,117 corrected observations, rigid counts restricted to those identities. GOOSE all original 24 and follow-up seven selected frames; p64/p128 comparison on the seven only. RADIATE tiny_foggy all 17 eligible frames and four target tracks. WildScenes pinned official splits at `9eb4e10b4483a634159e2b371be0437e465fe218`: five first chronological labelled frame pairs, one per K-01/K-03/V-01/V-02/V-03, 8,497,120 new raw bytes. Exact IDs and hashes are in the evidence manifests. Raw data remains outside Git.

## Steps and commands

Use the commands and external-data requirements in [the findings reproduction section](../docs/temporal-terrain-findings-oct03.md#reproduction). Scripts do not regenerate model predictions. For a fresh WildScenes sample acquisition, the public CSIRO API resolves individual file links; it reads a metadata listing and downloads only the selected bounded raw files. The unsigned direct S3 path returned HTTP 401; the public API's issued download links succeeded without private authentication. The source decoder and label map were captured from the pinned author revision.

Run `python scripts/validate_result.py`, `python scripts/validate_experiment_logs.py`, `python -m unittest discover -s tests -v` and `git diff --check`. Both analysis scripts were also rerun into a separate local output directory and their derived outputs compared with the published evidence.

## Outcome

- [x] Success — all bounded analyses executed, all selected raw/prediction hashes reconciled, derived outputs reproduced.
- [ ] Partial.
- [ ] Failure.

Seven candidate messages extend the preserved ten-message consolidation. The findings document reports practical uses and limitations; it does not claim that seventeen messages meet a twenty-message target. See [result 0038](../results/records/0038-temporal-terrain-evidence.json) and [verification](../results/evidence/p3-p4-oct03/verification.json).

## Attempted fixes

TruckDrive stored static/aligned populations differ, so the analysis uses the frozen shared-key rule and reports the key audit. Fog source observations contain both exact and expanded footprints; these were scored as separate sensitivity variants rather than duplicate consecutive samples. WildScenes author metadata confirmed the actual native IDs and ignored water class; an obsolete commented mapping was not used.

## Decision

- [ ] Retry.
- [ ] Change approach.
- [x] Stop — the authorised bounded analyses are complete; no new GPU, detector or transfer run follows automatically.

**Time spent:** not independently tracked; this log is not a claim of twelve weeks of effort.

## Next action

Human review of the candidate conclusions and their client decisions; retain the unmet twenty-distinct-conclusion target. Private planning and client report remain local.
