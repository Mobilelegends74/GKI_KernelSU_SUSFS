#!/usr/bin/env python3
"""Keep Kleaf's incremental outputs reusable after a fresh Actions checkout.

Only restore an input's old mtime when its SHA-256 and mode still match.
Changed/new inputs retain fresh timestamps, so Kbuild rebuilds their dependents.
Never restore source contents, commands, configuration or final images from here.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ROOTS = ('common', 'KernelSU-Next', 'build/kernel')
EXCLUDE = {'.git', '.repo', 'out', 'dist', '__pycache__'}


def inputs(kernel):
    for name in ROOTS:
        root = kernel / name
        if not root.is_dir():
            continue
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDE and not d.startswith('bazel-'))
            for name in sorted(files):
                p = Path(directory) / name
                if name == '.git' or p.is_symlink() or not p.is_file():
                    continue
                yield p.relative_to(kernel).as_posix(), p


def signature(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return [digest, stat.S_IMODE(path.stat().st_mode)]


def identity(kernel):
    # Do not reuse compiler outputs across different base/toolchain revisions.
    roots = ['common', 'build/kernel', 'build/bazel_common_rules']
    prebuilts = kernel / 'prebuilts'
    if prebuilts.is_dir():
        for directory, dirs, files in os.walk(prebuilts):
            if '.git' in dirs or '.git' in files:
                roots.append(Path(directory).relative_to(kernel).as_posix())
                dirs[:] = []
    versions = []
    for name in sorted(roots):
        p = kernel / name
        if not (p / '.git').exists():
            continue
        rev = subprocess.check_output(['git', '-C', str(p), 'rev-parse', 'HEAD'], text=True).strip()
        versions.append((name, rev))
    if not any(name == 'common' for name, rev in versions):
        raise ValueError('Cannot identify kernel source revision')
    return hashlib.sha256(json.dumps(versions).encode()).hexdigest()[:24]


def process(mode, kernel, manifest):
    old = {}
    if mode == 'restore' and manifest.exists():
        data = json.loads(manifest.read_text())
        if data.get('version') != 1:
            raise ValueError('Unsupported source timestamp manifest')
        old = data['files']
    files = {}
    restored = 0
    for name, path in inputs(kernel):
        sig = signature(path)
        info = path.stat()
        if mode == 'restore':
            previous = old.get(name)
            if previous and previous[:2] == sig:
                os.utime(path, ns=(info.st_atime_ns, previous[2]))
                restored += 1
        else:
            files[name] = sig + [info.st_mtime_ns]
    if mode == 'save':
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({'version': 1, 'files': files}) + '\n')
    print(f'Kernel input state: {len(files)} saved, {restored} content-identical timestamps restored')


if __name__ == '__main__':
    mode, kernel = sys.argv[1], Path(sys.argv[2]).resolve()
    if mode == 'identity':
        print('identity=' + identity(kernel))
    elif mode in ('restore', 'save'):
        process(mode, kernel, Path(sys.argv[3]))
    else:
        raise SystemExit('Expected identity, restore or save')
