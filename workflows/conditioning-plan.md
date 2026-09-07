---
skill: strength-training-design
category: planning
description: GPP/体能计划设计工作流——7 步渐进式设计（定三轴→选维度→测基线→对齐周期→出处方→预算审计→整合输出）。用于"以体能为主角"的请求，与功能三（力量计划含 GPP 附属）区分。
load_condition: 功能五——用户要求设计体能/GPP/conditioning/有氧计划时读取；或用户已有力量计划、需要把体能模块单独展开时读取
---

# GPP / 体能计划设计工作流

## 边界（先判定走哪条路）

| 用户想要 | 走哪个工作流 |
|---------|------------|
| 完整力量计划（GPP 只是其中一块） | **功能三** `design-plan.md` |
| **只要体能计划**，或体能需求复杂（发展型档、多维度组合） | **本工作流（功能五）** |
| 已有力量计划，只需把体能接进去 | 本工作流，重点看步骤 6–7 |
| "有氧会不会掉力量"这类问题 | **功能四** `consult.md` |

---

## 工作流（7 步，按顺序渐进式读取）

1. **确定三轴**（必做，不可跳过）
   → `references/methodology/gpp-framework.md` §3

   | 轴 | 选项 | 默认 |
   |---|------|------|
   | 定位档 | 维持型 / 渐进型 / 发展型 | **维持型** |
   | 器械层 | T1 商健 / T2 自由重量+户外 / T3 专项设备 | **T1 商健** |
   | 落位模式 | 混合 / 课后附加 / 独立日 | **混合** |

   🔴 用户未回答则采用默认值，但**必须在输出中注明"以下按默认档设计，可调整"**。

2. **确定覆盖哪几个维度**
   → `references/methodology/gpp-framework.md` §2（五维分类）

   ⚠️ **默认至少覆盖心肺 + 工作容量两个维度**。多数训练者只做有氧，长期遗漏工作容量与局部耐力——而这两维对力量主项支撑最直接且 CNS 代价低。
   → 活动度细节 `references/health/warmup-flexibility.md`；局部耐力与额外课 `references/westside/gpp-recovery.md`

   ⚠️ **增强式与爆发力（跳箱、药球抛）不在 GPP 五维之内**——它们属 SPP 侧的爆发力训练，归主项课管理，不占 GPP 恢复预算。见 `gpp-framework.md` §7.2。

3. **体能基线**
   → `references/exercises/aerobic-training.md` §7.3（测试协议）

   - 有测试条件：6-MWT / Rockport / 穿梭跑 / 次最大跑台
   - 无设备：**选一个可复现的固定功测试**（划船机 2000 m 计时、固定距离农夫行走计时），每 4–6 周同条件复测
   - 维持型档不需要正式测试，用 RPE 或说话测试确认"没退步"即可

4. **对齐周期结构**
   - **已有力量周期** → 按 `gpp-framework.md` §5 落位表把体能挂上去（容量期是主战场，冲刺期压到最低）
   - **纯体能计划（无力量周期）** → 自建 4–8 周线性进阶，用 NSCA 10% 规则
     🔧 `python scripts/gpp_calculator.py progress --start <起始值> --weeks <周数> --unit min`

5. **逐维度出处方**（必须给到可执行的参数，不能只写"做有氧"）

   - **心肺维度** → `references/exercises/aerobic-training.md` §1（强度 %HRR）、§2（五型谱系）
     🔧 `python scripts/gpp_calculator.py hr --hr_max <值> --hr_rest <值> --zone moderate`
     ⚠️ **必须输出 %HRR 区间 + Karvonen 目标心率；禁止使用 220 − 年龄**（ACSM 12th 明确不推荐）
   - **工作容量维度** → `references/exercises/aerobic-training.md` §3（work:rest）、`gpp-framework.md` §7.1（代谢体能手段库）
     🔧 `python scripts/gpp_calculator.py workrest --system glycolysis --work 20`
     ⚠️ 战绳、药球砸、壶铃摆动、农夫行走放**主项课之后**；若用户想做跳箱或药球**抛**，那是增强式，属 SPP，放**主项课之前**——见 §7.2
   - **局部耐力维度** → `references/westside/gpp-recovery.md`（额外课 15–30 min、2–3 动作）

