---
skill: strength-training-design
category: guardrails
description: 全局硬约束与反模式清单——5 条不可违反的设计约束 + 常见错误对照。所有 workflow 共享的单一约束入口。
load_condition: 任何功能执行时都必须遵守；设计/修改/咨询涉及规则判断时读取详述。
---

# 全局硬约束与反模式（Guardrails）

本文件是 skill 的**单一约束入口**：所有 workflow（设计/修改/咨询）共享的不可违反规则，以及常见错误对照。详细规则保留在各专业参考文件中，此处汇总指向。

## 五条硬约束（设计时强制）

1. **主项 TS/BO 时序（按 phase，不绑周数）**：仅在**强度聚焦 phase（力量期 + 冲刺期）**强制安排 TS/BO；**容量期（无论几周）无 TS**；**减载周无 TS/BO**。具体落在第几周由 phase 决定（如 8 周骨架的 W5-8、10 周带诱导骨架的对应强度周），不要写死成固定周次。
   → 详见 `references/methodology/block-length-and-phase-extension.md`（块长度与阶段延长）与 `references/output/output-templates.md`
2. **辅助双进阶**：孤立动作禁止"每周+2.5kg"线性加重；先加次数 → 到上限后加重 → 回到次数下限。
   → 详见 `references/intensity/rpe-reference-and-progressive-overload.md` 第十节
3. **Cluster Set 备选**：RPE ≥8.5 的 TS 必须提供备选方案。
   → 详见 `references/intensity/rpe-reference-and-progressive-overload.md` 第十节
4. **硬拉容量上限**：全程传统硬拉工作组 ≤6 组/周（中级）；后侧链分散到多日、不全堆硬拉日；RDL 等髋铰链补充距硬拉 ≥72h。
   → 详见 `references/volume-recovery/deadlift-volume-management.md`
5. **频率与 6 天约束**：每肌群每周 ≤2-3 次、两次重训间隔 ≥48h（MPS 窗口 + Schoenfeld 2019/Grgic 2018）；6 天/周模板第 6 天只放小肌群/功能/变式，不做大肌群重训，三大项不做 3 次/周。
   → 详见 `references/output/output-templates.md` 模板四

## 操作反例（不要做这些事）

| 反例 | 为什么 | 正确做法 |
|------|--------|---------|
| ❌ 对辅助动作每周 +2.5kg | 孤立小肌群无法线性加重 | ✅ 双进阶：先加次数 → 到上限后加重 → 回到次数下限 |
| ❌ 在容量期（任何周数的容量积累阶段）加入 TS | 容量期目标是肌肥大，TS 增加不必要的 CNS 疲劳 | ✅ 容量期只用固定重量直组 |
| ❌ TS 做到力竭（RPE 9.5-10） | ACSM 2026 确认力竭训练无额外收益，反而增加受伤风险和恢复时间 | ✅ TS 上限 RPE 8.5 |
| ❌ 减载周使用 TS/BO | 减载的目的是恢复，不是刺激 | ✅ 减载周降容 40-50%，RPE ≤6 |
| ❌ 手动心算 RPE 转换或重量取整 | 容易出错，且浪费 token | ✅ 必须调用批计算脚本 |
| ❌ 硬拉和深蹲大重量日安排在相邻天 | 违反 SRA 曲线——两者 CNS 疲劳叠加 | ✅ 间隔 ≥72h |
| ❌ 硬拉日堆大量后侧链（硬拉 4×6 + RDL 3×8） | 硬拉每组 CNS/疲劳代价相当于 2.5-3 组 RDL；同天叠加脊柱轴向负荷过度 | ✅ 硬拉日仅用低疲劳后侧链补充（背伸/臀桥）；RDL 移至深蹲日或辅助日 |
| ❌ 后侧链容量不够就加硬拉组 | 硬拉组是后侧链容量"最贵"的选项 | ✅ 优先用腿弯举、臀推、背伸堆后侧链容量（CNS 代价极低）；详见 `references/volume-recovery/deadlift-volume-management.md` |
| ❌ 分拆后侧链后每天都有后侧链训练 | 看似"分开练了"，实则整周无恢复窗口；连续后侧链刺激导致疲劳堆积 | ✅ 确保 ≥1 天零后侧链刺激日；连续后侧链训练天数 ≤2；详见 `references/volume-recovery/deadlift-volume-management.md` 第五节周疲劳曲线 |
| ❌ 有氧安排只说"快走 30 分钟" | 缺少强度量化，无法确保在目标区间 | ✅ 必须标注心率区间（如 Zone 2: 115-134 bpm） |
| ❌ 大肌群每周训练超过 3 次（如三大项 3 次/周） | 频率研究（Schoenfeld 2019 / Grgic 2018）显示 3 次 vs 2 次无额外收益，反而压缩单次容量、延长恢复 | ✅ 每肌群每周 ≤2-3 次，两次重训间隔 ≥48h |
| ❌ 6 天/周计划第 6 天仍做大肌群重训 | 越过 48h 间隔约束，疲劳堆积（反例：PHUL 6 天版把三大项排到 3 次/周且周五冲峰值） | ✅ 第 6 天只放小肌群/弱项变式/功能/体能，详见 `references/output/output-templates.md` 模板四 |
| ❌ 凭记忆回答咨询问题 | 可能遗漏或错误 | ✅ 先读对应咨询文件，标注来源 |
| ❌ 生成计划前不确认直接输出 | 用户可能需要调整，浪费 token | ✅ 步骤 7 必须先确认 |
