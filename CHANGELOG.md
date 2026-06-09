# Changelog

本文档记录 `strength-training-design` skill 的版本变更。

## [0.9.2] - 2026-06-09

### Added（新增）

**1. Barbell Medicine（BBM）循证医学框架整合**

由 Jordan Feigenbaum, MD 和 Austin Baraki, MD 创立（2016年），是将循证医学系统引入力量训练的权威机构。新增两个参考文件：

- `references/barbell-medicine/barbell-medicine-methodology.md` — BBM 核心方法论，包含：
  - 创始人背景（均为 MD，曾任 Starting Strength 教练，后因理念分歧独立）
  - 三大核心方法论：生物心理社会模型 / 压力-适应-恢复（适宜剂量）/ 基于证据的决策
  - BBM 的 RPE 实操框架（内部负荷 vs 外部负荷、热身流程、状态波动应对）
  - The Bridge 计划详解（8周，3天/周，新手→中级过渡）
  - BBM 与 SS / JTS / RTS / Westside 的关系定位
  - 对 skill 的集成价值（5个维度）

- `references/barbell-medicine/pain-management.md` — BBM 疼痛管理框架，包含：
  - 核心原则：疼痛 ≠ 结构性损伤
  - 生物心理社会模型三维度详解（生物/心理/社会）
  - 训练中出现疼痛的应对框架（排除红旗症状 → 修改训练计划 → 逐步回归）
  - 各部位疼痛的具体建议（腰痛/肩痛/膝痛）
  - 心理因素的管理（灾难化思维/恐惧回避/过度关注/身份危机）
  - 红旗症状清单（需立即就医的情况）

**2. 新增能力维度**

BBM 的整合填补了 skill 中以下空白：
- **疼痛/伤病管理**：现有 skill 几乎没有涉及"训练中出现疼痛怎么办"，BBM 的生物心理社会模型是最科学的框架
- **循证决策风格**：BBM 的"敢怼共识"风格（如"跑步伤膝盖"是错误观念）可以作为 skill 回答争议性问题的参考立场
- **适宜剂量量化**：BBM 的"10-20 组肌肥大容量"是比 MEV/MRV 更直观的快速参考
- **新手过渡方案**：The Bridge 是 SS 线性进步后最经典的过渡方案

### Changed（修改）

- **SKILL.md**：
  - 描述加入 BBM 作为第四大方法论文献来源
  - 方法论文献来源加入 BBM
  - 参考表新增 2 个 BBM 文件
  - 功能四知识匹配表新增 3 个 BBM 相关条目（疼痛管理 / BBM 循证理念 / RTS 条目已存在）
  - 版本号 → 0.9.2
- **README.md**：
  - 描述加入 BBM
  - 版本号 → 0.9.2
  - 功能特性新增 BBM 循证医学框架条目
  - 知识表新增 3 个 BBM 条目
  - 目录结构新增 `barbell-medicine/` 目录

### Rationale

**为什么整合 BBM**：
- BBM 是美国科学健身领域的权威机构，与 JTS/RTS/Westside 并列
- 现有 skill 缺少疼痛管理维度，BBM 的生物心理社会模型是最科学的框架
- BBM 的循证决策风格（敢怼共识）可以作为 skill 回答争议性问题的参考立场
- BBM 的"适宜剂量"理念与 JTS 的 MEV/MRV 互补，提供更直观的容量参考

**BBM 与其他体系的关系**：
- 与 Starting Strength：曾是 SS 教练，后分道扬镳（SS 教条化，BBM 循证灵活）
- 与 JTS：互补（JTS 偏编程框架，BBM 偏医学/疼痛管理）
- 与 RTS：互补（RTS 的 RPE 工具被 BBM 吸收，BBM 加入医学维度）

---

## [0.9.1] - 2026-06-08

### Added（新增）

**1. Westside 共轭法知识整合**
从 *The Westside Barbell Book of Methods* (Louie Simmons, 2007, 237页) 提取核心原理，内容已内化到现有文件中：
- `references/westside/westside-jts-integration.md` — Westside → JTS 方法论传承脉络（保留独立参考）
- 三层动作分类系统 → 内化至 `references/exercises/assistance-exercise-database.md`
- 四种特殊力量素质 → 内化至 `references/exercises/weak-points.md`
- 所有三大项薄弱点表已加入"力量素质类型"列

