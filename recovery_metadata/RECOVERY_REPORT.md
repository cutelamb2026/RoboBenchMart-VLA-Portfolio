# Recovery audit

- Source: `RoboBenchMart_project_delivery.tar.gz` (user-provided, original 77 MB archive).
- Verified: gzip integrity OK, tar member listing OK, extracted successfully.
- Original backup contains 277 tar members including directories, compiled Python files and generated RLDS data.
- Restored core: `dsynth/`, `scripts/`, `bash/`; intentionally dropped `__pycache__` and historical `*.bak` files from working tree (unchanged originals remain in the user archive).
- The original `git_changes.txt` says modifications existed in `dsynth/envs/pick_from_floor.py` and `scripts/eval_policy_composite_client.py`; new code in `scripts/eval_policy_client_custom.py` and `scripts/eval_policy_composite_client_improved.py`. Those statements are historical git status, not an audited upstream diff.
- OpenPI custom adapter and training config were separately captured in the original project_delivery folder. The package preserves them but does not certify compatibility with latest OpenPI.
- The original `tests/test_composite_stage_replanning.py` was listed as added but was absent in the source archive.
- `supplementary/` was restored from a separately produced ZIP, not from the original historical archive.
- The original 18GB `RoboBenchMart_full_experiments.tar.gz` was lost; no full original evaluation H5/video collection is claimed.
- Data in `data/rlds_nivea` is from the compact user backup.

Do not treat this package as an exact reproducible official benchmark state: original Git commit, model checkpoints, generated scenes and full trajectories are not present.


Supplementary evidence added: TRAIN single-episode diagnostic (600 steps, success=false) and original robot-code review archive. These do not recover missing full H5/MP4 dataset, nor prove deployment of a specific checkpoint.
