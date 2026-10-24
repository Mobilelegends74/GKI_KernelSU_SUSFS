#!/usr/bin/env python3
"""Verify the delivered GKI archive, including both existing Image variants."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

archive = Path(sys.argv[1])
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None, 'ZIP CRC failure'
    names = set(z.namelist())
    required = {'Image', 'anykernel.sh', 'uidfake/sync-tool',
                'uidfake/service.sh', 'uidfake/hma-uidfake-native.patch',
                'uidfake/README.md', 'uidfake/LICENSE', 'uidfake/NOTICE',
                'uidfake/kernel.config', 'uidfake/build-verification.txt'}
    assert required <= names, f'missing payload: {required - names}'
    image = z.read('Image')
    assert len(image) > 8 * 1024 * 1024 and image[56:60] == b'ARMd', 'not a raw ARM64 Image'
    assert b'hma_uidfake: native built-in policy ready' in image
    bypass = z.read('Bypass-Image')
    assert bypass[56:60] == b'ARMd' and b'hma_uidfake: native built-in policy ready' in bypass
    assert 'CONFIG_HMA_UIDFAKE_BUILTIN=y' in z.read('uidfake/kernel.config').decode().splitlines()
    tool = z.read('uidfake/sync-tool')
    assert tool[:4] == b'\x7fELF' and int.from_bytes(tool[18:20], 'little') == 183
    assert hashlib.sha256(tool).hexdigest() == 'efb4c77c11ea55e961024e6fe4d6fd1999dc281be2e11db3646939c546e3382f'
    assert not any('uidfake' in n.lower() and '.ko' in n.lower() for n in names), 'unexpected UIDFAKE LKM'
    assert not any(n.endswith('lkmloader') for n in names), 'unexpected LKM loader'
    installer = z.read('anykernel.sh').decode()
    assert installer.index('# UIDFAKE companion preflight:') < installer.index('# boot install')
    assert '/data/adb/service.d/97-uidfake-kernel.sh' in installer
    patch = z.read('uidfake/hma-uidfake-native.patch').decode()
    for file in ['kernel/sys.c', 'kernel/cred.c', 'block/ioprio.c', 'fs/open.c',
                 'kernel/user.c', 'include/linux/sched.h',
                 'drivers/misc/hma_uidfake/core.c', 'drivers/misc/hma_uidfake/policy.c']:
        assert '+++ b/' + file in patch, f'incomplete source patch: {file}'
    assert 'ANDROID_KABI_USE' in patch, 'Android task KABI reservation missing'
    assert 'hma_uidfake-y := core.o policy.o netlink.o' in patch
    assert archive.name.endswith('_UIDFAKE.zip'), 'archive label missing'
    metadata = json.loads(z.read('uidfake/build-metadata.json'))
    if metadata.get('VPNHIDE_COMMIT_SHA'):
        assert b'vpnhide_ctl' in image and b'vpnhide_ctl' in bypass
        config = z.read('uidfake/kernel.config').decode().splitlines()
        assert 'CONFIG_VPNHIDE=y' in config and 'CONFIG_VPNHIDE_FS_HIDING=y' in config
        assert hashlib.sha256(z.read('vpnhide/vpnhide.patch')).hexdigest() == metadata['VPNHIDE_PATCH_SHA256']
        assert {'vpnhide/report.json', 'vpnhide/report.md', 'vpnhide/LICENSE', 'vpnhide/README.md'} <= names
        assert not any(n.endswith('.ko') and 'vpnhide' in n.lower() for n in names)
    if metadata.get('SELINUX_TIMING_PATCH'):
        assert metadata['SELINUX_TIMING_PATCH'] == 'ec7eb93621c40c0cc2c304cca9c0ca43b7d4c23a'
        assert hashlib.sha256(z.read('uidfake/selinux-timing.patch')).hexdigest() == metadata['SELINUX_PATCH_SHA256']
        assert 'uidfake/SELINUX-PATCH.txt' in names
print('UIDFAKE ZIP verified: Image, native patch, checksum-pinned helper, boot service and no UIDFAKE LKM')
print(hashlib.sha256(archive.read_bytes()).hexdigest(), archive.name)
