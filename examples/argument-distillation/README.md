# 审核库蒸馏与新写作案例

本案例包含新AMMT段落改写和可运行评价入口，历史R4/R5例稿、报告与用户稿件保留原样。[段落候选](ammt-paragraph-revisions.md)使用既有证据，实际写出Methods、Results、Discussion三组改写；before为人为构造缺陷，不冒称用户原文或模型输出。

运行[语义反例](check_contracts.py)：

```powershell
python examples/argument-distillation/check_contracts.py
```

八组命题包括best-of-N/mean、选中候选/全体检验、非唯一性、约束范围、设计/评估、标定/独立检查、精简保留条件，以及作者总结与正文计数不一致。负例必须被拒绝，改变真实证据后相应判断才能反转。唯一性只做反证：有限搜索不能证明数学唯一。数值是构造反例，命题由评阅者标注，不从句子关键词生成。脚本成功不表示语言模型、论文或科学方法得到验证。

实际MAF/Codex前向入口使用当前AMMT稿件与证据，默认sibling `research-workflow/paper/ammt-study`。模型不收到上述after候选：

```powershell
python examples/argument-distillation/run_forward.py --workspace D:/my-runs/ammt-distillation-01 --prepare-only
python examples/argument-distillation/run_forward.py --workspace D:/my-runs/ammt-distillation-02
```

第一条只生成manifest，无模型调用；第二条使用`openai-codex==0.159.3`和已有登录，运行现有MAF graph的worker→reviewer→requester。`--paper`指定另一份AMMT目录；`--evidence PATH`追加已核对材料。工作目录与manifest必须是新路径；不覆盖历史输出或自动重放未知调用。

任务输出完整Methods/Results/Discussion候选与至少三组有定位的修订说明，不要求关键词、句式数量或更短字数。软件运行、模型完成、独立文稿评阅和实际物理证据分别记录。

2026-10-03主协调者尝试原生MAF前向运行，graph进入提供者后，SDK因C盘无可用空间而无法初始化`C:/Users/Administrator/.codex`下SQLite状态，返回TransportClosedError。模型尚未启动；原ledger保留，未自动重放。该次不能计为模型修稿成功。协调者另行安排Codex桌面agent实际修稿与独立评阅，两种路径须分别报告。
