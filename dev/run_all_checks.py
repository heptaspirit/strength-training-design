#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strength-training-design skill — 统一工程检查入口（P0 + P1）

串联：
  - P0: check_links.py（引用完整性）
  - P0: check_version.py --check-tag（版本一致性 + tag 存在）
  - P1: pytest tests/（设计器确定性逻辑固件）

退出码：任一子检查非 0 则整体非 0（可 gate CI / pre-commit）。

维护者专用：普通 skill 使用者无需运行本脚本。

用法：
  python dev/run_all_checks.py
  python dev/run_all_checks.py --skip-tests   # 仅跑 P0
  python dev/run_all_checks.py --skip-p0      # 仅跑 P1
"""
import argparse
import os
import subprocess
import sys

# 本文件位于 dev/，check 脚本与 tests/ 同目录
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _run(cmd):
    print(f"\n{'='*60}\n$ {' '.join(cmd)}\n{'='*60}")
    return subprocess.run(cmd, cwd=_SCRIPT_DIR, env={**os.environ,
                          "PYTHONPATH": _SCRIPT_DIR}).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-tests", action="store_true", help="跳过 P1 pytest")
    ap.add_argument("--skip-p0", action="store_true", help="跳过 P0 link/version 检查")
    ap.add_argument("--python", default=sys.executable, help="python 解释器路径")
    args = ap.parse_args()

    py = args.python
    failures = []

    # ── P0 ──
    if not args.skip_p0:
        rc = _run([py, "check_links.py"])
        if rc != 0:
            failures.append("check_links")
        rc = _run([py, "check_version.py", "--check-tag"])
        if rc != 0:
            failures.append("check_version")

    # ── P1 ──
    if not args.skip_tests:
        rc = _run([py, "-m", "pytest", "tests/", "-q"])
        if rc != 0:
            failures.append("pytest")
            if rc == 1:  # pytest 模块缺失会报 1（No module named pytest）
                print("  ↳ 当前解释器未安装 pytest。请用已装 pytest 的解释器重跑，"
                      "例如：python dev/run_all_checks.py --python <系统python路径>")

    print("\n" + "=" * 60)
    if not failures:
        print("✅ 全部检查通过（P0 引用/版本 + P1 测试）")
        return 0
    print(f"❌ 失败的检查：{', '.join(failures)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
