#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conftest for design_program.py 测试固件。
把 <skill根>/scripts/ 目录加入 sys.path，使测试能 import design_program 及其依赖脚本
（rpe_to_percentage / round_weight / calculate_mrv）。
本文件位于 dev/tests/，故 scripts 目录为 上两级 + scripts/。
"""
import os
import sys

_DEV_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dev/
_SKILL_ROOT = os.path.dirname(_DEV_DIR)                                  # skill 根
_SCRIPTS_DIR = os.path.join(_SKILL_ROOT, "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import design_program as dp  # noqa: E402

# 共享的示例 one_rm（与 c2_w3_sample.yaml 一致）
SAMPLE_ONE_RM = {
    "squat": 145,
    "bench": 105,
    "deadlift": 157.5,
    "ohp": 62.5,
    "hang_power_clean": 57.5,
    "hang_high_pull": 40,
    "pause_squat": 95,
    "rdl": 80,
    "pullup": 0,  # 自重，仅审计组数
}


def make_week(week_structure, **overrides):
    """构造最小可跑的 YAML dict（不写文件，直接喂 run_base）。"""
    base = {
        "template": "upper_lower",
        "one_rm": SAMPLE_ONE_RM,
        "week_structure": week_structure,
        "intent": {"phase": "volume"},
        "plate_step": 2.5,
    }
    base.update(overrides)
    return base
