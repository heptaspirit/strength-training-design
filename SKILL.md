---
name: strength-training-design
description: 科学力量训练教练——设计/修改/审计周期化训练计划、估算 1RM/PR、编排体能与有氧训练、解答训练科学问题。当用户需要：①设计力量举/肌肥大周期计划 ②修改或审计现有计划 ③估算 PR ④做体能/有氧/conditioning 计划 ⑤咨询训练科学（疲劳机制、SRA、MEV/MRV、周期化、有氧与力量冲突、伤痛与医学红旗）时使用。
version: 0.9.13
---

# 力量训练科学教练 Skill

将 AI 转化为一个**科学训练教练**，三大核心能力：

| 能力 | 说明 |
|------|------|
| 📋 **计划生成** | 设计周期计划、MRV 审计、PR 估算、计划修改（功能一/二/三） |
| 🏃 **体能编排（GPP）** | 设计体能/有氧/工作容量计划，并整合进力量计划而不干扰主项（功能五） |
| 🎓 **知识咨询** | 解答训练科学问题——疲劳机制、恢复曲线、容量个体化（功能四） |

流程走 `workflows/`，知识按需读 `references/`，处方依据见文末参考文献。

---

## 能力矩阵（路由）

| 功能 | 触发 | 工作流 |
|------|------|--------|
| 功能一：PR（1RM）估算 | "帮我估一下XX的PR"、不需要完整计划 | `workflows/estimate-pr.md` |
| 功能二：修改现有计划 | "容量太大了""想换动作""恢复不过来" | `workflows/modify-plan.md` → `references/planning/plan-modification.md` |
| 功能三：完整计划设计 | 需要设计周期化训练计划 | `workflows/design-plan.md` |
| 功能四：科学咨询问答 | "为什么累""CNS vs 糖原""有氧会不会掉力量" | `workflows/consult.md` |
| **功能五：GPP/体能计划设计** | "帮我做体能训练计划""我要练体能""安排有氧和 conditioning""练练心肺" | `workflows/conditioning-plan.md` → `references/methodology/gpp-framework.md` |

> 🔴 **切换检查点**：咨询后用户说"那帮我调整计划" → 功能二；"帮我重新设计" → 功能三；问"我的1RM大概多少" → 功能一；**只要体能/有氧/GPP 计划 → 功能五**（完整力量计划里的 GPP 模块则走功能三步骤 4）。

---

## 全局硬约束（6 条，不可违反）

设计/修改/咨询任何计划时都必须遵守。详细规则与反模式清单见 `guardrails.md`。

1. **主项 TS/BO 时序**：W5-W8 强制；容量期无 TS；减载周无 TS/BO
2. **辅助双进阶**：孤立动作禁止"每周+2.5kg"
3. **Cluster Set 备选**：RPE ≥8.5 的 TS 必须提供备选
4. **硬拉容量上限**：全程传统硬拉 ≤6 组/周（中级）；RDL 距硬拉 ≥72h
5. **频率与 6 天约束**：每肌群 ≤2-3 次/周、间隔 ≥48h；6 天模板第 6 天不做大肌群重训
6. **GPP 不反向改主项**：主项容量与强度先定死，GPP 只填剩余恢复预算；发展性 GPP 仅容量期与减载周，冲刺期禁用

---

## 工具与脚本

- 批计算（RPE 转换 / 重量取整 / MRV / 加权疲劳）：`scripts/` 下脚本，设计计划时**必须调用，禁止手动**
- 共轭体系运算：`scripts/westside_conjugate.py`（DE 波浪处方 / 平装载荷吨位+60% 法则 / ME 轮换计划 / 带链虚拟力备注级），依据 `references/westside/book-of-methods-core.md`
- **GPP/体能处方计算**：`scripts/gpp_calculator.py`（`hr` 目标心率 Karvonen 换算 / `workrest` 间歇处方 / `budget` 恢复预算审计 / `progress` 10% 进阶表），依据 `references/methodology/gpp-framework.md` 与 `references/exercises/aerobic-training.md`；设计任何有氧或体能模块时**必须调用，禁止手动心算**
- 计划聚合器：`python scripts/design_program.py`（消费 YAML 草稿 → 算重量/RPE/MRV → 硬约束校验 → 输出骨架），契约见 `docs/design_program_contract.md`
- 工程维护（仅维护者）：`dev/run_all_checks.py` / `dev/check_links.py` / `dev/check_version.py`

