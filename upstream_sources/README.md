# 官方源码的安全补全方式

历史 `dsynth/`, `scripts/`, `bash/` 是从用户备份恢复的源码快照，**不是已认证与官方 HEAD 一致的源码**。在联网的电脑上运行 `bash tools/fetch_official_sources.sh`，会将以下官方仓库完整检出到独立目录，并记录实际 commit：

- `upstream_sources/RoboBenchMart/` — https://github.com/emb-ai/RoboBenchMart （MIT）
- `upstream_sources/openpi/` — https://github.com/Physical-Intelligence/openpi （Apache-2.0；模型或部分第三方资源可能有额外条款）

脚本不会覆写原有自定义代码，已存在的 git 仓库也不会自动更新。OpenPI 包含 git submodules，脚本使用 `--recurse-submodules`。切记先查看 LICENSE、依赖及 `git diff --no-index` 再迁移个人改动；不要直接将旧 `config.py` 覆盖 OpenPI 最新版。

**本 ZIP 不含在线下载的官方完整 Git 仓库，也不含模型权重。** 下载公开源码只需 GitHub，无需百度网盘分享链接；分享的百度网盘地址为外部第三方来源，权重身份、校验和及许可证未经确认。

若打算将本项目推送 GitHub，建议保留 `upstream_sources/` 为单独克隆，设置在 `.gitignore` 中，或后续使用有固定版本的 submodule。不应直接递归提交嵌套的 .git 仓库。
