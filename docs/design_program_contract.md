# 设计契约：训练计划生成器 `design_program.py`（架构 B）

> 状态：v3 修订（吸收用户"C2 文档纠错 + 边界重谈"反馈：脚本=通用重复运算器，AI=编排器）
> 作者：Boyang + WorkBuddy
> 关联：strength-training-design v0.9.8
>
> **v3 核心修正**：v2 把设计器写成"三大项专用 + 大量要素丢给 AI"是错的。
> 真实 C2 文档（`8周力量训练计划_C2_v1.md`）含 OHP/高翻/高拉/弱点变式/后链分日/拉伸/有氧/核心/引体/孤立双进阶，
> 设计器应对**任何动作**通用地做重复算术（重量/MRV/合规/减载/AMRAP/TS校验），而非只绑 squat/bench/deadlift。
> 真正归 AI 的是"动作选择 + 排布编排"（排不排、排哪天、用什么变式），脚本只消费 AI 给的意图并做确定性校验。

## 0. 架构定位（为什么是 B 不是 A）

| 维度 | 架构 A（脚本端到端出计划） | 架构 B（脚本出数据，AI 编排）✅ |
|------|--------------------------|-------------------------------|
| 确定性计算（RPE→%、取整、TM 调节、MRV 审计、48h 校验） | 适合 | 适合 |
| 非结构化决策（弱点变式选择、同日肌群排布、减载切分、块间过渡） | ❌ 无法编码 | ✅ 留给 AI |
| 输出物 | 一份完整 plan 给人看 | 一份结构化周报（JSON/MD）+ 合规红绿灯，给 AI 消费 |
| 风险 | 退化成"又一个 PHUL 表格"，踩已知坑 | 复用现有 4 脚本，不重复造表 |

**结论：设计器是现有 4 个单步 CLI 的"聚合器 + 合规检查器"，不是计划编排器。**

---

## 1. 复用策略（不 fork 表逻辑）

`design_program.py` **import 现有脚本的函数层**，不重写 RPE_TABLE / MRV_TABLE：

```python
from scripts.rpe_to_percentage import rpe_to_percentage, calculate_weight_from_1rm
from scripts.round_weight import round_weight
from scripts.calculate_mrv import calculate_mrv_status, MRV_TABLE
from scripts.calculate_fatigue import calculate_weighted_fatigue, calculate_cns_fatigue
```

新增的 3 个计算函数（来自 v0.9.6 吸收）也在此层实现：
- `tm_adjust(last_rir_deviation)` → SBS 7 档 TM 调节
- `single_at_8_to_weight(one_rm_est)` → Single@8 当日锚（≈90% 1RM）
- `rir_target(percent_1rm)` → Last Set RIR 目标表查询

---

## 2. 总原则：新机制按需启用，不强制塞计划（v2 新增）

v0.9.5/v0.9.6 吸收的所有机制（SBS TM 调节 / Single@8 / 模块化 / 硬拉单次模式 / 超长周期分块 / TUT-RPS）都是**可选项**，是否出现在输出里，取决于**用户需求**，不是默认全开。

设计器 YAML 用 `enabled_modules` 白名单控制（默认最小集）。AI 在功能三 step1 按用户画像决定开哪些：

| module 键 | 对应机制 | 默认 | 命中场景举例 |
|-----------|---------|------|------------|
| `base_rpe_pct` | RPE→% + 取整 + MRV 审计 | 开 | 所有用户 |
| `tm_autoregulation` | SBS 7 档 TM 调节 | **关** | 用户确实记 RIR 或接受周期性 AMRAP 重估 |
| `single_at_8` | Single@8 当日锚 | 关 | 主项日想用锚定法 |
| `rir_target_table` | Last Set RIR 目标 | 关 | 想要"末组留几 RIR"明示 |
| `modular_config` | 模块化个体化清单 | 关 | 用户要自定义主项/辅助/频率 |
| `deadlift_single_mode` | SSPT/Ort 硬拉单次高质量 | 关 | 硬拉弱项 / 专项期 |
| `long_cycle_blocking` | YSY 9×4 周块 | 关 | 长周期冲总成绩（如 500kg 规划） |
| `tempo_rps` | TUT 节奏码 + RPS 休息 | 关 | 用户要节奏/休息参数 |

