#!/usr/bin/env python3
"""Ask a registry what tags an image has and what platforms a tag was built for.

Speaks the OCI distribution API directly with an anonymous token, so it works
for Docker Hub, GHCR, Quay and Codeberg without a login and without docker
installed.

  tools/registry.py tags ghcr.io/miniflux/miniflux
  tools/registry.py arch ghcr.io/miniflux/miniflux 2.2.7
  tools/registry.py latest ghcr.io/miniflux/miniflux

`latest` is the one used when refreshing the catalogue: it returns the highest
tag that looks like a release, ignoring `latest`, `stable`, `dev`, release
candidates, nightlies and date stamps.

`tags` reads every page the registry offers, not just the first. Registries
cap a page at 1000 tags (Quay at 100), sorted as strings, so on a busy
repository the first page can end years before the current release.
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request

TIMEOUT = 30
# Enough for the largest repositories seen (tens of thousands of tags); a
# listing still unfinished after this many pages is reported, not truncated.
MAX_PAGES = 300
RETRIES = 5

# Two or more numeric components, optionally v-prefixed. A suffix is allowed
# because plenty of projects ship `2.4.1-alpine` or `1.20.0-ls123` as the real
# release, but anything that smells prerelease is filtered separately.
RELEASE_RE = re.compile(r"^v?(\d+)\.(\d+)(?:\.(\d+))?(?:[.\-+].*)?$")
# `pre` only as its own marker (`4.6.0-pre.1`, `5.7.0-pre0`), not inside a word.
PRERELEASE_RE = re.compile(
    r"(rc|alpha|beta|dev|nightly|snapshot|canary|test|preview|pre(?=[.\-_\d]|$))", re.I
)
# A date stamp: 2026.08.01, 2026-09-22 or 20260801, with the month and day
# both two digits. Real for a few projects, but it sorts badly against semver
# and is almost never what you want to pin. Calendar-versioned releases such
# as authentik's 2026.10.1 don't pad the day, so they stay releases; the
# ambiguous case is a patch number of 10 or more in October to December.
DATE_RE = re.compile(
    r"^v?20\d{2}"
    r"(?:([.\-])(?:0[1-9]|1[0-2])\1(?:0[1-9]|[12]\d|3[01])"
    r"|(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))"
    r"(?!\d)"
)
# `version-6.6.6`. Firefly III and a few others prefix every release tag.
PREFIX_RE = re.compile(r"^(version|release|v)[-_]")
# `260728` — YYMMDD calendar versioning, which PhotoPrism and others use as
# their actual release tag. It has no dots, so it never matches RELEASE_RE, but
# it is an exact immutable tag and pinning it is entirely correct.
CALVER_RE = re.compile(r"^(\d{6})$")


def _split(ref: str) -> tuple[str, str]:
    """`ghcr.io/foo/bar` -> (registry host, repository path)."""
    if "/" not in ref:
        return "registry-1.docker.io", f"library/{ref}"
    head, rest = ref.split("/", 1)
    if "." not in head and ":" not in head and head != "localhost":
        # No registry host, so it's Docker Hub.
        return "registry-1.docker.io", ref if "/" in ref else f"library/{ref}"
    if head == "docker.io":
        return "registry-1.docker.io", rest
    # lscr.io redirects to GHCR and does not serve the API itself.
    if head == "lscr.io":
        return "ghcr.io", rest
    return head, rest


def _get(url: str, token: str | None = None, accept: str | None = None) -> dict:
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if accept:
        req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def _token(host: str, repo: str) -> str | None:
    """An anonymous pull token. Registries differ only in the auth host."""
    services = {
        "registry-1.docker.io": "https://auth.docker.io/token?service=registry.docker.io",
        "ghcr.io": "https://ghcr.io/token?service=ghcr.io",
        "quay.io": "https://quay.io/v2/auth?service=quay.io",
        "codeberg.org": "https://codeberg.org/v2/token?service=codeberg.org",
    }
    base = services.get(host)
    if not base:
        base = f"https://{host}/v2/token?service={host}"
    try:
        return _get(f"{base}&scope=repository:{repo}:pull").get("token")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None


def _get_page(url: str, token: str | None) -> tuple[dict, str | None]:
    """One page of a listing and its Link header, waiting out rate limits."""
    for attempt in range(RETRIES):
        req = urllib.request.Request(url)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read()), r.headers.get("Link")
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == RETRIES - 1:
                raise
            try:
                wait = min(float(e.headers.get("Retry-After") or 0), 60) or 2 ** (attempt + 1)
            except ValueError:
                wait = 2 ** (attempt + 1)
            time.sleep(wait)
    raise AssertionError("unreachable")


def _next_url(host: str, link: str | None) -> str | None:
    """The `rel="next"` target of a Link header, made absolute."""
    m = re.search(r'<([^>]+)>\s*;\s*rel="?next"?', link or "")
    if not m:
        return None
    target = m.group(1)
    return target if target.startswith("http") else f"https://{host}{target}"


def tags(ref: str) -> list[str]:
    """Every tag in the repository, following the registry's pagination.

    Returns an empty list for a repository that doesn't exist or can't be
    read anonymously. A failure after the first page raises instead of
    returning what it has: a truncated list is how `latest` ends up reporting
    a stale version with nothing to say anything is missing.
    """
    host, repo = _split(ref)
    token = _token(host, repo)
    out: list[str] = []
    url: str | None = f"https://{host}/v2/{repo}/tags/list?n=1000"
    refreshed = False
    for page in range(MAX_PAGES):
        try:
            data, link = _get_page(url, token)
        except urllib.error.HTTPError as e:
            if page == 0 and e.code in (401, 403, 404):
                return []
            # Anonymous tokens last a few minutes; a long listing can outlive one.
            if e.code == 401 and not refreshed:
                token, refreshed = _token(host, repo), True
                continue
            raise RuntimeError(
                f"{ref}: tag listing failed on page {page + 1} with HTTP {e.code} "
                f"after {len(out)} tags"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"{ref}: tag listing failed on page {page + 1} ({e.reason}) "
                f"after {len(out)} tags"
            ) from e
        refreshed = False
        out.extend(data.get("tags") or [])
        url = _next_url(host, link)
        if not url:
            return out
    raise RuntimeError(f"{ref}: more than {MAX_PAGES} pages of tags; refusing to truncate")


def latest(ref: str) -> str | None:
    """The highest release-looking tag."""
    best = None
    best_key = ()
    calver_best = None
    calver_key = 0
    for t in tags(ref):
        if PRERELEASE_RE.search(t) or DATE_RE.match(t):
            continue
        cal = CALVER_RE.match(t)
        if cal:
            n = int(cal.group(1))
            if n > calver_key:
                calver_key, calver_best = n, t
            continue
        stripped = PREFIX_RE.sub("", t)
        m = RELEASE_RE.match(stripped)
        if not m:
            continue
        key = tuple(int(x) for x in m.groups(default="0"))
        # At the same version, prefer the exact `v2.16.0` over the floating
        # `v2.16` that many projects also push, then a plain `1.2.3` over
        # `1.2.3-alpine`, so the catalogue records the tag most projects
        # document. Without this the winner depended on listing order.
        exact = 1 if m.group(3) is not None else 0
        plain = 1 if re.fullmatch(r"v?\d+\.\d+(\.\d+)?", stripped) else 0
        if (key, exact, plain) > best_key:
            best_key = (key, exact, plain)
            best = t
    # Semver wins when a repo has both; a project using calendar tags has no
    # semver tags at all, so this only fires where it is the real scheme.
    return best or calver_best


def _hub_arch(repo: str, tag: str) -> list[str] | None:
    """Architectures from Docker Hub's own API rather than the registry.

    Manifest requests against `registry-1.docker.io` count against the
    anonymous pull limit (100 per six hours per IP), and resolving a few dozen
    images exhausts it — at which point every lookup returns nothing and the
    catalogue quietly records "no architectures" for images that are fine.
    `hub.docker.com` serves the same information, is not metered the same way,
    and answers in one request. Returns None if the call fails, so the caller
    can still fall back to the registry.
    """
    try:
        data = _get(f"https://hub.docker.com/v2/repositories/{repo}/tags/{tag}")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None
    found = {
        i.get("architecture")
        for i in (data.get("images") or [])
        if i.get("os") == "linux" and i.get("architecture") in ("amd64", "arm64")
    }
    return sorted(found) if found else None


def arch(ref: str, tag: str) -> list[str]:
    host, repo = _split(ref)
    if host == "registry-1.docker.io":
        hub = _hub_arch(repo, tag)
        if hub is not None:
            return hub
    token = _token(host, repo)
    accept = ", ".join([
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ])
    try:
        data = _get(f"https://{host}/v2/{repo}/manifests/{tag}", token, accept)
    except (urllib.error.URLError, urllib.error.HTTPError):
        return []
    found = set()
    for m in data.get("manifests") or []:
        p = m.get("platform") or {}
        if p.get("os") == "linux" and p.get("architecture") in ("amd64", "arm64"):
            found.add(p["architecture"])
    if found:
        return sorted(found)

    # A single-platform manifest — no index, no platform list. This is the case
    # worth getting right rather than reporting as unknown: an image published
    # for one architecture is precisely the trap the `arch` field exists to
    # catch, and "unknown" reads as "probably fine". The architecture is in the
    # config blob, which costs one more request.
    digest = (data.get("config") or {}).get("digest")
    if not digest:
        return []
    try:
        cfg = _get(f"https://{host}/v2/{repo}/blobs/{digest}", token,
                   "application/vnd.oci.image.config.v1+json")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return []
    a = cfg.get("architecture")
    return [a] if a in ("amd64", "arm64") else []


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    cmd, ref = sys.argv[1], sys.argv[2]
    try:
        if cmd == "tags":
            print("\n".join(sorted(tags(ref))))
            return 0
        if cmd == "latest":
            v = latest(ref)
            print(v or "")
            return 0 if v else 1
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    if cmd == "arch":
        if len(sys.argv) < 4:
            print("arch needs a tag", file=sys.stderr)
            return 2
        a = arch(ref, sys.argv[3])
        print(",".join(a))
        return 0 if a else 1
    print(f"unknown command {cmd!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
