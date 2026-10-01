# 真实模型协作样例：给定合成数值的描述与交接

这个样例是 2026-10-01 在 Windows、Python 3.12.14、MAF 1.19.0 和可选 Codex SDK 0.159.3 上实际执行角色请求产生的文件。它用于检查协作路径，没有开展物理研究。输入的 synthetic 身份必须始终保留。

| 文件 | 作用 |
|---|---|
| [input.txt](input.txt) | 原始给定数值和合成数据说明 |
| [brief.txt](brief.txt) | 真实请求的有限任务范围 |
| [simulation-result.md](simulation-result.md) | 专业角色对原数值的描述性算术核对 |
| [simulation-contribution.md](simulation-contribution.md) | 返回对整体报告的贡献、不确定性及专业建议 |
| [report.md](report.md) | 写作角色依据实际输入和产物形成的简短报告 |

专业任务限制为两个阶段：一次分析、一次写作，每项最多一次尝试。两个专业结果各经过新的评阅角色和协调者处置。任务契约、输入绑定、模型返回及处置保存在本地账本；公开样例仅包含合成输入和可审阅文本，不发布账户配置、完整会话或本地主机账本。

本地最终状态为 `complete`，完成两个专业循环，协议审计 `protocol_ok=true`、风险列表为空；科学有效性仍记录为 `not_judged`。最终报告交付及数值、来源范围已由协调者对照实际文件检查。报告成稿后还修正了 Windows GBK 控制台不能输出减号符号的问题，防止完成状态被错误显示为命令失败；这一点已有回归测试。

## 实际遇到的两项问题

1. 专业返回引用了原始 `input.txt`，早期实现错误地要求所有证据都必须属于生产者写入范围。实现已改为允许明确登记且版本未变的输入作为来源。原模型的完成返回通过 SDK 公开读取接口恢复并核对，随后显式关联到账本；没有重做该专业任务。
2. 协调者第一次登记支持时，在 `evidence_indices` 中混入了 `kind=observation` 的原始输入。程序拒绝该处置，保留原返回，再提供一次有限的错误反馈。协调者修正了支持索引，证据规则没有放宽，也没有增加数值分析。

因此，这个案例经历了开发期修正与显式恢复，并不是一个声称首次运行就成功的演示。它检查了现有工作能否继续交接，也暴露了大模型对精确状态规则理解不完整的问题。修正后的行为由独立回归测试覆盖。

## 自行运行

在仓库根目录先安装 `.[codex]` 并确保 Codex 主机账户可用。下面是 PowerShell 示例；每次用一个新的项目目录，避免覆盖既有样例。

```powershell
New-Item -ItemType Directory -Path .\workspaces\my-smoke
Copy-Item .\examples\live-coordination\input.txt .\workspaces\my-smoke\input.txt
research-assistant run .\workspaces\my-smoke --brief (Get-Content .\examples\live-coordination\brief.txt -Raw -Encoding UTF8) --max-cycles 3 --parallel 2 --timeout 180
research-assistant status .\workspaces\my-smoke
```

新运行会使用模型额度，模型的任务命名和表述可能变化。此处 `simulation` 是分析责任名称：实际要求是描述给定数据，不是运行物理模拟。

A 与 B 的两组变化均为 0.002，A−B 均为 0.200。报告只能把这些事实解释为给定数值的观察和算术推导。coarse/fine 标签没有对应网格或离散参数，不能据此推断收敛、误差估计、物理机制或精度提高。没有实际科研效果实验，不能用本样例支持发现速度或论文质量提升。
