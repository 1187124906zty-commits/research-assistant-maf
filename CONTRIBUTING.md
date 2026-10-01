# 参与贡献

欢迎改进提供者、MAF 工作流、科学状态、恢复机制、工具适配、案例与文档。小修复可直接提交 Pull Request；涉及新模型提供者、状态 schema 或恢复语义的大改动，可先用 [Issue](https://github.com/1187124906zty-commits/research-assistant-maf/issues/new) 说明问题和验证方法。

## 报告问题与提出案例

| 类型 | 建议提供 |
|---|---|
| 安装与执行错误 | 操作系统、Python、MAF/SDK 版本、命令、复现步骤与关键日志 |
| 恢复或未知调用 | 请求 ID、执行状态、已核实的会话与产物事实；避免重复启动未知作业 |
| 提供者或专业工具 | 官方 API/版本、输入输出、调用完成判定、取消语义与所需权限 |
| 科研案例 | 问题、原始出处、数据角色、计算或实验条件、交付与验证范围 |

使用讨论可在 [QQ 社区](docs/COMMUNITY.md) 进行，需要持续跟踪的事项同步到 Issue。公开复现材料去除账户凭据及未经授权的私人资料，保留足以复现问题的输入。

## 开发与验证

建立项目环境并创建分支：

```powershell
git switch -c codex/your-change
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . build
```

阅读 [AGENTS.md](AGENTS.md) 和 [架构说明](docs/architecture.md)。本项目独立维护应用角色和 skills；修改本仓库相应文件。保留并行协作者的改动，声明独立的写入路径。

Python、协议和工作流修改执行：

```powershell
python -m unittest discover -s tests -v
python -m research_assistant demo ./local-runs/contribution-demo
python -m build
python scripts/check_installed_wheel.py
```

演示使用新的输出目录。受影响 CLI 另做实际运行；提供者更改需核对完成、超时、取消和未知状态。真实模型验收需说明所用环境与调用范围。skill 实质修改验证 frontmatter 并做独立现实使用检查；纯文档修改检查链接、示例命令和显示。

PR 说明具体触发条件、最终行为、验证路径及限制。离线返回、真实角色协作和科研效果分别报告。

## 保持科学与执行语义

- 科学状态是研究判断的权威来源，MAF 检查点与调用账本保留各自职责。
- 未知完成状态的外部调用先核实再处置；已完成返回可复用。
- 任务交付接收与科学支持分别判断，负面结果和反证继续可追溯。
- 证据保留来源、版本与范围，模型稿件依据已获得材料。
- 原始研究案例说明标定、验证、合成数据与未执行工作，公开材料具有明确分发许可。

本项目采用 [MIT 许可](LICENSE)。状态来源、上游依赖与外部材料遵循 [第三方说明](THIRD_PARTY.md) 及各自许可。
