---
name: strength-training-design
description: 力量训练计划设计，支持 JTS 周期化、Westside 共轭、近年 ACSM 指南、MRV 审计等方法论。当用户请求设计/修改/审计力量训练计划、评估训练容量、根据 RPE/RIR 制定周期化计划、**估算 1RM（PR）**、**修改现有训练计划**时触发此 skill。适用场景：(1) 设计 8 周/12 周力量周期计划，(2) 基于 JTS 原则做 TS/BO 结构，(3) 对现有计划做 MRV 审计，(4) 根据 RPE 数据调整训练容量/强度，(5) 生成适合 Obsidian 的 Markdown 训练计划文档，(6) 估算用户 1RM（PR），(7) 修改训练了一段时间后的现有计划。
version: 0.7.0
---

# 力量训练计划设计 Skill

## 概述

本 skill 提供基于多派系整合的力量训练计划设计能力，整合 JTS、Westside Barbell、近年 ACSM 指南 等方法论，支持 MRV（最大可恢复容量）审计和 RPE 自我调节。

## 核心方法论

详细方法论参考以下文件（按需加载）：

- **JTS 周期化原则** → `references/methodology/jts-periodization.md`
- **MRV 审计方法与数据** → `references/planning/mrv-audit.md`
- **Westside 共轭法 & 近年 ACSM 指南** → `references/methodology/westside-acsm.md`
- **RPE/RIR 自我调节** → `references/methodology/autoregulation.md`
- **身高/肢体比例与弱点分析** → `references/methodology/anthropometry-and-weak-points.md`（按需）
- **热身、放松与灵活度** → `references/methodology/warmup-flexibility.md`（按需）
- **实力推 OHP、核心稳定与有氧** → `references/accessories/ohp-core-aerobic.md`（按需）

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

1. **询问用户信息**：训练经验（新手/中级/高级）、性别、体重
2. **选择估算方法**（见 `references/planning/pr-estimation.md`）：
   - **方法一（推荐）**：引导用户做 AMRAP 测试，用 Epley 公式估算
   - **方法二**：根据训练经验 + 体重倍数法估算（保守值）
   - **方法三**：通过"能做 X 次的重量" + RPE 表反推
3. **输出估算结果**：给出保守值、参考范围、以及后续校准建议
4. **提醒用户**：估算结果仅作为计划起点，实际训练中通过 RPE 快速校准（2-3 周内找到真实 PR）

### 输出格式

```
## 您的 1RM 估算结果

### 深蹲（Squat）
- 估算 1RM：XXX kg
- 估算方法：AMRAP 测试 / 体重倍数法 / RPE 反推
- 保守建议：从 XX kg 开始训练（取估算值的 90-95%）

### 卧推（Bench Press）
[同上]

### 硬拉（Deadlift）
[同上]

---
**重要提醒**：
- 以上为估算值，仅作为计划起点
- 实际训练中通过 RPE 调节，2-3 周内就能找到真实 PR
- 建议每 8-12 周重测 AMRAP 或 1RM，更新 PR 数据
```

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

1. **获取现有计划**：请用户提供现有训练计划（文字、图片、或之前生成的 Markdown 文档）
2. **询问修改需求**：明确用户想要修改什么（动作、容量、频率、训练日安排等）
3. **读取修改工作流**：参考 `references/planning/plan-modification.md` 的完整修改流程
4. **执行修改**：
   - 根据用户需求调整计划
   - 重新进行 MRV 审计（确保修改后的计划不超过 MRV）
   - 更新周期结构和训练日安排
5. **输出修改后计划**：
   - 在计划开头添加**修订说明**
   - 记录**修订核心变化**（逐条列出）
   - 输出完整修改后的计划

### 修改原则

- **保守修改**：每次只修改 1-2 个变量，避免一次性大幅调整
- **保持方法论一致性**：修改后仍遵循 JTS 周期化、MRV 审计等核心原则
- **用户确认**：修改后展示修改要点，用户确认后再输出完整计划
- **记录修订**：在计划文档中记录修订说明和核心变化（方便后续追踪）

### 输出格式

```
## 修订说明

本版本在[原版本]基础上，依据用户反馈和 JTS / ACSM / Westside 文献的 MRV 原则进行修订。
详细审计结论见文末「MRV 审计与文献参考」章节。

## 修订核心变化

- [逐条列出修改内容，如：]
- 深蹲容量从 5×8 调整为 4×8（容量期 W1-3）
- 硬拉从主项日移除，改为辅助动作（RDL 2×8）
- 训练日安排从周一/周三/周五/周日 改为周二/周四/周六/周日
- [其他修改...]

---

[修改后的完整训练计划]
```

