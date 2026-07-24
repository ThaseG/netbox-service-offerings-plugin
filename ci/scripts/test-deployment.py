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

Stdlib-only (urllib), matching smoke-test.sh's dependency-free approach —
no extra `pip install` needed on the runner.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = None
API_AUTH_HEADER = None


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


def created(label, obj):
    print(f'  created {label}: {obj["display"]} (id={obj["id"]})')
    return obj


#
# Tenant
#


def create_tenant():
    print('Creating tenant...')
    obj = api('POST', 'tenancy/tenants/', {'name': 'Coca Cola', 'slug': 'coca-cola'})
    created('tenant', obj)
    return obj['id']


#
# Contact groups + contacts
#

CONTACT_GROUPS = [
    {'name': 'Portfolio Owners', 'slug': 'portfolio-owners'},
    {'name': 'Portfolio Managers', 'slug': 'portfolio-managers'},
    {'name': 'Service Managers', 'slug': 'service-managers'},
    {'name': 'Service Owners', 'slug': 'service-owners'},
    {'name': 'Service Offering Owners', 'slug': 'service-offering-owners'},
    {'name': 'Service Offering Managers', 'slug': 'service-offering-managers'},
    {'name': 'App1 Business Unit', 'slug': 'app1-business-unit'},
    {'name': 'App Support Group', 'slug': 'app-support-group'},
    {'name': 'App Change Group', 'slug': 'app-change-group'},
    {'name': 'App1 Owner Group', 'slug': 'app1-owner-group'},
]

# (first name, last name, group name) — one contact per group, except
# "App1 Owner Group" which gets two, per the request.
CONTACTS = [
    ('Alice', 'Johnson', 'Portfolio Owners'),
    ('Brian', 'Smith', 'Portfolio Managers'),
    ('Carla', 'Nguyen', 'Service Managers'),
    ('David', 'Kim', 'Service Owners'),
    ('Elena', 'Petrova', 'Service Offering Owners'),
    ('Franklin', 'Diaz', 'Service Offering Managers'),
    ('Grace', 'Muller', 'App1 Business Unit'),
    ('Henry', 'Osei', 'App Support Group'),
    ('Isabella', 'Rossi', 'App Change Group'),
    ('Jack', 'Thompson', 'App1 Owner Group'),
    ('Karen', "O'Brien", 'App1 Owner Group'),
]


def create_contact_groups():
    print('Creating contact groups...')
    ids = {}
    for group in CONTACT_GROUPS:
        obj = api('POST', 'tenancy/contact-groups/', group)
        created('contact group', obj)
        ids[group['name']] = obj['id']
    return ids


def create_contacts(group_ids):
    print('Creating contacts...')
    # group name -> [contact id, ...], so plugin objects created later can
    # pick "the" contact for a given role (e.g. contacts_by_group['Service
    # Owners'][0]) without caring about the numeric ids the API assigned.
    contacts_by_group = {}
    for index, (first, last, group_name) in enumerate(CONTACTS, start=1):
        email = f'{first.lower()}.{last.lower().replace(chr(39), "")}@coca-cola.example'
        phone = f'+1-555-01{index:02d}'
        obj = api(
            'POST',
            'tenancy/contacts/',
            {
                'name': f'{first} {last}',
                'email': email,
                'phone': phone,
                'groups': [group_ids[group_name]],
            },
        )
        created('contact', obj)
        contacts_by_group.setdefault(group_name, []).append(obj['id'])
    return contacts_by_group


#
# Sites
#

SITES = [
    {
        'name': 'HQ',
        'slug': 'hq',
        'physical_address': '100 Main Street, Atlanta, GA 30301, USA',
    },
    {
        'name': 'Branch',
        'slug': 'branch',
        'physical_address': '200 Commerce Avenue, Denver, CO 80202, USA',
    },
]


def create_sites(tenant_id):
    print('Creating sites...')
    ids = {}
    for site in SITES:
        obj = api('POST', 'dcim/sites/', {**site, 'tenant': tenant_id})
        created('site', obj)
        ids[site['name']] = obj['id']
    return ids


#
# Manufacturers, device roles, device types
#

MANUFACTURERS = [
    {'name': 'Cisco', 'slug': 'cisco'},
    {'name': 'Fortinet', 'slug': 'fortinet'},
    {'name': 'Dell', 'slug': 'dell'},
]

