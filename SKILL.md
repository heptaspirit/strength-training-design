---
name: strength-training-design
description: 力量训练计划设计，支持 JTS 周期化、Westside 共轭、近年 ACSM 指南、MRV 审计等方法论。当用户请求设计/修改/审计力量训练计划、评估训练容量、根据 RPE/RIR 制定周期化计划、**估算 1RM（PR）**、**修改现有训练计划**时触发此 skill。适用场景：(1) 设计 8 周/12 周力量周期计划，(2) 基于 JTS 原则做 TS/BO 结构，(3) 对现有计划做 MRV 审计，(4) 根据 RPE 数据调整训练容量/强度，(5) 生成适合 Obsidian 的 Markdown 训练计划文档，(6) 估算用户 1RM（PR），(7) 修改训练了一段时间后的现有计划。
version: 0.8.0
---

# 力量训练计划设计 Skill

## 概述

本 skill 提供基于多派系整合的力量训练计划设计能力，整合 JTS、Westside Barbell、近年 ACSM 指南 等方法论，支持 MRV（最大可恢复容量）审计和 RPE 自我调节。

## 核心方法论

详细方法论参考以下文件（按需加载）：

- **JTS 周期化原则** → `references/methodology/jts-periodization.md`
- **Westside 共轭法 & 近年 ACSM 指南** → `references/methodology/westside-acsm.md`
- **RPE/RIR 自我调节** → `references/methodology/autoregulation.md`
- **MRV 审计方法与数据** → `references/volume-recovery/mrv-audit.md`
- **恢复周期与训练频率** → `references/volume-recovery/recovery-and-frequency.md`
- **身高/肢体比例与弱点分析** → `references/exercises/anthropometry-and-weak-points.md`（按需）
- **热身、放松与灵活度** → `references/health/warmup-flexibility.md`（按需）
- **伤病预防** → `references/health/injury-prevention.md`（按需）
- **实力推 OHP** → `references/exercises/ohp-training.md`（按需）
- **核心稳定训练** → `references/health/core-training.md`（按需）
- **有氧训练** → `references/exercises/aerobic-training.md`（按需）

---

## 功能一：PR（1RM）估算

当用户**没有完整训练计划需求**，只是想估算自己的 1RM（PR）时，使用此功能。

### 触发条件

用户提问包含以下意图之一：
- "帮我估算一下我的 1RM"
- "我想知道我的深蹲/卧推/硬拉最大重量"
- "用 XXkg 做了 YY 次，帮我算算 1RM"
- "我没有测试过 1RM，怎么估算"

### 执行流程

详细流程、估算方法、输出格式等，请**先读取** `references/intensity/pr-estimation.md`，包括：
1. 询问用户信息（训练经验、性别、体重）
2. 选择估算方法（AMRAP 测试 / 体重倍数法 / RPE 反推）
3. 输出估算结果（保守值 + 参考范围 + 校准建议）

> ⚠️ **重要**：估算结果仅作为计划起点，实际训练中通过 RPE 快速校准（2-3 周内找到真实 PR）。
---

## 功能二：修改现有训练计划

当用户**已经按照计划训练了一段时间**（通常 1-2 周），觉得某些地方不妥，希望修改计划时使用此功能。

### 触发条件

用户提问包含以下意图之一：
- "我练了一周，觉得 XX 动作不合适，想换一下"
- "这个计划的容量太大了，能不能调整一下"
- "我想把训练日从周一到周三，改成周二到周四"
- "硬拉后恢复不过来，能不能减少硬拉的容量"
- "帮我修改一下现有的训练计划"

### 执行流程

完整修改工作流、需求收集、容量/强度/动作调整方法等，请**先读取** `references/planning/plan-modification.md`。

**修改原则**：保守修改（每次只修改 1-2 个变量），保持方法论一致性，用户确认后再输出完整计划。

---

## 功能三：完整训练计划设计（原有功能）

### 计划设计工作流

设计完整训练计划时，请按以下顺序**渐进式读取**参考文件：

1. **确定目标与约束** → 收集用户信息（PR、目标、频率、伤病、肢体比例等）
   - 若未测试过 1RM，先读取 `references/intensity/pr-estimation.md`
   - 身高/肢体比例与弱点分析：`references/exercises/anthropometry-and-weak-points.md`
   - 伤病预防自测：`references/health/injury-prevention.md`

