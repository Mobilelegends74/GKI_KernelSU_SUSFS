#!/usr/bin/env python3
"""Offline resolver and release-note rendering tests (not a kernel/device test)."""
import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import Mock, patch
import zipfile

root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('resolver', root / 'scripts/resolve-nomount-stable.py')
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)
for annotated in (False, True):
    refs = 'a' * 40 + '\trefs/tags/v9.2.0\n'
    if annotated:
        refs += 'b' * 40 + '\trefs/tags/v9.2.0^{}\n'
    resolved = resolver.resolve(Mock(side_effect=[json.dumps(
        dict(tag_name='v9.2.0', draft=False, prerelease=False)), refs]))
    assert resolved['nomount_sha'] == ('b' * 40 if annotated else 'a' * 40)
for release in [dict(tag_name='dev', draft=False, prerelease=False),
                dict(tag_name='v9.2.0', draft=True, prerelease=False),
                dict(tag_name='v9.2.0', draft=False, prerelease=True)]:
    try:
        resolver.resolve(Mock(return_value=json.dumps(release)))
    except ValueError:
        pass
    else:
        raise AssertionError('Accepted a non-stable release')

for modern in (False, True):
    metadata = dict(GITHUB_SHA='a' * 40, GITHUB_RUN_ID='1', KSU_VERSION='33405',
                    KSUN_COMMIT='b' * 40, SUSFS_SHA='c' * 40, susfs_version='v2.3.0',
                    NOMOUNT_SHA='7046c7ad3ee0bf4ae66e80f6b93b1e30db0cb4e3')
    if modern:
        metadata.update(NOMOUNT_TAG='v9.2.0', NOMOUNT_SHA='d' * 40,
                        SELINUX_TIMING_PATCH='ec7eb93621c40c0cc2c304cca9c0ca43b7d4c23a')
    with tempfile.TemporaryDirectory(prefix='gki-release-notes-test-') as tmp:
        with zipfile.ZipFile(Path(tmp) / 'AK3_test_UIDFAKE.zip', 'w') as z:
            z.writestr('uidfake/build-metadata.json', json.dumps(metadata))
        env = dict(BUILD_SOURCE_SHA='a' * 40, BUILD_RUN_ID='1', BUILD_RUN_NUMBER='2',
                   BUILD_RUN_ATTEMPT='1', GITHUB_REPOSITORY='Mobilelegends74/GKI_KernelSU_SUSFS',
                   GITHUB_RUN_ID='1', GITHUB_SHA='a' * 40, BUILD_JOB_URL='https://github.com/test/job/1')
        with patch.dict(os.environ, env), patch.object(sys, 'argv', ['publish', tmp, '--verify-only']), \
                patch.object(subprocess, 'run', return_value=Mock(returncode=0)):
            try:
                runpy.run_path(str(root / 'scripts/uidfake-publish-gki.py'), run_name='__main__')
            except SystemExit as e:
                assert e.code == 0
        notes = (Path(tmp) / 'release-notes.md').read_text()
        assert '/KernelSU-Next/commit/' + 'b' * 40 in notes
        assert '/susfs4ksu/-/commit/' + 'c' * 40 in notes
        if modern:
            assert '/nomount/releases/tag/v9.2.0' in notes
            assert '/nomount/commit/' + 'd' * 40 in notes
            assert 'v2.1.1' not in notes
            assert 'KernelSU/pull/3938' in notes
        else:
            assert '/nomount/releases/tag/v2.1.1' in notes

action = (root / '.github/actions/nomount/action.yml').read_text()
assert '--branch "$NM_TAG"' in action
assert '--branch v2.1.1' not in action
assert 'EXPECTED_NM_SHA' in action
build = (root / '.github/workflows/build.yml').read_text()
assert build.index('Apply reviewed SELinux timing backport') < build.index('Build Normal Kernel')
assert build.index('Apply reviewed SELinux timing backport') < build.index('Build Bypass Kernel')
print('OK: stable release resolution, annotated tags, safe refusal, actual-component links, legacy notes and patch ordering')
