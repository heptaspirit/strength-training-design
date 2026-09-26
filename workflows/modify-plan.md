---
skill: strength-training-design
category: planning
description: 修改现有训练计划工作流——需求收集、保守修改（每次1-2变量）、修改后检查清单。
load_condition: 功能二——用户要求修改现有训练计划时读取
---

# 修改现有训练计划工作流

**触发**：用户已按计划训练 1-2 周，觉得不妥想改（"容量太大了""想换动作""恢复不过来"）。

**执行**：读取 `references/planning/plan-modification.md` → 每次只改 1-2 个变量 → 用户确认后输出。
- 如改动的理由是疼痛/恢复问题，同时参考 `references/barbell-medicine/pain-management.md`（BBM 主动康复策略）和 `references/barbell-medicine/barbell-medicine-methodology.md`（适宜剂量）
- 如改动的理由是"流传的观念对不对"，同时参考 `references/barbell-medicine/barbell-medicine-methodology.md`（BBM 循证反共识表）
- 如改动的理由是"某天太累 / 某个动作做不动 / 想换动作顺序"，先跑课内应激审计 → `references/consultation/session-strain-modeling.md`（顺序只转移代价不改变总量，先分清是净增还是重排）
- 如改动是**把动作挪到别的训练日**，两层决策：先用训练学规则筛合法落点，再跑模型排序 → `references/planning/exercise-placement.md`（不能只按 sRPE 硬算）

**修改后检查清单**（详见 `references/planning/plan-modification.md` 末尾）：
1. 修改需求明确
2. 调整符合 JTS 原则（优先减少辅助动作）
3. MRV 审计（≤ MRV）
4. RPE 预期合理
5. 时间安排合理
6. 动作替换合理（同肌群）
7. 改动涉及顺序/日期时：重跑课内应激审计，确认没有动作落进"链条受限"或惩罚 >1.5
8. 改动涉及换训练日时（`references/planning/exercise-placement.md` §4）：七项同步已改全——原日节 / 新日节 / 速查表 / 周总量 / MRV 表（含单次峰值）/ 优先级与退阶 / 该日标题