**2. RTS（Reactive Training Systems）方法论整合**
从 *The Reactive Training Manual* (Mike Tuchscherer, 2007, 43页) 通过 PDFKit OCR 提取全部内容（111,764 字符），新增精选参考文件：
- `references/rts/reactive-training-system.md` — RTS 核心方法论完整概述，包含：
  - RTS 创始人 Mike Tuchscherer 与 JTS 创始人 Chad Wesley Smith 的关系说明（两个独立体系）
  - RPE 的历史脉络：Borg (1960s) → Tuchscherer/RTS (2004-2007, 首次引入力量举) → JTS (后期吸收与普及)
  - RPE 系统原始定义和百分比对应表
  - 疲劳停止点（Fatigue Stop）
  - 单向加载（Unidirectional Loading）
  - 疲劳百分比（Fatigue Percents）——精确容量控制工具
  - 额外训练结构（Extra Workouts）——五部分系统
  - 6 个推荐使用场景

### Technical Note
- Westside PDF: 直接文本提取（pdfplumber）
- RTS PDF: 扫描版，首次使用 PDFKit（pdfkit-py）的 `extract_text --ocr_fallback` 功能
- OCR 需要 Tesseract 5.4.0 OCR 引擎 + 配置 PATH
- OCR 准确率约 85-90%

### Changed（修改）
- **`assistance-exercise-database.md`**：新增"动作分类原则"章节（Main/Supplemental/Accessory 三层框架 + Westside vs JTS 改良对比）
- **`weak-points.md`**：新增"四种特殊力量素质"诊断框架；三大项薄弱点表加入"力量素质类型"列
- **SKILL.md**：参考表更新（Westside 独立文件从 3 个减至 1 个）；功能四知识匹配表更新
- **README.md**：知识表 + 目录结构更新（删除已内化文件引用）
- **CHANGELOG.md**：本条目（合并 Westside + RTS 两次变更）
- **删除**：`exercise-classification.md`、`special-strengths.md`（内容已内化）、`references/methodology/westside-acsm.md`

### Rationale

**Westside → JTS 传承**：JTS 方法论大量吸收自 Westside（并发周期化、动作分类、波浪形加载），但 Westside 原版针对用药精英运动员，JTS 加入了 RPE 自我调节和个体差异系统使之为自然训练者可用。

**RTS 的独立地位（重要修正）**：
- **Mike Tuchscherer (RTS)** ≠ **Chad Wesley Smith (JTS)**——两人是不同个体，各自创立了独立体系
- **RTS 是 RPE 的开创者**：Mike Tuchscherer 首次将 Borg 的 RPE 量表从有氧运动改编引入抗阻训练
- **JTS 是 RPE 的普及与优化者**：Chad Wesley Smith 在 JTS 后期教材中大量吸收了 RTS 的 RPE 方法论
- 关系是 **"开创-吸收-普及"**，而非"前身-后代"

### 方法论传承链（修正后）

```
Borg RPE 量表 (1960s) —— 有氧运动用
    ↓
Westside 共轭法 (Louie Simmons, 1990s-2007)
    ↓
RTS (Mike Tuchscherer, 2004-2007) —— RPE 首次引入力量举
    ↓  "开创-吸收-普及" 的关系
JTS (Chad Wesley Smith, 2009-now) —— 吸收 RPE + 体系化周期化
    + MEV/MRV 量化 + 9因素个体差异 + Bridge Phase
```

---

## [0.9.0] - 2026-06-06

### 重大变化
- **Skill 重新定位**：从"力量训练计划设计"升级为"力量训练科学教练"，具备两大并列能力
- **版本跃升至 0.9.0**：反映 skill 能力范围的重大扩展

### Added（新增）
- **功能四：科学训练咨询问答**（5 个独立咨询文件）：references/consultation/
  - fatigue-sources.md — 疲劳四来源 + mTOR/AMPk + 症状判断
  - sra-curves.md — SRA 四曲线 + 三大项排序 + SSR 范式
  - mev-mrv-individual-differences.md — 9 因素详细机制 + 调整示例
  - bridge-phase.md — Bridge vs 减载 + 设计原则 + 场景 + 误区
  - acsm-2026-position-stand.md — 137 篇系统评价 + Table 4 + 7 误区 + ACSM vs JTS
