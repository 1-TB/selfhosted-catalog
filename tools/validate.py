#!/usr/bin/env python3
"""Check every entry in apps/ against the schema.

Exits non-zero on the first file that fails, so it works as a CI gate.
Run with no arguments from the repo root.
"""

import re
import sys
from pathlib import Path

import yaml

SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
# POSIX-ish, not SHOUTING_ONLY. Gitea's `GITEA__database__HOST` and Vikunja's
# section-style names are real, documented environment variables, and a rule
# that rejected them would only mean the catalogue lied about the app.
ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
# Two or more numeric components, optionally prefixed, optionally suffixed —
# or a six-digit YYMMDD calendar tag, which is the real release scheme for a
# few projects and is just as immutable. Catches `latest`, `stable`, `dev`,
# bare `16` and floating branch tags.
VERSION_RE = re.compile(r"^((version-|release-)?v?\d+\.\d+|\d{6}$)")
MEM_RE = re.compile(r"^\d+(\.\d+)?[kmgKMG]$")

ARCHES = {"amd64", "arm64"}
DATABASES = {"none", "postgres", "mariadb", "mongo"}
AUTH = {"oidc", "proxy", "none"}
SECRET_SOURCES = {
    "generated",
    "oidc_client_id",
    "oidc_client_secret",
    "oidc_issuer",
    "oidc_discovery_url",
}
CATEGORIES = {
    "archiving", "automation", "communication", "developer", "documents",
    "feeds", "files", "games", "media", "monitoring", "network",
    "productivity", "security", "utilities",
}

REQUIRED = ("slug", "name", "category", "image", "version", "arch", "port")
KNOWN = set(REQUIRED) | {
    "description", "homepage", "source", "subdomain", "container_name",
    "mem_limit", "health_path", "database", "needs", "auth", "redirect_path",
    "env", "volumes", "notes",
}


def check(path: Path) -> list[str]:
    errs: list[str] = []

    def bad(msg: str) -> None:
        errs.append(f"{path.name}: {msg}")

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        return [f"{path.name}: not valid YAML: {e}"]
    if not isinstance(raw, dict):
        return [f"{path.name}: expected a mapping at the top level"]

    for key in REQUIRED:
        if not raw.get(key):
            bad(f"{key} is required")
    if errs:
        return errs

    for key in sorted(set(raw) - KNOWN):
        bad(f"unknown field {key!r}")

    slug = str(raw["slug"])
    if not SLUG_RE.match(slug):
        bad(f"slug {slug!r} is not a valid slug")
    if path.stem != slug:
        bad(f"filename does not match slug {slug!r}")

    if raw["category"] not in CATEGORIES:
        bad(f"unknown category {raw['category']!r}")

    image = str(raw["image"])
    if ":" in image.rsplit("/", 1)[-1] or "@" in image:
        bad("image must be the repository only, with no tag and no digest")

    version = str(raw["version"])
    # ente's official GHCR images publish only commit SHAs and latest —
    # there is no numbered tag to pin. latest is forbidden everywhere else.
    if version == "latest":
        if slug != "ente":
            bad("version 'latest' is not an exact version tag")
    elif not VERSION_RE.match(version):
        bad(f"version {version!r} is not an exact version tag")

    arch = raw["arch"]
    if not isinstance(arch, list) or not arch:
        bad("arch must be a non-empty list")
    else:
        for a in arch:
            if a not in ARCHES:
                bad(f"unknown arch {a!r}")

    try:
        port = int(raw["port"])
        if not 1 <= port <= 65535:
            bad("port must be 1-65535")
    except (TypeError, ValueError):
        bad(f"port {raw['port']!r} is not a number")

    if raw.get("database", "none") not in DATABASES:
        bad(f"unknown database {raw.get('database')!r}")

    auth = raw.get("auth", "proxy")
    if auth not in AUTH:
        bad(f"unknown auth {auth!r}")
    if auth == "oidc" and not raw.get("redirect_path"):
        bad("auth is oidc, so redirect_path is required")
    for field in ("health_path", "redirect_path"):
        val = raw.get(field)
        if val and not str(val).startswith("/"):
            bad(f"{field} must start with /")

    if raw.get("mem_limit") and not MEM_RE.match(str(raw["mem_limit"])):
        bad(f"mem_limit {raw['mem_limit']!r} is not a size like 512m or 2g")

    if not isinstance(raw.get("needs", []), list):
        bad("needs must be a list")

    seen_env: set[str] = set()
    for e in raw.get("env") or []:
        if not isinstance(e, dict) or not e.get("name"):
            bad("each env entry needs a name")
            continue
        name = str(e["name"])
        if not ENV_NAME_RE.match(name):
            bad(f"{name!r} is not a valid environment variable name")
        if name in seen_env:
            bad(f"{name} is set twice")
        seen_env.add(name)
        src = e.get("source")
        if src and src not in SECRET_SOURCES:
            bad(f"{name}: unknown source {src!r}")
        if src and not e.get("secret"):
            bad(f"{name}: has a source but is not marked secret")
        if e.get("secret") and "value" in e and not src:
            bad(f"{name}: a secret must not carry a value")

    seen_mounts: set[str] = set()
    for v in raw.get("volumes") or []:
        if not isinstance(v, dict) or not v.get("path") or not v.get("mount"):
            bad("each volume needs a path and a mount")
            continue
        if not str(v["mount"]).startswith("/"):
            bad(f"mount {v['mount']!r} must be absolute")
        if ".." in str(v["path"]).split("/"):
            bad(f"path {v['path']!r} must stay inside the app's data directory")
        if v["mount"] in seen_mounts:
            bad(f"{v['mount']} is mounted twice")
        seen_mounts.add(str(v["mount"]))

    return errs


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "apps"
    files = sorted(root.glob("*.yml"))
    if not files:
        print("no entries found in apps/", file=sys.stderr)
        return 1

    all_errs: list[str] = []
    slugs: dict[str, str] = {}
    for path in files:
        all_errs.extend(check(path))
        try:
            slug = (yaml.safe_load(path.read_text()) or {}).get("slug")
        except yaml.YAMLError:
            continue
        if slug in slugs:
            all_errs.append(f"{path.name}: duplicate slug {slug!r} (also {slugs[slug]})")
        elif slug:
            slugs[slug] = path.name

    for err in all_errs:
        print(err, file=sys.stderr)
    print(f"{len(files)} entries, {len(all_errs)} problems")
    return 1 if all_errs else 0


if __name__ == "__main__":
    sys.exit(main())
