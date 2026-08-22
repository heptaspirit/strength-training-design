#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试：用真实 C2 W3 样例（c2_w3_sample.yaml）跑 design_program，
验证通用边界（主项/奥举/辅助/自重/RDL 后侧链）全部正确且合规全绿。
"""
import os

from conftest import _SCRIPTS_DIR
from design_program import load_input, run_base, run_modules

SAMPLE = os.path.join(_SCRIPTS_DIR, "examples", "c2_w3_sample.yaml")  # scripts/examples/


def test_c2_w3_sample_runs_clean():
    assert os.path.exists(SAMPLE), f"样例缺失: {SAMPLE}"
    data = load_input(SAMPLE)
    result = run_base(data)
    result = run_modules(data, result, {ex: data["one_rm"][ex] for ex in data["one_rm"]})

    # 1) 关键动作重量正确（向下取整到 plate_step）
    by_ex = {l["exercise"]: l for l in result["lifts"]}
    assert by_ex["squat"]["weight"] == 100.0            # 145 * 0.69 = 100.05 → 100
    assert by_ex["bench"]["weight"] == 70.0             # 105 * 0.69 = 72.45 → 70
    assert by_ex["ohp"]["weight"] == 40.0               # 60 * 0.68 = 40.8 → 40
    assert by_ex["hang_power_clean"]["weight"] == 62.5  # 157.5*0.41=64.575 → 62.5（兜底 DL）
    assert by_ex["pullup"]["weight"] is None            # 自重

    # 2) 合规全绿（无 error、无 warning）
    assert result["compliance"]["errors"] == [], result["compliance"]["errors"]
    assert result["compliance"]["warnings"] == [], result["compliance"]["warnings"]

    # 3) RDL 周一距周四硬拉 3 天 → 放行（不应出现在 warnings）
    # （已由上一条 warnings==[] 覆盖）

    # 4) 退出码语义：无 error → 0
    assert not result["compliance"]["errors"]
