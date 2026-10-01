# AMMT：章节研究、有限 MAF 写作批次与整稿论证

**状态：已真实执行文献研究、章节写作和跨章节评阅；native MAF 写作批次局部成功，Discussion 调用在 1500 秒截止后中断，自动交接闭环尚未完成。** 2026-10-01。

本案例基于现有 AMMT IN625 单道数值证据，将近期文献、期刊阅读习惯、方法与结果核对、章节候选和整体论证连接起来。它是实际科研写作案例，不是预设返回的协议演示。协调者保留已有研究判断，不为运行框架重新发明选题或声称新的模拟发现。

## 实际完成范围

| 阶段 | 已完成工作 | 边界 |
|---|---|---|
| 文献与期刊研究 | 阅读既有和近期近邻来源，形成来源记录、研究线与期刊论证建议 | 来源读取范围分别记录；不把元数据检索当作全文阅读 |
| 研究论证与证据核对 | 接受论证地图，核对已执行 Methods/Results、观察定义、数据角色和机制限制 | 没有重跑 PDE；几何校准、非盲比较与派生时间仍保留原有范围 |
| 实际 MAF writer 批次 | 并行派发 Introduction 和 Discussion 两个有限写作合同，保存真实章稿和参数化调用账本 | Introduction 返回完整 JSON；Discussion 保存候选后截止中断，无最终 RESULT JSON |
| 协调者接收与章节交流 | Root 读取现存候选、选择修订，完成跨章节机制评阅并整合正文 | 这是 Codex 科研队伍的实际工作；不记为未执行的 native MAF reviewer/requester |
| 当前整稿 | 已完成 22 页英语初稿、39 条实际引用与 5 幅正文图；独立上下文整稿评阅、三项实质问题修复与受影响页面复核均已完成 | 可交人工科研评阅；物理热史验证、期刊贡献充分性与 AM 专属投稿合规仍未确立 |

