---
skill: strength-training-design
category: planning
description: 完整训练计划设计工作流——8 步渐进式设计、异常处理 if-then、重量取整规则、输出格式、脚本调用入口。
load_condition: 功能三——用户要求完整设计训练计划时读取
---

# 完整训练计划设计工作流

## 工作流（8 步，按顺序渐进式读取）

1. **确定目标与约束** → 收集 PR/目标/频率/伤病/肢体比例
   → `references/intensity/pr-estimation.md` / `references/exercises/anthropometry-and-weak-points.md` / `references/health/injury-prevention.md` / `references/barbell-medicine/pain-management.md`（如有疼痛/伤病）

2. **设计周期结构** → JTS 周期（容量期→减载→力量期→冲刺期→测试周）
   → `references/methodology/jts-periodization.md` / `references/volume-recovery/recovery-and-frequency.md`

3. **各动作类型设计** → 主项 TS/BO + 辅助动作选择
   → `references/intensity/rpe-reference-and-progressive-overload.md` / `references/exercises/assistance-exercise-database.md` / `references/exercises/weak-points.md` / `references/exercises/olympic-lifting-assistance.md`
   💡 增肌辅助动作可按需标注 **TUT 节奏码 + 组间休息（RPS）** → `references/exercises/tempo-and-rest.md`（节奏是执行规范，不是进阶工具）

   🔧 **批计算脚本（必须调用，禁止手动）**：
   - RPE 转换：`python scripts/rpe_to_percentage.py --reps <N> --rpe <RPE> --one_rm <PR>`
   - 重量取整：`python scripts/round_weight.py --weight <值> --plate_step <步进>`
   - MRV 审计 / 加权疲劳：`python scripts/calculate_mrv.py` / `calculate_fatigue.py`

   🔧 **计划聚合器（架构 B 入口）**：
   - 入口：`python scripts/design_program.py --input plan.yaml --out-json out.json --out-md week.md`
   - 角色：消费 AI 在 step1 生成的 YAML 草稿 → 复用上述 4 脚本算重量/RPE/MRV → 执行硬约束合规校验（频率/48h/硬拉容量）→ 输出 JSON + MD 周报骨架给 AI 续写编排
   - 设计契约：`docs/design_program_contract.md`（脚本=重复算术/AI=编排的边界红线）

   🔧 **工程维护脚本（仅 skill 维护者运行，普通使用者无需接触）**：
   - 入口：`python dev/run_all_checks.py`（P0 引用/版本检查 + P1 测试；pytest 装于系统 Python，请用该解释器或加 `--python`）；推送后 GitHub Actions 自动跑同样检查（workflow 在仓库根 `.github/workflows/`）
   - 引用死链检查：`python dev/check_links.py`
   - 版本号一致性：`python dev/check_version.py --check-tag`
   - 测试固件：`dev/tests/`（pytest，锁死设计器确定性逻辑）
   - 说明：以上均位于 `dev/`（维护者专用区），与消费者脚本 `scripts/` 物理隔离

   ⚠️ **强制规则（五条，详细规则见对应参考文件 / 汇总于 `guardrails.md`）**：
   - 主项 TS/BO：仅**强度聚焦 phase（力量期+冲刺期）**强制，容量期（无论几周）无 TS，减载周无 TS/BO（按 phase 判定，不绑固定周次，如 8 周骨架的 W5-8）→ 详见 `references/methodology/block-length-and-phase-extension.md` 与 `references/output/output-templates.md`
   - 辅助双进阶：孤立动作禁止"每周+2.5kg" → 详见 `references/intensity/rpe-reference-and-progressive-overload.md` 第十节
   - Cluster Set：RPE ≥8.5 的 TS 必须提供备选 → 详见 `references/intensity/rpe-reference-and-progressive-overload.md` 第十节
   - **硬拉容量上限**：全程传统硬拉工作组 ≤6 组/周（中级）；后侧链分散到多日、不全堆硬拉日；RDL 等髋铰链补充距硬拉 ≥72h → 详见 `references/volume-recovery/deadlift-volume-management.md`
   - **频率与 6 天约束**：每肌群每周 ≤2-3 次、两次重训间隔 ≥48h（MPS 窗口 + Schoenfeld 2019/Grgic 2018）；6 天/周模板第 6 天只放小肌群/功能/变式，不做大肌群重训，三大项不做 3 次/周 → 详见 `references/output/output-templates.md` 模板四

