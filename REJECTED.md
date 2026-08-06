# Considered and left out

Apps that were looked at and are deliberately not in `apps/`, with the reason.
Kept so the same dead ends don't get researched twice.

Being here isn't a judgement on the software. Almost every entry below is a
packaging problem, not a quality one, and a project that starts publishing
release tags should be moved into `apps/`.

| App | Why |
|---|---|
| Excalidraw | Publishes only `latest` and `sha-<commit>` tags. Nothing pinnable. |
| Lychee | No version tags on Docker Hub; the tags are all `testing-<build id>`. |
| Scribble.rs | Could not resolve a package at `ghcr.io/scribble-rs/scribble.rs`. Needs someone to confirm where the image actually lives. |
| JSON Crack | No official image found. The reference commonly passed around does not resolve. |
| Cronicle | No single project-maintained image. Docker Hub and GHCR only turn up third-party rebuilds (soulteary/cronicle, vimagick/cronicle, bluet/cronicle-docker, a community fork cronicle-edge/cronicle-edge); the upstream jhuckaby/Cronicle project doesn't publish its own. |
| Gotenberg | Resolves fine (gotenberg/gotenberg, pinnable tags, amd64+arm64) but it's a stateless internal conversion API with no web UI and no auth of its own - its own docs say to firewall it off, not expose it. Doesn't fit this catalogue's one-container-behind-a-subdomain model; would need a real consumer (like Paperless-ngx) in front of it, not a subdomain of its own. |
| Activepieces | Official image resolves, but a real deployment needs three containers minimum (app + worker + redis) plus Postgres built from `pgvector/pgvector`, not plain `postgres` - unclear whether the vector extension is a hard migration requirement or just powers an optional AI feature. SSO is Enterprise-only, so community edition is local-login only. Left out this run rather than guess at the Postgres image swap; worth revisiting with more time to confirm the pgvector requirement. |
| Shlink | Official image resolves and is well maintained, but `shlinkio/shlink` is an API-only backend with no web UI at all - the actual UI lives in a separate `shlinkio/shlink-web-client` container. Modeling it as one catalogue entry would either omit the UI or omit the backend's own config; left out rather than half-model a two-container app. |
| RSS-Bridge | `rssbridge/rss-bridge` only publishes date-stamped tags (e.g. `2025-08-05`) plus `latest`/`latest-arch` floats. No semver or calver release tag to pin. |
| Tiny Tiny RSS | Both `ghcr.io/tt-rss/tt-rss` and `ghcr.io/tt-rss/tt-rss-web-nginx` publish only `latest` and `sha-<commit>` tags. Nothing pinnable. |
| JupyterLab (Jupyter Docker Stacks) | `quay.io/jupyter/base-notebook` (and siblings) publish only date-stamped tags, same problem as RSS-Bridge. No numbered release to pin. |

## Not rejections

Two things that look like rejections but aren't:

**amd64-only images are still catalogued.** They get `arch: [amd64]` and that
is the useful answer — the field exists precisely so you find out before you
deploy. `calibre-web` is in the catalogue on those terms.

**Apps needing more than one container are still catalogued.** They carry
`needs:` listing what else they want. Immich, Paperless-ngx, SearXNG, Tube
Archivist and Yopass are all present and correct; they just aren't a
one-container install.