DEVICE_ROLES = [
    {'name': 'Firewall', 'slug': 'firewall', 'color': 'f44336'},
    {'name': 'Switch', 'slug': 'switch', 'color': '2196f3'},
    {'name': 'Server', 'slug': 'server', 'color': '4caf50'},
]

# (model, slug, manufacturer name, role name) — one device type per role,
# used below to build the per-site device inventory.
DEVICE_TYPES = [
    ('FortiGate-100F', 'fortigate-100f', 'Fortinet', 'Firewall'),
    ('Catalyst 9300 24-Port', 'c9300-24t', 'Cisco', 'Switch'),
    ('PowerEdge R750', 'poweredge-r750', 'Dell', 'Server'),
]


def create_manufacturers():
    print('Creating manufacturers...')
    ids = {}
    for manufacturer in MANUFACTURERS:
        obj = api('POST', 'dcim/manufacturers/', manufacturer)
        created('manufacturer', obj)
        ids[manufacturer['name']] = obj['id']
    return ids


def create_device_roles():
    print('Creating device roles...')
    ids = {}
    for role in DEVICE_ROLES:
        obj = api('POST', 'dcim/device-roles/', role)
        created('device role', obj)
        ids[role['name']] = obj['id']
    return ids


def create_device_types(manufacturer_ids):
    print('Creating device types...')
    # keyed by role name, since that's how create_devices() below looks
    # them up (each role has exactly one device type here)
    ids = {}
    for model, slug, manufacturer_name, role_name in DEVICE_TYPES:
        obj = api(
            'POST',
            'dcim/device-types/',
            {'model': model, 'slug': slug, 'manufacturer': manufacturer_ids[manufacturer_name]},
        )
        created('device type', obj)
        ids[role_name] = obj['id']
    return ids


#
# Devices — 2 firewalls, 2 switches, 2 servers on each site
#

# (role name, name suffix)
DEVICES_PER_SITE = [
    ('Firewall', 'FW'),
    ('Switch', 'SW'),
    ('Server', 'SRV'),
]

SITE_CODES = {'HQ': 'HQ', 'Branch': 'BR'}


def create_devices(site_ids, role_ids, device_type_ids):
    print('Creating devices...')
    for site_name, site_id in site_ids.items():
        site_code = SITE_CODES[site_name]
        for role_name, suffix in DEVICES_PER_SITE:
            for n in (1, 2):
                name = f'{site_code}-{suffix}-{n:02d}'
                obj = api(
                    'POST',
                    'dcim/devices/',
                    {
                        'name': name,
                        'role': role_ids[role_name],
                        'device_type': device_type_ids[role_name],
                        'site': site_id,
                    },
                )
                created('device', obj)


#
# Virtualization: cluster group/type, one cluster per site, 2 VMs each
#


def create_cluster_group():
    print('Creating cluster group...')
    obj = api(
        'POST',
        'virtualization/cluster-groups/',
        {'name': 'Proxmox Clusters', 'slug': 'proxmox-clusters'},
    )
    created('cluster group', obj)
    return obj['id']


def create_cluster_type():
    print('Creating cluster type...')
    obj = api('POST', 'virtualization/cluster-types/', {'name': 'Proxmox', 'slug': 'proxmox'})
    created('cluster type', obj)
    return obj['id']


def create_clusters(group_id, type_id, site_ids):
    print('Creating clusters...')
    ids = {}
    for site_name, site_id in site_ids.items():
        obj = api(
            'POST',
            'virtualization/clusters/',
            {
                'name': f'{site_name} Proxmox Cluster',
                'type': type_id,
                'group': group_id,
                'scope_type': 'dcim.site',
                'scope_id': site_id,
            },
        )
        created('cluster', obj)
        ids[site_name] = obj['id']
    return ids


def create_virtual_machines(cluster_ids):
    print('Creating virtual machines...')
    ids = {}
    for site_name, cluster_id in cluster_ids.items():
        site_code = SITE_CODES[site_name].lower()
        for n in (1, 2):
            name = f'{site_code}-app-vm{n:02d}'
            obj = api('POST', 'virtualization/virtual-machines/', {'name': name, 'cluster': cluster_id})
            created('virtual machine', obj)
            ids[name] = obj['id']
    return ids


def assign_vm_ci_functions(vm_ids, ci_function_id):
    """Gives every VM created above a 'Service Specification' entry (the
    tab on its own NetBox detail page) with just CI Function set — the
    plugin can't add real fields to VirtualMachine directly, so this is a
    VirtualMachineServiceInfo row in a 1:1 relationship with it. See
    models.py's ServiceSpecificationInfoBase for why lifecycle and the
    organization groups are left unset here rather than required.
    """
    print('Assigning CI Function to virtual machines...')
    for name, vm_id in vm_ids.items():
        obj = api(
            'POST',
            'plugins/service-specification/virtual-machine-service-infos/',
            {'virtual_machine': vm_id, 'ci_function': ci_function_id},
        )
        created('virtual machine service info', obj)


