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
| RSSHub | `diygod/rsshub` publishes only commit-hash tags (no semver/dated releases). Nothing pinnable. |
| JARR | No official image found on Docker Hub or GHCR under the project's namespace. |
| Tiny Tiny RSS | No official Docker image from the tt-rss project itself; only third-party rebuilds (e.g. `cthulhoo/ttrss-fpm-pgsql-official`) exist. |
| Goeland | No HTTP listening port — it's a feed-to-email/webhook processor with no web UI, which this catalogue's schema doesn't model. |
| TinyFeed | Its Dockerfile has no `EXPOSE`/`CMD`; it's a CLI that generates a static HTML page rather than a standing web server, so port/deployment shape is unclear. |
| Readflow | Requires a basic-auth passwd file mounted into the container but the exact env var name and mount path aren't documented clearly enough to pin with confidence. |
| Speedtest Tracker | The project's own image (`ghcr.io/alexjustesen/speedtest-tracker`, v0.19.0) looks stale next to the actively-updated LinuxServer.io build (`lscr.io/linuxserver/speedtest-tracker`, v1.10.0); unclear which is actually the maintained "official" image. |

## Not rejections

Two things that look like rejections but aren't:

**amd64-only images are still catalogued.** They get `arch: [amd64]` and that
is the useful answer — the field exists precisely so you find out before you
deploy. `calibre-web` is in the catalogue on those terms.

**Apps needing more than one container are still catalogued.** They carry
`needs:` listing what else they want. Immich, Paperless-ngx, SearXNG, Tube
Archivist and Yopass are all present and correct; they just aren't a
one-container install.
