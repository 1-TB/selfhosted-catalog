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
| BookStack | The project itself publishes no container image; the only actively maintained image is the third-party `linuxserver/bookstack` rebuild. No official namespace to point at. |
| RSSHub | `ghcr.io/diygod/rsshub` only publishes commit-hash tags (e.g. `c92f107...`) and date-stamped tags (e.g. `2026-08-06`) plus a floating `latest`/`chromium-bundled`. Nothing semver to pin. |
| Recipya | No official image resolves at all - `reaper47/recipya` returns no tags on Docker Hub or GHCR. |
| TinyFeed | `thebigroomxxl/tinyfeed` resolves fine, but the app itself is a static-site generator (or a daemon that periodically regenerates a static file), not a web server - its own docs say a separate web server container (Caddy/nginx) is required to actually serve the output. Doesn't fit the one-container-behind-a-subdomain model. |
| SiYuan | `b3log/siyuan` resolves fine, but since v3.7.0 the container requires the workspace path and access code to be passed as command-line arguments to an explicit `serve` subcommand, not environment variables. This schema has no field for a command override, so modeling it here would mean guessing whether an env-var equivalent is honored. |
| Wekan | `wekanteam/wekan`/`ghcr.io/wekan/wekan` resolves fine, but real-time updates require MongoDB running with a single-node replica set (`--replSet`) and a `MONGO_OPLOG_URL`, not a plain mongo sidecar - upstream's own current docker-compose has moved to bundling FerretDB instead of plain MongoDB precisely because of this. Too special-cased for the single-database-sidecar model this catalogue assumes for `database: mongo`. |
| OpenSign | `opensign/opensignserver` and `opensign/opensign` only publish a floating `main` tag - nothing pinnable. Even setting that aside, a real deployment is four containers (server, client, MongoDB, Caddy reverse proxy), well past this catalogue's one-extra-service model. |
| Selfoss | No official Docker image. The project's docs and repo only cover uploading files to a webserver or building from source with Composer/npm; no Docker Hub or GHCR namespace is published. |
| Docspell | Resolves fine (`docspell/restserver`, `docspell/joex`) but a real deployment needs the REST server, a separate job-executor (`joex`) container, and Solr for full-text search, on top of Postgres - two extra services beyond one database, past what `needs:` is meant to model here. |
| Feeds Fun | No official image published to any registry - the project only ships a `docker-compose.yml` and build scripts for building the image yourself. Also needs Postgres plus separate loader/librarian worker processes, past a one-container model. |
| yarr | No official image found on Docker Hub or GHCR under the project's own namespace; ships as a Go binary/systemd service, not a container. |
| Goeland | `slurdge/goeland` resolves fine (pinnable tags, amd64+arm64) but it's a config-file-driven RSS-to-email digest tool with no web UI and no listening port - doesn't fit the one-container-behind-a-subdomain model this catalogue assumes. |
| Readflow | `ncarlier/readflow` resolves (`1.2.0`, amd64 only) but that's the only versioned release tag ever cut, dated March 2024; everything since tracks the floating `edge` tag instead. A two-and-a-half-year-old pin behind an app whose maintainer has moved to a rolling release model isn't worth cataloguing over `edge`. |
| bewCloud | `ghcr.io/bewcloud/bewcloud` resolves fine (pinnable tags, amd64+arm64), but a real deployment needs Postgres plus a separate Radicale (CalDAV/CardDAV) container - and the app itself is a general personal-cloud (files/notes/photos), only loosely tagged under feed readers upstream. Left out this run for scope reasons; worth a second look as a `needs: [radicale]` entry for the files/productivity category instead. |
| blocky | `ghcr.io/0xerr0r/blocky` resolves fine (pinnable tags, amd64+arm64) but it's a DNS resolver with no built-in web UI - the dashboard is a separate companion project. Serves DNS on :53, not HTTP behind a subdomain; doesn't fit this catalogue's model the way Pi-hole/AdGuard Home/Technitium (which ship their own UI) do. |
| Upvote RSS | `ghcr.io/johnwarne/upvote-rss` resolves fine (pinnable tags, amd64+arm64) and has a web UI with no login, but it's a narrow Reddit/HN/Lemmy-aggregation tool with ~25 mostly-optional env vars (AI provider keys, Redis, Browserless, Mercury/Readability parsers) and no clear "these are the ones that matter" subset. Left out for being more niche than widely-recommended. |
| FreeScout | The project has no image in its own namespace; `freescout.net/docker/` redirects straight to a third-party rebuild (`tiredofit/docker-freescout`). No official image to point at. |
| LinkStack | `linkstackorg/linkstack` publishes no numbered release tags on Docker Hub - just `latest`, `beta`, `V4`, `laravel12`, `unraid` and separate per-arch tags (`amd64`, `arm64v8`, `arm32v6`, `arm32v7`) instead of one multi-arch manifest per version. Nothing pinnable that also carries both architectures. |
| Zammad | `zammad/zammad-docker-compose` resolves pinnable tags and multi-arch, but it's not a single app container - the real deployment splits the same image across railsserver/scheduler/websocket/nginx roles plus Postgres, Elasticsearch and Redis. Three extra services beyond one database, well past what `needs:` is meant to model. |
| TimeTagger | `almarklein/timetagger` returns no tags at all from the registry - either the project doesn't publish to that namespace or distributes some other way. Didn't chase down the correct location this run. |

## Not rejections

Two things that look like rejections but aren't:

**amd64-only images are still catalogued.** They get `arch: [amd64]` and that
is the useful answer — the field exists precisely so you find out before you
deploy. `calibre-web` is in the catalogue on those terms.

**Apps needing more than one container are still catalogued.** They carry
`needs:` listing what else they want. Immich, Paperless-ngx, SearXNG, Tube
Archivist and Yopass are all present and correct; they just aren't a
one-container install.
