#!/usr/bin/env bash
# Compare each entry's declared arch against what the registry actually
# publishes.
#
#   tools/check-arch.sh            # every entry
#   tools/check-arch.sh miniflux   # one entry
#
# Prints one line per app. Exits non-zero if anything disagrees, so it can run
# on a schedule and catch an upstream dropping an architecture.
#
# Uses registry.py rather than `docker buildx imagetools inspect`: it needs no
# docker and no login, so it runs anywhere python does, and it routes Docker
# Hub through the Hub API instead of spending the anonymous manifest quota.
# That quota matters here more than anywhere — checking the whole catalogue is
# 70 lookups, and once the limit is hit the registry returns nothing at all,
# which would read as "every image lost its architectures".
set -uo pipefail

cd "$(dirname "$0")/.."
JOBS="${JOBS:-4}"

entry() {
  local f="$1" slug image version declared actual
  slug=$(basename "$f" .yml)
  if [ ! -f "$f" ]; then
    printf '%-24s MISSING     no such entry\n' "$slug"
    return 1
  fi
  read -r image version declared < <(python3 - "$f" <<'PY'
import sys, yaml
d = yaml.safe_load(open(sys.argv[1]))
print(d["image"], d["version"], ",".join(sorted(d.get("arch") or [])))
PY
)
  actual=$(python3 tools/registry.py arch "$image" "$version" 2>/dev/null | tr ',' '\n' | sort | paste -sd, -)

  if [ -z "$actual" ]; then
    printf '%-24s UNRESOLVED  %s:%s\n' "$slug" "$image" "$version"
    return 1
  fi
  if [ "$actual" != "$declared" ]; then
    printf '%-24s MISMATCH    declared=%s actual=%s\n' "$slug" "$declared" "$actual"
    return 1
  fi
  printf '%-24s ok          %s\n' "$slug" "$actual"
}
export -f entry

if [ $# -gt 0 ]; then
  files=(); for s in "$@"; do files+=("apps/$s.yml"); done
else
  mapfile -t files < <(ls apps/*.yml)
fi

fail=0
printf '%s\n' "${files[@]}" | xargs -P "$JOBS" -I{} bash -c 'entry "$@"' _ {} || fail=1

# An UNRESOLVED sweep across every entry almost always means rate limiting or
# no network, not 70 broken images. Say so, because the alternative reading
# sends someone editing files that are fine.
if [ "$fail" -ne 0 ] && [ ${#files[@]} -gt 5 ]; then
  echo
  echo "note: widespread UNRESOLVED usually means the registry is rate-limiting" >&2
  echo "or the network is blocked, not that the entries are wrong." >&2
fi
exit $fail
