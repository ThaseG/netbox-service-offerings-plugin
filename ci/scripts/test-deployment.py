#!/usr/bin/env python3
"""Seeds the freshly-deployed NetBox instance with representative demo data
(tenant, contacts, sites, device/VM inventory) via the REST API, so there's
something real for the Service Specification plugin's own objects to link
against when showcasing/testing it manually.

Every CI deploy wipes the database (ci/scripts/pre-cleanup.sh), so this
always runs against an empty instance — no need to worry about existing
data or idempotency. Run after smoke-test.sh, against the same live HTTPS
instance and superuser token.

Covers core NetBox inventory (contacts, sites, devices, clusters, VMs) plus
the Service Specification plugin's own objects (lookup values, one
Portfolio/Service, two Service Offerings/Application Services), wired
together the same way they were originally built by hand through the UI.

All the actual data lives in test-deployment.json, next to this script, as
an ordered mapping of {api_endpoint_path: [payload, ...]}. This script is a
generic engine, not per-object-type logic: it POSTs every payload to its
endpoint, in file order, resolving any field listed in REFERENCE_FIELDS
below from a slug/name string into the real id of an object created
earlier in the same run.

File order in the JSON *is* creation order — an object referenced by a
later entry (by slug, or by name for models with no slug, e.g. Contact,
Device, Cluster, VirtualMachine, and the plugin's own Portfolio/Service/
ServiceOffering/AppService — or by contract_number for Contract, the one
model with neither a slug nor a name) must be listed earlier in the file.
JSON can't hold comments, so that ordering requirement — and the object
graph itself — is documented here and in REFERENCE_FIELDS instead.

Stdlib-only (urllib), matching smoke-test.sh's dependency-free approach —
no extra `pip install` needed on the runner.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = None
API_AUTH_HEADER = None

DATA_FILE = Path(__file__).with_name('test-deployment.json')

# For each endpoint, which fields hold references to other objects rather
# than literal values, and which endpoint those references resolve
# against. A referenced object is looked up by its own `slug` if it has
# one, else by its `name` (see resolve()) — deliberately explicit per
# field/endpoint rather than inferred from the value itself, so a typo'd
# or wrong-endpoint reference fails loudly instead of silently resolving
# against the wrong thing. This table is also the object graph's
# documentation: it replaces what the old per-object-type functions'
# parameter lists used to show.
REFERENCE_FIELDS = {
    'dcim/sites/': {
        'tenant': 'tenancy/tenants/',
    },
    'dcim/device-types/': {
        'manufacturer': 'dcim/manufacturers/',
    },
    'dcim/devices/': {
        'role': 'dcim/device-roles/',
        'device_type': 'dcim/device-types/',
        'site': 'dcim/sites/',
    },
    'tenancy/contacts/': {
        'groups': 'tenancy/contact-groups/',
    },
    'virtualization/clusters/': {
        'type': 'virtualization/cluster-types/',
        'group': 'virtualization/cluster-groups/',
        # Generic-FK-style scope (scope_type/scope_id): scope_type is a
        # literal content-type string ('dcim.site'), not a reference, but
        # scope_id needs the same slug -> id resolution as any other
        # reference to a Site.
        'scope_id': 'dcim/sites/',
    },
    'virtualization/virtual-machines/': {
        'cluster': 'virtualization/clusters/',
    },
    'plugins/service-specification/portfolios/': {
        'lifecycle': 'plugins/service-specification/lifecycles/',
        'portfolio_owner_contacts': 'tenancy/contacts/',
        'portfolio_owner_contact_groups': 'tenancy/contact-groups/',
        'portfolio_manager_contacts': 'tenancy/contacts/',
        'portfolio_manager_contact_groups': 'tenancy/contact-groups/',
    },
    'plugins/service-specification/services/': {
        'lifecycle': 'plugins/service-specification/lifecycles/',
        'ci_function': 'plugins/service-specification/ci-functions/',
        'service_owner_contacts': 'tenancy/contacts/',
        'service_owner_contact_groups': 'tenancy/contact-groups/',
        'service_manager_contacts': 'tenancy/contacts/',
        'service_manager_contact_groups': 'tenancy/contact-groups/',
        'service_portfolio': 'plugins/service-specification/portfolios/',
        'business_unit': 'tenancy/contact-groups/',
        'support_group': 'tenancy/contact-groups/',
        'change_group': 'tenancy/contact-groups/',
    },
    'plugins/service-specification/contracts/': {
        'parent_contract': 'plugins/service-specification/contracts/',
        'vendor': 'dcim/manufacturers/',
        'tenant': 'tenancy/tenants/',
        'tenant_group': 'tenancy/tenant-groups/',
        'contact_person': 'tenancy/contacts/',
        'primary_contact': 'tenancy/contacts/',
        'contract_manager': 'tenancy/contacts/',
        'approver': 'tenancy/contacts/',
        'business_unit': 'tenancy/contact-groups/',
    },
    'plugins/service-specification/contract-rate-cards/': {
        'contract': 'plugins/service-specification/contracts/',
    },
    'plugins/service-specification/service-offerings/': {
        'lifecycle': 'plugins/service-specification/lifecycles/',
        'contract': 'plugins/service-specification/contracts/',
        'service': 'plugins/service-specification/services/',
        'service_offering_owner_contacts': 'tenancy/contacts/',
        'service_offering_owner_contact_groups': 'tenancy/contact-groups/',
        'service_offering_manager_contacts': 'tenancy/contacts/',
        'service_offering_manager_contact_groups': 'tenancy/contact-groups/',
        'business_unit': 'tenancy/contact-groups/',
        'support_group': 'tenancy/contact-groups/',
        'change_group': 'tenancy/contact-groups/',
        'tenant': 'tenancy/tenants/',
    },
    'plugins/service-specification/app-services/': {
        'environment': 'plugins/service-specification/environments/',
        'lifecycle': 'plugins/service-specification/lifecycles/',
        'service_offering': 'plugins/service-specification/service-offerings/',
        'business_unit': 'tenancy/contact-groups/',
        'support_group': 'tenancy/contact-groups/',
        'change_group': 'tenancy/contact-groups/',
        'sla': 'plugins/service-specification/slas/',
        'owned_by_contact_group': 'tenancy/contact-groups/',
        'operation_time': 'plugins/service-specification/operation-times/',
        'availability': 'plugins/service-specification/availabilities/',
        'mtat': 'plugins/service-specification/mtats/',
        'service_criticality': 'plugins/service-specification/criticalities/',
    },
    'plugins/service-specification/virtual-machine-service-infos/': {
        'virtual_machine': 'virtualization/virtual-machines/',
        'application_services': 'plugins/service-specification/app-services/',
    },
    'plugins/service-specification/device-service-infos/': {
        'device': 'dcim/devices/',
        'application_services': 'plugins/service-specification/app-services/',
    },
    'plugins/service-specification/cluster-service-infos/': {
        'cluster': 'virtualization/clusters/',
        'application_services': 'plugins/service-specification/app-services/',
    },
    'plugins/service-specification/cluster-group-service-infos/': {
        'cluster_group': 'virtualization/cluster-groups/',
        'application_services': 'plugins/service-specification/app-services/',
    },
}


def env(name):
    value = os.environ.get(name)
    if not value:
        fail(f'{name} must be set')
    return value


def fail(message):
    print(f'TEST DEPLOYMENT FAILED: {message}', file=sys.stderr)
    sys.exit(1)


def api(method, path, payload=None):
    url = f'{BASE_URL}/api/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            'Authorization': API_AUTH_HEADER,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        fail(f'{method} {path} -> HTTP {e.code}\n{body}')
    except urllib.error.URLError as e:
        fail(f'{method} {path} -> {e}')


def created(endpoint, obj):
    print(f'  created {endpoint}: {obj["display"]} (id={obj["id"]})')
    return obj


def resolve(value, target_endpoint, created_objects):
    """Look up a single slug/name/contract_number reference against objects
    already created (earlier in the JSON file) at target_endpoint."""
    cache = created_objects.get(target_endpoint, {})
    if value not in cache:
        fail(
            f'Cannot resolve reference {value!r} against {target_endpoint} — no object with that slug/name has '
            f'been created yet. Check test-deployment.json lists it earlier, and that the value is spelled '
            f'exactly right.'
        )
    return cache[value]


def resolve_field(value, target_endpoint, created_objects):
    """A reference field's value is either a single slug/name (FK) or a
    list of them (M2M) — resolve whichever shape it is."""
    if isinstance(value, list):
        return [resolve(v, target_endpoint, created_objects) for v in value]
    return resolve(value, target_endpoint, created_objects)


def create_all(data):
    created_objects = {}  # endpoint -> {slug-or-name: id}
    for endpoint, payloads in data.items():
        print(f'Creating {len(payloads)} object(s) at {endpoint}...')
        reference_fields = REFERENCE_FIELDS.get(endpoint, {})
        cache = created_objects.setdefault(endpoint, {})
        for payload in payloads:
            resolved = dict(payload)
            for field, target_endpoint in reference_fields.items():
                if field in resolved and resolved[field] is not None:
                    resolved[field] = resolve_field(resolved[field], target_endpoint, created_objects)
            obj = api('POST', endpoint, resolved)
            created(endpoint, obj)
            # Almost everything is keyed by slug-else-name (see resolve()),
            # but Contract has neither — its own identity field is
            # contract_number instead (see models.py's Contract.__str__).
            key = payload.get('slug') or payload.get('name') or payload.get('contract_number')
            if key is not None:
                if key in cache:
                    fail(f'Duplicate slug/name {key!r} for {endpoint} in {DATA_FILE.name}')
                cache[key] = obj['id']


def main():
    global BASE_URL, API_AUTH_HEADER
    BASE_URL = f'https://{env("NETBOX_DOMAIN")}'
    # Same v2-token bearer scheme as smoke-test.sh: Bearer nbt_<key>.<secret>
    API_AUTH_HEADER = f'Bearer nbt_{env("NETBOX_SUPERUSER_API_KEY")}.{env("NETBOX_SUPERUSER_API_TOKEN")}'

    with DATA_FILE.open() as f:
        data = json.load(f)

    create_all(data)

    print('Test deployment data created successfully.')


if __name__ == '__main__':
    main()
