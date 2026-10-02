# 科研智能体的分节写作方法

本文件把原始指南的思想变成诊断与修复步骤；是项目自行撰写的操作方法，不是任何大学或期刊的统一规范。来源ID对应[source-ledger.md](source-ledger.md)。下面英文小例子均为**原创、假定条件下的语言示例**，不报告新的实验或计算结果；只有当真实证据满足例子写明的前提时才能采用其句式。不得把占位变量、假设效果或未执行流程写入论文。

<a id="title"></a>

## 标题：主题、关系、范围与自然搭配

**依据：MIT_CEE_TITLE、USC_TITLE、PLOS_STRUCTURE；精确语言依据UNC_SCIENTIFIC_STYLE。**

先从证据写一句普通话：研究对象是什么，改变/比较/解释什么，在哪些条件下。然后选择标题形态：主题式用于描述明确问题/适用性，关系式用于表达受控比较，结论式用于一个可支持的发现。三种都可用，结果为负时不必伪装成问句或正向改善。

检查时先读语法主干，再检查科学关系：

1. 主名词或主语是什么？修饰语分别修饰哪个名词？堆叠多个名词后，能否有两种理解？
2. 关系词是否准确？`effect of X on Y`需要说明X怎样被改变与控制；`association between X and Y`适用于关系分析；`prediction of Y`不自动意味验证；`validation of model`要有对应独立参照。`and`只说并列，不能代替真正研究的关系。
3. 范围是否诚实且有必要？材料、模型、工况、数据设计等保留能防止关键误读的部分；不用把所有假设、软件和结论塞入标题。
4. 术语是领域现有名称还是临时拼出来的抽象短语？检查最接近的原始论文正文和标题中该词的对象/搭配；拼写检查器只能判断形式，不能判断物理含义。新概念若确有必要，要定义并给依据。
5. 删掉修饰语后，会失去什么事实？没有事实损失的`novel/advanced/comprehensive`或`A study of`通常可以删除。删到无法识别范围时停止。

**原创例子。** 如果真实任务是物性假设对数值熔池输出的敏感性，`Thermal interpretation property influence framework`缺少清楚的名词关系；`Effects of high-temperature property assumptions on melt-pool geometry`直接标出对象与关系。若范围必须防止外推，可加`in an IN625 conduction model`。这是条件式编辑示例，不宣称该关系已由大学指南或新试验验证。若研究实际只有相关性，`X controls Y`应改为`Association between X and Y under Z`；只有受控证据支持时才选`Effects`。

**路由与返回。** 写作智能体给少量有不同科学含义的完整候选并说明含义差异；文献智能体核对陌生搭配和已有同方向工作；机制智能体检查关系词是否越过因果证据。候选一旦主干清楚、术语自然、范围匹配且所有关系可追证据就返回，不以词数或“听起来高级”评分。

<a id="abstract"></a>

## 摘要：问题—证据—回答—意义

**依据：MIT_ABSTRACT、MIT_CEE_TITLE、PLOS_STRUCTURE。**

从当前结果和讨论生成摘要，不从旧宣传性目标生成。先列每项可能结果及其作用：回答主要问题、区分解释、给出量级、展示反例、限定适用性。按作用合并，保留完成故事所需的内容。

摘要的读者应能回答：这个具体问题为什么值得问，研究如何问它，得到什么答案，答案改变了什么认识或使用方式。背景应为问题作铺垫；方法只写理解比较所需的设计；结果与回答连接；结尾的意义应由答案导出。结构顺序可按期刊和研究类型调整。前后不必每次都“广—窄—广”，也不必出现固定Here we show。

**数字选择。** 对每个数字问“没有它，读者会误判方向、量级、可信度还是适用范围吗？”选择能锚定核心回答的数值，同时保留该比较必要的基准、单位与条件。多个数值只有承担不同论证作用时才保留；不能规定两个数，也不能为了简洁移除决定性反证/不确定性。无统计检验时避免`significantly`；物理量和百分比混用时要说明各自对象。

**原创正结果示例，前提为独立比较确有支持。** 模糊：`The proposed approach is powerful and promising.` 具体：`Across the tested conditions, the revised source model reduced the depth error while preserving the width response.` 接下来的意义应说明哪种使用能力得到支持，而不是泛泛“推动领域”。如果只有某一个工况成立，必须保留工况，不写across。