当前正式初稿与状态说明在 [ResearchFlow 的 AMMT 论文目录](https://github.com/1187124906zty-commits/research-workflow/tree/codex/researchflow-release/paper/ammt-study)，可直接查看 [PDF](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/manuscript.pdf)、[LaTeX](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/manuscript.tex) 和 [完整源码包](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/submission-source.zip)。这些是有意维护的分支链接；具体版本以该目录说明为准。实际 [全文评阅](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/revision-r2/review/whole-review.md) 与 [修复处置](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/revision-r2/review/review-response.md) 支持当前初稿范围，本仓库不将中间候选复制为正式稿。

本次定位从可观测几何与可信热过程解释之间的关系出发，区分领域问题、知识缺口和固定源参数/物性续接对照等技术响应。Myers 等既有工作已经显示几何拟合与热场之间的歧义，本稿不将它包装为首次发现。当前 Discussion 保留后相界共同位移与相区间距的区别、潜热与显热储能的区别，以及表面恢复和通量反例对排他性机制解释的限制。

## 执行方式与合同

`run_sections.py` 使用真实 `run_project` native MAF fork/join 图与可选官方 Codex Python SDK。协调者先完成上游研究、读取原件、接受论证和材料，之后提供 manifest；runner 冻结这些实际文件，登记有限章稿合同并派发。它不自动检索文献、选择期刊、重跑数值模型或认证论文。

```bash
python -m pip install -e ".[codex]"
python examples/ammt-deep-revision/run_sections.py --manifest ../research-workflow/paper/ammt-study/revision-r2/maf-drafts.json --workspace ./local-runs/ammt-deep-revision/drafts
```

这里的 manifest 来自相邻 ResearchFlow 研究工作区，不随本例作为通用数据集发布。若相邻仓库或材料不可用，应先准备自己的真实 manifest，不能用缺失链接冒充已经获得的证据。

Manifest 结构包括：

- `brief`：被接受的研究目的、写作范围、数据角色、允许的来源和返回要求。
- `inputs`：每项材料的实际 `source` 与冻结后的项目相对 `path`。
- `tasks`：`id / role / question / purpose / outputs / writes / acceptance / budget`。
- `parallel / max_cycles / timeout_seconds`：角色调用并行数、有限会话循环数和每次 SDK 调用的时间上限。

本次两个 writer 合同分别拥有 `sections/introduction/` 和 `sections/discussion/`；输入是冻结的研究线、原文资料、期刊档案、论证地图及已执行 Methods/Results。runner 给章稿任务设置 `claim_ids=[]`，不进行物理证据提升。候选以修订目录保存，禁止覆盖已返回版本、改动 canonical TeX、原始科研软件、既有 skills 或其他角色文件。最终整合由 Root 完成。

任务预算 `max_attempts=2, max_no_progress=2` 约束正式任务返回；它不限制一次角色调用内部的所有阅读、工具动作或子任务。纯编辑变化诚实记录为 `changed_understanding=false`，具体编辑贡献在声明文件中解释。科学充分性和任务交付接收仍须分开判断。

Runner 拒绝在已有 `.research-assistant/research-state.json` 的 workspace 中重新初始化。新试验使用新的 workspace；恢复既有试验先检查账本和输入版本。不要删除旧状态或覆盖输入来伪装一次全新运行。

## 截止、诊断与恢复

此次 manifest 设置每次调用 `timeout_seconds=1500`。Introduction 调用成功保存返回；Discussion 调用在保存实际章稿后超时，父 turn 的持久状态为 `interrupted`，没有符合原 RESULT schema 的最终 JSON。该任务内部创建了章节评阅记录和 r002 候选，但诊断时缺少 r002 memory 文件，不能将其内部三文件交接声明当作已经闭合。

MAF 调用账本保持 `attention, cycles=0`。两个 writer 结果未完成批次导入；**native MAF reviewer 和 requester 均未运行**。本案例后续的章节接收、定向交流和全文评阅由真实 Codex 科研队伍完成，未将这些工作倒填为原生图节点成功。状态细节见 [公开诊断](recovery/diagnosis.md) 和 [脱敏调用摘要](recovery/call-diagnosis.json)。

SDK 截止会尽力请求活动 turn 中断并关闭客户端，但不能保证所有外部或子进程停止。出现 `started / failed / interrupted` 调用时，先通过官方公开 read API 核对原线程、实际输出及任务状态；不要盲目启动相同 writer。

```bash
research-assistant status ./local-runs/ammt-deep-revision/drafts
python examples/ammt-deep-revision/recovery/inspect_calls.py
```

诊断脚本从本地账本读取会话定位，默认只读，不发起 turn，也不打印 transcript、账号或凭据。公开摘要删除会话/turn 标识和开发机绝对路径；原始 JSON 仅保留在被忽略的本地恢复文件中。

仅当确实找到原调用的完整、符合 schema 且产物已核实的最终响应，才使用显式恢复接口：

```bash
research-assistant reconcile WORKSPACE "worker:TASK_ID:1" INSPECTED_RESPONSE.json --reason "已核实原会话的实际返回及其版本产物。"
research-assistant resume WORKSPACE --timeout 600
```

`reconcile` 不启动模型，不替换已完成返回，也不授予科学支持；随后的导入、评阅和请求者处置仍需真实执行。此次 Discussion 没有可恢复的最终 JSON，所以诊断没有编造响应、重复写章或宣称 native 闭环完成。接收已有候选是独立的研究编辑处置。

## 能力与评价

本例显示可以在 MAF 上派发真实的有限写作任务，并保留候选、冻结输入、返回或失败状态。它同时暴露出长角色调用、内部任务扩展和最终交接缺失会使原生自动闭环停在批次汇合处。专业角色产出有用内容与工作流完整成功是不同事实。

实际章节阅读、研究深度、机制互审和整稿评阅由 Codex 科研队伍承担；外部框架并未自动产生这些科学判断。本次不能证明更低成本、更快科研发现、更高论文接收率或完整无人介入研究能力。引用数量、图数、软件测试通过和已有候选也不构成这些效果的实证。后续需要以真实任务的耗时、重复劳动、反证使用、交接完整性及独立读者理解作具体评价。

后续完善应优先缩短并明确定义每次调用的返回单位、及时回传中间产物与未完成事项，并使协调者解释科学和编辑贡献；不为“完成自动化”扩大证据范围。架构背景见 [章节协作设计](../../docs/manuscript-collaboration.zh.md)，表达依据见 [摘要与引言定位](../../docs/abstract-introduction-positioning.zh.md)。
