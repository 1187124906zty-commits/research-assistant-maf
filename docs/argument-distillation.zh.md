# 从审核写作库到任务方法

本次增量把科学写作库的可迁移判断蒸馏为短参考，并按显式章节分发。运行时不依赖开发者的库目录，不把570条句型/搭配完整塞进prompt，也不把来源论文结论当成当前研究证据。先按读者要做的判断选择论证动作，再填入实际对象、命题、来源、比较与成立条件。

[argument-distillation.md](../skills/scientific-writing/references/argument-distillation.md)有五个可选部分：读者任务、语言与精简、文献综合、比较与推断，以及正文、图表和附录之间的证据分配。所有显式writing角色得到前两项；引言取得文献综合；摘要、方法/结果、讨论/结论取得比较与推断；方法/结果、讨论/结论和全文选择取得`evidence-medium`。引言、标题/摘要和没有显式writing选择的任务不注入该段正文。多章节合并去重，未显式选择的领域任务不会自动展开。既有section指南、scientific-object方法和补证协议继续承担原职责。

`evidence-medium`是从本次AMMT稿件文字承担过多信息、显示证据不足这一实际缺口提出的编辑方法扩展，没有将它包装成顶刊统一规范，也未宣称重新逐篇蒸馏得到该规则。它要求先按读者要做的判断选择载体：正文解释推断，表格承载精确比较与操作定义，曲线或分布图呈现关系，必要的示意图解释困难的空间或流程关系。主结果判断所需的证据应靠近主结果，完整输入和扩展检查按首次阅读需要分配到附录。图数、文字与图的比例或减少数字本身均不是质量依据；真实稿件和渲染页面仍须一同审阅。

词语选择检查完整关系：两个命题为何需要连接、动词断言什么、搭配还缺哪个对象或条件。精简删除报告外壳和重复介绍，保留会改变科学含义的条件、比较、数据角色、不确定性、候选原因与替代解释。设计目的不能改成已有效，标定不能改成验证，作者结论也须与其实际证据一致。

[来源账本](../skills/scientific-writing/references/distillation-source-ledger.json)保留库ID、DOI、实际定位、适配章节和迁移边界。本次依据审核库记录蒸馏，不宣称逐篇重新阅读全部全文。例如EXP-NMI-P007适配Methods，但原文是Discussion，不能把未来可做的制造性筛选写成已执行。EXP-NPCMOA-P012从Results学习约束说明，也不能由平均组成守恒推出局部动力学全部满足。未记录的base语言章节标为未记录，不按适配章节猜测。

[新案例](../examples/argument-distillation/README.md)提供真实AMMT证据上的手工段落候选、语义反例和原生MAF/Codex入口。旧稿、旧运行和历史报告不覆盖。单元测试检查分发、来源绑定和负例反转，不能证明文稿质量。实际读稿、证据核对与独立评阅判断新稿论证；原生远程模型执行和Codex桌面协作按真实路径分别报告。

2026-10-03前一批本地验证：102项完整unittest通过，新语义回归8组通过；实际离线MAF graph两轮完成。sdist和wheel在D盘隔离构建，源码目录外安装检查通过，33项包内role/skill资源与当时源文件内容一致，guidance代码一致。两项修改skill通过skill-creator的quick_validate。`run_forward --prepare-only`生成有效的真实AMMT输入manifest；原生SDK模型调用当时因C盘已满而未完成初始化，不能计作模型写作成功。主协调者另行组织的实际写作和独立评阅结果不由这些软件检查代替。

新增证据分配路由后，完整unittest为103项，全部通过。新增测试对六个角色的实际loader输出检查该段完整正文：方法/结果、讨论/结论和全文载入；引言、标题/摘要及无writing选择不注入；合并章节只载入一次。最终包构建、隔离安装和包内路由结果另以本轮`media-allocation-validation/validation.json`及`validation.md`记录，软件检查不证明论文质量或原生线上模型行为。

本轮增加[库使用契约](../skills/scientific-writing/references/library-use.md)：先确定`section × position × purpose`，再绑定科学对象、是否已引入、命题及证据。实际有外部库时读取`general/usage-index.json`，调用其structural query，并回到候选的原文和邻句判断适用性。sidecar的人工reviewed target是编辑推荐；原文`source_location/source_position`独立记录，未核对的位置保持unverified。候选不是成句，缺必要slot不能ready；关键词只辅助对象明确后的术语检索。MAF包仅带短契约，不拷贝完整库，不依赖开发者绝对路径；库不可用时明确披露检索未执行。

Loader按显式scope分发完整的必要正文：所有writing选择取得selection-contract；标题/摘要追加abstract-opening；引言追加introduction-bridge；标题/摘要、引言、方法/结果追加model-introduction；全文并集去重。原`evidence-medium`分发范围保留。无显式writing选择的任务不注入新增正文，尤其不因brief中出现“摘要/引言”等关键词扩展领域任务。

摘要首句允许背景或直接研究操作，只要求对象与具体关系可恢复，不强制先讲背景。引言逐段确认“上一段留下什么→下一段承担什么”，末段目标与路线由已有矛盾推出，真正认识或能力贡献有支持才写；不强制“综上所述”、贡献列表或连接词配额。模型首次实质引入交代研究adopts/formulates/modifies什么、名称与scope/role，再稳定短称；不是每章都写“本研究”，也不是以复杂新名词替代采用依据。禁止空roadmap不禁止必要的科学桥接。以上是项目编辑综合，不能包装成期刊统一要求。

新增测试验证实际loader正文路由、组合去重、原证据路线保留、资源树迁移后加载，以及缺失/重复anchor显式报错。这些软件不变量不证明agent已读原文或已写好稿件；实际检索记录、真实稿件和独立审阅仍承担该判断。本轮执行记录保存在`position-purpose/maf-validation/`，不覆盖前轮历史。
