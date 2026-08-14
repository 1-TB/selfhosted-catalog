# Entry schema

One YAML file per app, in `apps/`. The filename must match the `slug`.

## Required

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Lowercase, digits and dashes. Must start with a letter. Matches the filename. |
| `name` | string | Display name, as the project spells it. |
| `category` | string | One of the categories listed below. |
| `image` | string | Repository only, no tag and no digest. |
| `version` | string | An exact tag. Never `latest`. |
| `arch` | list | Architectures the image is actually published for. See below. |
| `port` | int | The port the app listens on inside the container. |

## Optional

| Field | Type | Default | Notes |
|---|---|---|---|
| `description` | string | `""` | One line. |
| `homepage` | string | `""` | Project site. |
| `source` | string | `""` | Repository URL. |
| `subdomain` | string | slug | Hostname label, when it differs from the slug. |
| `container_name` | string | slug | Only when the app needs a specific name. |
| `mem_limit` | string | `512m` | Roughly 2.5-3x observed idle RSS. |
| `health_path` | string | `""` | HTTP path for a healthcheck. Empty means don't probe. |
| `database` | string | `none` | `none`, `postgres`, `mariadb` or `mongo`. |
| `needs` | list | `[]` | Extra services beyond one database, e.g. `[redis]`. See below. |
| `auth` | string | `proxy` | `oidc`, `proxy` or `none`. |
| `redirect_path` | string | `""` | OAuth callback path. Required when `auth: oidc`. |
| `env` | list | `[]` | Environment variables. See below. |
| `volumes` | list | `[]` | Persistent data. See below. |
| `notes` | string | `""` | Anything a form can't express. |

## arch

Mandatory, and it is not a formality. A manifest for an amd64-only image
resolves perfectly happily on an arm64 machine — the failure shows up at
deploy time as an exec-format error, or as a container that restarts forever.
Several widely-recommended images are amd64-only: `postgis/postgis`,
`clamav/clamav` and `m1k1o/neko` among them.

Values are `amd64` and `arm64`. Check with:

```
docker buildx imagetools inspect <image>:<tag> | grep Platform
```

`tools/check-arch.sh` does this for every entry in the catalogue and reports
disagreements.

## needs

Some apps want more than one container and one database. `needs` records what,
so a consumer that only models a single database sidecar can filter those
entries out rather than rendering something that won't start:

```yaml
needs: [redis]
```

Entries with a non-empty `needs` are still useful — they carry the image, the
port, the env vars and the arch — they just aren't a one-shot install everywhere.

## auth

How the app authenticates, so a consumer knows whether to register an OAuth
client or put a proxy in front:

- `oidc` — the app speaks OpenID Connect itself. Set `redirect_path`.
- `proxy` — no usable auth of its own, or auth you'd rather not manage. Put a
  forward-auth proxy in front.
- `none` — meant to be reachable without a login.

## env

```yaml
env:
  - name: BASE_URL
    value: https://miniflux.${DOMAIN}/
  - name: ADMIN_PASSWORD
    secret: true
  - name: SESSION_SECRET
    secret: true
    source: generated
  - name: OAUTH2_CLIENT_ID
    secret: true
    source: oidc_client_id
```

`${DOMAIN}` is left for the consumer to substitute. `secret: true` means the
value must not be written into a compose file in cleartext. `source` says where
the value comes from, and a secret with no source is one the operator has to go
and get — an API token, a licence key, a password the app was given elsewhere:

- `generated` — any random string will do. A session key, a signing secret, an
  internal service password. This is the one that decides whether an install
  can run unattended, so it is worth setting: without it a consumer has to stop
  and ask a human for a value nobody will ever type again.
- `oidc_client_id`, `oidc_client_secret`, `oidc_issuer`, `oidc_discovery_url` —
  the value does not exist until an OAuth client has been created, so it cannot
  be filled in before the app is registered with the provider.

Where an app documents a length or an encoding (`openssl rand -hex 64`, an
exactly-32-character key), say so in `notes` — `generated` says a random value
is acceptable, not what shape it has to be.

Database connection strings reference the password by variable name, e.g.
`${MINIFLUX_DB_PASSWORD}`, using the convention `<SLUG>_DB_PASSWORD` with
dashes replaced by underscores.

## volumes

```yaml
volumes:
  - path: data
    mount: /var/lib/app
```

`path` is relative to wherever the consumer keeps that app's data. `mount` is
the absolute path inside the container.

## categories

`archiving`, `automation`, `communication`, `developer`, `documents`, `feeds`,
`files`, `games`, `media`, `monitoring`, `network`, `productivity`, `security`,
`utilities`
