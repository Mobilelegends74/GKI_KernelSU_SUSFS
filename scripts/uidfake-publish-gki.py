#!/usr/bin/env python3
"""Publish verified AnyKernel assets only after successful complete builds."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

root = Path(sys.argv[1]).resolve()
archives = sorted(root.glob('AK3_*_UIDFAKE.zip'))
assert len(archives) == 1, f'Expected one original UIDFAKE ZIP, got {archives}'
archive = archives[0]
with zipfile.ZipFile(archive) as z:
    metadata = json.loads(z.read('uidfake/build-metadata.json'))
assert metadata['GITHUB_SHA'] == os.environ['BUILD_SOURCE_SHA']
assert metadata['GITHUB_RUN_ID'] == os.environ['BUILD_RUN_ID']
subprocess.run([sys.executable, 'scripts/uidfake-verify-zip.py', str(archive)], check=True)
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
tag = f'gki-android14-6.1.145-{date}-build{os.environ["BUILD_RUN_NUMBER"]}-{os.environ["BUILD_RUN_ATTEMPT"]}-uidfake'
title = f'GKI Android 14 | Linux 6.1.145 | KSUN {metadata["KSU_VERSION"]} | UIDFAKE | Build {os.environ["BUILD_RUN_NUMBER"]}'
repo = os.environ['GITHUB_REPOSITORY']
run_url = f'https://github.com/{repo}/actions/runs/{os.environ["GITHUB_RUN_ID"]}'
notes = f'''# GKI Android 14 — Linux 6.1.145 · UIDFAKE

## Изменения

- Добавлен нативный патч **HMA UIDFAKE**, встроенный в ядро (`CONFIG_HMA_UIDFAKE_BUILTIN=y`). Отдельный `.ko`, LKM-загрузчик и установка модуля UIDFAKE не нужны.
- Автоматическая синхронизация правил HMA/HMA-OSS после загрузки Android и при изменениях. Сохранены фильтрация UID, работа с изолированными процессами и атомарное обновление политики.
- KernelSU Next и SUSFS получены из актуальных рабочих веток на момент запуска. Старые версии не закреплены; фактические SHA записаны ниже и внутри ZIP.
- NoMount переведён с dev на **v2.1.1 stable**.
- Сохранены функции исходной сборки: SUSFS, BBG, сетевые расширения, Droidspaces, NTSync, Unicode fix и штатные оптимизации. Сохранены оба исходных режима AnyKernel3: Normal и Bypass. Рекомендуется Normal; Bypass изменяет проверку версий модулей и не нужен для UIDFAKE.

## Состав

| Компонент | Версия / исходники |
|---|---|
| База | `android14-6.1.145_r00` |
| KernelSU Next | **{metadata['KSU_VERSION']}**, `dev-susfs`, `{metadata['KSUN_COMMIT']}` |
| SUSFS | **{metadata['susfs_version']}**, `{metadata['SUSFS_SHA']}` |
| NoMount | **v2.1.1 stable**, `{metadata['NOMOUNT_SHA']}` |
| UIDFAKE | Нативный патч, включён в Normal и Bypass Images |

[Исходники и патч UIDFAKE](https://github.com/{repo}/tree/{metadata['GITHUB_SHA']}/uidfake) · [Описание интеграции](https://github.com/{repo}/blob/{os.environ['GITHUB_SHA']}/docs/uidfake-gki.md) · [Успешная сборка]({os.environ['BUILD_JOB_URL']}) · [Публикация]({run_url})

Патч, конфигурация ядра и проверочные сведения включены в ZIP. CI проверяет тесты политики UIDFAKE, сохранение KABI, конфигурацию и оба ARM64 Image. Успешная сборка не является проверкой загрузки и всех хуков на устройстве.

## Установка

Только для совместимых ARM64-устройств Android GKI с ядром 6.1. Совпадения версии Android недостаточно: проверьте совместимость boot-образа и прошивки. Сделайте резервную копию boot. При наличии отдельного UIDFAKE LKM отключите его перед установкой. Прошивайте AnyKernel3 ZIP из загруженного Android с root и доступным `/data/adb` — установщик автоматически добавит службу синхронизации HMA.

SHA-256 (`{archive.name}`):
```text
{digest}
```

Благодарности: авторы HMA/UIDFAKE, KernelSU Next, pershoot, simonpunk, maxsteeel, WildKernels и разработчики включённых компонентов.
'''
notes_path = root / 'release-notes.md'
notes_path.write_text(notes)
if '--verify-only' in sys.argv:
    print(f'Verified original ZIP without repacking: {archive}\nTag: {tag}\nSHA256: {digest}')
    sys.exit(0)
# Do not send a historical target_commitish when the correct tag already
# exists: GitHub can reject that field for its restricted workflow token.
tag_commit = subprocess.run(['gh', 'api', f'repos/{repo}/commits/{tag}', '--jq', '.sha'],
                            text=True, capture_output=True)
if tag_commit.returncode == 0:
    assert tag_commit.stdout.strip() == metadata['GITHUB_SHA'], 'Release tag points to another build'
    target_flags = ['--verify-tag']
else:
    assert metadata['GITHUB_SHA'] == os.environ['GITHUB_SHA'], 'Pre-create the tag on the historical source commit before publishing this build'
    # Never substitute a moving branch tip for the commit actually compiled.
    target_flags = ['--target', metadata['GITHUB_SHA']]
subprocess.run(['gh', 'release', 'create', tag, '--repo', repo,
                *target_flags, '--title', title,
                '--notes-file', str(notes_path), '--draft', str(archive)], check=True)
flags = ['--prerelease', '--latest=false'] if os.environ['RELEASE_TYPE'] == 'Pre-Release' else ['--prerelease=false', '--latest']
subprocess.run(['gh', 'release', 'edit', tag, '--repo', repo, '--draft=false', *flags], check=True)
with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
    summary.write(f'## UIDFAKE release\n\nhttps://github.com/{repo}/releases/tag/{tag}\n\nSHA-256: `{digest}`\n')
