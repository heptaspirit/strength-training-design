#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strength-training-design skill — 单次训练应激计算器（多轴）
Used by: 功能三步骤5「容量与系统应激审计」、功能二容量/排期调整、功能四「为什么这么累/动作做不动」
提供: A 系统应激总量 / A% 相对刻度 / Rf 峰值瞬时应激 /
      每动作执行惩罚与崩坏风险 / 局部协同链协同比
依据: references/consultation/session-strain-modeling.md（模型说明与读法）

回答的问题（MRV 组数审计回答不了的那些）：
  - 这节课"整个人练完有多废"（A）
  - "最喘的那一刻"有多喘（Rf 峰值）
  - 某个动作排在这个位置会打几折（penalty）、会不会崩动作（break_risk）
  - 这个动作开始前，它最吃的那块协同肌被前面动作刮掉多少（协同比）

不做的三件事：
  - **不带默认参考 1RM** —— 外部负重动作的相对强度 = weight / ref，ref 必须由调用方给出
    （--params 文件 / 输入 JSON 的 one_rm / --init-params 导出的模板）。
    缺 ref 时直接报错并告诉你怎么补，不静默拿一个内置值去算。
  - 不给"过了/没过"的绝对阈值 —— 内置参数是估算值，只能做同文件内的相对比较。
    绝对阈值需标定，三条升级路径（估算 -> 实测标定 -> 用户自备长期参数）见
    references/consultation/srpe-calibration.md。
  - 不算"神经/强度轴" —— 该轴只对 %1RM 可算的外部负重动作成立，自重动作（引体/划船）
    会因缺负荷数据而被高估，暂不固化。

参数优先级（低 -> 高）：
  内置估算值  <  --params 文件  <  输入 JSON 内嵌 params  <  命令行 --beta/--a-ref/--anchor
用户若已有长期使用的参数集，存成一份 JSON 用 --params 传入即可，无需每次重报。
用 --init-params 可导出一份可编辑的参数模板。

用法:
  python scripts/session_strain.py --input session.json
  python scripts/session_strain.py --input session.json --params my-params.json --curve
  python scripts/session_strain.py --input session.json --json > out.json
  python scripts/session_strain.py --demo          # 跑自带样例
  python scripts/session_strain.py --list          # 列出可用动作 key
  python scripts/session_strain.py --init-params my-params.json
