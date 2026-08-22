#!/usr/bin/env python3
"""
strength-training-design skill — reference link integrity checker

Scans the *current* reference links in SKILL.md and README.md and verifies
that every cited file actually exists on disk.

Design notes (why this is stricter than a naive grep):
- Only scans backtick-wrapped `references/...` paths in SKILL.md and README.md.
- Explicitly ignores:
  - CHANGELOG.md (historical version descriptions contain old paths)
  - README's ASCII file-tree diagram (indented, no backticks)
  - Directory-only references (e.g. `references/consultation/` are OK)
- Exits non-zero if any dead link is found, so it can gate CI.

Usage:
  python scripts/check_links.py
  python scripts/check_links.py --root <skill_root>   # default: parent of scripts/
"""
import argparse
import os
import re
import sys

# Files whose *historical* content must NOT be treated as live links.
HISTORY_FILES = {"changelog.md"}

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
    scanned = []
    dead_files, dead_dirs = [], []

    for fname in ["SKILL.md", "README.md"]:
        fpath = os.path.join(root, fname)
        if not os.path.exists(fpath):
            print(f"[skip] {fname} not found")
            continue
        with open(fpath, encoding="utf-8") as fh:
            text = fh.read()
        files, dirs = find_links(text)
        scanned.append((fname, len(files), len(dirs)))
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
