# RoboBenchMart / π0-FAST 项目资产状态

## A. RoboBenchMart —— 已保存的历史记录

当前包包含从用户历史 77 MB 备份恢复的 `dsynth/`, `scripts/`, `bash/`（可能含官方源码和用户更改的混合状态），OpenPI 自定义适配文件、RLDS 示例、35组/135条历史记录及部分 OOD/TRAIN 日志和视频。**原始约18GB全量评测轨迹、模型权重、原云服务器已丢失**。不得把 CSV 统计当作全部原始轨迹已恢复。

## B. RoboBenchMart / OpenPI 官方完整源码

当前环境无法直接从 GitHub 下载完整源码，不声称已经含有它们的最新版本或 git 历史。在有 GitHub 网络的电脑运行 `bash tools/fetch_official_sources.sh`，会在 `upstream_sources/` 分别克隆官方 RoboBenchMart 与 OpenPI，记录 Git commit。**不能无差别覆盖历史恢复文件。**

## C. π0-FAST / LIBERO 独立实验

用户报告执行 `libero_spatial`、`libero_object`、`libero_goal`、`libero_10` 四套件，设置为每个任务 50 次推理评测。四套件通常各10个任务，完整执行规模为2000次。用户现已提供四套件各十任务的网页截图，逐项成功率已录入 results.csv；原始逐 episode 日志仍未提供。截图成绩已核对，但详细运行配置仍待核验。

## D. 权重

官方 OpenPI 公开仓库有权重获取说明。用户给出的百度网盘分享地址为外部第三方来源，不能据此确认与目标模型版本对应。大权重不应放入 Git；下载后应记录文件 SHA256、checkpoint 版本、数据许可。不得把它混为 π0、π0-FAST 或 π0.5 的某个特定 checkpoint。


## 2026-11-13 LIBERO 实际截图结果已补录

`libero_pi0_fast/results.csv` 从用户截图录入：spatial 480/500（96.00%）、object 485/500（97.00%）、goal 438/500（87.60%）、libero_10 301/500（60.20%）；累计 1704/2000（85.20%）。这是根据网页截图反算的成功数，原始逐 episode 日志、checkpoint 和 seed 尚缺；详细见 `libero_pi0_fast/RESULTS_ANALYSIS.md`。之前“尚无成功率”的描述已由此更新。