**原创负结果示例，前提为受控变化未修复偏差。** 错误：`The new closure improves the model and provides excellent agreement.` 具体：`The closure change shifted the rear boundary but retained the width–depth discrepancy.` 可支持的意义：`This separates sensitivity of the thermal tail from correction of the fusion shape.` 这是一种认识上的区分，并非性能改善；是否能用需回到真实对照。

**非结论示例。** 若置信/误差范围仍含有无变化，写`The comparison did not resolve an improvement in X`并交代何种精度/样本限制；不能改成`X has no effect`。反方向结果应报告方向和条件，不把失败改成“robustness”。

**返回条件。** 每句可标明问题、设计、发现、解释或意义；标题和摘要回答同一个问题；数值与正文一致；没有由助手工作流生成的“验证”。如果意义需要新实验才能成立，先收窄意义，返回那个实验问题，不用形容词填补。

<a id="introduction"></a>

## 引言：综合已有认识并推导研究问题

**依据：MIT_INTRODUCTION、MANCHESTER_INTRODUCTION、PLOS_STRUCTURE、UNC_PARAGRAPHS。**

先定义目前读者应接受的认识，再说明哪些证据建立了它、什么条件限制了它、这些条件为什么使本研究问题值得检验。按问题/机制/观察对象综合来源，不按作者年份轮流介绍。每个文献组应有共同作用：确立可行性、给出成功条件、揭示歧义、提出另一解释或说明测量范围。

段内推理需要闭合：读者理解此段谈什么；看到与它直接相关的证据；理解证据怎样支持判断；看到判断和论文问题的关系。闭合可以是一个综合认识、条件界定、反例、尚未解决的问题或下一步定义，不要求每段都“仍然缺乏研究”。原文资料如果已经解释了该现象，新的引言必须承认并收窄问题。

**原创例子，假设两项源文献确实提供所述事实。** 松散：`Smith used model A. Jones used model B. Many challenges remain.` 综合：`Both models recover cross-sectional dimensions after source calibration, but they use different observables to constrain the fit. Their agreement therefore leaves the thermal-profile comparison dependent on how those observables are defined.` 这一推理需要原件核对拟合对象与温度比较；若第二句超出原文，只能写条件式问题，不能借两个引用制造结论。

引言最终研究目的应匹配这条推理。若已知几何拟合可成功，不能宣称“传统模型无法预测几何”；可问“在一种已拟合模型中，哪些物性假设改变尾部位置和相间隔？”贡献要体现改变了哪个认识/比较，而不自动叫“新算法”。

**段间诊断。** 摘出各段关键判断，连读判断链。后一段是否使用了前段已经建立的词、条件或问题？如果新对象突然出现，补必要定义或调整顺序。引言首段可以直接从具体可理解问题开始；“应用很重要—研究很多—有挑战”不能代替动机。

**路由与返回。** 文献智能体负责已有认识、可比条件和缺口；写作智能体负责把核对过的认识变成完整段落；协调者判断是否改变研究贡献。引言满足问题的合理来由与末段可兑现的目标就返回。若搜索没覆盖足够范围，写明实际未解决的问题，不使用first/no previous study。

<a id="continuity"></a>

## 段落与章节衔接：先有关系，再有语言

**依据：UNC_TRANSITIONS、UNC_PARAGRAPHS、MANCHESTER_TRANSITIONS、PLOS_STRUCTURE。**

反向提纲每段只写两项：此段的控制思想；它从前段接到什么、交给下段什么。这是临时诊断，不必把表格写进论文。相邻关系可以是范围收窄、补充证据、比较条件、反例、解释、假说判别或从空间量转向时间量。先让科学名词/指代稳定，再选择自然的连接语。

**原创桥接例子，假设前段已建立共同尾部位移。** 空：`Furthermore, cooling rates are important.` 实：`The two rear boundaries move together, so their position relative to the source and their separation must be considered separately.` 后段若进入材料时间，可写：`Converting that separation to a passage time also requires the scan speed.` 桥接有具体对象和所需条件，不依靠“上一节/本节/下一节”统一路标。

使用`therefore`前，写出前提怎样推出结论；使用`however`前，确认两句存在真实对立。没有关系时移段/补证，而不添加更多副词。保留必要的显式路线，例如跨领域或长节切换，但上下文已经顺畅时无需每节重复总结。

**返回条件。** 邻近读者能够准确复述前后两段的关系；指代不歧义；移除装饰连接词后逻辑仍然成立。若无法复述，应返回结构缺口而非继续同义词修饰。