- **JTS 官方手册知识整合**：SPST + PPDM 两本书
- **MRV 增强**：容量 5 区 + MEV/MRV 个体差异（9 因素）
- **恢复增强**：SRA 四曲线 + 三大项 SRA 排序
- **ACSM 2026**：最高级别循证指南
- **Darwin 优化**：反例黑名单（9 条）+ 异常处理（7 if-then）+ 检查点标记
- **全部 26 个文件**：统一添加 YAML frontmatter/docstring

### Changed（修改）
- **SKILL.md**：双核教练、功能四正式化、299→181 行
- **README.md**：教练定位前置、咨询示例优先
- **设计文件精简**：咨询内容移至 references/consultation/ + 交叉引用

### Darwin 评分
- 基线 75.6 → 优化后 83.9（+8.3）

---

## [0.8.2] - 2026-06-04

### Added（新增）
- **脚本 `scripts/calculate_fatigue.py`**：补建加权疲劳 + CNS 疲劳双计算脚本（之前 mrv-audit.md 引用了但文件不存在）
- **SKILL.md 新增强制规则块**（步骤 3）：
  - 主项 TS/BO 结构：W5-W8 必须包含，容量期无 TS，减载周无 TS/BO
  - 辅助动作双进阶（Double Progression）：孤立动作禁止"每周+2.5kg"，强制使用双进阶
  - Cluster Set：RPE ≥ 8.5 的 TS 必须提供 Cluster 备选方案
- **SKILL.md 新增有氧强制要求**（步骤 4）：必须含心率区间（Zone 2）+ 有氧进阶递减表
- **SKILL.md 新增加批计算脚本调用**（步骤 3 + 步骤 5）：rpe_to_percentage.py、round_weight.py、calculate_mrv.py、calculate_fatigue.py 从弱引用提升为强制调用
- **SKILL.md 新增全局重量取整规则**：按实际哑铃片配置取整，禁止硬编码 2.5kg

### Changed（修改）
- **SKILL.md 版本号**：v0.8.0 → v0.8.2
- **步骤 3（动作设计）**：新增脚本调用 + 强制规则两个子块
- **步骤 5（MRV 审计）**：新增加批计算脚本强制调用
- **步骤 8（输出）**：从"可选"升级为"最终输出强制组成"，训练日志模板升为必附
- **output-templates.md**：有氧表新增心率区间、RPE、递减逻辑；使用说明新增双进阶/Cluster Set/重量步进规则

### Fixed（修复）
- 修复 `mrv-audit.md` 引用的 `scripts/calculate_fatigue.py` 不存在的死引用问题
- 修复 SKILL.md 对 `rpe_to_percentage.py` 和 `calculate_mrv.py` 零引用的问题（之前只在参考文件深处弱引用）
- 修复 `round_weight.py` 在 SKILL.md 中仅标注"可使用"（弱语气），改为"必须调用"

## [0.8.1] - 2026-06-04

### Added（新增）
- 无

### Changed（修改）
- **文件结构重组**：将 references/ 从 4 个目录重组为 7 个功能目录
  - 新增 `intensity/`：pr-estimation.md、rpe-reference-and-progressive-overload.md
  - 新增 `volume-recovery/`：mrv-audit.md、recovery-and-frequency.md
  - 新增 `health/`：injury-prevention.md、warmup-flexibility.md、core-training.md
  - 拆解 `accessories/ohp-core-aerobic.md` 为三个独立文件：
    - `exercises/ohp-training.md`
    - `health/core-training.md`
    - `exercises/aerobic-training.md`
- **SKILL.md 版本号**：v0.8.0 → v0.8.1
- **SKILL.md 参考文件引用更新**：所有文件路径更新为新结构

### Fixed（修复）
- 修复 references/ 目录结构混乱、功能边界不清的问题
- 修复 ohp-core-aerobic.md 内容过于臃肿、不利于按需加载的问题

### Removed（删除）
- 移除 `references/accessories/` 目录（内容已迁移到 exercises/ 和 health/）
- 移除 `references/planning/` 目录下的旧路径文件（已迁移到新目录）

## [0.8.0] - 2026-05-30

