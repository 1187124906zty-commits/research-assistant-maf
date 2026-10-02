# 有来源的章节写作：真实旧稿、候选与反馈

本案例将公开写作指导整理为项目技能，在旧版 IN625 熔池稿上运行一次真实 MAF 标题、摘要与引言修订，再检查实际候选。最终研究稿由协调者整合和另行全文评阅，见 [R4 研究稿与审查](https://github.com/1187124906zty-commits/research-workflow/tree/codex/researchflow-release/paper/ammt-study/revision-r4)、[PDF](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/manuscript.pdf)与 [LaTeX](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/manuscript.tex)。

## 实际输入与任务

输入为冻结的 R3 稿、已核实数值和逐句来源账本。任务指定 `writing.mode=revise`、`writing.sections=[title_abstract,introduction]`；运行时给 writer 加载公共科学写作、科学编辑和选中章节技能，给 reviewer 加载对应审查方法。详细分发和后续反馈见 [技能说明](../../docs/writing-skills.zh.md)。

请求没有提供完成的 R4 替换正文。详细指南已有与这一案例相邻的原创示例，所以这次运行检验的是同案例应用，不能作为未见任务的迁移测试。初始任务要求保持原数量及引用键，实际使用表明该表述容易变成“在摘要继续保留每组旧数字”。当前示例任务改为“事实准确、使用的键有效，并按章节用途选择信息”；保存的旧请求仍保留旧要求，避免把后来改进回写成已观察效果。

## 候选与实际评价

候选题目语法和范围明确，原始论文核对支持几何/温度信息、物性覆盖和材料时间的论证。它保留负面几何结果、校准角色及派生热历史边界。不过，摘要仍重复很多数值，引言末段仍像方法清单。[独立应用评价](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/revision-r4/forward-use/coordinator-evaluation.md)由真实候选和工具轨迹得出这些判断。

指南据此补充整体摘要理解负担、事实保持与每节信息选择的区别，以及继续原件调研前指出可改变的断言。最终 R4 稿采用了经过整合和全文评阅的修订文本；前向候选作为评价材料保留，二者身份明确。

实际第二轮接收定位反馈后，摘要将数值表示组织为物性响应、后界共同位移、保留的形状失配和速度相关材料时间；引言末段把详细观测/样本定义留在已有方法中。[第二轮实际复查](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/revision-r4/forward-use/attempt-2-recheck.md)接收这两项修复，并核对全部四种 B 物性组合仍偏宽、偏浅的限定表述。指南改进与明确反馈同时存在，因此不能分离两者的因果作用。I2–I5 的相似边界句保留为可选编辑意见，不无限追加改写。

公开的 [第一候选](outputs/attempt-1-frontmatter.tex)、[第二候选](outputs/attempt-2-frontmatter.tex)、[初次审查](outputs/attempt-1-review.json)和[实际执行摘要](execution-summary.json)供直接比较。它们是章节替换片段，引用使用原稿的文献库；当前完整阅读稿的渲染和科学审查另行记录。

## 时间检查点与交接

本次初始运行使用旧版固定时限。writer 在 358.7 秒、300 秒两次中断后完成候选，再用 35.9 秒完成实际结构化报告；这些历史中断保留。后续 reviewer 也被旧 timer 中断。

用户指出固定计时器会错误中断慢推理后，协调者先向原 reviewer 发送进度询问。真实返回说明：关键核对已完成，尚未组合结构化报告，已可交付；没有反复修改或证据阻塞。协调者据此要求交付现有最佳审查，同时参考另一评阅者的定位意见，不再用 elapsed time 强制停止。新的 [进度治理实现](../../docs/agent-progress.zh.md)将活动调用时限改为询问和处置检查点；明确的调用者取消和启动传输故障分别处理。

本目录的公开输出和执行摘要记录实际状态、协调干预与限制。文件存在、协议通过、引用数或篇幅变化都不能独立证明论文质量提高。这是自动化同模型评阅，尚需负责作者和真实同行评价。

最终原生状态为 **complete，2 个专业循环、7 个已完成角色请求**。两轮 writer→reviewer→coordinator 交接闭合，最后规划返回完成，不新增可选修订任务。第二轮评阅无未解决的重要发现；协调者读取实际稿件和数值记录后接收，并保留物理证据与渲染边界。最终协议审计为 `protocol_ok=true`，没有活动风险。旧计时器中断、两次恢复及报告格式纠正均保留，不能把这次完成描述为完全无人协调。

审计保留四项非阻塞的历史版本提醒：第二轮更新相同输出位置，使第一轮证据和第一轮 review 输入不再是当前文件版本。两个候选在本目录分别冻结发布，当前接收基于第二轮版本。历史提醒不被删除，也不被解释为当前证据故障。

第二轮 writer 实际回应了带标记的进度询问，程序记录 `source_work` 和继续决定，随后模型完成返回。报告因把 `:250` 附在声明的输入文件路径后而被拒绝。协调者只请求修正返回中的文件路径，将行号保留在说明，并显式对账；[被拒绝的原返回](outputs/attempt-2-rejected-return.json)保留。这个交接格式问题没有改变文本证据或触发科学工作重跑。

## 重复运行与检查

在安装本项目及 `codex` 可选依赖后，准备同级 ResearchFlow 仓库与原始阅读资料；使用新的工作区运行：

```powershell
python examples/ammt-writing-skills/run_forward.py --workspace ./local-runs/my-forward-case --timeout 360
python examples/ammt-writing-skills/inspect_forward.py ./local-runs/my-forward-case
```

当前 `--timeout` 表示活动 turn 的进度检查间隔。历史请求及其原始输出不会被新的技能版本或计时语义改写。原件全文仅在本地阅读，不随此案例发布。

未知/中断调用先检查原线程和产物。`recover_review.py` 用原线程先询问，再由协调者显式选择继续；只有真实返回可以通过 CLI `reconcile` 对账。`finalize_interrupted_worker.py`用于已核实旧 writer 的同上下文恢复，适用范围和历史干预见执行摘要。
