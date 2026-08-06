#!/usr/bin/env bash
# Compare each entry's declared arch against what the registry actually
# publishes. Needs docker with buildx.
#
#   tools/check-arch.sh            # every entry
#   tools/check-arch.sh miniflux   # one entry
#
# Prints one line per app. Exits non-zero if anything disagrees, so it can run
# on a schedule and open an issue when an upstream drops an architecture.
set -uo pipefail

cd "$(dirname "$0")/.."
JOBS="${JOBS:-8}"
fail=0

entry() {
  local f="$1"
  local slug image version declared actual
  slug=$(basename "$f" .yml)
  image=$(awk '/^image:/{print $2; exit}' "$f")
  version=$(awk '/^version:/{gsub(/"/,"",$2); print $2; exit}' "$f")
  declared=$(python3 - "$f" <<'PY'
import sys, yaml
d = yaml.safe_load(open(sys.argv[1]))
print(",".join(sorted(d.get("arch") or [])))
PY
)

  actual=$(timeout 120 docker buildx imagetools inspect "$image:$version" 2>/dev/null \
    | grep -oE 'linux/(amd64|arm64)' | sed 's|linux/||' | sort -u | paste -sd, -)

  if [ -z "$actual" ]; then
    printf '%-24s UNRESOLVED  %s:%s\n' "$slug" "$image" "$version"
    return 1
  fi
  if [ "$actual" != "$declared" ]; then
    printf '%-24s MISMATCH    declared=%s actual=%s\n' "$slug" "$declared" "$actual"
    return 1
  fi
  printf '%-24s ok          %s\n' "$slug" "$actual"
  return 0
}
export -f entry

if [ $# -gt 0 ]; then
  files=()
  for s in "$@"; do files+=("apps/$s.yml"); done
else
  mapfile -t files < <(ls apps/*.yml)
fi

printf '%s\n' "${files[@]}" | xargs -P "$JOBS" -I{} bash -c 'entry "$@"' _ {} || fail=1
exit $fail