---

## 功能三：完整训练计划设计（原有功能）

### 计划设计工作流

### 第一步：确定目标与约束

收集以下信息：

1. **基本信息**：身高、体重、年龄（影响杠杆和恢复期）
2. **当前 PR（1RM）**：深蹲 / 卧推 / 硬拉（若未测试过 1RM，参见 `references/planning/pr-estimation.md` 估算方法）
3. **目标 PR**：下一周期目标重量
4. **训练频率**：每周几天（常见 3-4 天）
5. **周期长度**：通常 8 周（含测试周）
6. **时间约束**：每次训练最长时长（建议 ≤ 90 min）
7. **已有伤情/限制**：影响动作选择（损伤预防与自测见 `references/methodology/injury-prevention.md`）
8. **肢体比例备注**：如"腿长躯干短"等（影响动作选择和弱点）

**身高/肢体比例的影响**（简要原则）：

- **高个子**（≥180cm）：动作幅度大，股四头肌和上肢后链需求更高；弱点常出现在动作底部（起跑）和锁定阶段
- **矮个子**（≤170cm）：动作幅度小，相对力量有优势；弱点常出现在动作中途和全身协调性
- **肢体比例特殊者**：如"长腿短躯干"，深蹲需更多踝关节灵活性，硬拉可能更适合相扑式

> 详细身高与弱点分析见 `references/methodology/anthropometry-and-weak-points.md`
>
> 💡 **弱点分析与奥举辅助**：`references/exercises/weak-points-and-olympic-lifting.md` 提供薄弱点识别与辅助动作选择指南。

### 第二步：设计周期结构

> 💡 **恢复周期考虑**：不同肌群恢复时间不同，设计训练频率与次序时请参考 `references/methodology/recovery-and-frequency.md`

标准 JTS 风格周期（8 周）：

```
W1-3: 容量积累期（Volume Accumulation）
  - 目标：堆量，RPE 6-7
  - TS：无（容量期不做 Topset）
  - BO：固定重量，5×8 或 4×8

W4: 减载周（Deload）
  - 降容 40-50%，RPE 6
  - 2-3 组，给身体恢复时间

W5-6: 力量建立期（Strength Building）
  - 引入 TS（Top Set）1 组，RPE 7.5-8.5
  - BO 3 组，重量比 TS 降 8-12%
  
W7-8: 力量冲刺期（Strength Sprint/Peaking）
  - TS 重量继续递增，1 组
  - BO 2 组（容量降低，聚焦恢复）
  - 组次数降至 1-3 次（神经适应）

W9: 测试周
  - 测试新 PR
```

### 第三步：各动作类型设计

#### 主项（深蹲/卧推/硬拉）

| 周期阶段 | TS（Top Set） | BO（Back Off） | RPE 范围 |
|---------|----------------|----------------|----------|
| 容量期 W1-3 | 无 | 4-5 组 × 8 次 | 6-7 |
| 减载周 W4 | 无 | 2-3 组 × 6 8 次 | 6 |
| 力量期 W5-6 | 1 组 × 5 次 | 3 组 × 5 次 | 7.5-8.5 |
| 冲刺期 W7-8 | 1 组 × 1-3 次 | 2 组 × 1-3 次 | 8-9 |

**BO 重量 = TS 重量 × (1 - 8~12%)**

> 💡 **RPE 参考与重量计算**：RPE ↔ %1RM 对照表及渐进超负荷方案见 `references/planning/rpe-reference-and-progressive-overload.md`
> 
> 💡 **减轻 token 消耗**：
> - 若需频繁转换 RPE ↔ %1RM，可调用 `scripts/rpe_to_percentage.py` 脚本
> - 若需根据 1RM 计算训练重量，也可使用该脚本
> - 若需根据杠铃片步进取整重量，可调用 `scripts/round_weight.py`
> ```bash
> python scripts/rpe_to_percentage.py --reps 5 --rpe 8 --one_rm 140
> python scripts/round_weight.py --weight 93.2 --plate_step 2.5
> ```

#### 辅助动作容量设计

> 💡 **辅助动作选择**：从 `references/exercises/assistance-exercise-database.md` 中根据用户的薄弱点、器械条件、训练经验选择合适动作。

