# GKI 6.1.145 native UIDFAKE — validation

Branch: `UIDFAKE-android14-6.1.145-build-base37505913520`.
Baseline repository commit: `dc57c5cdbcdd38451de06dca44a378e4cd0e64cc`,
original successful build: <https://github.com/Mobilelegends74/GKI_KernelSU_SUSFS/actions/runs/37505913520>.
The main branch was not modified.

## Delivered build

- Compiled source: `6a9055425d52b346b0bf9856a9d06d351b5ee19d`.
- Successful kernel job (both Normal and Bypass):
  <https://github.com/Mobilelegends74/GKI_KernelSU_SUSFS/actions/runs/39202921674/job/117899595717>.
- Successful publication workflow:
  <https://github.com/Mobilelegends74/GKI_KernelSU_SUSFS/actions/runs/39205555052>.
- Release:
  <https://github.com/Mobilelegends74/GKI_KernelSU_SUSFS/releases/tag/gki-android14-6.1.145-2026-10-19-build53-1-uidfake>.
- Asset: `AK3_6.1.145-android14_KSUN_33403_NM_7046c7a_UIDFAKE.zip`.
- SHA-256: `2922b54be8d0e4f5a5e6eb2a0156899a353fc6092e08fd52bf6113b5859047c1`.

Kernel: `android14-6.1.145_r00`.
KernelSU Next: 33403, `46768436ff35de01b1475a4ae6c19d6d4884abcf`.
SUSFS: v2.3.0, `2385dab487c3abb8c4a2990ea5c852f55fb47dc8`.
NoMount stable v2.1.1: `7046c7ad3ee0bf4ae66e80f6b93b1e30db0cb4e3`.
These SHA values describe this build, not frozen defaults: new builds resolve
the live `dev-susfs` and `gki-android14-6.1` branch tips again.

## Checks performed

- ASan/UBSan tests of native policy and netlink, 24,000 differential queries,
  65,536-pair capacity, revocation, malformed input, allocation failure retention,
  authorization, CRC and upload ownership.
- Exact clean GKI 6.1.145 source-hook integration and idempotence checked locally.
- CI used unconditional task KABI reserve slot 5, avoiding Droidspaces/SYSVIPC
  reservations. Size, trailing offsets and genksyms representation checks passed.
- Both ARM64 Images contain the native initialization marker. The archive
  contains the generated source patch, configuration, symbol evidence,
  SHA-verified ARM64 sync companion and automatic service.d installer.
- Final configuration preserves `CONFIG_HMA_UIDFAKE_BUILTIN=y`, `CONFIG_KSU=y`,
  `CONFIG_KSU_SUSFS=y`, `CONFIG_NOMOUNT=y`, `CONFIG_SECURITY_SELINUX=y`,
  `CONFIG_CFI_CLANG=y`, `CONFIG_ARM64_PTR_AUTH_KERNEL=y` and KABI reservations.
- Release asset digest equals the original Actions artifact digest exactly.

The first run's kernel job succeeded; only publication failed because the new
artifact downloader layout was not handled. The publisher now retains the
original ZIP instead of repacking it. Historical-tag publication also required
creating the tag separately and omitting historical target_commitish when a
verified tag exists. Publication was retried separately; the kernel was not
recompiled. Future workflows can publish an existing successful build using
`uidfake_artifact_run_id`; an old source tag may need to be pre-created with an
authorized account if GitHub refuses historical tag creation by GITHUB_TOKEN.

No on-device boot or HMA rule-effectiveness claim is made. Still test boot,
SELinux audit, service restart after reboot, HMA/HMA-OSS edits, isolated processes,
compat applications and rule removal. Sync log:
`/data/adb/uidfake-kernel/sync.log`.
