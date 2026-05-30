# Changelog

本文档记录 `strength-training-design` skill 的版本变更。

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
- **膝上高翻/膝上高拉作为硬拉日热身/启动训练**：`references/exercises/weak-points-and-olympic-lifting.md` 新增完整章节，包含理论依据、适用/不适用场景、安排建议、注意事项（基于实证反馈与运动科学研究）
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
