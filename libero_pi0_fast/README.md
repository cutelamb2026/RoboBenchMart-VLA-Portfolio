# π0-FAST / LIBERO 评测记录（独立实验线）

四套件：`libero_spatial`、`libero_object`、`libero_goal`、`libero_10`。官方 OpenPI `examples/libero/main.py` 使用 `num_trials_per_task=50`；四套件各 10 个 task 时，全部执行相当于 4×10×50=2000 次 rollout。

**已经根据用户上传的 40 个任务截图补录成功率和换算成功次数**；checkpoint、seed、控制步数、原始逐 episode 日志仍缺失。`results_TEMPLATE.csv` 仅为模板，`results.csv` 才是截图录入的数据。

## 已收录的截图结果（2026-11-13）

目前 `results.csv` 已由用户提供的四套件截图逐任务录入（每任务50次、共2000次、1704次成功、85.20%），`report.json` 为分析脚本再计算的报告。详细数值、出处和限制见 `RESULTS_ANALYSIS.md`。

**成功次数由截图展示的两位百分比反算**；当前未拿到单 episode 原始日志、checkpoint 信息与 seed，不能宣称原始 rollout 已恢复或官方 benchmark 完全一致。

## 填写真实原始计数

每行一条 `(suite, task_id, successes, trials)`，如你实际做满 50 次，填写 `trials=50`，`successes` 填 0–50 的实际整数。保存为 `results.csv`（推荐有真实任务说明），并运行以下命令（目录名不含空格）：

```bash
python libero_pi0_fast/analyze_libero.py --input libero_pi0_fast/results.csv --output libero_pi0_fast/report.json
```

脚本检查范围、重复任务和计数；输出每个任务的成功率、每套件的平均成功率、总成功率及 Wilson 95% 区间。对于每个任务都执行相同次数的情况，先求十个任务成功率的平均值与 `sum(successes)/sum(trials)` **数值相同**。若有缺失或提前中断，不能擅自按 50 补齐。

要与论文/其他模型比较，必须一致：LIBERO 版本、初始状态与种子、最大环境步数、动作 chunk 长度、摄像机预处理、模型 checkpoint、训练数据与评估脚本。不同 Benchmark 的成功率不能直接进行优劣排序。

## 关键来源

- OpenPI LIBERO 客户端：https://github.com/Physical-Intelligence/openpi/blob/main/examples/libero/main.py
- OpenPI 模型仓库：https://github.com/Physical-Intelligence/openpi
- RoboBenchMart：https://github.com/emb-ai/RoboBenchMart
- 官方发布：https://www.pi.website/blog/openpi

第三方模型文件：https://pan.baidu.com/s/1yIVbdptUQunlyiuGbAcZjw?pwd=vu4e （用户提供，未核实权重具体内容与校验和；不要在仓库中公开附带权重）。
