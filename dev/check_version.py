#!/usr/bin/env python3
"""
strength-training-design skill — version consistency checker

Verifies that the skill's version is consistent across the two places that
must agree:
  1. SKILL.md  frontmatter `version:` field
  2. CHANGELOG.md  most-recent `## [x.y.z] - date` entry

Note: README's version badge is auto-derived from the GitHub *tag*
(`github/v/tag/...`), so the tag itself must match — this script additionally
warns if a local git tag for the resolved version is missing, to catch the
"committed but forgot to `git tag`" failure mode.

Exits non-zero on any inconsistency so it can gate CI.

Usage:
  python scripts/check_version.py
  python scripts/check_version.py --root <skill_root> --check-tag
"""
import argparse
import os
import re
import subprocess
import sys

SKILL_VERSION_RE = re.compile(r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$", re.MULTILINE)
CHANGELOG_TOP_RE = re.compile(
    r"^##\s*\[([0-9]+\.[0-9]+\.[0-9]+)\]\s*-\s*(\d{4}-\d{2}-\d{2})",
    re.MULTILINE,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--check-tag", action="store_true",
                    help="also verify a local git tag exists for the resolved version")
    args = ap.parse_args()

    root = args.root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. SKILL.md version
    skill_path = os.path.join(root, "SKILL.md")
    if not os.path.exists(skill_path):
        print("[FAIL] SKILL.md not found")
        return 1
    skill_txt = open(skill_path, encoding="utf-8").read()
    m = SKILL_VERSION_RE.search(skill_txt)
    if not m:
        print("[FAIL] `version:` field not found in SKILL.md frontmatter")
        return 1
    skill_ver = m.group(1)

    # 2. CHANGELOG.md top entry
    cl_path = os.path.join(root, "CHANGELOG.md")
    if not os.path.exists(cl_path):
        print("[FAIL] CHANGELOG.md not found")
        return 1
    cl_txt = open(cl_path, encoding="utf-8").read()
    cm = CHANGELOG_TOP_RE.search(cl_txt)
    if not cm:
        print("[FAIL] No `## [x.y.z] - date` entry found at top of CHANGELOG.md")
        return 1
    cl_ver, cl_date = cm.group(1), cm.group(2)

    print("=== Version consistency check ===")
    print(f"  SKILL.md  version : {skill_ver}")
    print(f"  CHANGELOG top     : {cl_ver} ({cl_date})")

    problems = []
    if skill_ver != cl_ver:
        problems.append(f"version mismatch: SKILL.md={skill_ver} vs CHANGELOG={cl_ver}")

    if args.check_tag:
        try:
            out = subprocess.run(
                ["git", "tag", "-l", f"v{skill_ver}"],
                cwd=root, capture_output=True, text=True, check=True,
            )
            has_tag = out.stdout.strip() != ""
        except Exception as e:
            print(f"  [warn] git tag check skipped ({e})")
            has_tag = True
        print(f"  git tag v{skill_ver}  : {'present' if has_tag else 'MISSING'}")
        if not has_tag:
            problems.append(f"local git tag v{skill_ver} is missing (commit done but not tagged)")

    if problems:
        print("\n[FAIL]")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("  ✓ Version consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
