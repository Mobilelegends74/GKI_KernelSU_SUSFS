#!/usr/bin/env python3

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: merge_nomount_task_mmu.py <task_mmu.c>")

p = Path(sys.argv[1])
s = p.read_text()

marker = "nomount_spoof_mmap_metadata(inode, &dev, &ino)"

if marker in s:
    print("NoMount task_mmu hook already present")
    raise SystemExit(0)

needle = "\t\tino = inode->i_ino;\n"

count = s.count(needle)

if count != 1:
    raise SystemExit(
        f"ERROR: expected exactly one 'ino = inode->i_ino' insertion point, found {count}"
    )

hook = """#ifdef CONFIG_NOMOUNT
\t\t{ extern void nomount_spoof_mmap_metadata(const struct inode *,
\t\t\t\t\t\t\t  dev_t *, unsigned long *);
\t\t  nomount_spoof_mmap_metadata(inode, &dev, &ino); }
#endif
"""

s = s.replace(needle, needle + hook, 1)
p.write_text(s)

if marker not in p.read_text():
    raise SystemExit("ERROR: NoMount task_mmu hook insertion failed")

print("NoMount task_mmu hook merged with SUSFS")