参考 `references/planning/mrv-audit.md` 中的 MRV 数据表，确保：
- 各肌群每周组数 ≤ MRV
- 接近 MRV 时（≥80% MRV）需监控疲劳信号
- 容量期可适当超过 MEV（最小有效容量），但不超过 MRV

### 第四步：核心稳定训练设计

> 💡 **核心与 OHP 参考**：动作选择、安排建议与周期整合见 `references/accessories/ohp-core-aerobic.md`

根据用户的训练经验、器械条件和恢复能力，设计核心稳定训练：

1. **实力推 OHP**：作为主项或辅助动作，安排在合适训练日（见 `ohp-core-aerobic.md` 周期安排示例）
2. **核心训练**：平板支撑、鸟狗式、侧平板，每周 2-3 次，安排在训练日末尾
3. **训练频率整合**：核心肌群恢复快（24-48h），可较高频率安排

### 第五步：适度有氧训练设计

> 💡 **有氧训练参考**：LISS/HIIT 安排、心率区间见 `references/accessories/ohp-core-aerobic.md`

根据用户的恢复能力和训练阶段安排有氧：

| 训练阶段 | 有氧类型 | 安排 | RPE |
|-----------|-----------|------|-----|
| 容量期 | LISS（快走、单车）| 非训练日 30-45 min | 3-4 |
| 力量期 | LISS | 非训练日 20-30 min | 3-4 |
| 冲刺期 | 恢复性有氧 | 休息日 20-30 min | 2-3 |

> ⚠️ 有氧不是必选项，视用户恢复能力和时间而定。

### 第六步：MRV 审计

在计划初稿完成后，**必须进行 MRV 审计**：

1. 统计每周各肌群的组数（主项 + 辅助）
2. 对照 `references/planning/mrv-audit.md` 中的 MRV 基准
3. 若超过 MRV → 减少该肌群的辅助动作组数
4. 若远低于 MRV（<60%）→ 可以考虑增加容量

> 💡 **减轻 token 消耗**：若计划涉及大量 MRV 计算，可调用 `scripts/calculate_mrv.py` 脚本：
> ```bash
> python scripts/calculate_mrv.py --muscle_group chest --weekly_sets 18 --mrv 22
> ```

### 第七步：退阶方案与自我调节

> 详细的 JTS 自我调节原则见 `references/methodology/autoregulation.md`

#### 退阶方案模板

```
【退阶方案】TS 当天 RPE 比预期高 2 点以上 
→ BO 组数减 1 组（3→2，或 2→1），保 TS 质量。

【通用原则】自我调节（JTS 原则）：
- TS 是「探测状态」而非力竭组
- BO 降重 8-12% 做 2-3 组
- 若 TS RPE 超标，优先减 BO 容量而非降 TS 重量
```

### 第八步：输出前确认（必做）

在输出完整计划文档前，必须先展示概要供用户确认：

1. **展示训练安排概要**（不展示具体重量和容量数值）
   - 训练频率与训练日安排
   - 周期结构（各阶段重点）
   - 主项与辅助动作选择
2. **展示周期结构**
   - 各阶段周数、RPE 范围、组次配置思路
3. **展示恢复周期检查结果**
   - 各肌群训练频率是否符合恢复周期
   - 训练日次序是否合理（避开高峰、符合恢复窗口）
4. **询问用户是否有调整需求**
   - 替换动作、加入动作、调整时间、修改训练日等
5. **用户确认后**，再输出完整计划文档

> ⚠️ 未经用户确认，不得直接输出完整计划。

### 第九步：输出后与在线文档同步（可选）

输出完整 Markdown 计划文档后，**主动询问用户**是否需要将计划同步到在线文档：

**询问话术模板**：
```
计划已生成完毕！请问是否需要将这份计划同步到在线文档中，方便你在手机/平板上查看和记录训练数据？

支持的平台：
- 金山文档（WPS）
- 飞书文档
- 腾讯文档
- Notion
- 谷歌文档（Google Docs）

如果不需要，可以忽略本条消息。
```

**如果用户选择同步**，根据用户选择的操作：

1. **金山文档（WPS）**
   - 检查是否安装 `kdocs` skill 或 MCP 工具
   - 如有则直接调用创建智能文档（Markdown 格式）
   - 如无则提供 Markdown 内容，引导用户手动粘贴

2. **飞书文档**
   - 检查是否安装飞书 CLI 相关 skill（如 `lark-cli` 或 `feishu-cli`）
   - 如有则调用飞书 CLI 创建/更新文档（支持 Markdown 格式）
   - 飞书 CLI 安装：`npm install -g @larksuite/cli && npx skills add larksuite/cli -y -g`
   - 如无则提供 Markdown 内容，引导用户手动粘贴到飞书文档

