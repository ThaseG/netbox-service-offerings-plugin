#!/usr/bin/env python3
"""Seeds the freshly-deployed NetBox instance with representative demo data
(tenant, contacts, sites, device/VM inventory) via the REST API, so there's
something real for the Service Specification plugin's own objects to link
against when showcasing/testing it manually.

Every CI deploy wipes the database (ci/scripts/pre-cleanup.sh), so this
always runs against an empty instance — no need to worry about existing
data or idempotency. Run after smoke-test.sh, against the same live HTTPS
instance and superuser token.

This is a first pass covering core NetBox inventory only (contacts, sites,
devices, clusters, VMs) — plugin objects (Portfolios, Services, etc.) will
be layered on top in a later update, per the request that introduced this
script.

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
    for site_name, cluster_id in cluster_ids.items():
        site_code = SITE_CODES[site_name].lower()
        for n in (1, 2):
            name = f'{site_code}-app-vm{n:02d}'
            obj = api('POST', 'virtualization/virtual-machines/', {'name': name, 'cluster': cluster_id})
            created('virtual machine', obj)


def main():
    global BASE_URL, API_AUTH_HEADER
    BASE_URL = f'https://{env("NETBOX_DOMAIN")}'
    # Same v2-token bearer scheme as smoke-test.sh: Bearer nbt_<key>.<secret>
    API_AUTH_HEADER = f'Bearer nbt_{env("NETBOX_SUPERUSER_API_KEY")}.{env("NETBOX_SUPERUSER_API_TOKEN")}'

    tenant_id = create_tenant()
    group_ids = create_contact_groups()
    create_contacts(group_ids)
    site_ids = create_sites(tenant_id)
    manufacturer_ids = create_manufacturers()
    role_ids = create_device_roles()
    device_type_ids = create_device_types(manufacturer_ids)
    create_devices(site_ids, role_ids, device_type_ids)
    cluster_group_id = create_cluster_group()
    cluster_type_id = create_cluster_type()
    cluster_ids = create_clusters(cluster_group_id, cluster_type_id, site_ids)
    create_virtual_machines(cluster_ids)

    print('Test deployment data created successfully.')


if __name__ == '__main__':
    main()