> ⚠️ 这条是用户明确强调的红线：**脚本绝不因为"我们有这个机制"就把它塞进计划**。AI 判断用户不需要 → 机制静默。

---

## 3. 输入契约（input schema）

输入一份 YAML/JSON，描述"这一周的状态 + 计划意图"。**AI 在功能三 step1 生成草稿，用户确认后再跑**（用户反馈 1）。

```yaml
meta:
  user: "Boyang"
  cycle: "C2"
  week: 5              # 用于波浪/减载判断
  training_days: 4     # v1 仅支持 3/4/5（用户反馈 4：6/7 天不做自动生成）

template: "upper_lower"   # 顶层字段：upper_lower | full_body | ppl（v1 仅经典 3/4/5 天模板）

one_rm:                 # 当前各项 1RM（kg），用于 % 计算
  squat: 145
  bench: 105
  deadlift: 157.5

# TM 调节信号源（用户反馈 2：默认不用每周 RIR，用计划末 AMRAP 重估）
tm_mode: "amrap_reestimate"   # amrap_reestimate（默认）| weekly_rir（可选）
tm_overrides:           # 取决于 tm_mode
  # amrap_reestimate 模式：计划级 TM 锚定，周期性覆盖
  squat: { tm_anchor: 142.5 }      # 由上次 AMRAP→Epley 算出，整段固定
  bench: { tm_anchor: 102.5 }
  deadlift: { tm_anchor: 155.0 }
  # weekly_rir 模式（仅当用户确实记 RIR 时填）：上周末组 RIR 偏离 → 触发调节
  # squat: { last_rir_deviation: +1.5 }   # +1.5 → TM +1.5%

enabled_modules:        # 用户反馈 5：按需启用，默认只开基础
  - base_rpe_pct
  # - tm_autoregulation
  # - single_at_8
  # - rir_target_table
  # - modular_config
  # - deadlift_single_mode
  # - long_cycle_blocking
  # - tempo_rps

week_structure:        # AI 给出意图（哪天练什么、主项+辅助+奥举+核心都带重量），脚本做重复算术+合规
  - day: "Mon"
    lifts:
      - { exercise: "squat", sets: 5, reps: 8, rpe: 7, category: "primary" }
      - { exercise: "pause_squat", sets: 3, reps: 8, rpe: 7, category: "assistance" }
      - { exercise: "pullup", sets: 4, reps: 6, category: "assistance" }   # 引体爆发向
  - day: "Wed"
    lifts:
      - { exercise: "bench", sets: 5, reps: 8, rpe: 7, category: "primary" }
      - { exercise: "close_grip_bench", sets: 3, reps: 8, rpe: 7, category: "assistance" }
  - day: "Fri"
    lifts:
      - { exercise: "hang_power_clean", sets: 4, reps: 3, rpe: 7, category: "olympic", pct: 41 }  # 高翻，按 %DL
      - { exercise: "deadlift", sets: 3, reps: 6, rpe: 7, category: "primary" }
  - day: "Sat"
    lifts:
      - { exercise: "ohp", sets: 3, reps: 8, rpe: null, pct: 68, category: "primary" }  # 实力推容量期 65-70% 1RM
      - { exercise: "light_bench", sets: 3, reps: 8, rpe: 6.5, category: "assistance" }
  # 注：有氧（Zone 2 休息日）不进本设计器（用户实际 4 天主训 + 2 天自由有氧）
  # 拉伸/灵活度模块由 AI 在最终文档编排，不进重量运算

intent:                 # 本周训练目标
  phase: "volume"       # volume | intensity | deload | peak
  deload_factor: 0.6    # phase=deload 时默认 ×0.6，可覆盖 0.5–0.7
```

**边界：脚本不决定 week_structure 怎么排**（那是非结构化决策，AI 给）。脚本只对列出的每个 lift 做：
- 重量换算（RPE→% 或直给 `pct`→重量→取整）
- 按 `category` 与 `exercise` 查 MRV 表做周容量审计
- 主项（category=primary/olympic 且需间隔约束的）做 48h/频率校验
- 后侧链规则（§3.3）校验

### 3.2 动作 → 容量区间配置表（可配置，AI 可覆盖）

脚本内置常用动作默认值（自然中级参考，来源：skill references 的 MRV/MEV/MAV 表），AI 可在 YAML `mrv_overrides` 覆盖：

