# RoboBenchMart reproducible evaluation harness (additional implementation)

This code is **newly implemented for the portfolio** based on the already executed RoboBenchMart experiment clients. It is NOT part of the original evaluated 135-trajectory experiments, and is not yet tested with the live simulator/model server. It does not implement a new VLA model or claim any task-success improvement.

The framework adds (i) a typed validated experiment spec, (ii) reproducible command/manifests, (iii) optional launching of the existing atomic client, (iv) offline CSV consistency checks, model×scene-group aggregation and Wilson intervals, and (v) tests.

Copy the whole folder next to `scripts` inside the RoboBenchMart repo or set `PYTHONPATH` to this folder. Run with Python 3.10+.

```bash
python -m unittest discover -s tests -v
python -m rbm_eval.cli audit /path/to/evaluation_summary.csv --out artifacts/framework_audit.csv
python -m rbm_eval.cli plan examples/atomic_unseen.json --out artifacts/framework_runs
# only when exact scene_dir / checkpoint / running policy server are verified:
python -m rbm_eval.cli run examples/atomic_unseen.json --out artifacts/framework_runs
```

IMPORTANT: `examples/atomic_unseen.json` is an illustrative configuration and may not match your actual scene directory. Edit the scene path and record code revision/checkpoint ID before a live run. Full composite evaluation and complete action-space verification are outside this adapter's current supported scope; the existing `scripts/eval_policy_composite_client_improved.py` remains the composite runner. Audit output includes **all** summary rows, including smoke/diagnostics, unless you create a curated input CSV. Do not compare these totals to published benchmark scores.

Source boundaries: `scripts/eval_policy_client_custom.py` is the original user-run evaluation client; all code under `rbm_eval/` here is newly authored and unit-tested offline. The manifest's `model` tag is metadata, not a safeguard that the correct checkpoint was loaded into the externally running server; checkpoint identity must be independently verified.