### Added（新增）
- **疲劳系数加权 MRV 系统**：`references/planning/mrv-audit.md` 新增"加权疲劳审计"章节
  - 动作疲劳系数（FC）：区分主项 TS/BO/复合辅助/孤立动作的真实疲劳负荷
  - RPE 修正系数：高 RPE 组的疲劳权重更大
  - CNS 疲劳独立维度：追踪神经疲劳（硬拉 TS 最高），设定单次训练 CNS 阈值
  - 跨肌群重叠表：复合动作对次要肌群的疲劳叠加计算
  - 加权 MRV 参考阈值（10-14 单位/周，替代简单组数统计）
- **心率区间指引**：`references/accessories/ohp-core-aerobic.md` 新增 Zone 1-5 心率区间表，力量训练者黄金区间 = Zone 2
- **有氧容量进阶递减逻辑**：不同周期阶段的有氧频率/时长/强度递减方案
- **减脂期 vs 增肌期有氧差异**：明确两者在有氧频率、类型、时长上的区别
- **双进阶（Double Progression）方法**：`references/planning/rpe-reference-and-progressive-overload.md` 新增
- **Cluster Set（组簇训练）方法**：同文件新增，5×1 @ 20s 休息替代 1×5，降低 CNS 疲劳
- **训练日志模板**：`references/output/output-templates.md` 新增每日/每周/RPE 追踪模板
- **动作进退阶链**：`references/exercises/assistance-exercise-database.md` 新增第九章，覆盖深蹲/卧推/硬拉/背部/OHP 的进退阶链条

### Changed（修改）
- **SKILL.md 版本号**：v0.7.1 → v0.8.0
- **工作流步骤更新**：步骤 3（动作设计）增加进退阶链引用；步骤 5（MRV 审计）增加加权疲劳审计引用；步骤 8（输出）增加训练日志模板引用
- **MRV 审计方法**：新增"加权疲劳审计（进阶）"作为补充审计手段

## [0.7.1] - 2026-05-16

### Added（新增）
- **膝上高翻/膝上高拉作为硬拉日热身/启动训练**：`references/exercises/weak-points.md` 新增完整章节，包含理论依据、适用/不适用场景、安排建议、注意事项（基于实证反馈与运动科学研究）
- **BO 组逐级减重指引**：`references/output/output-templates.md` 退阶方案新增 BO 组第 3 组起主动减重、训练者按感觉自行调整的指引，避免累积疲劳导致受伤（基于用户实证反馈）

### Changed（修改）
- **SKILL.md 结构优化**：将"功能一"（PR 估算）、"功能二"（修改计划）、"功能三"（完整计划设计）的详细流程迁移到对应参考文件，SKILL.md 仅保留触发条件和参考文件指针，支持 AI 触发时渐进式查询，减少 token 消耗
- **SKILL.md 版本号**：v0.7.0 → v0.7.1

### Fixed（修复）
- 无

---

## [0.7.0] - 2026-05-13

### Added（新增）
- **PR（1RM）估算独立功能**：用户可在没有完整训练计划需求时，单独调用 PR 估算工具
  - 触发条件：用户提问"帮我估算 1RM"、"用 XXkg 做了 YY 次，帮我算算"等
  - 支持三种估算方法：AMRAP 测试、体重倍数法、RPE 反推
  - 输出格式：分肌群给出估算结果、保守建议、校准提醒
- **现有计划修改功能**：用户训练 1-2 周后觉得不妥，可请求修改现有计划
  - 触发条件：用户提问"我练了一周，觉得 XX 不合适"、"容量太大想调整"等
  - 修改流程：获取现有计划 → 询问修改需求 → 执行修改 → 重新 MRV 审计 → 输出修改后计划
  - 输出格式：修订说明 + 修订核心变化 + 修改后的完整计划
- **SKILL.md 功能分区**：将原有"计划设计工作流"改为"功能三"，新增"功能一（PR 估算）"和"功能二（修改现有计划）"

### Changed（修改）
- **SKILL.md description**：新增触发场景 (6) 估算用户 1RM（PR）、(7) 修改训练了一段时间后的现有计划
- **SKILL.md 结构**：重新组织为三个独立功能模块，提升可读性和可维护性

### Fixed（修复）
- 无

---

## [0.6.1] - 2026-05-13

### Added（新增）
- **设计哲学整合到输出模板**：将"训练计划设计哲学"从注释改为实际输出内容，确保生成计划时包含
- **Hermes Agent 兼容性确认**：朋友测试通过，添加至 README 已测试平台列表
- **参考文档添加脚本引用**：`mrv-audit.md` 和 `rpe-reference-and-progressive-overload.md` 添加对应 Python 脚本引用