```yaml
mrv_defaults:            # 脚本内置（示例，实际以 references 为准）
  squat:        { mev: 10, mav: 16, mrv: 18 }
  bench:        { mev: 8,  mav: 14, mrv: 20 }
  deadlift:     { mev: 4,  mav: 6,  mrv: 6 }    # 全程硬拉专项期上限 ≤6 组/周（硬约束）
  ohp:          { mev: 8,  mav: 14, mrv: 16 }
  hang_power_clean: { mev: 3, mav: 6, mrv: 9 }  # 高翻（爆发力，容量低）
  pause_squat:  { mev: 6,  mav: 10, mrv: 12 }   # 弱点变式按间接刺激计
  pullup:       { mev: 10, mav: 18, mrv: 22 }
  # ……其余辅助动作 AI 可不配（脚本仅做重量换算，不强制审计）
mrv_overrides: {}        # AI 按需覆盖某动作上限
```

### 3.3 后侧链距硬拉间隔规则（可配置，C2 真实用法）

```yaml
gap_rules:               # 动作A 刺激后，动作B 至少间隔 N 天（C2：RDL/GM 在周一距周五硬拉 96h）
  - { after: "deadlift", before: ["rdl", "good_morning"], min_gap_days: 3 }
  - { after: "deadlift", before: ["pause_deadlift", "front_squat"], min_gap_days: 2 }
```
脚本按这些规则出红绿灯；不配置则不做此项校验。

---

## 4. 输出契约（output schema）

输出一份结构化 JSON + 一份 AI 可读的 Markdown 周报。

### 4.1 每个主项的计算结果
```json
{
  "squat": {
    "tm_after_adjust": 142.5,
    "single_at_8_weight": null,        // 仅 use_single_at_8=true 时算
    "prescribed_sets": [
      {"set": 1, "reps": 5, "rir_target": 3, "pct_1rm": 77, "weight_raw": 109.7, "weight_rounded": 110},
      {"set": 2, "reps": 5, "rir_target": 3, "pct_1rm": 77, "weight_raw": 109.7, "weight_rounded": 110},
      {"set": 3, "reps": 5, "rir_target": 2, "pct_1rm": 82, "weight_raw": 116.9, "weight_rounded": 117.5},
      {"set": 4, "reps": 3, "rir_target": 1, "pct_1rm": 87, "weight_raw": 124.0, "weight_rounded": 122.5}
    ],
    "weekly_volume_sets": 4,
    "mrv_status": {"percentage": 80, "status": "安全", "emoji": "✅"}
  }
}
```

### 4.2 合规校验报告（红绿灯）
```json
{
  "compliance": {
    "frequency_check": {
      "squat": {"times_per_week": 1, "ok": true, "note": "≤2-3 次/周"},
      "bench": {"times_per_week": 2, "ok": true},
      "deadlift": {"times_per_week": 1, "ok": true}
    },
    "interval_48h_check": {
      "ok": true,
      "violations": [],
      "note": "所有大肌群两次刺激间隔 ≥48h"
    },
    "deadlift_volume_check": {
      "full_deadlift_sets": 4,
      "ok": true,
      "note": "≤6 组/周（专项期上限）"
    }
  }
}
```

### 4.3 Markdown 周报（给 AI 直接读）
- 表格：每天每动作的重量/次数/RIR 目标/取整重量
- 红绿灯汇总：哪些合规、哪些报警
- TM 调节说明：本周各主项 TM 变化原因（仅 tm_autoregulation 开启时）
- **未启用的机制不出现在周报里**（呼应第 2 节总原则）

---

## 5. 脚本负责 vs AI 负责（明确红线 — v3 重画）

> 核心判据：**这件事是不是"对每个动作都一样的确定性重复算术"？是→脚本；否（涉及选择/排布/主观判断）→AI。**

### 5.1 脚本做（通用重复运算，对任何动作适用，不绑三大项）

