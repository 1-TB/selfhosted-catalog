# selfhosted-catalog

Machine-readable definitions for self-hosted apps: which image, which port,
which environment variables, what it stores, and which CPU architectures it
actually ships for.

It is data, not a deployment tool. Nothing here runs anything. The point is
that the boring research behind adding an app — reading a README, digging the
port out of a Dockerfile, working out whether the thing runs on arm64 — is
written down once in a form a script can read.

70 apps so far. Every entry is validated in CI and its architectures are
checked against the registry.

## Why not just read the upstream compose file

Most upstream compose files are written to get you running in one command, so
they tend to carry things you don't want in a managed setup: `latest` tags,
named volumes, published ports, `restart: always`, and a database password
inline. They also don't tell you the two things that most often waste an
afternoon:

**Architecture.** A manifest for an amd64-only image resolves perfectly happily
on an arm64 machine. Nothing complains until deploy, and then it's an
exec-format error or a container that restarts forever. `postgis/postgis`,
`clamav/clamav` and `m1k1o/neko` are all amd64-only, and plenty of guides
recommend them without mentioning it. Every entry here records what the
registry actually publishes.

**What else it needs.** "Install Paperless" is four containers. `needs:` says so
up front, so a tool that only models one app plus one database can filter those
entries out instead of rendering something that won't start.

## Layout

```
apps/           one YAML file per app, named after its slug
tools/          validator and registry helpers
SCHEMA.md       the field reference
```

## Using it

Read the YAML. That's the whole interface.

```python
import yaml, pathlib

apps = {}
for p in pathlib.Path("apps").glob("*.yml"):
    entry = yaml.safe_load(p.read_text())
    apps[entry["slug"]] = entry

arm = [a for a in apps.values() if "arm64" in a["arch"]]
simple = [a for a in arm if not a.get("needs")]
```

Entries deliberately do not carry a digest. The catalogue records which image
and which release; resolve the digest against the registry when you install, so
you get the right one for the architecture you're installing on.

`${DOMAIN}` in a value is left for you to substitute. Database passwords are
referenced by variable name (`${MINIFLUX_DB_PASSWORD}`), never by value.

## Tools

```
tools/validate.py              check every entry against the schema
tools/registry.py latest REPO  highest release tag for an image
tools/registry.py arch REPO TAG  architectures that tag was built for
tools/check-arch.sh            compare every entry against the registry
```

These need python and network access. Nothing here needs docker or a registry
login — `registry.py` speaks the OCI distribution API directly. For Docker Hub images it reads architectures from the Hub API
rather than pulling manifests, because manifest requests count against the
anonymous pull limit and resolving a few dozen images exhausts it — after which
every lookup returns nothing and looks like "no architectures" rather than
"rate limited".

## Contributing

Add a file to `apps/`, named after the slug, and run `tools/validate.py`.

Things that will get an entry rejected:

- A floating tag. `latest`, `stable`, `dev` and bare major versions are not
  pinnable, and an entry that can't be pinned isn't much use.
- A missing or guessed `arch`. Check it: `tools/registry.py arch <image> <tag>`.
- A secret with a value in it.
- A volume path that escapes the app's own data directory.

Corrections are as welcome as additions. A wrong port or a stale env var is
worse than a missing entry, because it looks like it works.

[REJECTED.md](REJECTED.md) lists apps that were looked at and left out, with
the reason. Check it before adding something, and add to it if you rule
something out, so the same dead ends don't get researched twice.

## License

MIT. See [LICENSE](LICENSE).
