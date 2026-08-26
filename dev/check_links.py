#!/usr/bin/env python3
"""
strength-training-design skill — reference link integrity checker

Scans the *current* reference links in the routing layer, the single-rule
source (guardrails.md), every workflow file, and README.md, then verifies
that every cited file actually exists on disk.

Design notes:
- Whitelist scan: only the files below are checked, so historical docs
  (CHANGELOG.md) are never treated as live links.
- Only backtick-wrapped `references/...` file/dir paths are matched.
- Directory-only references (e.g. `references/consultation/`) are OK.
- Exits non-zero if any dead link is found, so it can gate CI.

Usage:
  python scripts/check_links.py
  python scripts/check_links.py --root <skill_root>   # default: parent of scripts/
"""
import argparse
import os
import re
import sys

# File link: backtick-wrapped `references/...md`
LINK_RE = re.compile(r"`(references/[^\s`]+\.md)`")          # file link
DIR_RE = re.compile(r"`(references/[^\s`]+/)`")              # directory link


def find_links(text):
    files, dirs = set(), set()
    for m in LINK_RE.finditer(text):
        files.add(m.group(1))
    for m in DIR_RE.finditer(text):
        dirs.add(m.group(1))
    return files, dirs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None, help="skill root dir (default: parent of this script)")
    args = ap.parse_args()

    root = args.root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Whitelist: routing layer + single-rule source + every workflow + README.
    scan_files = ["SKILL.md", "README.md", "guardrails.md"]
    wf_dir = os.path.join(root, "workflows")
    if os.path.isdir(wf_dir):
        for fn in sorted(os.listdir(wf_dir)):
            if fn.endswith(".md"):
                scan_files.append(os.path.join("workflows", fn))

    scanned = []
    dead_files, dead_dirs = [], []

    for rel in scan_files:
        fpath = os.path.join(root, rel)
        if not os.path.exists(fpath):
            print(f"[skip] {rel} not found")
            continue
        with open(fpath, encoding="utf-8") as fh:
            text = fh.read()
        files, dirs = find_links(text)
        scanned.append((rel, len(files), len(dirs)))
        for ref in files:
            target = os.path.normpath(os.path.join(root, ref))
            if not os.path.exists(target):
                dead_files.append((fname, ref))
        for ref in dirs:
            target = os.path.normpath(os.path.join(root, ref))
            if not os.path.isdir(target):
                dead_dirs.append((fname, ref))

    print("=== Reference link check ===")
    for fname, nf, nd in scanned:
        print(f"  {fname}: {nf} file links, {nd} dir links scanned")
    if not dead_files and not dead_dirs:
        print("  ✓ All referenced files/dirs exist.")
        return 0

    print("\n[FAIL] Dead references found:")
    for fname, ref in dead_files:
        print(f"  file  {fname}: `{ref}` -> NOT FOUND")
    for fname, ref in dead_dirs:
        print(f"  dir   {fname}: `{ref}` -> NOT A DIR")
    return 1


if __name__ == "__main__":
    sys.exit(main())