| 职责 | 说明 | 是否始终开 |
|------|------|-----------|
| 重量换算：1RM→%档、RPE→%→重量、高次直接用 `pct` | OHP/高翻/辅助全通用 | 始终 |
| 重量取整（按 `plate_step`，默认 2.5kg） | 任何动作 | 始终 |
| MRV/MEV/MAV 周容量审计 | 按「动作→容量区间」可配置表（见 §3.2），OHP/高翻/辅助都能挂 | 始终 |
| 48h 间隔 / 频率合规 | 任何标记为需间隔约束的主项；每主项 ≤2-3 次/周 | 始终（红绿灯） |
| 后侧链距硬拉间隔（如 RDL 周一距周五硬拉 96h） | 可配置「动作A→动作B 最小间隔 N 天」规则（见 §3.3） | 配置即开 |
| 减载倍数（deload_factor 默认 0.6，可 0.5–0.7） | 整周权重统一乘 | phase=deload 时 |
| AMRAP→1RM 估算（Epley，向下取整至步进） | 供 TM 锚定 / W9 估算周 | 启用 amrap 时 |
| TS 跳跃校验（W5-8 TS 反算 %PR，确认冲刺轨迹） | 主项冲刺周 | 启用 ts_jump 时 |
| SBS TM 7 档调节 | 仅 `tm_autoregulation` 开启 | 按需 |
| Single@8 当日锚 / RIR 目标表 | 仅对应模块开启 | 按需 |

### 5.2 AI 做（编排 + 选择，脚本不预置）

| 职责 | 说明 |
|------|------|
| **动作选择**：排不排 OHP / 高翻 / 高拉 / 拉伸 / 有氧 / 核心 / 引体 / 孤立 | 由用本 skill 的 AI 按用户画像决定，脚本不预置任何动作清单 |
| **排布 / 同日肌群组合**：周一深蹲+引体、周五硬拉+高翻、周六轻量+OHP | 非结构化决策，AI 给 `week_structure` 意图，脚本只校验合规 |
| **弱点变式选择**：暂停深蹲 vs 窄距卧推、前蹲 vs 暂停硬拉 | AI 选，脚本只算重量 |
| **退阶 / 双进阶**：引体做不完用弹力带、侧平举先加次数到上限再加重量 | AI 决策 |
| **RPE 主观记录**：实际 RPE 由人记，不进脚本 | — |
| **最终计划文档编排** | 把周报 + references 合成交付物 |

> ⚠️ 用户红线（原话）：**脚本充其量做的是重复性运算的工作**。凡是"选什么、怎么排、弱点在哪、主观感受如何"都归 AI；脚本只负责"给定意图后，把重量/容量/合规这些重复算术跑对、出红绿灯"。

---

## 6. 与现有工作流的衔接

- 输入 YAML 由 AI 在"功能三"第一步生成（读用户背景 + 周期目标 + 判断启用哪些模块）
- 输出 JSON 喂回"功能三"第 2-5 步，替代手动串 4 脚本
- 输出 Markdown 周报成为 AI 写最终 plan 的骨架
- 合规红绿灯 = 自动化的"审计能力"（原靠 AI 人工 check）
- **有氧日不进本设计器**：用户实际是 4 天主训 + 2 天自由有氧，有氧由用户自行安排（用户反馈 4）

---

## 7. v1 范围与明确排除

- ✅ v1 支持模板：3 天（full_body）、4 天（upper_lower）、5 天（ppl）
- ❌ v1 **不做** 6/7 天模板自动生成（用户反馈 4：一般人不常用；个人是 4+有氧）
- ❌ v1 不做多周批处理（先单周稳定）
- ❌ v1 不自动生成弱点变式名称（AI 负责，脚本只给容量/RPE 框架）

---

## 8. 未来扩展（不在 v1 范围）

- `design_program.py` 输出喂给 `tests/` 做单元测试（P1，等本脚本稳定后补）
- 多周批处理：输入 N 周意图 → 输出整周期波浪（需先有单周稳定）
- CLI 模式：`--input plan.yaml --format json|md`
- 6/7 天模板：待用户需求明确且 4/5 天验证成熟后再评估

---

## 9. 版本历史

- v1（初稿）：原始架构 B 设计
- v2（本版）：吸收用户 5 点反馈
  1. 输入由 AI 生成草稿、用户确认后跑
  2. TM 调节默认 `amrap_reestimate`（非每周 RIR）；`weekly_rir` 降为可选
  3. 减载 `deload_factor` 默认 0.6，可覆盖 0.5–0.7
  4. v1 仅 3/4/5 天经典模板；6/7 天不做；有氧日不进设计器
  5. 新增第 2 节总原则：新机制按需启用（`enabled_modules` 白名单）