#
# Service Specification plugin: Support lookup objects
#

LIFECYCLES = [
    (
        'Draft',
        'The CI has been created but is still being defined. Information is incomplete and the CI is not yet '
        'approved for further lifecycle activities.',
    ),
    (
        'Design',
        'The CI is in the planning or design phase. Architecture, requirements, and specifications are being '
        'developed.',
    ),
    (
        'Build',
        'The CI is currently being developed, configured, or implemented and is not yet ready for production use.',
    ),
    (
        'Available',
        'The CI is ready for deployment or assignment but is not yet actively providing a production service.',
    ),
    ('Operational', 'The CI is deployed, fully functional, and actively supporting business or IT services in production.'),
    (
        'In Maintenance',
        'The CI is temporarily undergoing maintenance, upgrades, or repairs. It may have limited or no availability '
        'during this period.',
    ),
    (
        'End of Support',
        'Vendor or internal support has ended or has been scheduled to end. The CI may still be operational but '
        'will no longer receive support, updates, or patches.',
    ),
    (
        'End of Life',
        'The CI has reached the end of its intended lifecycle and should no longer be used for production. '
        'Replacement or retirement should be planned or completed.',
    ),
    (
        'Expired',
        'The CI is no longer valid due to the expiration of its license, certificate, contract, subscription, or '
        'other time-based entitlement.',
    ),
    (
        'Decommissioned',
        'The CI has been permanently removed from service and is no longer operational. It is retained in the '
        'CMDB for historical, audit, or compliance purposes.',
    ),
    (
        'Cancelled',
        'The CI was planned but the implementation or deployment was cancelled before becoming operational.',
    ),
]

# (name, slug, sla_definition)
SLAS = [
    ('Change Support', 'change-support', 'Change Support facilitates the implementation of changes to services or systems.'),
    (
        'Basic Support',
        'basic-support',
        'Basic Support provides foundational assistance for troubleshooting and resolving',
    ),
    (
        'Catch & Dispatch',
        'catch-dispatch',
        'This model focuses on the initial handling of incidents or service requests.',
    ),
    (
        'Incident Support',
        'incident-support',
        'This SLA model aids with identifying, diagnosing, and resolving incidents.',
    ),
    (
        'Lifecycle package',
        'lifecycle-package',
        'This package offers end-to-end support for the entire lifecycle of a service or system.',
    ),
    ('Monitoring', 'monitoring', 'Monitoring services track the performance, health, and availability of systems.'),
    (
        'On-site service',
        'on-site-service',
        'On Site Service provides physical, on-site support for troubleshooting',
    ),
]

# (name, slug)
OPERATION_TIMES = [('24/7', '247'), ('8/5', '85'), ('10/5', '105')]
AVAILABILITIES = [('99.99%', '99-99'), ('99.50%', '99-50'), ('99.00%', '99-00'), ('98.00%', '98-00'), ('95.00%', '95-00')]
CRITICALITIES = [
    ('Not Critical', 'not-critical'),
    ('Less Critical', 'less-critical'),
    ('Somewhat Critical', 'somewhat-critical'),
    ('Most Critical', 'most-critical'),
]
ENVIRONMENTS = [
    ('Production', 'production'),
    ('Staging', 'staging'),
    ('Test', 'test'),
    ('Development', 'development'),
    ('QA', 'qa'),
]

# (name, slug, value, unit)
MTATS = [
    ('Category A', 'category-a', 12, 'hours'),
    ('Category B', 'category-b', 24, 'hours'),
    ('Category C', 'category-c', 32, 'hours'),
]

CI_FUNCTIONS = [('Managed Exchange Service', 'managed-exchange-service')]


def _create_lookup(label, path, items, extra_fields=lambda item: {}, plural=None):
    """Shared helper for the plugin's simple name/slug(/description) lookup
    models below — each `items` entry is a tuple starting with (name, slug),
    with any model-specific fields appended and picked out by extra_fields.
    """
    print(f'Creating {plural or f"{label}s"}...')
    ids = {}
    for item in items:
        name, slug = item[0], item[1]
        payload = {'name': name, 'slug': slug, 'description': name, **extra_fields(item)}
        obj = api('POST', path, payload)
        created(label, obj)
        ids[name] = obj['id']
    return ids


