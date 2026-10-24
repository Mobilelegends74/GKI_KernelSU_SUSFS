#!/usr/bin/env python3
"""Exercise incremental input reuse without hiding real source/header changes."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import time

spec = importlib.util.spec_from_file_location('cache', Path(__file__).with_name('gki-cache-state.py'))
cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache)
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    common = root / 'common'
    common.mkdir()
    (common / 'value.h').write_text('#define VALUE 1\n')
    (common / 'main.c').write_text('#include "value.h"\nint main(void) { return VALUE; }\n')
    (common / 'Makefile').write_text('../result: main.c value.h\n\tcc main.c -o ../result\n')
    manifest = root / 'cache/state.json'
    subprocess.run(['make', '-C', str(common)], check=True, capture_output=True)
    # Like Kleaf, place build outputs outside the source snapshot.
    cache.process('save', root, manifest)
    time.sleep(0.03)
    os.utime(common / 'main.c', None)
    os.utime(common / 'value.h', None)
    cache.process('restore', root, manifest)
    assert subprocess.run(['make', '-q', '-C', str(common)], capture_output=True).returncode == 0
    (common / 'value.h').write_text('#define VALUE 2\n')
    # A source archive can carry an old timestamp despite different contents.
    os.utime(common / 'value.h', ns=(1_000_000_000, 1_000_000_000))
    changed = (common / 'value.h').stat().st_mtime_ns
    cache.process('restore', root, manifest)
    assert (common / 'value.h').stat().st_mtime_ns > changed
    assert subprocess.run(['make', '-q', '-C', str(common)], capture_output=True).returncode == 1
    subprocess.run(['make', '-C', str(common)], check=True, capture_output=True)
    assert subprocess.run([str(root / 'result')]).returncode == 2
    (common / 'new.c').write_text('/* new */\n')
    fresh = (common / 'new.c').stat().st_mtime_ns
    cache.process('restore', root, manifest)
    assert (common / 'new.c').stat().st_mtime_ns >= fresh
    assert (common / 'value.h').read_text() == '#define VALUE 2\n'
print('OK: unchanged inputs reused; changed headers rebuild; new inputs and contents preserved')