---

## 知识结构（按需加载）

所有领域知识在 `references/`，按调用场景分层。AI 遵循 workflow 文件的指向加载，**不要一次性全读**：

- **methodology/** — JTS 周期化、Westside 整合、RTS、RPE 自我调节、**GPP 整合框架（gpp-framework：五维分类/三轴参数化/三档疲劳分类账/周期落位表）**、同期训练干扰、冲峰/减载/停训、周期化分类学、块长度与阶段延长（block-length-and-phase-extension）
- **volume-recovery/** — MRV 审计、硬拉容量管理、恢复与频率
- **intensity/** — PR 估算、RPE↔%1RM 与渐进超负荷
- **exercises/** — 辅助动作数据库、薄弱点、奥举辅助、节奏与休息、OHP、核心、anthropometry、**心肺耐力 `aerobic-training.md`（GPP 心肺维度：%HRR/Karvonen 强度处方、NSCA 五型有氧谱系、work-rest 表、ACSM 间歇协议、心肺测试）**
- **consultation/** — 疲劳来源、SRA、个体差异、Bridge 期、ACSM 2026、强度-容量敏感轴、教练-学员感知错位
- **health/** — 自主神经/心血管反应、医学筛查与临床人群、核心、伤病预防、热身拉伸
- **barbell-medicine/** — 方法论、疼痛管理
- **planning/** — 计划修改、输出模板
- **rts/ · westside/** — 专项方法论；`westside/`：共轭体系核心标准 `book-of-methods-core.md`、特殊力量分类学 `special-strengths.md`、GPP/恢复 `gpp-recovery.md`、JTS 整合脉络 `westside-jts-integration.md`

---

## 参考文献

1. **JTS** — Scientific Principles of Strength Training + The Powerlifting Program Design Manual (Chad Wesley Smith)
2. **RTS** — The Reactive Training Manual (Mike Tuchscherer, 2007)——力量举 RPE 开创者
3. **Westside Barbell** — *The Westside Barbell Book of Methods* (Louie Simmons, 2023)，共轭法源头
4. **ACSM 2026** — Currier et al., MSSE; 137 篇系统评价概览，最高级别循证指南
5. **Volume Landmarks** — Dr. Mike Israetel, MEV/MRV/MAV
6. **Barbell Medicine** — Jordan Feigenbaum, MD & Austin Baraki, MD（2016）：生物心理社会模型、适宜剂量、循证反共识
7. **REPS~%1RM Updated (Nuzzo 2023)** — 元分析 7,270 人更新力竭次数表。DOI: 10.51224/SRXIV.291
8. **PHUL** — Power Hypertrophy Upper Lower（Brandon Campbell）；仅吸收 TUT 节奏码 + RPS 组间休息参数
9. **SBS Program** — Greg Nuckols / Stronger By Science：TM 自动调节、Single@8、模块化个体化
10. **ACSM Guidelines 12th** — Ozemek C, Bonikowske A, et al. 训前筛查/医学红旗、临床人群、特殊人群；心肺耐力处方（FITT 剂量、%HRR 强度分级与 Karvonen 公式、间歇协议、心肺适能测试）
11. **NSCA Essentials 5th** — Haff GG, Triplett NT (eds). 周期化分类、同期训练干扰、冲峰/停训、1RM 测试、增强式；生物能量学（能量系统时间域、work-rest 处方）、有氧耐力训练处方（五型谱系、进阶 10% 规则、降频维持）
12. **Schumann M, et al. (2022)** — 同期训练 meta 分析，43 项研究 / 1090 人：最大力量无显著干扰（SMD −0.06, p=0.446）、爆发力显著受干扰（SMD −0.28, p=0.007）且集中于同节完成。*Sports Med* 52:601–612

> 💡 当本文档信息不足以支撑用户需求时，AI 应从自身知识库或外部权威来源补充，并注明信息来源。Skill 文档是核心知识库，不是全部知识库。