### Changed（修改）
- **README.md**：添加 Hermes Agent 到已测试平台（v0.6.0 确认可用）
- **README.md**：更新平台兼容性说明，移除冗余的"欢迎提交适配方案"提示
- **output-templates.md**：设计哲学添加到三个模板（4天/周、3天/周、5天/周）

### Fixed（修复）
- 修复设计哲学未出现在生成计划中的问题（之前仅是文档注释，未整合到输出模板）

---

## [0.6.0] - 2026-05-12

### Added（新增）
- **第九步：输出后与在线文档同步（可选）**：输出 Markdown 计划后询问用户是否同步到在线文档
- 支持同步到 5 大主流平台：金山文档、飞书、腾讯文档、Notion、谷歌文档
- 输出后询问话术模板

### Changed（修改）
- **输出格式章节**：明确默认输出为 Markdown，Word/PDF 用 Markdown 转换
- **MDX 格式说明**：明确 MDX 仅适用于腾讯文档，不适用其他平台
- **添加其他平台输出建议表格**：金山文档、飞书、Notion、谷歌文档的推荐格式和操作方式
- **README.md**：模糊化 agent 软件信息（移除具体 agent 名称，改为通用描述）
- **README.md**：修复"ACSM 2026" → "近年 ACSM 指南"（2 处）
- **SKILL.md**：版本号更新为 0.6.0

### Fixed（修复）
- 修复 README.md 中"ACSM 2026"引用错误（共 2 处）
- 修复 README.md 中过时的 agent 兼容性描述

---

## [0.5.0] - 2026-05-11

### Added（新增）
- 添加 `README.md`：完整的项目说明文档
- 添加 `LICENSE`：MIT 许可证
- 添加 `.gitignore`：排除打包文件、备份、临时文件
- 添加 `references/planning/pr-estimation.md`：独立的 PR 估算参考文件

### Changed（修改）
- **版本号**：v0.4.0 → v0.5.0
- **SKILL.md**：更新版本信息和作者
- **SKILL.md**：PR 估算流程改为引用独立文件（减少主文件体积）
- **references/methodology/recovery-and-frequency.md**：Section 5 改为引用 `pr-estimation.md`

### Removed（删除）
- 删除所有临时 Python 脚本（*.py）
- 删除备份文件（*.bak）
- 删除空的 `scripts/` 目录
- 清理冗余内容，优化文件结构

### Fixed（修复）
- 修复 PR 估算流程在多个文件中重复的问题
- 采用分层文档架构：SKILL.md 摘要 + references/ 详细内容

---

## [0.4.0] - 2026-05-11

### Added（新增）
- `references/planning/pr-estimation.md`：独立的 PR 估算方法文件
- PR 估算流程：AMRAP 测试、训练经验估算、RPE 反推

### Changed（修改）
- 从 SKILL.md 和 recovery-and-frequency.md 中提取 PR 估算内容到独立文件
- 使用交叉引用替代内容重复

---

## [0.3.0] - 2026-05-11

### Added（新增）
- `references/planning/plan-modification.md`：计划修改工作流程
- 第八步：输出前确认流程

### Changed（修改）
- 优化计划设计工作流（原七步 → 八步）
- 增强用户确认机制

---

## [0.2.0] - 2026-05-10

### Added（新增）
- `references/methodology/autoregulation.md`：RPE/RIR 自我调节详解
- `references/planning/rpe-reference-and-progressive-overload.md`：RPE 参考表与渐进超负荷
- `references/methodology/recovery-and-frequency.md`：恢复周期与训练频率

### Changed（修改）
- 整合 Westside 共轭法与近年 ACSM 指南研究方法论
- 优化 MRV 审计流程

---

## [0.1.0] - 2026-05-10

### Added（新增）
- 初始版本
- 核心功能：JTS 周期化、MRV 审计、RPE 调节
- 基础参考文件架构
- `references/exercises/`：动作数据库
- `references/accessories/`：辅助训练指南

---

**版本号规则**：语义化版本 `MAJOR.MINOR.PATCH`
- MAJOR：不兼容的架构变更
- MINOR：向后兼容的功能新增
- PATCH：向后兼容的问题修复
