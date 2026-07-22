# netbox-service-offerings-plugin (Service Specification)

A [NetBox](https://github.com/netbox-community/netbox) plugin that lets you build a **Service Specification**
model directly in NetBox: Service Portfolios, Services, Service Offerings and Application Services, all linked to
the infrastructure objects (devices, virtual machines, clusters, cluster groups) NetBox already knows about, and
to the contacts/contact-groups/tenants that own and support them.

The plugin's Django app label is `service_specification`.

## Screenshots

> _TODO: add screenshots here._

| Service Portfolio list | Service Offering detail | Data model menu |
| --- | --- | --- |
| _placeholder_ | _placeholder_ | _placeholder_ |

## Data model

Models are organized into two groups, matching the plugin's navigation menu.

### Data Model group

A `Portfolio` groups one or more `Service`s; a `Service` is sold to customers as one or more `ServiceOffering`s;
each `ServiceOffering` is realized by one or more `AppService`s.

| Model | Description |
| --- | --- |
| **Portfolio** (Service Portfolio) | Top-level grouping of related services. Has an owner and a manager (each a contact and/or contact group) and a `Lifecycle`. |
| **Service** | A business or technical service. Belongs to one or more portfolios; has owner/manager, business unit, support group and change group (contact groups); optionally linked to a `CIFunction`. |
| **ServiceOffering** | A specific offering of a service to customers, identified by a contract number. Belongs to one or more services; optionally scoped to a `Tenant`/`TenantGroup`. |
| **AppService** | An application-level realization of a service offering, carrying operational commitments: accepted downtime, TTR, RPO, RTO, BCM, plus links to `SLA`, `OperationTime`, `Availability`, `Criticality` and `MTAT`. Requires an `Environment`. |

A ServiceOffering's detail page also shows a read-only rollup table of its parent Service(s)' own parameters, and
an AppService's detail page shows read-only rollups of both its Service Offering(s) and the Service(s) behind
them — for context only; the actual relationships are still edited via the `service` / `service_offering` fields.

### Support group

Small organizational/lookup models referenced by the models above — each just a name, optional description,
tags and comments (plus a couple of extra fields noted below):

| Model | Extra fields | Used by |
| --- | --- | --- |
| **Lifecycle** | — | Portfolio, Service, ServiceOffering, AppService |
| **SLA** | `sla_definition` | AppService |
| **OperationTime** | — | AppService |
| **Availability** | — | AppService |
| **Criticality** | — | AppService (as `service_criticality`) |
| **Environment** | — | AppService |
| **MTAT** | `value` (integer), `unit` (Seconds/Minutes/Hours/Days/Weeks/Months/Years) | AppService |
| **CIFunction** | — | Service, and Device/VirtualMachine/Cluster/ClusterGroup (see below) |

All models support NetBox's standard object features: tags, comments (Markdown), custom fields, custom links,
change logging, journaling and bookmarks.

### Service Specification on core NetBox objects

`Device`, `VirtualMachine`, `Cluster` and `ClusterGroup` are core NetBox models — plugins can't add real database
fields to them directly. Instead, each gets a **Service Specification** tab on its own detail page (`/dcim/devices/
<id>/service-specification/` and the virtualization equivalents), backed by a plugin-owned side table
(`DeviceServiceInfo`, `VirtualMachineServiceInfo`, `ClusterServiceInfo`, `ClusterGroupServiceInfo`) in a one-to-one
relationship with the core object. Each carries a `CIFunction`, a `Lifecycle`, and Business Unit/Support Group/
Change Group (contact groups only, no individual contacts). The tab is read-only; an **Edit** button opens the
matching form. These side tables aren't separately listed in the plugin's own navigation menu or REST API — they're
reached only through the core object's tab.

## Compatibility

| Plugin Version | NetBox Version | Python Version |
| --- | --- | --- |
| 2.0.* | 4.6.x | \>= 3.10 |

The pinned combination actually built and deployed by this repo's CI/CD pipeline is tracked in
[`versions.sh`](versions.sh) (currently NetBox `v4.6.5`).

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
    "service_specification",
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

Once enabled, a **Service Specification** entry appears in NetBox's plugins navigation menu, with **Data Model**
and **Support** groups matching the tables above. Each model gets the standard NetBox list/detail/add/edit/delete
views.

### REST API

All models are exposed under `/api/plugins/service-specification/`, following NetBox's usual REST conventions
(list/detail views, filtering, `?brief=true`, bulk operations). API endpoint names are deliberately plural and
match the plugin's own UI paths exactly (e.g. UI `/plugins/service-specification/lifecycles/` <-> API
`/api/plugins/service-specification/lifecycles/`) — from any page in the plugin's UI, adding `/api` right after
the hostname takes you straight to the same list in the browsable API, nothing else in the path changes. Example —
create a `Lifecycle`, then read it back:

