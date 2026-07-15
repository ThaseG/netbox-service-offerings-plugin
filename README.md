# netbox-service-offerings-plugin (CSDM)

A [NetBox](https://github.com/netbox-community/netbox) plugin that lets you build a **Common Service Data Model
(CSDM)** directly in NetBox: Service Portfolios, Services, Service Offerings, Application Services and Technical
CIs, all linked to the infrastructure objects (devices, virtual machines, clusters) NetBox already knows about, and
to the contacts/contact-groups/tenants that own and support them.

The plugin's Django app label is `csdm`.

## Screenshots

> _TODO: add screenshots here._

| Service Portfolio list | Service Offering detail | Data model menu |
| --- | --- | --- |
| _placeholder_ | _placeholder_ | _placeholder_ |

## Data model

Models are organized into two groups, matching the plugin's navigation menu.

### Data Model group

A `Portfolio` groups one or more `Service`s; a `Service` is sold to customers as one or more `ServiceOffering`s;
each `ServiceOffering` is realized by one or more `AppService`s; and any of the three can reference the
`TechCI`s that implement them.

| Model | Description |
| --- | --- |
| **Portfolio** (Service Portfolio) | Top-level grouping of related services. Has an owner and a manager (each a contact and/or contact group) and a `Lifecycle`. |
| **Service** | A business or technical service. Belongs to one or more portfolios; has owner/manager, business unit, support group and change group (contact groups); optionally linked to `TechCI`s. |
| **ServiceOffering** | A specific offering of a service to customers, identified by a contract number. Belongs to one or more services; optionally scoped to a `Tenant`/`TenantGroup`. |
| **AppService** | An application-level realization of a service offering, carrying operational commitments: accepted downtime, TTR, RPO, RTO, BCM, plus links to `SLA`, `OperationTime`, `Availability`, `Criticality` and `MTAT`. Requires an `Environment`. |
| **TechCI** (Technical CI) | A technical configuration item with a function, optionally linked to NetBox `Device`, `VirtualMachine`, `Cluster` and `ClusterGroup` objects. |

### Support group

Small organizational/lookup models referenced by the models above — each just a name, optional description,
tags and comments (plus a couple of extra fields noted below):

| Model | Extra fields | Used by |
| --- | --- | --- |
| **Lifecycle** | — | Portfolio, Service, ServiceOffering, AppService, TechCI |
| **SLA** | `sla_definition` | AppService |
| **OperationTime** | — | AppService |
| **Availability** | — | AppService |
| **Criticality** | — | AppService (as `service_criticality`) |
| **Environment** | — | AppService |
| **MTAT** | `value` (integer), `unit` (Seconds/Minutes/Hours/Days/Weeks/Months/Years) | AppService |

All models support NetBox's standard object features: tags, comments (Markdown), custom fields, custom links,
change logging, journaling and bookmarks.

## Compatibility

| CSDM Plugin Version | NetBox Version | Python Version |
| --- | --- | --- |
| 1.0.* | 4.6.x | \>= 3.10 |

The pinned combination actually built and deployed by this repo's CI/CD pipeline is tracked in
[`versions.sh`](versions.sh) (currently NetBox `v4.6.4`).

## Installation

### Option A: existing NetBox installation

Install the plugin into NetBox's virtual environment:

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/<org>/netbox-service-offerings-plugin.git
```

Enable it in `/opt/netbox/netbox/netbox/configuration.py` (or `plugins.py` if you split your config that way):

```python
PLUGINS = [
    "csdm",
]
```

Then run migrations and collect static files as usual:

```bash
python manage.py migrate
python manage.py collectstatic --no-input
```

Restart NetBox (`systemctl restart netbox netbox-rq` or equivalent).

### Option B: Docker (bundled demo/CI stack)

This repo includes a full Docker Compose deployment under [`ci/docker/`](ci/docker/) that builds NetBox with this
plugin (and a few third-party plugins — see [`ci/docker/plugin_requirements.txt`](ci/docker/plugin_requirements.txt))
baked in via [`ci/docker/Dockerfile-Plugins`](ci/docker/Dockerfile-Plugins). It's what
[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) deploys automatically on every push, complete with
HTTPS via Let's Encrypt. To run it yourself:

```bash
source versions.sh
cp ci/docker/.env.example ci/docker/.env   # fill in real values, see comments in the file
docker compose --env-file ci/docker/.env -f ci/docker/docker-compose.yml up -d --build
```

## Usage

### Web UI

Once enabled, a **CSDM** entry appears in NetBox's plugins navigation menu, with **Data Model** and **Support**
groups matching the tables above. Each model gets the standard NetBox list/detail/add/edit/delete views.

### REST API

All models are exposed under `/api/plugins/csdm/`, following NetBox's usual REST conventions (list/detail views,
filtering, `?brief=true`, bulk operations). Example — create a `Lifecycle`, then read it back:

```bash
curl -X POST https://<netbox-host>/api/plugins/csdm/lifecycle/ \
  -H "Authorization: Bearer nbt_<key>.<secret>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Pilot", "slug": "pilot"}'

curl https://<netbox-host>/api/plugins/csdm/lifecycle/ \
  -H "Authorization: Bearer nbt_<key>.<secret>"
```

(Use `Authorization: Token <value>` instead if you're using a legacy v1 API token.)

### GraphQL

If `GRAPHQL_ENABLED` is on, all CSDM models are also queryable at `/graphql/`, e.g.:

```graphql
query {
  portfolio_list {
    name
    lifecycle { name }
  }
}
```

### Permissions

Access is controlled by NetBox's standard per-model permissions, e.g. `csdm.view_service`, `csdm.add_service`,
`csdm.change_service`, `csdm.delete_service` (and equivalently for every other model).

## Development

| Path | Purpose |
| --- | --- |
| [`csdm/`](csdm/) | The plugin itself — models, REST API, UI views, GraphQL, migrations, tests. |
| [`ci/docker/`](ci/docker/) | Docker Compose stack + Dockerfile used both for local runs and the CI/CD deploy. |
| [`ci/scripts/`](ci/scripts/) | Shell scripts used by the CI/CD pipeline (cert issuance, pre-cleanup, smoke tests). |
| [`versions.sh`](versions.sh) | Single source of truth for the pinned NetBox version and the plugin's own release version. |
| [`pyproject.toml`](pyproject.toml) | Package metadata, plus `ruff` lint/format configuration. |

Run the test suite and linters the same way CI does:

```bash
ruff check csdm/
ruff format --check csdm/
python manage.py test csdm
```

### CI/CD

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on every push, as five staged jobs:

1. **Pre-Clean** — tears down any previously running stack, guaranteeing a clean slate.
2. **Code-Review** — `ruff`, `shellcheck`, `yamllint`, and a check that `pyproject.toml`'s version matches
   `versions.sh`.
3. **Build** — builds the NetBox + plugins Docker image per `versions.sh`.
4. **Test** — deploys the stack, runs `manage.py check`, a migration drift check, the Django test suite, and a
   live HTTPS smoke test (session login + a full API POST/GET/PATCH/DELETE round trip).
5. **Deploy** — tags the repo `v<CSDM_PLUGIN_VERSION>` (from `versions.sh`), if that tag doesn't already exist.

The instance left running after a successful **Test** stage doubles as a live showcase.

## License

[MIT](LICENSE)
