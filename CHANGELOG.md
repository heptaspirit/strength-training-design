# Changelog

本文档记录 `strength-training-design` skill 的版本变更。

## [0.9.10] - 2026-08-26

### refactor: 三层分离架构 + 知识库扩展 + 工具修复

- **架构重构（三层分离）**：SKILL.md 从 236 行瘦身至 ~83 行纯路由层；新建 `workflows/`（4 功能详细工作流）+ `guardrails.md`（单一约束入口）；references/ 知识层内容不动，仅删重复索引（ponytail「单一规则源」精神）
- **知识库扩展（中高优先级融合）**：新增 7 个参考文件（A/B/C 三块缺口 + clinical/population、concurrent training、tapering、periodization taxonomy），并 augment 奥举辅助（增强式）+ PR 估算（1RM 测试协议 + Brzycki）；主 SKILL.md 索引更新
- **README 简化**：306 → ~97 行，去重、补三层架构说明
- **dev/check_links.py 修复**：扫描范围扩展至含 guardrails.md + workflows/*.md，消除重构后链接最密文件的假安全感盲区

## [0.9.9] - 2026-08-26

### feat: 知识库缺口 A/B/C 文献支撑

- 新增 `references/health/autonomic-cardiovascular-response-heavy-lifting.md`（大重量 Valsalva/黑视/呼吸处方）
- 新增 `references/consultation/intensity-volume-sensitivity-axis.md`（强度-容量敏感轴）
- 新增 `references/consultation/coach-athlete-perception-gap.md`（教练-学员感知错位）
- 来源：ACSM 12th / NSCA 5th / Enoka 2016 / Narloch 1995 等

## [0.9.8] - 2026-08-22

### build+test: 工程 hygiene 自动化 + P1 测试固件 + dev/ 维护者专用区隔离

> 普通 skill 使用者无需接触本版本的任何内容；以下均位于 `dev/`（与消费者脚本 `scripts/` 物理隔离），仅 skill 维护者运行。

**一、工程维护脚本（P0 自动化，迁入 dev/）**
- `dev/check_links.py`：扫描 SKILL.md/README.md 当前反引号引用，校验目标文件存在，排除 CHANGELOG 历史段落与 README 文件树 ASCII 图；退出码非 0 可 gate CI
- `dev/check_version.py`：校验 SKILL.md `version:` ↔ CHANGELOG.md 顶部版本条目 ↔ 本地 git tag 三者一致（`--check-tag`）；防"提交忘打 tag"类错误
- `dev/run_all_checks.py`：统一入口，串联 P0（check_links / check_version）+ P1（pytest），退出码可 gate CI / pre-commit

**二、P1 自动化测试固件（pytest，迁入 dev/tests/）**
- `dev/tests/`（conftest + 5 个测试文件，18 个用例），覆盖设计器确定性逻辑：
  - 重量换算（pct 优先 / 向下取整到 plate_step / RPE 路径 / 缺 pct 报错）
  - MRV 审计（边界 100%=超过 MRV 契约 / >MRV 红 / 自重动作仅审计组数）
  - 合规红绿灯（硬拉容量上限 / 48h 间隔 / gap_rules 顺向间隔放行与违规）
  - 减载系数（默认 ×0.6 / 自定义 / volume 周 ×1.0）
  - 端到端：跑 c2_w3_sample.yaml 断言关键重量 + 合规全绿
- 锁定的真实行为契约：`round_weight` 向下取整（非四舍五入）；`calculate_mrv_status` 100% 恰好临界返回「超过 MRV」
- pytest 已装于系统 Python（9.1.1）

**三、dev/ 维护者专用区隔离 + 测试提示词迁移**
- 将 check_links/check_version/run_all_checks/tests 从 scripts/ 根与仓库根迁移至 `dev/`，与消费者脚本物理隔离
- `test-prompts.json` 从仓库根迁移至 `dev/test-prompts.json`（维护者测试提示词）
- SKILL.md 功能三补"工程维护脚本（仅维护者）"段并改指 dev/ 路径；README 文件树补 dev/ 段
- `.gitignore` 补 `**/.pytest_cache/`

**四、GitHub Actions CI（维护者专用，新增 `.github/workflows/checks.yml`）**
- **位置在仓库根目录**：GitHub Actions 仅扫描根 `.github/workflows/`，子目录（如 `dev/.github`）不会被触发，故 workflow 必须置于根；这也是本轮从 `dev/.github` 迁出的原因。
- 触发：push（含 tag）/ pull_request
- 普通 push / PR：`cd dev && python run_all_checks.py --skip-p0`（仅跑引用检查 + pytest，不依赖 tag）
- tag 推送：完整 `python run_all_checks.py`（额外校验 SKILL.md version ↔ CHANGELOG ↔ git tag 一致性）
- CI 自带环境：`setup-python` 固定 3.13 + `pip install pytest`，与本地双 Python 环境错乱无关，云端每次都是干净容器。
- 消费者完全无感：CI 文件不进入 `scripts/` 路径；普通使用者无需配置任何 CI
- 注意：本地 `dev/run_all_checks.py` 逻辑与 CI 一致，推送前本地跑一遍即可预知云端结果

## [0.9.7] - 2026-08-22

### feat+refactor: 计划聚合器 design_program.py（架构 B）+ 边界重画为通用重复运算器

> 用户红线（原话）：**脚本充其量做的是重复性运算的工作**。本版本把"聚合器设计"与"边界重画"合并收口——设计器从"三大项专用"改造为"对任何动作通用的重复运算器"，并明确划分脚本 vs AI 的职责红线。

**一、新增计划聚合器 `scripts/design_program.py`（架构 B）**
- 训练计划聚合器 + 合规检查器（非编排器），复用现有 4 脚本函数层（rpe_to_percentage / round_weight / calculate_mrv / calculate_fatigue），不重写表逻辑
- 输入：AI 在功能三 step1 生成的 YAML 草稿（one_rm + week_structure + intent.phase + enabled_modules）
- 输出：每动作计算重量+RIR目标+MRV状态 JSON + 红绿灯合规报告（频率/48h/硬拉容量）+ Markdown 周报骨架
- 减载 `deload_factor` 默认 ×0.6（phase=deload），可覆盖 0.5–0.7
- v1 模板：full_body(3) / upper_lower(4) / ppl(5)；**6/7 天不做自动生成**（有氧日不进设计器）
- `enabled_modules` 白名单（用户红线：新机制按需引入，不强制塞计划）：默认仅 `base_rpe_pct`；可选 `tm_autoregulation`(amrap_reestimate 默认/weekly_rir 可选) / `single_at_8` / `rir_target_table` / `long_cycle_blocking`(YSY) / `deadlift_single_mode`(SSPT·Ort) / `tempo_rps`

**二、边界重画（通用重复运算器，非三大项专用）**
- 重量换算 / MRV 审计 / 48h 合规 / 减载倍数 / AMRAP→1RM / TS 跳跃校验 对**任何动作**通用（不绑死三大项）
- `MRV_DEFAULTS` 可配置表预置常用动作（squat/bench/deadlift/ohp/高翻/高拉/暂停深蹲/前蹲/暂停硬拉/RDL/早安式/引体），AI 可在 `mrv_overrides` 覆盖
- 新增 `gap_rules`：可配置「后侧链动作 A 距硬拉 B 最小间隔 N 天」（C2 真实用法：RDL 周一距周五硬拉 96h=3 天）
- 支持 `pct` 直接 %1RM（高次/奥举/辅助，RPE 表只到 5 次）、`no_weight`（引体等自重/次数导向动作仅审计组数不换算重量）
- `week_structure` 改为 list of `{day, lifts:[{exercise, sets, reps, rpe?, pct?, category, no_weight?}]}`，每个 lift 都进运算
- **明确红线（契约 §5）**：脚本做确定性算术（重量/MRV/合规/减载/AMRAP/TS 校验）；AI 做动作选择（含 OHP/奥举/拉伸/有氧/核心排不排排哪天）、排布、弱点变式、退阶、双进阶、RPE 记录

**三、契约与样例**
- 设计契约 `docs/design_program_contract.md` 升 v3（§2/§3/§5 重写）
- 样例 `scripts/examples/c2_w3_sample.yaml`（基于真实 C2 文档 W3 抽取，含 OHP 类主项/高翻奥举/引体自重/RDL 后侧链间隔），验证通用边界
- 验证：C2 第5周 4天 upper_lower 实例 + C2 W3 样例均跑通

## [0.9.6] - 2026-08-22

### Added（新增）

**1. TM 自动调节机制（SBS RIR 版）**

- `references/methodology/autoregulation.md` 新增「TM 自动调节」章节：7 档 TM 增减表（-5% / -2% / 0 / +0.5%~+3%）、Single@8 当日调节锚（≈90% 1RM，可调 87-93%）、减载周规则（无 RIR 目标、TM 不动、固定 4-6 组）
- 来源：SBS Strength Program Last Set RIR（Greg Nuckols / Stronger By Science）

**2. RIR 目标表 + Rep Target 表（SBS 机制）**

- `references/intensity/rpe-reference-and-progressive-overload.md` 新增「二·补」章节：Last Set RIR 目标表（50-72.5%→3 RIR / 75-82.5%→2 / 85-95%→1 / 97.5-100%→0）+ Rep Target 表（50-57.5%→8 次…90-100%→1 次）
- 与 Nuzzo 表互补：「能做几次」vs「该留几 RIR」

**3. 模块化个体化 + 2×3 周波模式（SBS/YSY）**

- `references/methodology/jts-periodization.md` 新增「模块化个体化」章节（Quick Setup 式可配置清单：主项/辅助/组数/TM 幅度/Single@8/强度矩阵/减载/频率）+「2×3 周波 + 减载模式」章节（21 周强度矩阵，每波起点 +2.5%，减载 60%，辅助低 10%）

**4. 硬拉单次高质量模式（SSPT + Mag/Ort）**

- `references/volume-recovery/deadlift-volume-management.md` 新增「九、硬拉单次高质量模式」：模式 A 单次波浪（SSPT：15×1@65%→4×1@92.5%，组数降×强度升，1x/2x/3x 频率变体）+ 模式 B 后撤组模型（Mag/Ort：4×4+双次+8+ 后撤组，每周 1 天）
- 含 SBS Hypertrophy Template 用 Block Pull 半程硬拉做主的佐证

**5. 超长周期分块（YSY）**

- `references/volume-recovery/recovery-and-frequency.md` 新增「九、超长周期分块」：9×4 周块结构（容量→波动→强度→容量→积累→实现→GPP 主动恢复→力量×2）、块间主动恢复、%→RPE 平滑过渡、Total Lifts 自动量化

### Changed（修改）

- **SKILL.md**：
  - 版本 0.9.5 → 0.9.6
  - 核心方法论参考表更新（autoregulation 条目注明含 TM 自动调节）
  - 参考文献 +1（SBS / Stronger By Science）
- **README.md** — 无需改动（文件树不变，内容均为现有文件增补）

## [0.9.5] - 2026-08-22

### Added（新增）

**1. 节奏与休息参数体系（TUT 节奏码 + RPS 组间休息）**

- `references/exercises/tempo-and-rest.md` — 新增：TUT 4 位节奏码定义与常用码表（4111/4101/3111/3101 等）、RPS 组间休息与训练目标对应表、与 RPE/双进阶/MRV 审计的叠加用法、周期内节奏推进策略（4s→3s 离心、75s→60s 休息）
- 来源：PHUL Advanced 6 天版（J. Bui 改编，LiftVault 发布）增肌日参数体系 + 通用肌肥大训练学常识；PHUL 原版为 Brandon Campbell（Muscle & Strength）
- **只吸收其节奏/休息参数，不吸收其 6 天×三大项 3 次/周的高频结构**（违反 48h 间隔约束，见 Changed）

**2. 合规 6 天/周模板（模板四）**

- `output-templates.md` 新增「模板四：6 天/周」——5 天大肌群 + 1 天功能/小肌群结构，强制标注硬约束：每肌群 ≤2-3 次/周、重训间隔 ≥48h、三大项不做 3 次/周、第 6 天不做大肌群重训
- 模板四辅助动作示范带 TUT/RPS 参数（呼应新增的 tempo-and-rest.md）
- 使用说明新增第 9 条（节奏/休息参数可选标注）与第 1 条 6 天模板选择项

### Changed（修改）

- **SKILL.md**：
  - 版本 0.9.4 → 0.9.5
  - 核心方法论参考表 +1（tempo-and-rest.md）
  - 功能三步骤 3 增加 TUT/RPS 可选标注提示；强制规则四条 → 五条（新增「频率与 6 天约束」：每肌群 ≤2-3 次/周、间隔 ≥48h）
  - 操作反例 +2（大肌群 >3 次/周、6 天第 6 天仍做大肌群重训）
  - 参考文献 +1（PHUL，明确注明仅吸收节奏/休息参数）
- **输出模板 (`output-templates.md`)**：模板四 + 使用说明第 9 条
- **README.md** — 文件树补充 tempo-and-rest.md；移除 agent 软件兼容性章节（默认兼容所有 AI Agent）；版本号由 GitHub tag badge 自动获取

## [0.9.4] - 2026-08-11

### Added（新增）

**1. 拉伸 Delphi 共识整合（Warneke et al. 2025, *J Sport Health Sci*）**

- 从共识 EPUB 提取 Fig.3（8 大主题效应总览）与 Graphical abstract（推荐/不推荐信息图），信息**全部重绘为 AI 可读 Markdown 表格**（见下文速查图小节）；原始 JPG 不保留
- `references/health/warmup-flexibility.md` 新增「拉伸共识速查图」小节，将两张图重写为 **AI 可读 Markdown 表格**（↑↓=/? 矩阵 + 推荐/不推荐 + 剂量/一致度）；不内嵌图片（skill 参考被当纯文本上下文加载，内嵌图对 AI 无效）
- 共识核心结论落地：练前 >60s 静态拉伸禁忌（急性力量/爆发力下降）、慢性 ROM 有效剂量（静态/PNF，2–3 组 × 30–120s/肌）、弹簧(SSC 反弹) caveat、拉伸不促恢复/DOMS/体态/防伤

### Changed（修改）

- **灵活度锚定原则**：`warmup-flexibility.md` 练前动态 / 练后静态 / 日常灵活度三处统一改为按「训练日类型（部位/动作日）」锚定，**不绑周几**，便于周表重排时整块移动
- **Westside 方法论修正**（基于原书交叉校对）：
  - `westside-jts-integration.md`：Dynamic Method 百分比从 60-80% 修正为 50-60%（+弹力带/铁链），加注 JTS/RTS 演化为 70-80%
  - `westside-jts-integration.md`：3-5-1 波浪格式修正为正确的「三周钟摆波」（50%→55%→60%），注明 Wendler 5/3/1 为同源独立发展
  - `westside-jts-integration.md`：训练频率从"14次/周"修正为"4次/周（核心）+ GPP"
- **MEV/MRV 来源标注**：`mrv-audit.md` 各肌群 MRV 表增加来源说明（数值来自 Dr. Mike Israetel RP Volume Landmarks，非 JTS 书原文）

## [0.9.3] - 2026-07-30

### Added（新增）

**1. 硬拉容量管理原则**

- `references/volume-recovery/deadlift-volume-management.md` — 全程硬拉为何不适合堆容量、容量上限参考表、后侧链分拆四模块策略、周疲劳曲线与恢复窗口验证规则
- 所有硬拉变式全量标记：8 种全程硬拉 / 3 种半程可控 / 7 种非硬拉后侧链，统一标记 🔴/🟡/🟢
- 补全三种缺失变式：触底硬拉 (Touch-and-Go)、直腿硬拉 (SLDL)、宽握硬拉 (Snatch-grip)

**2. Nuzzo 2023 元分析引用**

- `references/intensity/rpe-reference-and-progressive-overload.md` 末节新增 Nuzzo et al. 2023 研究参考章节
- 含更新 REPS~%1RM 对照表、sex/age/status 无调节效应确认、上下肢差异参考值、个体间变异 SD

### Changed（修改）

- **SKILL.md**：
  - 强制规则从三条扩为四条（新增硬拉容量上限）
  - 异常处理新增硬拉容量超限分支
  - 功能四知识匹配表新增 RPE/次数查询 + 硬拉容量后侧链条目
  - 参考文献 +1（Nuzzo 2023）
  - 操作反例新增 3 条（硬拉堆容量、后侧链不够加硬拉组、分拆后每天后侧链训练）
- **MRV 审计 (`mrv-audit.md`)**：
  - 后链 MRV 新增"仅硬拉"��限行（6 组/周）
  - 等效疲劳系数表从 7 行扩至 13 行
  - CNS 疲劳阈值增加 >5.0 危险级别 + 硬拉日 CNS 预算
- **输出模板 (`output-templates.md`)**：
  - 硬拉日减容量：容量期 3-4×6，BO 2 组
  - RDL 移出硬��日，移至辅助日（距硬拉 ≥72h）
  - 使用说明第 8 条新增周疲劳曲线验证
- **辅助动作数据库 (`assistance-exercise-database.md`)**：
  - 每个硬拉变式新增分类标签（🔴🟡🟢）
  - 新增第十节"后侧链分拆策略"
  - 决策树所有变式标注容量分类
- **README.md** — 版本号 0.9.2 → 0.9.3
- **rpe_to_percentage.py** — 不变（现有值与 Nuzzo 2023 主模型一致）

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