6. **恢复预算审计**（🔴 强制）
   🔧 `python scripts/gpp_calculator.py budget --phase <阶段> --maintenance <次数> --development <次数>`

   - 恢复性 0% / 维持性 5–10% 每次 / 发展性 15–25% 每次
   - **发展性仅允许容量期与减载周**；冲刺期、测试周禁用
   - 超限时：**砍 GPP，主项容量与强度不动**（全局硬约束 6）

7. **整合与输出**
   → 时序规则 `gpp-framework.md` §6：分天 > 同天间隔 ≥6 h > 同节抗阻在前
   → 爆发力课（高翻/高拉/速度课）所在日不放中高强度有氧；下肢主导有氧距深蹲/硬拉 ≥48 h
   → 手段时序：`gpp-framework.md` §7 的**代谢体能放课后、增强式放课前**

---

## 硬约束（4 条）

1. **主项不动**：若用户已有力量计划，GPP 只填剩余预算，永不反向修改主项
2. **三轴必定**：定位档/器械层/落位模式必须在输出中显式写明（含默认值来源）
3. **强度必量化**：有氧必须标 %HRR + Karvonen 目标心率，不得只写"快走 30 分钟"
4. **阶段必对齐**：发展性 GPP 不得进入冲刺期与测试周

---

## 异常处理（if-then）

| 触发条件 | 处理方式 |
|---------|---------|
| 用户只要"跑跑步"这么简单 | 仍走本工作流，但只输出心肺维度，其余维度省略并说明理由 |
| 用户想同时把力量和体能都当主角 | ⚠️ 明确告知两者会互相挤压；建议分周期切换（休赛期发展型 / 冲 PR 周期维持型），见 `gpp-framework.md` §3 轴一 |
| 用户要练战绳/波比跳/药球/跳箱 | 先判性质：**波比跳、药球砸** = 代谢体能（GPP，课后）；**跳箱、药球抛** = 增强式（SPP，课前，需先评估落地技术）。见 `gpp-framework.md` §7 |
| 用户有伤病/疼痛 | 读 `references/health/injury-prevention.md`；优先低冲击模态（游泳/椭圆/自行车），避开受伤部位主导的动作 |
| 用户没有心率设备 | 用 RPE（6–20 量表）与说话测试锚定强度，见 `aerobic-training.md` §1.3 最右列 |
| 用户目标是减脂 | 有氧量可上调但仍受恢复预算上限约束；优先增加 NEAT 而非堆有氧时长 |
| 用户体能基础很差（久坐起步） | 定位档强制降为维持型；先 4–6 周广泛耐力打基础，再考虑任何间歇（NSCA 明确要求） |
| 用户未做基线测试且拒绝测试 | 用 RPE 自评起步，4 周后复评；在输出中标注"未测基线，强度为估计值" |

---

## 输出格式（六项）

1. **三轴配置**（定位档 / 器械层 / 落位模式，标注是否为默认值）
2. **各维度处方表**：维度 / 手段 / 频率 / 时长 / 强度（含目标心率）/ 周期落位 / **课前或课后**
3. **恢复预算审计结果**（脚本输出，含是否超限）
4. **进阶与测试安排**（10% 规则进阶表 + 复测时间与方法）
5. **与力量训练的时序**（若适用：哪天做、与主项间隔多久）
6. **调整触发条件**（什么情况下降档：如主项连续两周 RPE 异常升高 → 先砍发展性）

---

## 参考

- 编排骨架：`references/methodology/gpp-framework.md`（🔴 全程参考）
- 心肺处方：`references/exercises/aerobic-training.md`
- 干扰机制：`references/methodology/concurrent-training-interference.md`
- 恢复性小课：`references/westside/gpp-recovery.md`
- 脚本：`scripts/gpp_calculator.py`（hr / workrest / budget / progress 四子命令）

*最后更新：2026-09-07*
