# Synthetic 数据描述性核对

任务：simulation_01；尝试：1（唯一一次）；阶段：exploration。对应主张：C_SYNTHETIC_TREND、C_EVIDENCE_BOUNDARY。用途是为后续简短中文报告提供可对照输入的描述性结果。

## 输入与直接观察

实际读取项目根目录 `input.txt`。原文如下，保留原始数值：

> This is a coordination smoke test. Synthetic observations: coarse QoI A=1.000, B=0.800; fine QoI A=1.002, B=0.802. No real experiment or physical validation. Do not interpret these as new scientific discovery.

| 输入标签 | A | B |
| --- | --- | --- |
| coarse | 1.000 | 0.800 |
| fine | 1.002 | 0.802 |

这些数值是输入明确标注的 synthetic observations。两组中 A 均大于 B。QoI 的物理含义、单位、生成方法和误差模型均未知；coarse、fine 仅作为原文标签使用。

## 算术推导

以 PowerShell decimal 算术核对，输出保留输入已有的三位小数：

```text
fine A - coarse A = 0.002
fine B - coarse B = 0.002
coarse A - B = 0.200
fine A - B = 0.200
```

因此，在给定两组 synthetic 数值中，fine 标签下 A、B 相对于 coarse 标签下均增加 0.002；A−B 均为 0.200。这里只描述两组输入之间的关系，不能据此外推连续趋势。

## 证据边界与检查适用性

证据等级限定为 **observation**；上述差值属于给定数据的算术推导，不构成求解器数值验证或物理验证。原始四个数值与输入逐项对照，差值核对已完成，无缺失输入或算术失败。

没有控制方程、材料参数、初始或边界条件、网格尺度、离散方法、时间步或真实实验参照，故单位一致性、守恒、稳定性、误差估计和数值收敛检查不适用于本次数据描述任务，也未执行。coarse/fine 标签不能证明网格细化或收敛；相同增量不能证明精度改善。

本次未启动外部求解器，未检索网络，未拟合、外推、生成新数据或增加精度。没有物理验证、真实科研发现或效率提升证据。结果足以支撑限定在给定 synthetic 数值内的报告表述；任何机制、真实系统行为或方法性能解释仍缺乏依据。

## 实际产物与成本

产物为项目根目录 `simulation-result.md` 与 `simulation-contribution.md`。只进行了本地输入读取、decimal 差值核对及两份文本输出；任务尝试 1 次，外部求解器调用 0 次，网络检索 0 次。没有额外精度研究，未计量性能或效率。