def create_lifecycles():
    print('Creating lifecycles...')
    ids = {}
    for name, description in LIFECYCLES:
        slug = name.lower().replace(' ', '-')
        obj = api('POST', 'plugins/service-specification/lifecycles/', {'name': name, 'slug': slug, 'description': description})
        created('lifecycle', obj)
        ids[name] = obj['id']
    return ids


def create_slas():
    print('Creating SLAs...')
    ids = {}
    for name, slug, sla_definition in SLAS:
        obj = api('POST', 'plugins/service-specification/slas/', {'name': name, 'slug': slug, 'sla_definition': sla_definition})
        created('SLA', obj)
        ids[name] = obj['id']
    return ids


def create_operation_times():
    return _create_lookup('operation time', 'plugins/service-specification/operation-times/', OPERATION_TIMES)


def create_availabilities():
    return _create_lookup(
        'availability', 'plugins/service-specification/availabilities/', AVAILABILITIES, plural='availabilities'
    )


def create_criticalities():
    return _create_lookup(
        'criticality', 'plugins/service-specification/criticalities/', CRITICALITIES, plural='criticalities'
    )


def create_environments():
    return _create_lookup('environment', 'plugins/service-specification/environments/', ENVIRONMENTS)


def create_mtats():
    return _create_lookup(
        'MTAT',
        'plugins/service-specification/mtats/',
        MTATS,
        extra_fields=lambda item: {'value': item[2], 'unit': item[3]},
    )


def create_ci_functions():
    return _create_lookup('CI Function', 'plugins/service-specification/ci-functions/', CI_FUNCTIONS)


#
# Service Specification plugin: Portfolio / Service / Service Offerings /
# Application Services
#


def create_portfolio(lifecycle_ids, group_ids, contacts_by_group):
    print('Creating portfolio...')
    obj = api(
        'POST',
        'plugins/service-specification/portfolios/',
        {
            'name': 'Primary Service Portfolio',
            'description': 'Primary Service Portfolio',
            'lifecycle': lifecycle_ids['Operational'],
            'portfolio_owner_contacts': [contacts_by_group['Portfolio Owners'][0]],
            'portfolio_owner_contact_groups': [group_ids['Portfolio Owners']],
            'portfolio_manager_contacts': [contacts_by_group['Portfolio Managers'][0]],
            'portfolio_manager_contact_groups': [group_ids['Portfolio Managers']],
        },
    )
    created('portfolio', obj)
    return obj['id']


def create_service(lifecycle_ids, ci_function_ids, group_ids, contacts_by_group, portfolio_id):
    print('Creating service...')
    obj = api(
        'POST',
        'plugins/service-specification/services/',
        {
            'name': 'Workspace',
            'description': 'Workspace services',
            'lifecycle': lifecycle_ids['Operational'],
            'ci_function': ci_function_ids['Managed Exchange Service'],
            'service_owner_contacts': [contacts_by_group['Service Owners'][0]],
            'service_owner_contact_groups': [group_ids['Service Owners']],
            'service_manager_contacts': [contacts_by_group['Service Managers'][0]],
            'service_manager_contact_groups': [group_ids['Service Managers']],
            'service_portfolio': [portfolio_id],
            'business_unit': [group_ids['App1 Business Unit']],
            'support_group': [group_ids['App Support Group']],
            'change_group': [group_ids['App Change Group']],
        },
    )
    created('service', obj)
    return obj['id']


# (name, contract_number)
SERVICE_OFFERINGS = [
    ('Managed Exchange Service High Availability', '12345'),
    ('Managed Exchange Service Standalone', '54321'),
]


def create_service_offerings(lifecycle_ids, group_ids, contacts_by_group, service_id, tenant_id):
    print('Creating service offerings...')
    ids = {}
    for name, contract_number in SERVICE_OFFERINGS:
        obj = api(
            'POST',
            'plugins/service-specification/service-offerings/',
            {
                'name': name,
                'description': name,
                'contract_number': contract_number,
                'lifecycle': lifecycle_ids['Operational'],
                'service': [service_id],
                'service_offering_owner_contacts': [contacts_by_group['Service Offering Owners'][0]],
                'service_offering_owner_contact_groups': [group_ids['Service Offering Owners']],
                'service_offering_manager_contacts': [contacts_by_group['Service Offering Managers'][0]],
                'service_offering_manager_contact_groups': [group_ids['Service Offering Managers']],
                'business_unit': [group_ids['App1 Business Unit']],
                'support_group': [group_ids['App Support Group']],
                'change_group': [group_ids['App Change Group']],
                'tenant': [tenant_id],
            },
        )
        created('service offering', obj)
        ids[name] = obj['id']
    return ids


