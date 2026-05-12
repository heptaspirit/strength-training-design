# Changelog

本文档记录 `strength-training-design` skill 的版本变更。

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
