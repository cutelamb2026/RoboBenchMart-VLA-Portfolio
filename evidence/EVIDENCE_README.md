# New evidence recovery supplement

These files were provided separately after the original source backup. This is a preservation bundle, not evidence that the model is currently deployable.

## Recovered evidence
- octo_100.mp4 and pi05_100.mp4: 512x512 H.264 videos, 501 frames and 16.7 seconds each. Filenames do not independently establish model weight or task identifier.
- octo_ood10_review.zip / pi05_ood10_review.zip: each contains 10-episode evaluation log, config yaml, and metadata json. Both logs end with success 0/10; each episode reports maximum 500 steps.
- pi05_adapter_review.zip: recovered code copies for robot config and policy adapter; may duplicate original backup.
- source_excerpts/*.txt: extracted method snippets for PI0, PI0-FAST and Pi05. These are *study/reference artifacts*, not proof of actually deployed PI0 or PI0-FAST models.
- robot_contact_sheet.jpg: sampled visual comparison. Visual appearances alone cannot establish precise action magnitudes or task success.

## Limits
- Full 18GB trajectory/video archive remains missing. Detailed per-step H5 cannot be reconstructed from these files.
- OOD logs show successful execution of evaluation loops and zero task success; they do not diagnose root cause.
- Videos are sampled evidence only; not a substitute for full episode counts or machine-readable actions.

## SHA-256 inventory

| File | SHA-256 |
|---|---|
| images/robot_contact_sheet.jpg | `27a1a9bbd49f1f3dcddf7a1083ef776c129513950cbd689ad7017c11050b8b1c` |
| ood_reviews/octo_ood10_review.zip | `d571947190d2c9c34dd60c675469d016e0565a6ba2941e60bd17a26432f70596` |
| ood_reviews/pi05_adapter_review.zip | `f6cdaf2d98d38ecff244f6678d507e4e6ca2e5ea8e8aa6daa5aa2574dd82544a` |
| ood_reviews/pi05_ood10_review.zip | `389823f7a4f7e9e1f5ba0325442821ea3f68c2749e859a23b7c8b370bd9e27d0` |
| source_excerpts/pi05_state_pipeline.txt | `ab28d829285d020b4ffa94a6e9d91cc3151da07f26ba8612affa8ff05330d479` |
| source_excerpts/pi0_core_methods.txt | `ff665450788d9f33e97487dbd22bb560e09a869f0f5eb77250f2340d8f501115` |
| source_excerpts/pi0_fast_core_methods.txt | `f7515ed3ace1510e4f658f03c4e4b0e69276b8452d97d9d5f1b9b20744055765` |
| source_excerpts/pi0_fast_tokenizer_pipeline.txt | `6fb360a57f666b0b742190e7d6769d267d236548c48dd7346c6f63ba074d1372` |
| videos/octo_100.mp4 | `b5b8505a4aa184f23bf60f414f46fc6c2c8404abe70fa4570ba5d6f8bef3bfbe` |
| videos/pi05_100.mp4 | `eaf0c40ce47eff522a180bd79259aff87079641ac7f8810733d9e080510534d9` |


## Supplemental recovery: TRAIN diagnostic and robot source review

- `train_diagnosis/pi05_train_diagnosis.zip`: original `pi05_train_nivea_smoke.log`, scene JSON, and 0.mp4. JSON records PickToBasketContNiveaEnv, seed=0, pd_joint_pos, elapsed_steps=600 and success=false (one trial). The log's `Octo evaluation` header is a generic client print string and does not independently verify the served policy; label derived from archived filename. This smoke run may overlap other reported trials: do not add it to the 135-episode total without deduplication.
- `source_reviews/robot_code_review.zip`: original source snapshot including `ds_fetch.py`, `eval_policy_client_custom.py`, `octo_server_custom.py`, `openpi_config.py`, and `robobenchmart_policy.py`. It is preserved separately for provenance and comparison; do not overwrite recovered source automatically.
- The two `task2_*` archives supplied in the same upload were inspected. They document unrelated RLHF/LLM judging coursework, not RoboBenchMart, so are deliberately excluded from this repository.