```bash
curl -X POST https://<netbox-host>/api/plugins/service-specification/lifecycles/ \
  -H "Authorization: Bearer nbt_<key>.<secret>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Pilot", "slug": "pilot"}'

curl https://<netbox-host>/api/plugins/service-specification/lifecycles/ \
  -H "Authorization: Bearer nbt_<key>.<secret>"
```

(Use `Authorization: Token <value>` instead if you're using a legacy v1 API token.)

### GraphQL

If `GRAPHQL_ENABLED` is on, all Service Specification models are also queryable at `/graphql/`, e.g.:

```graphql
query {
  portfolio_list {
    name
    lifecycle { name }
  }
}
```

### Permissions

Access is controlled by NetBox's standard per-model permissions, e.g. `service_specification.view_service`,
`service_specification.add_service`, `service_specification.change_service`, `service_specification.delete_service`
(and equivalently for every other model).

## Development

| Path | Purpose |
| --- | --- |
| [`service_specification/`](service_specification/) | The plugin itself — models, REST API, UI views, GraphQL, migrations, tests. |
| [`ci/docker/`](ci/docker/) | Docker Compose stack + Dockerfile used both for local runs and the CI/CD deploy. |
| [`ci/scripts/`](ci/scripts/) | Scripts used by the CI/CD pipeline (cert issuance, pre-cleanup, smoke tests, demo data seeding). |
| [`versions.sh`](versions.sh) | Single source of truth for the pinned NetBox version and the plugin's own release version. |
| [`pyproject.toml`](pyproject.toml) | Package metadata, plus `ruff` lint/format configuration. |

Run the test suite and linters the same way CI does:

```bash
ruff check service_specification/
ruff format --check service_specification/
python manage.py test service_specification
```

### CI/CD

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on every push, as six staged jobs:

1. **Pre-Clean** — tears down any previously running stack *and wipes its named volumes*
   ([`ci/scripts/pre-cleanup.sh`](ci/scripts/pre-cleanup.sh)), so every deploy starts NetBox from a completely
   empty database.
2. **Code-Review** — `ruff`, `shellcheck`, `yamllint`, and a check that `pyproject.toml`'s version matches
   `versions.sh`.
3. **Build** — builds the NetBox + plugins Docker image per `versions.sh`.
4. **Test** — deploys the stack, runs `manage.py check`, a migration drift check, the Django test suite, and a
   live HTTPS smoke test (session login + a full API POST/GET/PATCH/DELETE round trip).
5. **Test Deployment** — seeds the now-verified instance with demo data (tenant, contacts, sites, devices,
   clusters, VMs) via the REST API ([`ci/scripts/test-deployment.py`](ci/scripts/test-deployment.py)), so the
   showcase instance has real objects to look at. A work in progress — see that script's own header comment.
6. **Deploy** — tags the repo `v<SERVICE_SPECIFICATION_PLUGIN_VERSION>` (from `versions.sh`), if that tag doesn't
   already exist.

The instance left running after a successful **Test** stage doubles as a live showcase — but since every deploy
wipes the database, it starts empty each time and never carries data over from a previous deploy. This is also
why the plugin's own migration ([`service_specification/migrations/0001_initial.py`](service_specification/migrations/0001_initial.py))
is hand-edited in place for schema changes rather than accumulating incremental migration files: there's never an
already-migrated instance whose existing data a later migration would need to preserve.

## License

[MIT](LICENSE)
