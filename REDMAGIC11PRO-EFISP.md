# RedMagic 11 Pro — EFISP integrity experiment (GKI 6.12.23)

This branch is isolated from main and other GKI builds.

## Target
- Device under test: **RedMagic 11 Pro**, stock Android 16 GKI 6.12.23.
- Source: official Google GKI `android16-6.12-2025-06` / latest source tag for that release.
- Kernel root: **BakaSU**, formerly **ReSukiSU**, built in.
- SUSFS: simonpunk `gki-android16-6.12`.
- Integrity hypothesis from freeza-inc: do not enable `CONFIG_POSIX_MQUEUE` or `CONFIG_DEVTMPFS` (and do not enable DroidSpaces).
- No PIF, injected keybox, or root-hiding success guarantees.

## Why this is an experiment
Those two settings are not a proven universal fix for Google Play Integrity. Disabling **DEVTMPFS** in particular can affect Android boot and devices. This is not an OEM-tested RedMagic kernel. A successful compilation does **not** establish device compatibility, functional recovery, or a specific Play Integrity verdict.

The workflow deliberately creates a raw `Image` and an optional AnyKernel3 test ZIP; it does not produce a pretended stock `boot.img`. Back up the original boot image and use recovery-capable test procedures before any flashing. Do not flash without an exact match to the current stock kernel/firmware and a known recovery route.

## Trigger
The dedicated workflow is `.github/workflows/redmagic11pro-efisp.yml` and builds on its own changes in this branch or via manual dispatch (if available).

## Verification
Logs must confirm source Makefile version 6.12.23, SUSFS patch application, BakaSU checkout SHA, requested config values, and build success. An actual generated kernel config will be checked where accessible; no claim of verified effective config is made without evidence.

## Sources
- https://source.android.com/docs/core/architecture/kernel/gki-android16-6_12-deprecated-builds
- https://github.com/Baka-SU/BakaSU
- https://gitlab.com/simonpunk/susfs4ksu