3. **腾讯文档**
   - 检查是否安装 `tencent-docs` skill
   - 如有则调用创建智能文档（MDX 格式）
   - 如无则提供 Markdown 内容，引导用户手动操作

4. **Notion**
   - 检查是否安装 Notion API 相关 skill 或 MCP 工具
   - 如有则调用创建页面并填充内容
   - 如无则提供 Markdown 内容，引导用户手动粘贴到 Notion

5. **谷歌文档（Google Docs）**
   - 检查是否安装 Google Workspace CLI（`gws`）相关 skill
   - 如有则调用 `gws docs` 命令创建/更新文档
   - Google Workspace CLI 安装：`npm install -g @googleworkspace/cli` 或从 [GitHub Releases](https://github.com/googleworkspace/cli/releases) 下载二进制文件
   - 如无则提供 Markdown 内容，引导用户手动粘贴到 Google Docs

> 💡 **实现说明**：
> - 各平台通常都有对应的 **skill** 或 **MCP 工具**支持，AI 应优先检查并调用
> - **飞书 CLI**（`lark-cli`）：官方工具，支持 200+ 命令，提供 19 个 AI Agent Skills，覆盖文档、表格、日历等
> - **Google Workspace CLI**（`gws`）：一站式命令行工具，支持 Google Docs/Sheets/Slides 等，内置 100+ Agent 技能
> - 如果未配置对应 skill/MCP，提供 Markdown 原始内容，引导用户自行粘贴到目标平台
> - 不要强制用户同步，纯 Markdown 输出也是完整体验
> - AI 在尝试同步前，应先用 `Skill` 工具或 `ToolSearch` 搜索是否有可用的相关工具

## 输出格式

> 💡 **使用前必读**：完整的输出模板（含 4天/周、3天/周、5天/周三种模板）见 `references/output/output-templates.md`，生成计划前应先读取该文件，根据用户的训练频率选择合适的模板框架，再按下方格式输出。

**默认输出格式：Markdown**

所有计划默认以 Markdown 格式输出。如需 Word、PDF 等格式，用户可自行通过以下方式转换：
- **Markdown → Word**：使用 Pandoc、Typora、或在线转换工具
- **Markdown → PDF**：使用浏览器打印、Typora、Pandoc、或 `md-to-pdf-cjk` skill
- **Markdown → 其他格式**：用户自行选择工具转换

> 💡 本 skill 不内置 Word/PDF 直接生成能力，统一使用 Markdown 作为源头格式。

### 格式 A：Markdown（默认）

适合本地知识库管理、打印、或转换为其他格式，使用标准 Markdown 表格：

```markdown
## 周一：深蹲 + 后链 + 上身拉

**深蹲（主项）**

| 周次 | 工作内容 |
|-----|---------|
| W1 | 5×8 @ RPE 6, 90×8×5 |
| W2 | 5×8 @ RPE 6.5, 92.5×8×5 |
| W7 | TS 132.5×3 (1组) + BO 122.5×3 (2组) |
```

### 格式 B：MDX（仅适用于腾讯文档智能文档）

> ⚠️ **平台限制**：MDX 是腾讯文档智能文档的专用格式，**不适用于**金山文档、飞书、Notion、谷歌文档等其他平台。

**仅当目标平台为腾讯文档时使用此格式**，使用 MDX 语法：

```markdown
<Heading level="3">周一：深蹲 + 后链 + 上身拉</Heading>

<Paragraph>**深蹲（主项）**</Paragraph>

<Table>
  <TableRow>
    <TableCell>周次</TableCell>
    <TableCell>工作内容</TableCell>
  </TableRow>
  <TableRow>
    <TableCell>W1</TableCell>
    <TableCell>5×8 @ RPE 6, 90×8×5</TableCell>
  </TableRow>
</Table>
```

**其他平台输出建议**：

| 目标平台 | 推荐格式 | 操作方式 |
|---------|----------|---------|
| 金山文档（WPS） | Markdown | 使用 `kdocs` skill 直接创建，或手动复制 Markdown |
| 飞书文档 | Markdown | 手动复制 Markdown 内容到飞书文档 |
| Notion | Markdown | 手动复制 Markdown 内容到 Notion |
| 谷歌文档 | Markdown | 手动复制 Markdown 内容到 Google Docs |
| 腾讯文档 | MDX | 使用 `tencent-docs` skill 创建智能文档 |

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