4. **核心稳定与有氧** → OHP/核心/有氧
   → `references/exercises/ohp-training.md` / `references/health/core-training.md` / `references/exercises/aerobic-training.md`
   ⚠️ 有氧必须含心率区间（Zone 2）+ 进阶递减表

5. **MRV 审计** → 简单 MRV + 容量5区 + 个体差异调整 + 加权疲劳 + **硬拉等效疲劳换算**
   → `references/volume-recovery/mrv-audit.md` / `references/volume-recovery/deadlift-volume-management.md`
   🔧 `python scripts/calculate_mrv.py` / `calculate_fatigue.py`

6. **退阶方案** → `references/methodology/autoregulation.md`

7. 🔴 **确认点** → 展示周期概要 + MRV审计结果 + 动作清单，等待用户确认。**未确认前禁止输出完整计划**。

8. **最终输出**（四项强制）：
   - 完整训练计划（周次×动作×组次×重量×RPE）
   - MRV 审计表 + 加权疲劳审计
   - 退阶方案与自我调节指引
   - 训练日志模板 → `references/output/output-templates.md` 末尾

## 异常处理（工作流中的 if-then 分支）

| 触发条件 | 处理方式 |
|---------|---------|
| 用户未提供 1RM | 先切到功能一估算 PR，再返回步骤 1 |
| 用户未回复哑铃片最小重量 | 默认按 1.25kg 片（步进 2.5kg），在输出中注明"假设标准片" |
| 脚本执行失败（Python 不可用） | 手动查表计算，但必须标注"未使用脚本，可能存在取整偏差" |
| 用户有伤病/疼痛限制 | 读取 `references/health/injury-prevention.md` + `references/barbell-medicine/pain-management.md`（BBM 疼痛应对框架）+ `references/exercises/assistance-exercise-database.md` 进退阶链；疼痛≠完全停训，优先用 BBM 主动康复策略修改计划而非直接排除动作 |
| MRV 审计超限（>100% MRV） | 优先减少辅助动作组数（保留主项），最多减 3 组；如仍超限，减少 BO 组数 |
| 硬拉容量超限（>6 组/周 或等效疲劳 >40% MRV） | 优先将 RDL/Good Morning 移至距硬拉 ≥72h 的其他训练日；用低 CNS 动作（腿弯举/臀推/背伸）替代多余的髋铰链组；详见 `references/volume-recovery/deadlift-volume-management.md` |
| 参考文件内容不足以回答咨询问题 | 结合自身知识库补充，明确标注"此部分信息来自文档外，仅供参考" |
| 用户咨询后想改计划 | 切到功能二；用户咨询后想新设计计划 | 切到功能三 |

## 重量取整规则（全局）

所有计算出的重量必须按**用户的实际哑铃片配置**取整，不得硬编码为 2.5kg 倍数：

| 用户配置 | 最小步进 | 取整规则 | 示例（计算值 93.2kg） |
|---------|---------|---------|---------------------|
| 有 1.25kg 片（标准商业健身房） | 2.5kg | 取 2.5kg 的整数倍 | → 92.5kg |
| 有 0.5kg 片 | 1kg | 取 1kg 的整数倍 | → 93kg |
| 用户自备小片 | 0.5kg 或更小 | 取用户指定步进的整数倍 | → 按实际 |

**设计计划前务必询问用户**："你健身房的哑铃片最小是多少？" 若用户未回复，默认按最小 1.25kg 片（步进 2.5kg）处理。
批量取整时**必须调用** `python scripts/round_weight.py --weight <值> --plate_step <步进>`，禁止手动心算取整。

## 输出格式

读取 `references/output/output-templates.md`（含 3天/4天/5天三种模板），默认 Markdown。
