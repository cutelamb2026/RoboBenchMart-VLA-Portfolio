# π0-FAST 在 LIBERO 四套件的评测结果（截图录入）

## 结果口径

用户于 2026-11-13 提供四套件 40 个任务的网页截图，每项显示实验轮次 50 与任务成功率。以下成功次数是从截图百分比反算的整数（例如 94% × 50 = 47），不是重新执行模型或重新读取 rollout 原始日志。截图显示的“执行到当前任务的成功率”属于**累计平均值**，不能误当作该任务单独成功率。

| 套件 | 成功次数 | Episodes | 平均任务成功率 |
|---|---:|---:|---:|
| libero_spatial | 480 | 500 | 96.00% |
| libero_object | 485 | 500 | 97.00% |
| libero_goal | 438 | 500 | 87.60% |
| libero_10 | 301 | 500 | 60.20% |
| **合计** | **1704** | **2000** | **85.20%** |

全部四套件均显示 10 个任务、每任务 50 个 episode。因为各任务样本量相等，任务成功率的算术平均与所有成功次数除以总次数相等。此 85.20% 是本次四套件的**等任务权重整体平均**，不是官方论文的数值，更不是 RoboBenchMart 的结果。

## 逐任务复核（截图成功率反算）

| 套件 | task_id（0-based） | 成功 / 50 | 成功率 | 任务说明 |
|---|---:|---:|---:|---|
| libero_spatial | 0 | 50/50 | 100% | pick up the black bowl between the plate and the ramekin and place it on the plate |
| libero_spatial | 1 | 45/50 | 90% | pick up the black bowl next to the ramekin and place it on the plate |
| libero_spatial | 2 | 49/50 | 98% | pick up the black bowl from table center and place it on the plate |
| libero_spatial | 3 | 50/50 | 100% | pick up the black bowl on the cookie box and place it on the plate |
| libero_spatial | 4 | 47/50 | 94% | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate |
| libero_spatial | 5 | 44/50 | 88% | pick up the black bowl on the ramekin and place it on the plate |
| libero_spatial | 6 | 50/50 | 100% | pick up the black bowl next to the cookie box and place it on the plate |
| libero_spatial | 7 | 47/50 | 94% | pick up the black bowl on the stove and place it on the plate |
| libero_spatial | 8 | 48/50 | 96% | pick up the black bowl next to the plate and place it on the plate |
| libero_spatial | 9 | 50/50 | 100% | pick up the black bowl on the wooden cabinet and place it on the plate |
| libero_object | 0 | 46/50 | 92% | pick up the alphabet soup and place it in the basket |
| libero_object | 1 | 49/50 | 98% | pick up the cream cheese and place it in the basket |
| libero_object | 2 | 50/50 | 100% | pick up the salad dressing and place it in the basket |
| libero_object | 3 | 50/50 | 100% | pick up the bbq sauce and place it in the basket |
| libero_object | 4 | 50/50 | 100% | pick up the ketchup and place it in the basket |
| libero_object | 5 | 43/50 | 86% | pick up the tomato sauce and place it in the basket |
| libero_object | 6 | 47/50 | 94% | pick up the butter and place it in the basket |
| libero_object | 7 | 50/50 | 100% | pick up the milk and place it in the basket |
| libero_object | 8 | 50/50 | 100% | pick up the chocolate pudding and place it in the basket |
| libero_object | 9 | 50/50 | 100% | pick up the orange juice and place it in the basket |
| libero_goal | 0 | 36/50 | 72% | open the middle drawer of the cabinet |
| libero_goal | 1 | 50/50 | 100% | put the bowl on the stove |
| libero_goal | 2 | 48/50 | 96% | put the wine bottle on top of the cabinet |
| libero_goal | 3 | 46/50 | 92% | open the top drawer and put the bowl inside |
| libero_goal | 4 | 49/50 | 98% | put the bowl on top of the cabinet |
| libero_goal | 5 | 45/50 | 90% | push the plate to the front of the stove |
| libero_goal | 6 | 50/50 | 100% | put the cream cheese in the bowl |
| libero_goal | 7 | 47/50 | 94% | turn on the stove |
| libero_goal | 8 | 50/50 | 100% | put the bowl on the plate |
| libero_goal | 9 | 17/50 | 34% | put the wine bottle on the rack |
| libero_10 | 0 | 43/50 | 86% | put both the alphabet soup and the tomato sauce in the basket |
| libero_10 | 1 | 50/50 | 100% | put both the cream cheese box and the butter in the basket |
| libero_10 | 2 | 12/50 | 24% | turn on the stove and put the moka pot on it |
| libero_10 | 3 | 19/50 | 38% | put the black bowl in the bottom drawer of the cabinet and close it |
| libero_10 | 4 | 44/50 | 88% | put the white mug on the left plate and put the yellow and white mug on the right plate |
| libero_10 | 5 | 28/50 | 56% | pick up the book and place it in the back compartment of the caddy |
| libero_10 | 6 | 40/50 | 80% | put the white mug on the plate and put the chocolate pudding to the right of the plate |
| libero_10 | 7 | 45/50 | 90% | put both the alphabet soup and the cream cheese box in the basket |
| libero_10 | 8 | 2/50 | 4% | put both moka pots on the stove |
| libero_10 | 9 | 18/50 | 36% | put the yellow and white mug in the microwave and close it |

## 主要观察

1. `libero_spatial` 96.00%、`libero_object` 97.00%，两套件的表现较高。
2. `libero_goal` 87.60%，其中 put the wine bottle on the rack 为 **17/50（34%）**，显著低于同套件其他任务。
3. `libero_10` 为 **60.20%**，内部差异很大：put both moka pots on the stove 仅 **2/50（4%）**，turn on the stove and put the moka pot on it 为 **12/50（24%）**；另有部分任务达到 50/50。
4. 这些差异与复杂组合操作可能更困难的假设一致，但没有阶段分解日志，不能由此证明长时序是唯一失败原因。

## 证据及可复现性边界

- **截图证据**：`evidence/libero_results/screenshots/`，从用户提供的网页评测截图保存；单任务 50 次和比例为用户提供的记录。
- **数值换算**：全部任务成功率均为 2% 的整数倍，因此能对应 0–50 个成功 episode。
- **尚缺**：模型 checkpoint 标识与 SHA-256、官方评测脚本 commit、任务初始化随机种子、原始逐 episode success、具体是否有跳过/重试、评测环境和动作 chunk 参数。不能据此断言完全复现官方对比实验。
- **不要混用**：RoboBenchMart 历史 35 组/135 条/0 成功，与 LIBERO π0-FAST 截图 2000 次/1704 成功，是不同任务、模型和评测协议的两条证据链。
- **置信区间提醒**：`report.json` 给出的 Wilson 区间按独立伯努利试验近似估算，若 episode 初态或策略运行存在相关性，不应把它当作严格独立的统计保证。

## 使用方式

```bash
python libero_pi0_fast/analyze_libero.py --input libero_pi0_fast/results.csv --output libero_pi0_fast/report.json
python -m unittest libero_pi0_fast/test_analyze_libero.py -v
```
