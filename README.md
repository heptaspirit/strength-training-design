# 🏋️ Strength Training Coach Skill

> **科学训练教练** —— 以 JTS 方法论（Chad Wesley Smith）为核心，追溯 Westside 共轭法（Louie Simmons），融入 RTS 的 RPE 开创（Mike Tuchscherer），整合 Barbell Medicine 循证医学框架（Jordan Feigenbaum / Austin Baraki），并以 ACSM 12th / NSCA 5th 教科书与 ACSM 2026 循证立场声明背书。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/heptaspirit/strength-training-design?color=green&label=Version)](CHANGELOG.md)

加载本 Skill 后，AI 具备两大核心能力：

| 能力 | 说明 |
|------|------|
| 🎓 **知识咨询** | 解答"为什么"类问题——SRA 曲线、疲劳机制、mTOR/AMPk、MEV/MRV 个体化、Bridge Phase、自主神经/心血管反应等 |
| 📋 **计划生成** | 设计周期计划、MRV 审计、PR 估算、计划修改 |

## 🎯 能力矩阵

| 功能 | 触发场景 | 工作流 |
|------|----------|--------|
| 一 · PR 估算 | "估算我的 1RM" / "这个重量能做几次" | `workflows/estimate-pr.md` |
| 二 · 计划修改 | "这个计划太累了帮我调" / "加一个辅助动作" | `workflows/modify-plan.md` |
| 三 · 计划生成 | "设计一个 8 周力量计划" | `workflows/design-plan.md` |
| 四 · 科学咨询 | "为什么硬拉恢复慢" / "CNS 疲劳是什么" | `workflows/consult.md` |

> 所有硬约束（不可跳过减载、硬拉容量上限、医学红旗等）集中在 [`guardrails.md`](guardrails.md)，SKILL.md 仅作极简路由。

## 🏗️ 架构（v0.9.10 重构为三层分离）

```
strength-training-design/
├── SKILL.md          # 薄路由层：能力矩阵 + 硬约束极简版 + 工具入口 + 文献
├── guardrails.md     # 单一约束入口：5 条硬约束详述 + 操作反例
├── workflows/        # 流程层：4 功能的详细工作流（从 SKILL.md 抽出）
├── references/       # 知识层：35 个参考文件，按主题分类，按需加载
├── scripts/          # 使用者/AI 直接调用的批计算脚本
├── dev/              # 维护者专用：检查脚本 + pytest 固件（普通使用者无需接触）
├── docs/             # 设计器契约等工程文档
└── .github/          # CI（push/PR 自动跑 dev/run_all_checks.py）
```

**设计原则**：每个事实只有一个家 —— 流程在 `workflows/`、约束在 `guardrails.md`、知识在 `references/`，改一处不必改两处（参考 ponytail 的"单一规则源"精神，但只学其神、不套其多宿主壳）。

## 📚 参考知识体系（references/）

按目录分组，每个文件自描述，详细内容见文件内 frontmatter：

- **consultation/** — 疲劳四来源、SRA 曲线、MEV/MRV 个体差异、Bridge Phase、ACSM 2026 立场声明、**强度-容量敏感轴（新增）**、**教练-学员感知错位（新增）**
- **methodology/** — JTS 周期化、RPE 自我调节、并发训练干扰（新增）、冲峰与减量（新增）、周期化分类学（新增）
- **health/** — 损伤预防、热身拉伸、核心训练、**大重量自主神经/心血管反应（新增，含 Valsalva/黑视）**、**临床人群与安全筛查（新增）**
- **exercises/** — 辅助动作库、薄弱点、奥举辅助、节奏休息、OHP、有氧、人体测量
- **intensity/** — PR 估算、RPE 参考与渐进超负荷
- **volume-recovery/** — 硬拉容量管理、MRV 审计、超长周期分块
- **barbell-medicine/ / westside/ / rts/ / planning/ / output/** — 四大体系源流 + 计划修改 + 输出模板

## 🚀 安装使用

推荐使用**源码安装**（`.skill` 格式已默认兼容多数 Agent）：

```bash
git clone https://github.com/heptaspirit/strength-training-design.git
cp -r strength-training-design ~/.workbuddy/skills/
```

验证：向 AI 提问"为什么硬拉比卧推恢复慢那么多？"，若能从 SRA 曲线角度科学解答即安装成功。

## 📝 使用示例

**咨询**：`为什么硬拉恢复比卧推慢那么多？我该多久练一次？`
→ AI 基于 `references/consultation/sra-curves.md`：硬拉 > 深蹲 > 卧推的 SRA 曲线最长，建议每周 1–1.5 次。

**计划**：`帮我设计一个 8 周力量举计划，目标深蹲 140 / 卧推 100 / 硬拉 160kg`
→ AI 按 `workflows/design-plan.md` 走：收集约束 → 周期结构 → 各动作 TS/BO → MRV 审计 → 输出前确认 → 完整计划。

## 🧠 关键概念速览

- **SRA 曲线**：技术(<1天) < 肌肥大(2-4天) < 神经力量(~1周) < 结缔组织(最长) —— 决定训练频率
- **疲劳四来源**：糖原 / CNS / 化学信使 / 肌肉损伤，性质与恢复时长各异
- **MEV/MRV**：最小/最大可恢复容量，9 因素个体化
- **RPE/RIR**：自觉疲劳度，RPE 8 = 还能做 2 次
- **MRV 审计**：基于动作疲劳系数 × RPE 修正的真实疲劳负荷

## 🤝 贡献与工程维护

欢迎 Issue / PR。代码规范：Markdown + UTF-8，参考文件间交叉引用避免重复，SKILL.md 保持精简。

**维护者专用（`dev/`）**：
- `run_all_checks.py` — 统一检查入口（引用/版本 + pytest）
- `check_links.py` — 引用死链检查（扫 SKILL.md / README.md / guardrails.md / workflows/*.md）
- `check_version.py` — 版本号一致性
- `tests/` — pytest 固件（锁死设计器确定性逻辑）

改完本地跑 `python dev/run_all_checks.py`，推送后 GitHub Actions 自动复跑。

## 📄 许可证 / 作者 / 更新日志

MIT 许可证（[LICENSE](LICENSE)）· 作者 **heptaspirit** · 详见 [CHANGELOG.md](CHANGELOG.md)

**Keywords**: 力量训练, 力量举, 训练计划, JTS, Westside, MRV, RPE, ACSM, NSCA, 周期化, AI Skill
