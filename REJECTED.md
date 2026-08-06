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

## Not rejections

Two things that look like rejections but aren't:

**amd64-only images are still catalogued.** They get `arch: [amd64]` and that
is the useful answer — the field exists precisely so you find out before you
deploy. `calibre-web` is in the catalogue on those terms.

**Apps needing more than one container are still catalogued.** They carry
`needs:` listing what else they want. Immich, Paperless-ngx, SearXNG, Tube
Archivist and Yopass are all present and correct; they just aren't a
one-container install.