# (name, description, offering name, sla name, availability name, accepted_downtime, ttr, rpo, rto, bcm)
APP_SERVICES = [
    (
        'Application Service - Managed Exchange Server High Availability - Prod',
        'Application Service - Managed Exchange Server High Availability',
        'Managed Exchange Service High Availability',
        'Lifecycle package',
        '99.99%',
        2,
        2,
        4,
        4,
        2,
    ),
    (
        'Application Service - Managed Exchange Server Standalone - Prod',
        '',
        'Managed Exchange Service Standalone',
        'Catch & Dispatch',
        '99.50%',
        2,
        2,
        2,
        4,
        2,
    ),
]


def create_app_services(
    environment_ids,
    lifecycle_ids,
    group_ids,
    offering_ids,
    sla_ids,
    operation_time_ids,
    availability_ids,
    mtat_ids,
    criticality_ids,
    tenant_id,
):
    print('Creating application services...')
    for name, description, offering_name, sla_name, availability_name, downtime, ttr, rpo, rto, bcm in APP_SERVICES:
        obj = api(
            'POST',
            'plugins/service-specification/app-services/',
            {
                'name': name,
                'description': description,
                'environment': environment_ids['Production'],
                'lifecycle': lifecycle_ids['Operational'],
                'service_offering': offering_ids[offering_name],
                'business_unit': [group_ids['App1 Business Unit']],
                'support_group': [group_ids['App Support Group']],
                'change_group': [group_ids['App Change Group']],
                'sla': [sla_ids[sla_name]],
                'owned_by_contact_group': group_ids['App1 Owner Group'],
                'operation_time': [operation_time_ids['24/7']],
                'availability': [availability_ids[availability_name]],
                'mtat': [mtat_ids['Category A']],
                'service_criticality': [criticality_ids['Most Critical']],
                'accepted_downtime': downtime,
                'ttr': ttr,
                'rpo': rpo,
                'rto': rto,
                'bcm': bcm,
                'tenant': [tenant_id],
            },
        )
        created('application service', obj)


def main():
    global BASE_URL, API_AUTH_HEADER
    BASE_URL = f'https://{env("NETBOX_DOMAIN")}'
    # Same v2-token bearer scheme as smoke-test.sh: Bearer nbt_<key>.<secret>
    API_AUTH_HEADER = f'Bearer nbt_{env("NETBOX_SUPERUSER_API_KEY")}.{env("NETBOX_SUPERUSER_API_TOKEN")}'

    tenant_id = create_tenant()
    group_ids = create_contact_groups()
    contacts_by_group = create_contacts(group_ids)
    site_ids = create_sites(tenant_id)
    manufacturer_ids = create_manufacturers()
    role_ids = create_device_roles()
    device_type_ids = create_device_types(manufacturer_ids)
    create_devices(site_ids, role_ids, device_type_ids)
    cluster_group_id = create_cluster_group()
    cluster_type_id = create_cluster_type()
    cluster_ids = create_clusters(cluster_group_id, cluster_type_id, site_ids)
    vm_ids = create_virtual_machines(cluster_ids)

    lifecycle_ids = create_lifecycles()
    sla_ids = create_slas()
    operation_time_ids = create_operation_times()
    availability_ids = create_availabilities()
    criticality_ids = create_criticalities()
    environment_ids = create_environments()
    mtat_ids = create_mtats()
    ci_function_ids = create_ci_functions()

    assign_vm_ci_functions(vm_ids, ci_function_ids['Managed Exchange Service'])

    portfolio_id = create_portfolio(lifecycle_ids, group_ids, contacts_by_group)
    service_id = create_service(lifecycle_ids, ci_function_ids, group_ids, contacts_by_group, portfolio_id)
    offering_ids = create_service_offerings(lifecycle_ids, group_ids, contacts_by_group, service_id, tenant_id)
    create_app_services(
        environment_ids,
        lifecycle_ids,
        group_ids,
        offering_ids,
        sla_ids,
        operation_time_ids,
        availability_ids,
        mtat_ids,
        criticality_ids,
        tenant_id,
    )

    print('Test deployment data created successfully.')


if __name__ == '__main__':
    main()
