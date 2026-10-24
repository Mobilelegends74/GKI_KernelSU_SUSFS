#!/usr/bin/env python3
"""Validate actual built GKI outputs and package reproducibility metadata."""
import json
import os
from pathlib import Path
import re
import sys

ak3 = Path(sys.argv[1])
workspace = Path(os.environ['GITHUB_WORKSPACE'])
roots = [workspace / 'kernel/bazel-bin/common', Path('/home/runner/out')]


def find_output(name, predicate):
    for root in roots:
        if not root.exists():
            continue
        for directory, dirs, files in os.walk(root, followlinks=True):
            dirs[:] = [d for d in dirs if d not in ('.git', '.repo')]
            if name in files:
                p = Path(directory) / name
                if predicate(p.read_text(errors='replace')):
                    return p
    raise SystemExit(f'Missing actual UIDFAKE build output: {name}')


config = find_output('.config', lambda s: 'CONFIG_HMA_UIDFAKE_BUILTIN=y' in s.splitlines())
symbols = find_output('System.map', lambda s: 'hma_uidfake_translate' in s)
for name in ('Image', 'Bypass-Image'):
    image = (ak3 / name).read_bytes()
    assert image[56:60] == b'ARMd' and b'hma_uidfake: native built-in policy ready' in image
payload = ak3 / 'uidfake'
(payload / 'kernel.config').write_bytes(config.read_bytes())
summary = [f'Source commit: {os.environ["GITHUB_SHA"]}',
           'CONFIG_HMA_UIDFAKE_BUILTIN=y; Normal and Bypass Image markers verified']
summary += [s for s in symbols.read_text().splitlines()
            if any(t in s for t in ('hma_uidfake', 'uidfake_policy', 'kaux_family'))]
(payload / 'build-verification.txt').write_text('\n'.join(summary) + '\n')
metadata = {key: os.environ.get(key, '') for key in (
    'GITHUB_SHA', 'GITHUB_RUN_ID', 'KSU_VERSION', 'KSUN_COMMIT',
    'KSU_SOURCE_REF', 'SUSFS_SHA', 'SUSFS_BRANCH', 'NOMOUNT_SHA', 'NOMOUNT_TAG',
    'SELINUX_TIMING_PATCH')}
metadata['kernel'] = 'android14-6.1.145_r00'
susfs = workspace / 'kernel/common/include/linux/susfs.h'
metadata['susfs_version'] = re.search(r'#define SUSFS_VERSION\s+"([^"]+)"', susfs.read_text())[1]
assert metadata['KSU_VERSION'].isdigit()
assert re.fullmatch(r'v?\d+\.\d+\.\d+', metadata['NOMOUNT_TAG'])
assert metadata['SELINUX_TIMING_PATCH'] == 'ec7eb93621c40c0cc2c304cca9c0ca43b7d4c23a'
selinux_patch = workspace / 'patches/selinux/0001-ksu-reduce-selinux-hide-timing.patch'
import hashlib
metadata['SELINUX_PATCH_SHA256'] = hashlib.sha256(selinux_patch.read_bytes()).hexdigest()
(payload / 'selinux-timing.patch').write_bytes(selinux_patch.read_bytes())
(payload / 'SELINUX-PATCH.txt').write_bytes((workspace / 'patches/selinux/README.md').read_bytes())
for key in ('KSUN_COMMIT', 'SUSFS_SHA', 'NOMOUNT_SHA'):
    assert re.fullmatch(r'[0-9a-f]{40}', metadata[key]), (key, metadata[key])
(payload / 'build-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps(metadata, indent=2))
