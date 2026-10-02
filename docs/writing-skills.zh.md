# 按科研任务分发的写作技能

本项目将通用科研写作方法作为项目资源发布，并在创建新的 agent 请求时自动加载。共享方法用于明确读者、论证与证据边界；章节方法只在任务显式选择对应章节时加载。分发组件无需修改原 ResearchFlow 安装或用户全局 skills；稿件修订由已授权的写作任务执行，版本和实际改动另行记录。

共享技能和角色不内置具体研究课题、材料、工况、评价量或默认期刊。领域对象、比较与参数由当前任务契约和原始来源提供；案例材料留在案例目录。分节指南采用通用诊断与返回条件，后续修改共享资源时检查其关联参考，避免把案例发现变成通用指令。

## 使用与选择

协调者派发写作任务时，可在现有任务契约中增加可选字段：

```json
{
  "writing": {
    "mode": "revise",
    "sections": ["introduction"]
  }
}
```

该对象随原有契约一起登记，原有 `question`、`purpose`、`inputs`、`outputs`、`writes`、`acceptance`、`budget` 等要求继续适用。写作技能不自行创建新的章节调度器，也不改变科学论断支持状态。

`mode` 可选 `draft`、`revise`、`audit`。`sections` 可选择 `title_abstract`、`introduction`、`methods_results`、`discussion_conclusions`，允许明确的多个章节；`["full_manuscript"]` 表示全部章节，不能再与其他章节混用。选择由任务元数据确定，不依据题目中的 “abstract”“introduction” 等词猜测。

| 接受任务的角色 | 自动加入的写作方法 | 责任 |
| --- | --- | --- |
| writer | 共享核心、科学编辑、选定章节；audit 模式另加写作审阅 | 实际段落、结构修订与证据缺口 |
| coordinator | 仅显式写作任务中加入核心、科学编辑与选定章节 | 整体论证、反馈处置和后续任务 |
| reviewer | 被审任务的选择转为 audit 模式，加入核心、审阅与选定章节 | 检查实际修订、来源和读者理解 |
| literature | 显式写作任务中加入核心、选定章节并指向来源综合参考 | 文献综合、句子与来源匹配 |
| mechanism | 显式写作任务中加入核心和选定章节 | 解释范围、替代解释与讨论依据 |
| simulation | 保留模拟 skill；显式写作任务再加入核心和选定章节 | 方程、条件、参数、方法与结果充分性 |

未指定 `writing` 的旧 writer 任务得到简短核心与科学编辑方法，不自动展开全部章节。旧 writer 的审阅任务获得简短写作审阅方法。其他未指定的角色保留原有领域职责，不加入整套写作指南。协调者的初始计划请求会说明如何显式选择章节，具体的编辑方法在收到相关写作任务交接后加载。

## 技能与知识位置

- `skills/scientific-writing`：共享核心及读者论证、来源使用、机构指导来源等按需读取资料。
- `skills/scientific-editor`：论证链、章节职责、顺序、节奏与反馈分工。
- `skills/paper-title-abstract`：题目、摘要、关键词。
- `skills/paper-introduction`：问题、相关研究综合、研究缺口与贡献。
- `skills/paper-methods-results`：必要方法定义、再现信息、比较、观察与不确定性。
- `skills/paper-discussion-conclusions`：解释、替代原因、限制与有边界的结论。
- `skills/paper-writing-review`：原文检查、定位问题、最小有用修订与复查。

多个角色共享同一知识来源，避免复制多份越来越长的规则。请求会给出 `SKILL.md` 的实际绝对路径；链接相对该技能目录解析。完整参考不会默认塞入所有请求，agent 应根据当前问题读取需要的原始资料。wheel 将这些 Markdown 技能及参考一起发布到包内资源，安装后无需依赖开发者机器上的原仓库路径。

R5 对显式 `writing` 请求直接加载一份[科学对象与句间衔接短指南](../skills/scientific-writing/references/object-and-continuity.md)，覆盖对象来源、比较身份、主语/动作、旧新信息、唯一前件，以及相邻句衔接与整段论证的分别核验。协调者和 `full_manuscript` 请求还直接获得[章节依赖方法](../skills/scientific-writing/references/chapter-contracts.md)，包含按证据类型组织引言、Methods–Results 共同责任、全稿标题/摘要和目录反向审查。其余细节仍按需读取；无选择的非写作任务保持原来的窄上下文。载入保证方法到达提示，实际采用和内容质量仍由产物评阅判断。

新增句子方法实读 [Duke Graduate School Lessons 1–2](https://sites.duke.edu/scientificwriting/) 与 Purdue 等原始指导，[精确来源与许可](../skills/scientific-writing/references/cohesion-source-ledger.md)单独保留。章节责任与比较身份核对是项目科学编辑方法，未冒称大学规定的多智能体分工。Gopen/Swan 原网页本轮未取得，未把 Duke 的教学综合写成已读该原文。

## 评阅反馈如何返回

实际流程为：有选择的 worker 请求 → 对原始产物的 reviewer 请求 → coordinator 的结果处置。评阅请求继承对应章节并转为 audit 模式；协调者收到同一任务的写作范围与审阅结果，决定接收、继续、缩小范围或暂缓。

继续原任务时，下一次 worker 上下文会带入版本核验后的 `review_feedback`，包含审阅文件路径、版本和具体发现。下一次协调者计划也收到这些反馈，可安排带有原文与证据定位的新任务：来源问题交 literature，解释问题交 mechanism，修订交 writer，复查交 reviewer。程序传递了反馈并检查记录状态；agent 仍需判断问题和修订是否正确。

审阅反馈文件被修改时，系统拒绝直接复用，要求检查。已有完成请求保留当时保存的提示和输出契约，新技能不会偷偷刷新旧调用，也不会使未知完成状态的调用自动重放。缓存响应仍按当前允许的结构校验；任务内容、章节选择、角色或上下文发生实质变化时需要新请求。

## 验证边界

单元与实际 MAF 图测试检查显式选择、逐步加载、旧契约兼容、元数据往返、评阅及协调者接收、反馈定位与缓存行为。安装检查从 wheel 外部临时目录启动，读取随包技能、解析本地参考并运行实际图演示。

这些测试只能证明分发和交接行为，不能证明写作质量、来源完整性或符合某期刊标准。文本质量仍需要读取真实稿件、证据和来源进行独立评阅；没有实证数据的设计稿不能因指南采用常见结构而制造结果或声称测得效率增益。

项目公开契约的 writing 字段为可选属性，旧契约可以不含该字段。Codex 模型服务要求对象全部属性列为 required，因此 provider 边界递归转换模型传输 schema：原来的可选属性在模型响应中变为“必须出现、可为 null”。返回时仅移除原本可选的 null 字段，再按照原来的项目契约校验；原来必需的 nullable 字段仍保留，科学证据规则不变。保存的请求和公开 schema 不被改写。

维护者可运行 `python scripts/check_writing_provider.py` 做一次明确的真实兼容检查。它使用已有 Codex 登录，在临时目录创建一个新请求，仅要求原样返回包含 writing 字段的契约，不执行契约或写作。该检查需要模型调用；它与离线图演示以及文本质量评阅分别报告。
