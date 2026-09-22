# EXP-0012 — Extended dataset range and object-support comparison

- Date: 22 September 2026.
- Project owner: Ricky Yuen; execution and analysis through Codex.
- Outcome: 400 TruckScenes samples processed across three channels; 25,750
  publisher annotation point counts grouped by range, class and scene; 961 GOOSE
  scan/label pairs streamed and hashed; committed TruckDrive tables reaggregated.
- Environment, commands, figures and interpretation:
  [full report](../docs/sprint3-dataset-findings.md).
- Records: 0013 TruckScenes, 0014 GOOSE, 0015 TruckDrive saved evidence.
- TruckDrive raw limitation: dataset account access is granted; the authenticated
  CDN download failed with `ERR_BLOCKED_BY_CLIENT`. No raw TruckDrive run is claimed.
- Model limitation: no new radar/LiDAR detector inference. Publisher point support,
  raw coverage and ground-truth semantic remaps are not accuracy scores.
- Session guard: branch/up-to-date/data-file checks apply, but its old blanket
  `docs/evidence/*` ownership entry flags generated evidence as Damien-owned.
  The user's explicit request authorises this cross-dataset work. The ownership
  guard and protected-branch review requirements have not been changed.

Raw datasets stay outside Git. New reports have separate paths and do not overwrite
the historical 80-sample evidence. This entry records agent execution, not human
review completion or time worked by a team member.
