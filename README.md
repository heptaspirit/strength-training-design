# 🏋️ Strength Training Coach Skill

> **科学训练教练** —— 不仅能设计训练计划，更能解答训练科学问题。基于 JTS 两本官方手册等权威来源，让 AI 成为你的力量训练顾问。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version: 0.9.0](https://img.shields.io/badge/Version-0.9.0-green.svg)](CHANGELOG.md)

加载本 Skill 后，AI 具备两大核心能力：

| 能力 | 说明 |
|------|------|
| 🎓 **知识咨询** | 解答"为什么"类问题——SRA 曲线、疲劳机制、mTOR/AMPk、MEV/MRV 个体化、Bridge Phase 等 |
| 📋 **计划生成** | 设计周期计划、MRV 审计、PR 估算、计划修改 |

## 🎯 功能特性

### 🎓 科学训练咨询（功能四）

作为教练的核心能力，解答一切关于力量训练的科学问题：

- ✅ **疲劳机制**：判断你是糖原耗尽、CNS 疲劳、化学信使失衡还是肌肉损伤
- ✅ **SRA 曲线**：理解为什么硬拉恢复最慢，如何根据恢复周期安排训练频率
- ✅ **MEV/MRV 个体化**：9 因素系统（性别/体重/身高/力量/经验/年龄/饮食/睡眠/压力）精确调整容量
- ✅ **mTOR/AMPk 机制**：从分子层面理解减载为什么不能跳过，为什么不能同时大量做有氧
- ✅ **Bridge Phase**：周期之间的过渡期设计，打破训练倦怠和适应性抵抗
- ✅ **训练科学原理**：肌肉纤维类型变化、神经适应、特异性原则等
- ✅ **ACSM 2026 循证指南**：137 篇系统评价的最新证据——推翻 7 个误区，澄清力竭/周期化/频率的科学真相

### 📋 训练计划生成（功能一/二/三）

## 📚 知识体系

| 知识领域 | 内容 | 参考文件 |
|--------|------|----------|
| **疲劳管理进阶** | 4 来源 + mTOR/AMPk + 症状判断 | `references/consultation/fatigue-sources.md` |
| **SRA 曲线体系** | 4 维曲线 + 三大项排序 + SSR 范式 | `references/consultation/sra-curves.md` |
| **MEV/MRV 个体化** | 9 因素详细机制 + 调整示例 | `references/consultation/mev-mrv-individual-differences.md` |
| **Bridge Phase** | 周期过渡设计 + 适应性抵抗 | `references/consultation/bridge-phase.md` |
| **ACSM 2026 立场声明** | 137 篇系统评价概览 + 7 个误区 + ACSM vs JTS 对比 | `references/consultation/acsm-2026-position-stand.md` |
| JTS 官方手册 | 七大原则 + 周期/MEV/MRV/动作选择 | Scientific Principles of Strength Training & Program Design Manual |
| JTS 周期化 | 周期结构、TS/BO 设计 | `references/methodology/jts-periodization.md` |
| Westside 共轭法 | 辅助动作、弱点针对性 | `references/methodology/westside-acsm.md` |
| ACSM 指南 | RPE/RIR、恢复策略 | `references/methodology/westside-acsm.md` |
| MRV 审计 | 容量管理、加权疲劳 | `references/volume-recovery/mrv-audit.md` |
| RPE 自我调节 | 强度自动调节、退阶 | `references/methodology/autoregulation.md` |

## 📂 文件结构

```
strength-training-design/
├── SKILL.md                          # 主文件（AI 加载入口）
├── CHANGELOG.md                       # 版本变更记录
├── README.md                          # 本文件
├── LICENSE                            # MIT 许可证
├── scripts/                           # 批计算脚本（设计计划时调用）
│   ├── rpe_to_percentage.py           # RPE ↔ %1RM 批量转换
│   ├── round_weight.py                # 重量按哑铃片步进取整
│   ├── calculate_mrv.py               # MRV 审计批量计算
│   └── calculate_fatigue.py           # 加权疲劳 + CNS 疲劳计算
└── references/
    ├── consultation/                   # 🎓 科学训练咨询（功能四）
    │   ├── fatigue-sources.md          # 疲劳四来源 + mTOR/AMPk
    │   ├── sra-curves.md               # SRA 曲线体系详解
    │   ├── mev-mrv-individual-differences.md  # MEV/MRV 个体差异系统
    │   └── bridge-phase.md             # Bridge Phase 过渡期
    ├── methodology/                   # 核心方法论
    │   ├── jts-periodization.md
    │   ├── westside-acsm.md
    │   └── autoregulation.md
    ├── intensity/                     # 强度与重量计算
    │   ├── pr-estimation.md
    │   └── rpe-reference-and-progressive-overload.md
    ├── volume-recovery/               # 容量与恢复管理
    │   ├── mrv-audit.md
    │   └── recovery-and-frequency.md
    ├── health/                        # 健康与安全
    │   ├── injury-prevention.md
    │   ├── warmup-flexibility.md
    │   └── core-training.md
    ├── exercises/                     # 动作库与专项
    │   ├── assistance-exercise-database.md
    │   ├── weak-points-and-olympic-lifting.md
    │   ├── anthropometry-and-weak-points.md
    │   ├── ohp-training.md
    │   └── aerobic-training.md
    ├── planning/                      # 计划设计工具
    │   └── plan-modification.md
    └── output/                        # 输出模板
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
为什么硬拉比卧推恢复慢那么多？
```

如果 AI 从 JTS 官方手册的角度科学地解答了 SRA 曲线原理和三大项恢复差异，说明安装成功。

也可以试试计划生成：
```
帮我设计一个 8 周力量训练计划
```

## 📝 使用示例

### 🎓 咨询问答示例

**用户提问**：
```
为什么硬拉恢复比卧推慢那么多？我该多久练一次硬拉？
```

**AI 响应**（基于 `references/consultation/sra-curves.md`）：

根据 JTS 官方手册，不同动作的 SRA（刺激-恢复-适应）曲线长度不同：硬拉 > 深蹲 > 卧推。硬拉对身体的神经和物理压力最大，SRA 曲线最长，建议每周 1-1.5 次。如果你的硬拉是相扑式，可以比传统硬拉略频繁一些。

---

**用户提问**：
```
我感觉一直很累但 MRV 审计说没超，怎么回事？
```

**AI 响应**（基于 `references/consultation/fatigue-sources.md`）：

疲劳不只是容量的函数。JTS 手册分解为 4 种疲劳来源：糖原耗尽（几天恢复）、CNS 疲劳（数天到数周）、化学信使失衡（数周到数月）、肌肉损伤（数天到数周）。你可能是 CNS 疲劳——特点是"杠铃感觉异常沉重"而不仅仅是酸痛。建议降低训练强度（不是容量），同时检查睡眠和压力。

### 📋 计划生成示例
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
第一步：确定目标与约束（PR 估算、伤病、肢体比例）
    ↓
第二步：设计周期结构（容量期 → 减载 → 力量期 → 冲刺期 → 测试周）
    ↓
第三步：各动作类型设计（主项 TS/BO + 辅助双进阶 + Cluster Set）
          🔧 批计算：rpe_to_percentage.py / round_weight.py
    ↓
第四步：核心稳定 + 有氧设计（含心率区间 + 进阶递减表）
    ↓
第五步：MRV 审计 + 加权疲劳审计
          🔧 批计算：calculate_mrv.py / calculate_fatigue.py
    ↓
第六步：退阶方案与自我调节
    ↓
第七步：输出前确认 ← 展示概要，用户确认后再输出完整计划
    ↓
第八步：最终输出（计划 + MRV 审计 + 退阶方案 + 训练日志模板）
```

## 🧠 关键训练科学概念

- **SRA 四曲线**：技术适应（~1天）< 肌肥大（2-4天）< 神经力量（~1周）< 结缔组织（最长）——直接决定训练频率
- **疲劳四来源**：糖原耗尽（数天）、CNS 疲劳（数天-数周）、化学信使失衡（数周-数月）、肌肉损伤（数天-数周）
- **mTOR/AMPk**：合成代谢 vs 分解代谢的细胞开关，解释了减载为什么不能跳过
- **MEV/MRV 个体差异**：9 因素系统——性别、体重、身高、力量、经验、年龄、饮食、睡眠、压力
- **Bridge Phase**：周期之间的 1-2 周过渡期，用于心理休息、伤病康复、打破适应性抵抗
- **MRV（Maximum Recoverable Volume）**：最大可恢复容量，超过此容量会导致过度训练
- **加权疲劳审计**：基于动作疲劳系数（FC）× RPE 修正的真实疲劳负荷
- **RPE（Rating of Perceived Exertion）**：自觉疲劳度评分，RPE 8 = 还能做 2 次
- **JTS 周期化**：容量期高容量中等强度 → 力量期中等容量高强度 → 峰值期低容量极高强度
- **TS/BO（Top Set / Back-off）**：顶级组 + 降重组，JTS 核心训练结构，W5-W8 强制使用
- **双进阶（Double Progression）**：辅助动作递增方式——先加次数再加重量
- **Cluster Set**：组簇训练，如 5×1 @ 20s 休息替代 1×5，降低 CNS 疲劳
- **心率区间**：Zone 2（60-70% HRmax）为力量训练者有氧黄金区间

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