2. **设计周期结构** → JTS 风格周期（容量期 → 减载 → 力量期 → 冲刺期 → 测试周）
   - 详细周期化原则：`references/methodology/jts-periodization.md`
   - 恢复周期与训练频率：`references/volume-recovery/recovery-and-frequency.md`

3. **各动作类型设计** → 主项 TS/BO 结构、辅助动作选择
   - RPE ↔ %1RM 参考表：`references/intensity/rpe-reference-and-progressive-overload.md`
   - 辅助动作数据库：`references/exercises/assistance-exercise-database.md`
   - 动作进退阶链（伤病/限制时的降级方案）：`references/exercises/assistance-exercise-database.md` 第九节
   - 薄弱点与奥举辅助：`references/exercises/weak-points-and-olympic-lifting.md`

4. **核心稳定与有氧设计** → OHP、核心训练、有氧安排
   - OHP 训练：`references/exercises/ohp-training.md`
   - 核心稳定：`references/health/core-training.md`
   - 有氧训练：`references/exercises/aerobic-training.md`

5. **MRV 审计** → 确保各肌群容量 ≤ MRV
   - MRV 数据表与审计方法：`references/volume-recovery/mrv-audit.md`
   - 加权疲劳审计（进阶）：`references/volume-recovery/mrv-audit.md` 加权疲劳审计章节

6. **退阶方案与自我调节** → JTS 自我调节原则
   - 详细内容：`references/methodology/autoregulation.md`

7. **输出前确认** → 展示概要供用户确认，不得擅自输出完整计划

8. **输出并与在线文档同步**（可选） → 支持多平台
   - 输出后附训练日志模板，供用户追踪实际 RPE 和调节计划

### 输出格式

完整的输出模板（含 4天/周、3天/周、5天/周三种模板）见 `references/output/output-templates.md`，生成计划前**必须先读取**该文件。

默认输出格式为 Markdown。如需 Word、PDF 等格式，用户可自行通过 Pandoc、Typora 等工具转换。

## 计划修订记录规范

> 💡 **修改现有计划**：若用户提出修改需求（如调整容量、替换动作、重新安排训练日），请参考 `references/planning/plan-modification.md` 的完整修改工作流。

每次修订需在计划开头添加修订说明：

```markdown
---
title: 8周力量训练计划
---

<BlockQuote>
  **修订说明**：本版本在[原先版本]基础上，依据 JTS / ACSM / Westside 文献的 MRV 原则进行审计。
  详细审计结论见文末「MRV 审计与文献参考」章节。
</BlockQuote>
```

并在「修订核心变化」章节记录：

```markdown
## 修订核心变化

- 目标 PR 下调：XXX
- 重量跳跃平滑化：XXX
- 容量期取消 Topset，力量/冲刺期 Topset 仅 1 组
- （逐条列出）
```

## 参考文献

本 skill 整合以下文献与方法论（具体版本和细节请参考官方最新资料）：

1. **JTS (Juggernaut Training Systems)** - 周期化原则、TS/BO 结构、RPE 调节
2. **Westside Barbell** - 共轭法、高容量与高强度永不配对原则
3. **ACSM 近年指南** - RIR/RPE 作为强度衡量标准
4. **Volume Landmarks (Dr. Mike Israetel)** - MEV/MRV/MAV 框架
5. **Barbell Medicine** - 实务训练建议、 injury prevention

详细内容见 `references/` 目录下的各参考文件。

> 💡 **AI 使用兜底条款**：
> 
> 当本 Skill 文档中的信息**不足以支撑用户的特定需求**时（如：特殊伤病情况、小众动作变式、最新研究进展），AI **不应拘泥于已有信息**，而应：
> 1. 在自己的知识库中寻找相关答案（基于训练学、解剖学、生理学常识）
> 2. 从外部权威信息中提取（如 PubMed、ACSM、NSCA、JTS 等官方资料）
> 3. 明确告知用户：此信息来自文档外，仅供参考
> 
> **原则**：Skill 文档是"核心知识库"，但不是"全部知识库"。