<a id="methods"></a>

## 方法：客观定义、参数角色与可复现配置

**依据：MIT_METHODS、MANCHESTER_METHODS、UNC_SCIENTIFIC_STYLE。**

先说明研究设计如何回答问题，再定义模型/样本/观察/比较和必要数值设置。方法并非每项结果后的免责声明，也不是软件功能清单。主动/被动语态由清楚的科学主语决定：`The model solves...`、`Samples were selected...`和`We calibrated...`都可客观；它们必须描述实际行为。时态按功能：已执行程序可用过去时，方程/定义可用现在时，当前论文目的另择清楚表述；不套用全节统一时态。

对每个参数标明角色：材料/测量来源、数值控制、假设闭合、拟合参数或观察阈值。给相应依据：材料状态与单位；控制方程/边界条件；拟合数据、目标与约束；观测操作；网格/时间步与结论相关的敏感性。软件若影响算法行为就说明其作用；纯版本/命令/路径转到可访问的复现记录。若算法实现本身是论文贡献，细节应在正文充分展开。

**原创客观披露示例，前提为真实设计。** 防御：`This is not independent validation and is not a statistical experiment.` 描述：`Condition B length defines the calibration objective. Width and depth are assessed after fitting, and the other conditions retain the fitted factor.` 必要时再加：`All reference targets were available during model development, making these comparisons retrospective and nonblind.` 这个事实不能为减少负句而删除。

**参数来源示例。** 模糊：`Accurate liquid properties were used.` 客观：`Tabulated properties are interpolated to their upper endpoints; above those endpoints the model uses the stated continuation rule.` 若端点低于固相线，说明温区并保留续接是假设的界定；不能把它美化成测得液态数据。

**比较设计示例。** 与其`The branch was not recalibrated`单独重复，可写`All branches retain the baseline source factor, isolating their responses to the specified property changes.` “isolating”只用于确实保持其余控制与观察一致的设计；若改变了恢复算子等，应交代该分支改变的完整组成，不夸大隔离层级。

**信息分配诊断。** 此细节改变理解、推导、比较或误差判断吗？放正文。复现需要但会打断论证吗？附录/方法补充/代码说明并留关联位置。仅记录程序调试经过吗？开发/复现记录。不能仅凭“数字很多”或“软件”决定去留，也不能移动后让复现链断裂。

**返回条件。** 读者可重建控制、参数、目标和观测的关系；新方法/改动足以评估并复现；重要材料/校准/验证事实仍公开客观；不存在用声明或库清单替代必要收敛证据的问题。无此证据时交给计算智能体一个命名比较，不盲目扩大测试。

<a id="results-discussion-conclusions"></a>

## 结果、讨论与结尾：让相同证据承担不同工作

**依据：PLOS_STRUCTURE、UNC_SCIENTIFIC_STYLE；证据层级采用项目研究方法，不是大学文体规则。**

结果提供问题所需的比较、方向、量级、异常和误差，避免逐面板复述。讨论解释这些证据改变的认识、与最近可比工作的一致/差异、仍存替代解释及真正限制。结尾提炼已回答的问题和重要含义，不增新机制或未测试的应用。

负结果可说明某个具体控制方案不足，不能证明所有方法都失败；无变化可指出当前精度未分辨效应，不能证明零效应。一个联合变化改善了结果，不证明某部件独立导致改善。派生量可帮助理解同一场，但不应增加独立验证终点数。

限制在它改变解释的地方说明：如果峰温超出模型含蒸发过程的范围，说明它影响物理温度预测；不用在每个已经限定的结果句旁再写“仅模型”。如果图像可能被误认作实验/流场，图注应保留局部事实说明，即使正文已有总体界限。一次说明原则不是禁止所有科学上必要的局部限定。

**原创例子，假设诊断区域会随温度变化。** 过强：`Lower conductivity reduces heat escape and causes the longer tail.` 证据匹配：`The tail lengthens under conductivity holding, while the temperature-selected region and its gradients also change. A matched-region flux comparison is needed to isolate the proposed heat-escape explanation.` 若实际净导热功率上升，保留该反证；不要为简洁删掉它。

**返回条件。** 讨论较结果多做了综合/解释/条件比较；结尾与标题摘要同一认识；未检验机制仍为可检验解释；缺证据有明确问题和较便宜的判别替代。停止不改变读者认识的可选润色，交付完整段落或章节。
