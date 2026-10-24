#!/usr/bin/env bash
set -euo pipefail
resolution="$(python3 scripts/resolve-vpnhide-ci.py)"
sha="$(jq -er .vpnhide_sha <<< "$resolution")"
run_id="$(jq -er .vpnhide_run_id <<< "$resolution")"
run_url="$(jq -er .vpnhide_run_url <<< "$resolution")"
source_dir="$GITHUB_WORKSPACE/vpnhide-source"
kernel_dir="$GITHUB_WORKSPACE/kernel/common"
review_dir="$GITHUB_WORKSPACE/vpnhide-review"
git init "$source_dir"
git -C "$source_dir" remote add origin https://github.com/okhsunrog/vpnhide.git
git -C "$source_dir" fetch --depth 1 origin "$sha"
git -C "$source_dir" checkout --detach FETCH_HEAD
test "$(git -C "$source_dir" rev-parse HEAD)" = "$sha"
python3 -m unittest discover -s "$source_dir/builtin/scripts" -p 'test_*.py' -v
python3 "$source_dir/builtin/scripts/integrate.py" export \
  --kernel "$kernel_dir" --kmi android14-6.1 --output "$review_dir"
git -C "$kernel_dir" apply --check "$review_dir/vpnhide.patch"
git -C "$kernel_dir" apply "$review_dir/vpnhide.patch"
"$kernel_dir/scripts/config" --file "$kernel_dir/arch/arm64/configs/gki_defconfig" \
  -e VPNHIDE -e VPNHIDE_FS_HIDING
{
  echo "VPNHIDE_COMMIT_SHA=$sha"
  echo "VPNHIDE_RUN_ID=$run_id"
  echo "VPNHIDE_RUN_URL=$run_url"
} >> "$GITHUB_ENV"