"""

import argparse
import difflib
import json
import math
import os
import sys

# ─────────────────────────────────────────────────────────────────────
# 动作库
#   m     肌肉质量/系统负荷系数（同等相对强度下，参与的肌群越大越高）
#   td    技术需求（0-1）：疲劳下动作质量崩坏的风险权重
#   eff   自重/不可加载动作的等效强度系数（0-1）
#   rest  默认组间休息（秒）
#   wpr   默认每次用时（秒/次）
#
# ⚠ 外部负重动作**不带内置参考 1RM**。相对强度 = weight / ref，ref 必须由调用方提供
#   （--params 的 one_rm / 输入 JSON 的 one_rm / --init-params 模板）。缺失时报错，不猜。
# ─────────────────────────────────────────────────────────────────────
CATALOG = {
    "squat":       {"zh": "深蹲",      "m": 1.00,  "td": 0.90, "rest": 150, "wpr": 3.5},
    "pause_squat": {"zh": "暂停深蹲",   "m": 1.00,  "td": 0.65, "rest": 120, "wpr": 3.5},
    "front_squat": {"zh": "前蹲",      "m": 0.85,  "td": 0.70, "rest": 120, "wpr": 3.5},
    "dl_conv":     {"zh": "传统硬拉",   "m": 1.00,  "td": 1.00, "rest": 180, "wpr": 3.5},
    "dl_sumo":     {"zh": "相扑硬拉",   "m": 0.90,  "td": 1.00, "rest": 180, "wpr": 3.5},
    "pause_dl":    {"zh": "暂停硬拉",   "m": 0.95,  "td": 0.60, "rest": 90,  "wpr": 3.5},
    "rdl":         {"zh": "RDL",      "m": 0.55,  "td": 0.45, "rest": 90,  "wpr": 3.0},
    "goodmorning": {"zh": "早安式",     "m": 0.45,  "td": 0.50, "rest": 90,  "wpr": 3.0},
    "bench":       {"zh": "卧推",      "m": 0.50,  "td": 0.60, "rest": 150, "wpr": 2.5},
    "cg_bench":    {"zh": "窄距卧推",   "m": 0.42,  "td": 0.40, "rest": 90,  "wpr": 2.5},
    "pause_bench": {"zh": "暂停卧推",   "m": 0.45,  "td": 0.45, "rest": 120, "wpr": 2.5},
    "ohp":         {"zh": "OHP 实力推", "m": 0.40,   "td": 0.70, "rest": 120, "wpr": 2.5},
    "clean":       {"zh": "高翻",      "m": 0.72,   "td": 1.00, "rest": 120, "wpr": 2.0},
    "high_pull":   {"zh": "高拉",      "m": 0.55,   "td": 0.85, "rest": 120, "wpr": 2.0},
    "leg_press":   {"zh": "腿举",      "m": 0.55, "eff": 0.65,   "td": 0.20, "rest": 90,  "wpr": 3.0},
    "row":         {"zh": "划船",      "m": 0.32, "eff": 0.70,   "td": 0.25, "rest": 90,  "wpr": 2.5},
    "pullup":      {"zh": "引体向上",   "m": 0.42, "eff": 0.75,   "td": 0.80, "rest": 150, "wpr": 2.5},
    "face_pull":   {"zh": "面拉",      "m": 0.12, "eff": 0.45,   "td": 0.15, "rest": 75,  "wpr": 2.0},
    "chest_fly":   {"zh": "夹胸",      "m": 0.13, "eff": 0.50,   "td": 0.15, "rest": 75,  "wpr": 2.0},
    "rear_fly":    {"zh": "反飞鸟",     "m": 0.10, "eff": 0.45,   "td": 0.15, "rest": 75,  "wpr": 2.0},
    "lat_raise":   {"zh": "侧平举",     "m": 0.08, "eff": 0.45,   "td": 0.15, "rest": 75,  "wpr": 2.0},
    "pallof":      {"zh": "帕洛夫推",   "m": 0.10, "eff": 0.40,   "td": 0.15, "rest": 75,  "wpr": 2.0},
    "back_ext":    {"zh": "山羊挺身",   "m": 0.25, "eff": 0.40,   "td": 0.20, "rest": 60,  "wpr": 2.5},
    "farmers":     {"zh": "农夫行走",   "m": 0.75, "eff": 0.60,   "td": 0.55, "rest": 90,  "wpr": 4.0},
    "kb_swing":    {"zh": "壶铃摆荡",   "m": 0.62, "eff": 0.60,   "td": 0.50, "rest": 75,  "wpr": 1.5},
}

# 局部协同链：动作 → {肌群: 承担比例}
CHAIN = {
    "squat":       {"quads": 0.78, "glutes": 0.58, "erectors": 0.50, "hams": 0.25},
    "pause_squat": {"quads": 0.78, "glutes": 0.55, "erectors": 0.50, "hams": 0.22},
    "front_squat": {"quads": 0.85, "glutes": 0.45, "erectors": 0.45},
    "leg_press":   {"quads": 0.80, "glutes": 0.55},
    "dl_conv":     {"hams": 0.60, "glutes": 0.70, "erectors": 0.85, "quads": 0.45, "upper_back": 0.40},
    "dl_sumo":     {"glutes": 0.75, "quads": 0.55, "erectors": 0.70, "hams": 0.45, "upper_back": 0.35},
    "pause_dl":    {"hams": 0.65, "glutes": 0.70, "erectors": 0.85, "quads": 0.45, "upper_back": 0.40},
    "rdl":         {"hams": 0.75, "glutes": 0.60, "erectors": 0.70, "upper_back": 0.25},
    "goodmorning": {"hams": 0.60, "erectors": 0.80, "glutes": 0.45},
    "back_ext":    {"erectors": 0.75, "glutes": 0.35, "hams": 0.30},
    "kb_swing":    {"glutes": 0.65, "hams": 0.55, "erectors": 0.55, "core": 0.30},
    "clean":       {"glutes": 0.55, "quads": 0.60, "hams": 0.45, "erectors": 0.60,
                    "upper_back": 0.45, "front_delt": 0.30},
    "high_pull":   {"glutes": 0.45, "quads": 0.40, "upper_back": 0.50,
                    "front_delt": 0.35, "triceps": 0.10},
    "bench":       {"chest": 0.62, "front_delt": 0.32, "triceps": 0.38},
    "pause_bench": {"chest": 0.62, "front_delt": 0.32, "triceps": 0.38},
    "cg_bench":    {"chest": 0.38, "front_delt": 0.22, "triceps": 0.72},
    "ohp":         {"front_delt": 0.68, "triceps": 0.62, "upper_back": 0.18, "core": 0.30},
    "chest_fly":   {"chest": 0.55, "front_delt": 0.22, "triceps": 0.06},
    "lat_raise":   {"side_delt": 0.70, "front_delt": 0.20, "upper_back": 0.15},
    "pullup":      {"lats": 0.78, "biceps": 0.58, "upper_back": 0.38},
    "row":         {"lats": 0.55, "upper_back": 0.52, "biceps": 0.40, "rear_delt": 0.25},
    "face_pull":   {"upper_back": 0.55, "rear_delt": 0.48, "biceps": 0.18},
    "rear_fly":    {"rear_delt": 0.55, "upper_back": 0.35},
    "pallof":      {"core": 0.50},
    "farmers":     {"core": 0.55, "upper_back": 0.45, "quads": 0.30, "glutes": 0.30},
}

# 各动作的主动肌（用于协同比的分子/分母定位）
PRIME = {
    "squat": "quads", "pause_squat": "quads", "front_squat": "quads", "leg_press": "quads",
    "dl_conv": "glutes", "dl_sumo": "glutes", "pause_dl": "glutes", "clean": "glutes",
    "rdl": "hams", "goodmorning": "hams", "back_ext": "erectors", "kb_swing": "hams",
    "high_pull": "upper_back",
    "bench": "chest", "pause_bench": "chest", "chest_fly": "chest",
    "cg_bench": "triceps", "ohp": "front_delt", "lat_raise": "side_delt",
    "row": "upper_back", "pullup": "lats",
    "face_pull": "rear_delt", "rear_fly": "rear_delt",
    "pallof": "core", "farmers": "core",
}

MUSCLE_ZH = {
    "chest": "胸", "front_delt": "前三角", "side_delt": "中三角", "rear_delt": "后三角",
    "triceps": "三头", "lats": "背阔", "upper_back": "上背", "biceps": "肱二头",
    "quads": "股四", "glutes": "臀", "hams": "腘绳", "erectors": "竖脊", "core": "核心",
}

# ── 别名表：中文名 / 常见英文写法 → 动作库 key ────────────────────────
# 输入 JSON 里的 exercise 字段走这一层归一，中文也能直接写。
ALIASES = {
    "squat": "squat", "深蹲": "squat", "back squat": "squat", "颈后深蹲": "squat",
    "pause_squat": "pause_squat", "暂停深蹲": "pause_squat", "pause squat": "pause_squat",
    "front_squat": "front_squat", "前蹲": "front_squat", "front squat": "front_squat",
    "dl_conv": "dl_conv", "传统硬拉": "dl_conv", "硬拉": "dl_conv", "deadlift": "dl_conv",
    "conventional deadlift": "dl_conv", "conventional dl": "dl_conv",
    "dl_sumo": "dl_sumo", "相扑硬拉": "dl_sumo", "相扑拉": "dl_sumo", "sumo deadlift": "dl_sumo",
    "pause_dl": "pause_dl", "暂停硬拉": "pause_dl", "pause deadlift": "pause_dl",
    "rdl": "rdl", "罗马尼亚硬拉": "rdl", "直腿硬拉": "rdl", "romanian deadlift": "rdl",
    "goodmorning": "goodmorning", "早安式": "goodmorning", "good morning": "goodmorning",
    "bench": "bench", "卧推": "bench", "bench press": "bench", "bp": "bench",
    "pause_bench": "pause_bench", "暂停卧推": "pause_bench", "pause bench": "pause_bench",
    "cg_bench": "cg_bench", "窄距卧推": "cg_bench", "窄推": "cg_bench",
    "close grip bench": "cg_bench", "close-grip bench": "cg_bench", "cgbp": "cg_bench",
    "ohp": "ohp", "实力推": "ohp", "肩推": "ohp", "站姿推举": "ohp",
    "overhead press": "ohp", "press": "ohp", "strict press": "ohp",
    "clean": "clean", "高翻": "clean", "power clean": "clean",
    "high_pull": "high_pull", "高拉": "high_pull", "high pull": "high_pull",
    "leg_press": "leg_press", "腿举": "leg_press", "leg press": "leg_press",
    "row": "row", "划船": "row", "杠铃划船": "row", "barbell row": "row",
    "pullup": "pullup", "引体向上": "pullup", "引体": "pullup", "pull up": "pullup",
    "pull-up": "pullup", "chin up": "pullup", "chinup": "pullup",
    "face_pull": "face_pull", "面拉": "face_pull", "face pull": "face_pull",
    "chest_fly": "chest_fly", "夹胸": "chest_fly", "飞鸟": "chest_fly", "chest fly": "chest_fly",
    "rear_fly": "rear_fly", "反飞鸟": "rear_fly", "反向飞鸟": "rear_fly",
    "rear delt fly": "rear_fly", "rear fly": "rear_fly",
    "lat_raise": "lat_raise", "侧平举": "lat_raise", "lateral raise": "lat_raise",
    "pallof": "pallof", "帕洛夫推": "pallof", "帕洛夫": "pallof", "pallof press": "pallof",
    "back_ext": "back_ext", "山羊挺身": "back_ext", "背屈伸": "back_ext",
    "back extension": "back_ext",
    "farmers": "farmers", "农夫行走": "farmers", "农夫走": "farmers",
    "farmer carry": "farmers", "farmers walk": "farmers", "farmer walk": "farmers",
    "kb_swing": "kb_swing", "壶铃摆荡": "kb_swing", "壶铃摇摆": "kb_swing",
    "kettlebell swing": "kb_swing", "kb swing": "kb_swing",
}

# 自定义动作（catalog 里新增）允许/必需的字段
#   必需: m（肌肉质量系数）、td（技术需求）、以及 ref（有外部负重）或 eff（自重的等效强度）二选一
#   可选: zh（显示名）、rest、wpr、chain（{肌群: 承担比例}）、prime（主动肌）
EXTRA_KEYS = ("zh", "m", "ref", "td", "eff", "rest", "wpr", "chain", "prime")
EXTRA_DEFAULTS = {"rest": 90, "wpr": 3.0}

# ── 内置估算参数（工程值，非文献值；标定后覆盖）──────────────────────
BUILTIN_PARAMS = {
    "beta": 0.75,           # 累积放大上限
    "a_ref": 8.0,           # 放大半饱和点
    "tau_fast": 60.0,       # 快池恢复时间常数（秒）
    "tau_slow": 720.0,      # 慢池恢复时间常数（秒）
    "transition": 120.0,    # 动作间转换默认间隔（秒）
    "reps_ref": 8.0,        # 次数效应基准
    "reps_pow": 0.75,       # 次数效应幂次
    "intensity_ref": 0.7,   # 相对强度基准（70% 1RM 记 1.0）
}

SOURCE_LABEL = {
    "estimate": "内置估算值（未标定）",
    "calibrated": "sRPE 标定值",
    "user": "用户自备参数",
}
SOURCE_ORDER = {"estimate": 0, "calibrated": 1, "user": 2}

# ── 模型分辨率 ────────────────────────────────────────────────────────
# A 的有效分辨率为 1%（跨全部可能排列实测极差 <0.7%，参数本身的不确定度是 ±100% 量级）。
# 因此：
#   · 只报整数刻度，不报小数（小数位是运算过程的精度，不是模型的精度）
#   · 差异 <1% 一律判为"不可分辨"，即视为相等
# 这条约定的直接后果：'顺序不影响总量、只转移代价'在模型分辨率内严格成立。
RESOLUTION_PCT = 1.0


# ─────────────────────────────────────────────────────────────────────
# 参数配置（三层：内置估算 < params 文件 < 输入文件；CLI 最高）
# ─────────────────────────────────────────────────────────────────────
def default_config():
    return {"profile": "builtin-estimate",
            "source": "estimate",
            "note": "",
            "params": dict(BUILTIN_PARAMS),
            "one_rm": {},
            "catalog": {}}


def merge_config(cfg, override):
    """把 override 合并进 cfg（返回新 dict，不改原对象）。"""
    if not override:
        return cfg
    out = {"profile": cfg["profile"], "source": cfg["source"], "note": cfg["note"],
           "params": dict(cfg["params"]), "one_rm": dict(cfg["one_rm"]),
           "catalog": {k: dict(v) for k, v in cfg["catalog"].items()}}
    for field in ("profile", "note"):
        if override.get(field):
            out[field] = override[field]
    if override.get("source"):
        src = override["source"]
        if src not in SOURCE_LABEL:
            raise ValueError(f"source 需为 estimate/calibrated/user，收到 '{src}'")
        # 只向上升级来源标签，不被低层覆盖
        if SOURCE_ORDER[src] >= SOURCE_ORDER[out["source"]]:
            out["source"] = src
    for k, v in (override.get("params") or {}).items():
        if k not in BUILTIN_PARAMS:
            raise ValueError(f"未知参数 '{k}'。可用：{', '.join(sorted(BUILTIN_PARAMS))}")
        out["params"][k] = float(v)
    # catalog 先处理：它可能新增动作，后面的 one_rm / 输入校验都要看见这些新 key
    for raw_k, v in (override.get("catalog") or {}).items():
        # 已登记的 key / 别名 -> 归一到官方 key；否则视为"新增动作"，原样采用
        if isinstance(raw_k, str) and raw_k in valid_keys(out) | set(ALIASES):
            k = normalize_key(raw_k, out)
        else:
            k = raw_k.strip() if isinstance(raw_k, str) else raw_k
        if not isinstance(k, str) or not k:
            raise ValueError("catalog 的动作 key 不能为空")
        if not isinstance(v, dict):
            raise ValueError(f"catalog['{k}'] 应为对象")
        payload = {kk: vv for kk, vv in v.items() if kk in EXTRA_KEYS}
        if k in CATALOG:                      # 调参：允许只给部分字段
            out["catalog"].setdefault(k, {}).update(payload)
            continue
        # 新增动作：必填校验，避免建出一个算不动的空壳
        missing = [f for f in ("m", "td") if f not in payload]
        if "ref" not in payload and "eff" not in payload:
            missing.append("ref 或 eff（有外部负重给 ref=参考1RM，自重给 eff=等效强度）")
        if missing:
            raise ValueError("新增动作 '%s' 缺必需字段：%s" % (k, "；".join(missing)))
        if bool(payload.get("prime")) != bool(payload.get("chain")):
            raise ValueError("新增动作 '%s' 的 chain 与 prime 必须成对给出（协同比要用）" % k)
        out["catalog"].setdefault(k, {}).update(payload)
    for k, v in (override.get("one_rm") or {}).items():
        k = normalize_key(k, out)
        if k not in valid_keys(out):
            raise ValueError(f"one_rm 含未知动作 '{k}'。注意用动作库 key"
                             f"（硬拉为 dl_conv 传统 / dl_sumo 相扑）。可用："
                             f"{', '.join(sorted(valid_keys(out)))}")
        if v is not None:
            out["one_rm"][k] = float(v)
    return out


def valid_keys(cfg=None):
    """可用动作 key = 内置动作库 + 本配置里新增的自定义动作。"""
    extra = set((cfg or {}).get("catalog", {}))
    return set(CATALOG) | extra


def normalize_key(name, cfg=None):
    """把用户写的动作名归一成动作库 key：先查库、再查别名、再模糊建议。"""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("exercise 字段为空")
    raw = name.strip()
    if raw in valid_keys(cfg):
        return raw
    low = " ".join(raw.lower().replace("-", " ").replace("_", " ").split())
    if low in valid_keys(cfg):
        return low
    if low.replace(" ", "_") in valid_keys(cfg):
        return low.replace(" ", "_")
    hit = ALIASES.get(raw) or ALIASES.get(low) or ALIASES.get(low.replace(" ", "_"))
    if hit is not None and (cfg is None or hit in valid_keys(cfg)):
        return hit
    near = difflib.get_close_matches(raw, sorted(valid_keys(cfg)), n=3, cutoff=0.5)
    tip = "；是想写 %s 吗" % " / ".join(near) if near else ""
    raise ValueError("未知动作 '%s'%s。库里没有的动作可在输入 JSON 的 catalog 里新增"
                     "（必填 m、td，以及 ref 或 eff 之一）。已有 key：%s"
                     % (name, tip, ", ".join(sorted(valid_keys(cfg)))))


def spec_of(key, cfg):
    """合并后的动作参数（内置 + 新增/覆盖）。"""
    if key in CATALOG:
        spec = dict(CATALOG[key])
        spec.update(cfg["catalog"].get(key, {}))
    else:
        spec = dict(EXTRA_DEFAULTS)
        spec.update(cfg["catalog"][key])
        spec.setdefault("zh", key)
    if key in cfg["one_rm"]:
        spec["ref"] = cfg["one_rm"][key]
    return spec


def zh_of(key, cfg):
    """显示名：中文名 -> key -> 英文名，逐级回退。"""
    spec = spec_of(key, cfg)
    return spec.get("zh") or key


def muscle_zh(m):
    return MUSCLE_ZH.get(m, m)


def chain_profile(key, cfg):
    return spec_of(key, cfg).get("chain") or CHAIN.get(key)


def prime_of(key, cfg):
    return spec_of(key, cfg).get("prime") or PRIME.get(key)


# ─────────────────────────────────────────────────────────────────────
# 模型
# ─────────────────────────────────────────────────────────────────────
NO_REF_HINT = ("%s 缺参考 1RM —— 动作库不再内置默认值。请通过 --params 文件、"
               "输入 JSON 的 one_rm 提供，例如 {\"one_rm\": {\"%s\": 100}}；"
               "也可先跑 --init-params 导出模板再填。")


def _intensity(key, weight, cfg):
    spec = spec_of(key, cfg)
    ref = spec.get("ref")
    if ref is None:
        eff = spec.get("eff")
        if eff is None:                      # 外部负重动作，但没人给参考 1RM
            raise ValueError(NO_REF_HINT % (key, key))
        if weight is not None:
            raise ValueError(f"{key} 为自重动作，不接受 weight")
        return eff
    if weight is None:
        raise ValueError(f"{key} 需要 weight（当前参考 1RM={ref}）")
    return weight / ref


def unit_load(key, reps, weight, cfg):
    """单组基础应激（未计累积放大）。"""
    p = cfg["params"]
    return (spec_of(key, cfg)["m"]
            * (reps / p["reps_ref"]) ** p["reps_pow"]
            * (_intensity(key, weight, cfg) / p["intensity_ref"]) ** 1.6)


def simulate(blocks, cfg):
    """跑一次 session。返回 A / Rf 峰值 / 时长 / 每动作明细 / 逐组曲线。

    明细按**动作位置**索引（同一动作在一次课里出现两次时各占一行）。
    每个 block 至少要有 exercise / sets / reps；rest 与 work_per_rep 缺省取动作库值，
    weight 缺省为 None（自重动作本就不该给）。
    """
    p = cfg["params"]
    F = S = A = 0.0
    rf_peak = 0.0
    t = 0.0
    per = []
    timeline = []

    for idx, b in enumerate(blocks):
        key = b["exercise"]
        spec = spec_of(key, cfg)
        sets, reps = b["sets"], b["reps"]
        weight = b.get("weight")
        rest = b.get("rest") if b.get("rest") is not None else spec["rest"]
        wpr = b.get("work_per_rep") if b.get("work_per_rep") is not None else spec["wpr"]
        lb = unit_load(key, reps, weight, cfg)
        rec = {"index": idx, "exercise": key, "unit": lb, "eff": 0.0, "sets": 0,
               "rf_start": None, "rf_peak": 0.0, "weight": weight, "penalty": 1.0}
        for i in range(sets):
            if not (idx == 0 and i == 0):
                F *= math.exp(-rest / p["tau_fast"])
                S *= math.exp(-rest / p["tau_slow"])
                t += rest
            rf0 = F + S
            if i == 0:
                rec["rf_start"] = rf0
            amp = 1.0 + p["beta"] * (1.0 - math.exp(-A / p["a_ref"]))
            leff = lb * amp
            F += leff * 0.55
            S += leff * 0.45
            A += leff
            rf1 = F + S
            rec["eff"] += leff
            rec["sets"] += 1
            rec["rf_peak"] = max(rec["rf_peak"], rf1)
            rf_peak = max(rf_peak, rf1)
            t += reps * wpr
            timeline.append({"index": idx, "exercise": key, "set": i + 1, "rf": rf1,
                             "load_eff": leff, "amp": amp, "min": t / 60.0})
        rec["penalty"] = rec["eff"] / (lb * sets) if sets else 1.0
        per.append(rec)
        F *= math.exp(-p["transition"] / p["tau_fast"])
        S *= math.exp(-p["transition"] / p["tau_slow"])
        t += p["transition"]

    return {"A": A, "rf_peak": rf_peak, "duration_min": t / 60.0,
            "per": per, "timeline": timeline}


def chain_analysis(blocks, cfg):
    """协同链：动作开始前，主动肌 / 主协同肌各自已积累的等效组。

    返回 (rows, accum, untracked)。rows **按 blocks 位置一一对应**（无档案处为 None），
    这样调用方不能用位置错配去索引。untracked 是缺链条档案、没被计入 accum 的动作。
    """
    accum = {}
    rows = []
    untracked = []
    for b in blocks:
        key = b["exercise"]
        spec = spec_of(key, cfg)
        prof = spec.get("chain") or CHAIN.get(key)
        if prof is None:
            rows.append(None)
            if key not in untracked:
                untracked.append(key)
            continue
        sets = b["sets"]
        prime = spec.get("prime") or PRIME.get(key)
        if prime is None:
            rows.append(None)
            if key not in untracked:
                untracked.append(key)
            continue
        syn = sorted(((m, c) for m, c in prof.items() if m != prime and c >= 0.25),
                     key=lambda t: -t[1])
        p_acc = accum.get(prime, 0.0)
        if syn:
            syn_m = syn[0][0]
            s_acc = accum.get(syn_m, 0.0)
            ratio = (s_acc / p_acc) if p_acc > 0 else None
        else:
            syn_m, s_acc, ratio = None, 0.0, None
        if ratio is None:
            verdict = "主动肌首次使用" if s_acc > 0 else "新鲜"
        elif ratio >= 1.5 and s_acc >= 3:
            verdict = f"链条受限：限制环节是 {muscle_zh(syn_m)}"
        elif ratio >= 1.2:
            verdict = "边缘"
        else:
            verdict = "主动肌仍是限制环节"
        rows.append({"exercise": key, "sets": sets, "prime": prime, "synergist": syn_m,
                     "prime_depth": p_acc, "syn_depth": s_acc, "ratio": ratio,
                     "verdict": verdict})
        for m, c in prof.items():
            accum[m] = accum.get(m, 0.0) + sets * c
    return rows, accum, untracked


# ─────────────────────────────────────────────────────────────────────
# 输入解析
# ─────────────────────────────────────────────────────────────────────
def parse_session(obj, index, cfg):
    name = obj.get("name") or f"session {index + 1}"
    blocks = []
    for pos, raw in enumerate(obj.get("blocks", []) or []):
        key = normalize_key(raw.get("exercise"), cfg)
        for f in ("sets", "reps"):
            if raw.get(f) is None:
                raise ValueError("%s 第 %d 个动作 '%s' 缺 %s" % (name, pos + 1, key, f))
        blocks.append({
            "exercise": key,
            "sets": int(raw["sets"]),
            "reps": int(raw["reps"]),
            "weight": raw.get("weight"),
            "rest": raw.get("rest"),
            "work_per_rep": raw.get("work_per_rep"),
        })
    if not blocks:
        raise ValueError(f"{name}: blocks 为空")
    return {"name": name, "blocks": blocks}


def load_input(path, base_cfg=None):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    cfg = merge_config(base_cfg or default_config(), data)
    if "sessions" in data:
        raw_sessions = data["sessions"]
    elif "blocks" in data:
        raw_sessions = [data]
    else:
        raise ValueError("输入需含 sessions 数组或单个 blocks")
    return [parse_session(s, i, cfg) for i, s in enumerate(raw_sessions)], cfg, data.get("anchor")


# ─────────────────────────────────────────────────────────────────────
# 报告
# ─────────────────────────────────────────────────────────────────────
def ssi_legend(anchor_is_custom):
    base = "  读法（A%，以一次「已完成且恢复过来」的课为锚点）:"
    if not anchor_is_custom:
        base = "  读法（A% 目前是本文件内的相对刻度，不是绝对阈值）:"
    return [base,
            "    <= 60    有余量，可以加",
            "    60 - 85  正常",
            "    85 - 100 接近已验证的恢复上限：只重排，不净增",
            "    > 100    未验证区。不是危险，是你没做过，不免费"]


def render(sessions, cfg, anchor, curve=False):
    out = []
    results = []
    for s in sessions:
        r = simulate(s["blocks"], cfg)
        rows, accum, untracked = chain_analysis(s["blocks"], cfg)
        results.append({"session": s, "sim": r, "chain": rows, "accum": accum,
                        "untracked": untracked})

    anchor_is_custom = anchor is not None
    if anchor is None:
        anchor = max(x["sim"]["A"] for x in results)
        anchor_note = "以本文件最高者 A=%.2f 为 100（文件内相对刻度）" % anchor
    else:
        anchor_note = "锚点 A=%.2f（自定义）" % anchor

    out.append("=" * 92)
    out.append("单次训练应激（A 系统应激 / Rf 峰值 / 排布质量）")
    out.append("=" * 92)
    out.append("")
    out.append("参数: profile=%s  来源=%s" % (cfg["profile"], SOURCE_LABEL[cfg["source"]]))
    out.append("      beta=%(beta).2f  a_ref=%(a_ref).1f  tau=%(tau_fast).0f/%(tau_slow).0fs"
               % cfg["params"])
    if cfg["one_rm"]:
        out.append("      1RM 覆盖: " + "  ".join(
            "%s=%g" % (zh_of(k, cfg), v) for k, v in sorted(cfg["one_rm"].items())))
    if cfg["catalog"]:
        tuned = [k for k in cfg["catalog"] if k in CATALOG]
        added = [k for k in cfg["catalog"] if k not in CATALOG]
        seg = []
        if added:
            seg.append("新增动作 %s" % " / ".join(zh_of(k, cfg) for k in sorted(added)))
        if tuned:
            seg.append("覆写参数 %s" % " / ".join(zh_of(k, cfg) for k in sorted(tuned)))
        out.append("      自定义: " + "；".join(seg))
    if cfg["note"]:
        out.append("      备注: " + cfg["note"])
    if cfg["source"] == "estimate":
        out.append("      ⚠ 估算参数只支持同文件内的相对比较，不给绝对阈值（标定见引用文件）")
    out.append("刻度: " + anchor_note)
    out.append("分辨率: %g%%（差异 <%.0f%% 视为相等；A 只读整数刻度，小数位是运算精度不是模型精度）"
               % (RESOLUTION_PCT, RESOLUTION_PCT))
    out.append("")
    out.append("%-30s%9s%8s%9s%9s%9s" % ("训练课", "A", "A%", "Rf峰值", "时长min", "动作数"))
    out.append("-" * 92)
    for x in results:
        s, r = x["session"], x["sim"]
        out.append("%-30s%9.2f%8.0f%9.2f%9.1f%9d"
                   % (s["name"], r["A"], r["A"] / anchor * 100, r["rf_peak"],
                      r["duration_min"], len(s["blocks"])))
    out.append("")

    for x in results:
        s, r, rows, accum = x["session"], x["sim"], x["chain"], x["accum"]
        out.append("=" * 92)
        out.append("%s   A=%.2f (A%%=%.0f)   Rf峰值=%.2f   时长=%.1fmin"
                   % (s["name"], r["A"], r["A"] / anchor * 100, r["rf_peak"], r["duration_min"]))
        out.append("=" * 92)
        out.append("顺序: " + " -> ".join(
            "%s %dx%d" % (zh_of(b["exercise"], cfg), b["sets"], b["reps"]) for b in s["blocks"]))
        out.append("")
        out.append("%-13s%4s%9s%8s%9s%9s%8s  %s"
                   % ("动作", "组", "起始Rf", "惩罚", "技术需求", "崩坏风险", "协同比", "判读"))
        out.append("-" * 92)
        for i, b in enumerate(s["blocks"]):
            key = b["exercise"]
            spec = spec_of(key, cfg)
            v = r["per"][i]
            row = rows[i]
            br = spec["td"] * v["penalty"]
            flag = "高" if br >= 1.6 else ("中" if br >= 1.2 else "")
            ratio = "n/a" if (row is None or row["ratio"] is None) else "%.2f" % row["ratio"]
            verdict = "" if row is None else row["verdict"]
            out.append("%-13s%4d%9.2f%8.2f%9.2f%9s%8s  %s"
                       % (zh_of(key, cfg), b["sets"], v["rf_start"], v["penalty"],
                          spec["td"], "%.2f %s" % (br, flag), ratio, verdict))
        out.append("")
        if x["untracked"]:
            out.append("⚠ 无链条档案（未计入下方等效组，也不参与协同比）：%s。"
                       "补档案 = 在 catalog 里给该动作加 chain + prime。"
                       % " / ".join(zh_of(k, cfg) for k in x["untracked"]))
        out.append("课末肌群等效组（降序）: " + "  ".join(
            "%s %.2f" % (muscle_zh(m), v) for m, v in
            sorted(accum.items(), key=lambda t: -t[1]) if v > 0))
        out.append("")

    worst = max(results, key=lambda x: x["sim"]["A"])
    out.append("-" * 92)
    out.append("最高 A: %s (%.2f)。A 只抓「整个人剩多少」，链条受限动作见上表判读列。"
               % (worst["session"]["name"], worst["sim"]["A"]))
    out.append("")
    out.extend(ssi_legend(anchor_is_custom))
    out.append("")
    out.append("崩坏风险 = 技术需求 x 惩罚。>= 1.6 高（动作质量大概率走样）；>= 1.2 中（需留意）。")
    out.append("协同比 >= 1.5 且协同深度 >= 3 = 这个动作练到的是协同肌的极限，不是主动肌。")

    if curve:
        out.append("")
        out.append("逐组曲线")
        out.append("-" * 92)
        for x in results:
            out.append("【%s】" % x["session"]["name"])
            out.append("%-13s%4s%8s%9s%7s%7s  %s"
                       % ("动作", "组", "Rf", "L_eff", "放大", "min", "柱"))
            for e in x["sim"]["timeline"]:
                out.append("%-13s%4d%8.2f%9.3f%7.2f%7.1f  %s"
                           % (zh_of(e["exercise"], cfg), e["set"], e["rf"],
                              e["load_eff"], e["amp"], e["min"], "#" * int(e["rf"] * 4)))
            out.append("")
    return "\n".join(out), results, anchor


def to_json(results, cfg, anchor):
    payload = {"anchor": anchor,
               "config": {"profile": cfg["profile"], "source": cfg["source"],
                          "calibrated": cfg["source"] != "estimate",
                          "params": cfg["params"], "one_rm": cfg["one_rm"],
                          "custom_exercises": sorted(k for k in cfg["catalog"]
                                                     if k not in CATALOG)},
               "sessions": []}
    for x in results:
        s, r = x["session"], x["sim"]
        items = []
        for i, b in enumerate(s["blocks"]):
            key = b["exercise"]
            spec = spec_of(key, cfg)
            v = r["per"][i]
            row = x["chain"][i] or {}
            items.append({
                "exercise": key, "zh": zh_of(key, cfg),
                "sets": b["sets"], "reps": b["reps"],
                "weight": v["weight"],
                "rf_start": round(v["rf_start"], 3),
                "penalty": round(v["penalty"], 3),
                "tech_demand": spec["td"],
                "break_risk": round(spec["td"] * v["penalty"], 3),
                "chain_ratio": None if row.get("ratio") is None else round(row["ratio"], 3),
                "chain_verdict": row.get("verdict"),
            })
        payload["sessions"].append({
            "name": s["name"],
            "A": round(r["A"], 3),
            "A_pct": round(r["A"] / anchor * 100, 1),
            "rf_peak": round(r["rf_peak"], 3),
            "duration_min": round(r["duration_min"], 1),
            "exercises": items,
            "untracked_exercises": [{"exercise": k, "zh": zh_of(k, cfg)}
                                    for k in x["untracked"]],
            "muscle_equivalent_sets": {k: round(v, 2) for k, v in x["accum"].items() if v > 0},
        })
    return json.dumps(payload, ensure_ascii=False, indent=2)


def init_params(path):
    """导出可编辑的参数模板（用户可改成自己的长期参数集）。

    one_rm 列出**所有需要外部负重的动作**（值为 null，待填），填完即可原样回填给 --params；
    自重动作（带 eff 的）不需要 1RM，不列入。
    （硬拉的键是 dl_conv / dl_sumo，不是 deadlift。中文名与常见英文别名也能直接用。）
    """
    one_rm = {k: None for k in sorted(CATALOG) if CATALOG[k].get("eff") is None}
    tpl = {"profile": "my-params",
           "source": "user",
           "note": "在此填写参数来源与标定日期。one_rm 用动作库 key"
                   "（深蹲 squat / 卧推 bench / 硬拉 dl_conv 传统·dl_sumo 相扑 /"
                   " OHP ohp）。**只有填了数值的项才生效**——留 null 的动作在被用到时会报错。"
                   "catalog 可用来调参或新增动作，字段见 session-strain-modeling.md。",
           "one_rm": one_rm,
           "params": dict(BUILTIN_PARAMS),
           "catalog": {}}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tpl, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("已写出参数模板 -> %s（one_rm 列出 %d 个需外部负重的动作，填上你的成绩后再用；"
          "不用的项可以删掉）" % (path, len(one_rm)))


DEMO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "examples", "session_strain_sample.json")


def main():
    ap = argparse.ArgumentParser(description="单次训练应激三轴计算器")
    ap.add_argument("--input", help="输入 JSON 路径")
    ap.add_argument("--params", help="参数集 JSON 路径（覆盖内置估算值）")
    ap.add_argument("--demo", action="store_true", help="跑自带样例")
    ap.add_argument("--list", action="store_true", help="列出动作库 key")
    ap.add_argument("--init-params", metavar="PATH", help="导出可编辑的参数模板")
    ap.add_argument("--anchor", type=float, help="自定义锚点 A（用于 A%% 刻度）")
    ap.add_argument("--beta", type=float, help="覆盖累积放大上限")
    ap.add_argument("--a-ref", type=float, help="覆盖放大半饱和点")
    ap.add_argument("--curve", action="store_true", help="打印逐组曲线")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    if args.init_params:
        init_params(args.init_params)
        return 0

    if args.list:
        cfg0 = default_config()
        for k in sorted(CATALOG):
            spec = spec_of(k, cfg0)
            if spec.get("ref") is not None:
                load = "%g" % spec["ref"]
            elif spec.get("eff") is not None:
                load = "自重(eff=%.2f)" % spec["eff"]
            else:
                load = "需自备 1RM"
            print("%-13s %-11s m=%.2f  参考=%s  td=%.2f" % (k, spec["zh"], spec["m"], load, spec["td"]))
        print("")
        print("内置动作 %d 个；除 key 外，中文名与常见英文写法也可直接写在 exercise 字段"
              "（如 深蹲 / deadlift / RDL / 引体 / 实力推）。" % len(CATALOG))
        print("外部负重动作必须先给参考 1RM：用 --init-params 导出模板填写，"
              "或用 --params / 输入 JSON 的 one_rm。缺失时会报错并给出示例。")
        print("需要库里没有的动作：在输入 JSON 的 catalog 里新增，必填 m、td，"
              "以及 ref（外部负重）或 eff（自重）之一；可选 zh / rest / wpr / chain / prime。")
        return 0

    path = DEMO_PATH if args.demo else args.input
    if not path:
        ap.error("需要 --input <file> 或 --demo")
    if not os.path.exists(path):
        print("找不到输入文件: %s" % path, file=sys.stderr)
        return 1

    cfg = default_config()
    if args.params:
        if not os.path.exists(args.params):
            print("找不到参数文件: %s" % args.params, file=sys.stderr)
            return 1
        with open(args.params, encoding="utf-8") as fh:
            cfg = merge_config(cfg, json.load(fh))

    try:
        sessions, cfg, anchor = load_input(path, cfg)
    except ValueError as e:
        print("输入错误: %s" % e, file=sys.stderr)
        return 1

    cli = {}
    if args.beta is not None:
        cli["params"] = {**cli.get("params", {}), "beta": args.beta}
    if args.a_ref is not None:
        cli["params"] = {**cli.get("params", {}), "a_ref": args.a_ref}
    if cli:
        cfg = merge_config(cfg, cli)
    if args.anchor is not None:
        anchor = args.anchor

    try:
        text, results, anchor = render(sessions, cfg, anchor, curve=args.curve)
    except ValueError as e:          # 缺参考 1RM / 自重动作给了 weight 等，给可读提示而非回溯
        print("输入错误: %s" % e, file=sys.stderr)
        return 1
    if args.json:
        print(to_json(results, cfg, anchor))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ─────────────────────────────────────────────────────────────────────
# 扩展动作库
#
# 一、动作名怎么写
#   exercise 字段接受三类写法，都会自动归一成动作库 key：
#     ① 库内 key（squat / dl_sumo / rdl ...）
#     ② 中文名（深蹲 / 相扑硬拉 / 窄距卧推 / 引体 ...）
#     ③ 常见英文写法（deadlift / bench press / pull up / RDL / close grip bench ...）
#   匹配不上时报错并给出最接近的候选，不会静默取错动作。
#   别名表见本文件 ALIASES。
#
# 二、库里没有的动作怎么办
#   不需要改本文件——在输入 JSON（或 --params 文件）里用 catalog 新增即可：
#
#     "catalog": {
#       "muscle_up": {
#         "zh": "双力臂", "m": 0.45, "eff": 0.85, "td": 0.85,
#         "rest": 150, "wpr": 2.5,
#         "chain": {"lats": 0.75, "biceps": 0.55, "upper_back": 0.40},
#         "prime": "lats"
#       }
#     }
#
#   必填：m（肌肉质量系数，1.0 ≈ 深蹲/硬拉量级）、td（技术需求 0-1）、
#         以及 ref（有外部负重，给参考 1RM 的绝对重量）或 eff（自重动作的等效强度 0-1）二选一。
#         ⚠ 内置动作库同样不预置 ref——自重动作靠 eff，外部负重动作必须由调用方给 1RM。
#   可选：zh 显示名、rest 组间秒、wpr 每次秒、chain 各肌群承担比例、prime 主动肌。
#   若两者给了 chain 却没给 prime（或反之）——协同比算不出来，脚本直接报错而不是硬凑。
#
# 三、缺 chain 档案的后果（脚本会显式提示，不静默跳过）
#   A / Rf / 惩罚 / 崩坏风险照常算（只依赖 m / ref / td）；
#   但该动作不计入「课末肌群等效组」，协同比列为 n/a——
#   报告里会出现「⚠ 无链条档案」提示，看到它就知道等效组被低估了。
# ─────────────────────────────────────────────────────────────────────
