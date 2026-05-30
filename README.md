# Strength Training Design Skill

> 力量训练计划设计 Skill - 整合 JTS 周期化、Westside 共轭法、近年 ACSM 指南、MRV 审计等方法论

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version: 0.7.0](https://img.shields.io/badge/Version-0.7.0-green.svg)](CHANGELOG.md)

本 Skill 为 AI 助手提供专业力量训练计划设计能力，适用于支持标准 skill 格式的 AI Agent 平台。

## 🎯 功能特性

- ✅ 设计 6/8/12/16 周力量周期计划
- ✅ 基于 JTS 原则设计 Top Set / Back-off 结构
- ✅ 对现有计划进行 MRV（最大可恢复容量）审计
- ✅ 根据 RPE/RIR 数据动态调整训练容量与强度
- ✅ 输出 Markdown 或同步至在线文档（腾讯文档/金山文档/Notion）

## 📚 方法论整合

| 方法论 | 应用场景 | 参考文件 |
|--------|----------|----------|
| JTS 周期化 | 周期结构、TS/BO 设计 | `references/methodology/jts-periodization.md` |
| Westside 共轭法 | 辅助动作选择、弱点针对性 | `references/methodology/westside-acsm.md` |
| 近年 ACSM 指南 | 最新运动生理学研究 | `references/methodology/westside-acsm.md` |
| MRV 审计 | 容量管理、过度训练预防 | `references/volume-recovery/mrv-audit.md` |
| RPE/RIR 自我调节 | 强度自动调节 | `references/methodology/autoregulation.md` |

## 📂 文件结构

```
strength-training-design/
├── SKILL.md                          # 主文件（AI 加载入口）
├── CHANGELOG.md                       # 版本变更记录
├── README.md                          # 本文件
├── LICENSE                            # MIT 许可证
└── references/
    ├── methodology/                  # 核心方法论
    │   ├── jts-periodization.md
    │   ├── westside-acsm.md
    │   └── autoregulation.md
    ├── intensity/                    # 强度与重量计算
    │   ├── pr-estimation.md
    │   └── rpe-reference-and-progressive-overload.md
    ├── volume-recovery/              # 容量与恢复管理
    │   ├── mrv-audit.md
    │   └── recovery-and-frequency.md
    ├── health/                       # 健康与安全
    │   ├── injury-prevention.md
    │   ├── warmup-flexibility.md
    │   └── core-training.md
    ├── exercises/                    # 动作库与专项
    │   ├── assistance-exercise-database.md
    │   ├── weak-points-and-olympic-lifting.md
    │   ├── anthropometry-and-weak-points.md
    │   ├── ohp-training.md
    │   └── aerobic-training.md
    ├── planning/                     # 计划设计工具
    │   └── plan-modification.md
    └── output/                       # 输出模板
        └── output-templates.md
```

## 🚀 安装使用

本 Skill 提供两种安装方式，推荐使用**方式一（源码安装）**。

### 方式一：源码安装（推荐）

适用于所有支持 `.skill` 格式的 AI Agent：

#### 1. 克隆仓库到本地

```bash
git clone https://github.com/heptaspirit/strength-training-design.git
```

#### 2. 复制到 Agent 的 skills 目录

**WorkBuddy / CodeBuddy**（已测试 ✅）：
```bash
cp -r strength-training-design ~/.workbuddy/skills/
```

**Hermes Agent**（已测试 ✅）：
```bash
cp -r strength-training-design ~/.hermes/skills/
```

**其他 AI Agent**：
将 `strength-training-design/` 目录复制到对应 Agent 的 skills 目录（请查阅对应 Agent 的文档）。

---

### 方式二：手动打包 .skill 文件（高级用户）

如果你需要将 Skill 分享给没有 Git 的用户，可以手动打包：

```bash
# 进入 skill 目录
cd strength-training-design/

# 打包为 .skill 文件（本质是 Zip 压缩包）
# macOS/Linux:
zip -r strength-training-design.skill * -x "*.git*"

# Windows (PowerShell):
Compress-Archive -Path * -DestinationPath strength-training-design.skill -Force
```

然后将 `.skill` 文件分享给其他用户，在他们的 AI Agent 中导入即可。

> 💡 **提示**：`.skill` 文件本质上是 Zip 压缩包，只是扩展名改成了 `.skill`。AI Agent 导入时会自动解压到 skills/ 目录。

---

### 验证安装

安装完成后，在 AI Agent 中提问：
```
帮我设计一个 8 周力量训练计划
```

如果 AI 正确触发 skill 并询问你的训练信息，说明安装成功。

## 📝 使用示例

**用户提问**：
```
帮我设计一个 8 周力量举训练计划，目标是深蹲 140kg、卧推 100kg、硬拉 160kg
```

**AI 响应流程**：
1. 收集用户信息（训练经验、当前 PR、可用频率）
2. 如果用户无 1RM 数据，引导进行 PR 估算（见 `references/intensity/pr-estimation.md`）
3. 设计周期结构（容量期 → 力量期 → 峰值期）
4. 各动作 TS/BO 设计
5. MRV 审计
6. 输出确认 → 完整计划

## 🔧 核心工作流

```
第一步：收集用户个性化信息（含 PR 估算）
    ↓
第二步：设计周期结构（含恢复周期检查）
    ↓
第三步：各动作类型设计（主动作 + 辅助）
    ↓
第四步：核心稳定训练设计
    ↓
第五步：适度有氧训练设计
    ↓
第六步：MRV 审计
    ↓
第七步：退阶方案与自我调节
    ↓
第八步：输出前确认 ← 展示概要，用户确认后再输出完整计划
```

## 🧠 关键技术概念

- **MRV（Maximum Recoverable Volume）**：最大可恢复容量，超过此容量会导致过度训练
- **RPE（Rating of Perceived Exertion）**：自觉疲劳度评分，RPE 8 = 还能做 2 次
- **RIR（Reps in Reserve）**：剩余次数，RIR 2 = 还能做 2 次
- **JTS 周期化**：容量期高容量中等强度 → 力量期中等容量高强度 → 峰值期低容量极高强度
- **TS/BO（Top Set / Back-off）**：顶级组 + 降重组，JTS 核心训练结构

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

**贡献前请阅读**：
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

**代码规范**：
- 所有文档使用 Markdown 格式
- 中文使用 UTF-8 编码
- 参考文件之间避免内容重复，使用交叉引用
- 保持 `SKILL.md` 简洁，详细信息放在 `references/` 目录

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## ✍️ 作者

**heptaspirit**

## 📋 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

---

## 🌟 支持的平台

本 Skill 使用标准 `.skill` 格式（Zip 压缩包，内含 `SKILL.md` 入口文件和 `references/` 参考文档目录）。

**格式兼容性**：
- ✅ **WorkBuddy / CodeBuddy**：原生支持 `.skill` 格式
- ✅ **Hermes Agent**：原生支持 `.skill` 格式（已测试）
- ✅ **OpenClaw**：支持类似 skill 格式，可能需要调整目录结构
- ✅ **其他 AI Agent**：若支持 `.skill` 格式或类似 skill 系统，可参考本 Skill 的方法论和参考文档，适配到对应格式

> 💡 **格式说明**：`.skill` 格式正逐渐成为 AI Agent 技能分发的通用格式。采用标准 `.skill` 格式的 Agent 应可直接使用本 Skill，或仅需少量适配。

**已测试平台**：
- ✅ WorkBuddy / CodeBuddy
- ✅ Hermes Agent（v0.6.0 确认可用）

**其他 AI Agent 平台适配**：
本 Skill 的知识体系和方法论可用于任何 AI Agent，但不同 Agent 的 skill 格式可能不同。如果你的 Agent 使用不同的 skill 格式，可以参考本 Skill 的方法论和参考文档，适配到对应格式。

---

**Keywords**: 力量训练, 力量举, 训练计划, JTS, Westside, MRV, RPE, ACSM, 周期化, AI Skill, Strength Training, Powerlifting, Program Design
