#!/usr/bin/env python3
"""Regenerates ci/scripts/test-deployment.json at scale — 20 customers each
with their own site/device/cluster/VM infrastructure, and a 20x20x20
Portfolio/Service/Service-Offering hierarchy (each Service Offering backing
exactly one Application Service, per the plugin's 1:1 constraint) — as a
stress-test dataset for pages like Service View that previously struggled
with larger, denser trees.

This is a one-off *generator*, not part of the actual deploy pipeline:
ci/scripts/test-deployment.py itself stays a generic "read JSON, POST it,
resolve references" engine with zero knowledge of how the JSON was
produced. Run this script, by hand, whenever the seeded dataset's shape or
scale needs to change; commit the regenerated test-deployment.json.

Scale is deliberately hand-tunable at the top of main() rather than an
inherent property of the data model.
"""

import json
from pathlib import Path

OUTPUT_FILE = Path(__file__).with_name('test-deployment.json')

NUM_TENANTS = 20
SITES_PER_TENANT = 2
NUM_PORTFOLIOS = 20
SERVICES_PER_PORTFOLIO = 20
OFFERINGS_PER_SERVICE = 20

# (role slug, device type slug, name suffix) — shared across every tenant's
# sites, same as the original single-tenant dataset; 2 of each per site.
DEVICE_ROLES = [
    ('firewall', 'fortigate-100f', 'FW'),
    ('switch', 'c9300-24t', 'SW'),
    ('server', 'poweredge-r750', 'SRV'),
]

# (name, slug, description, color) — only 11 of these regardless of scale
# (lookup values are shared, not per-tenant/portfolio/offering), so there's
# no cost to using the real descriptions rather than a placeholder.
LIFECYCLES = [
    (
        'Draft',
        'draft',
        'The CI has been created but is still being defined. Information is incomplete and the CI is not yet '
        'approved for further lifecycle activities.',
        '9e9e9e',
    ),
    (
        'Design',
        'design',
        'The CI is in the planning or design phase. Architecture, requirements, and specifications are being '
        'developed.',
        '2196f3',
    ),
    (
        'Build',
        'build',
        'The CI is currently being developed, configured, or implemented and is not yet ready for production use.',
        'ffc107',
    ),
    (
        'Available',
        'available',
        'The CI is ready for deployment or assignment but is not yet actively providing a production service.',
        '4caf50',
    ),
    (
        'Operational',
        'operational',
        'The CI is deployed, fully functional, and actively supporting business or IT services in production.',
        '2f6a31',
    ),
    (
        'In Maintenance',
        'in-maintenance',
        'The CI is temporarily undergoing maintenance, upgrades, or repairs. It may have limited or no availability '
        'during this period.',
        'ff9800',
    ),
    (
        'End of Support',
        'end-of-support',
        'Vendor or internal support has ended or has been scheduled to end. The CI may still be operational but '
        'will no longer receive support, updates, or patches.',
        'ff5722',
    ),
    (
        'End of Life',
        'end-of-life',
        'The CI has reached the end of its intended lifecycle and should no longer be used for production. '
        'Replacement or retirement should be planned or completed.',
        'f44336',
    ),
    (
        'Expired',
        'expired',
        'The CI is no longer valid due to the expiration of its license, certificate, contract, subscription, or '
        'other time-based entitlement.',
        'aa1409',
    ),
    (
        'Decommissioned',
        'decommissioned',
        'The CI has been permanently removed from service and is no longer operational. It is retained in the '
        'CMDB for historical, audit, or compliance purposes.',
        '607d8b',
    ),
    (
        'Cancelled',
        'cancelled',
        'The CI was planned but the implementation or deployment was cancelled before becoming operational.',
        '795548',
    ),
]

SLAS = [
    ('Change Support', 'change-support'),
    ('Basic Support', 'basic-support'),
    ('Catch & Dispatch', 'catch-dispatch'),
    ('Incident Support', 'incident-support'),
    ('Lifecycle package', 'lifecycle-package'),
    ('Monitoring', 'monitoring'),
    ('On-site service', 'on-site-service'),
]

OPERATION_TIMES = [('24/7', '247'), ('8/5', '85'), ('10/5', '105')]
AVAILABILITIES = [
    ('99.99%', '99-99'),
    ('99.50%', '99-50'),
    ('99.00%', '99-00'),
    ('98.00%', '98-00'),
    ('95.00%', '95-00'),
]
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
MTATS = [('Category A', 'category-a', 12), ('Category B', 'category-b', 24), ('Category C', 'category-c', 32)]
CI_FUNCTIONS = [
    ('Managed Exchange Service', 'managed-exchange-service'),
    ('Managed Backup Service', 'managed-backup-service'),
    ('Managed Database Service', 'managed-database-service'),
    ('Managed Network Service', 'managed-network-service'),
    ('Managed Identity Service', 'managed-identity-service'),
]

CONTACT_GROUPS = [
    'Portfolio Owners',
    'Portfolio Managers',
    'Service Managers',
    'Service Owners',
    'Service Offering Owners',
    'Service Offering Managers',
    'App1 Business Unit',
    'App Support Group',
    'App Change Group',
    'App1 Owner Group',
]

# (first, last, group) — one contact per group, reused across every
# Portfolio/Service/Offering/AppService regardless of scale: ownership
# groups are an org-chart concept, not something that multiplies with the
# number of customers or offerings.
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
]


def slugify(name):
    return name.lower().replace(' ', '-').replace('/', '-').replace('&', 'and')


def build_tenants_and_infra(data):
    data['tenancy/tenants/'] = []
    data['dcim/sites/'] = []
    data['dcim/devices/'] = []
    data['virtualization/clusters/'] = []
    data['virtualization/virtual-machines/'] = []

    device_pool = []  # [(endpoint_field_key, device_name), ...]
    cluster_pool = []
    vm_pool = []

    for t in range(1, NUM_TENANTS + 1):
        tenant_name = f'Customer {t:02d}'
        tenant_slug = f'customer-{t:02d}'
        data['tenancy/tenants/'].append({'name': tenant_name, 'slug': tenant_slug})

        for s in range(1, SITES_PER_TENANT + 1):
            site_slug = f'{tenant_slug}-site-{s}'
            data['dcim/sites/'].append(
                {
                    'name': f'{tenant_name} Site {s}',
                    'slug': site_slug,
                    'physical_address': f'{100 + t} Example Street, Site {s}',
                    'tenant': tenant_slug,
                }
            )

            for role_slug, device_type_slug, suffix in DEVICE_ROLES:
                for n in (1, 2):
                    device_name = f'{site_slug}-{suffix}-{n:02d}'
                    data['dcim/devices/'].append(
                        {
                            'name': device_name,
                            'role': role_slug,
                            'device_type': device_type_slug,
                            'site': site_slug,
                        }
                    )
                    device_pool.append(device_name)

            cluster_name = f'{tenant_name} Site {s} Cluster'
            data['virtualization/clusters/'].append(
                {
                    'name': cluster_name,
                    'type': 'proxmox',
                    'group': 'proxmox-clusters',
                    'scope_type': 'dcim.site',
                    'scope_id': site_slug,
                }
            )
            cluster_pool.append(cluster_name)

            for n in (1, 2):
                vm_name = f'{site_slug}-vm{n:02d}'
                data['virtualization/virtual-machines/'].append({'name': vm_name, 'cluster': cluster_name})
                vm_pool.append(vm_name)

    return device_pool, cluster_pool, vm_pool


def build_lookups(data):
    data['dcim/manufacturers/'] = [
        {'name': 'Cisco', 'slug': 'cisco'},
        {'name': 'Fortinet', 'slug': 'fortinet'},
        {'name': 'Dell', 'slug': 'dell'},
    ]
    data['dcim/device-roles/'] = [
        {'name': 'Firewall', 'slug': 'firewall', 'color': 'f44336'},
        {'name': 'Switch', 'slug': 'switch', 'color': '2196f3'},
        {'name': 'Server', 'slug': 'server', 'color': '4caf50'},
    ]
    data['dcim/device-types/'] = [
        {'model': 'FortiGate-100F', 'slug': 'fortigate-100f', 'manufacturer': 'fortinet'},
        {'model': 'Catalyst 9300 24-Port', 'slug': 'c9300-24t', 'manufacturer': 'cisco'},
        {'model': 'PowerEdge R750', 'slug': 'poweredge-r750', 'manufacturer': 'dell'},
    ]
    data['virtualization/cluster-groups/'] = [{'name': 'Proxmox Clusters', 'slug': 'proxmox-clusters'}]
    data['virtualization/cluster-types/'] = [{'name': 'Proxmox', 'slug': 'proxmox'}]

    data['tenancy/contact-groups/'] = [{'name': name, 'slug': slugify(name)} for name in CONTACT_GROUPS]
    data['tenancy/contacts/'] = [
        {
            'name': f'{first} {last}',
            'email': f'{first.lower()}.{last.lower()}@example.com',
            'phone': f'+1-555-{i:04d}',
            'groups': [slugify(group)],
        }
        for i, (first, last, group) in enumerate(CONTACTS, start=1)
    ]

    data['plugins/service-specification/lifecycles/'] = [
        {'name': name, 'slug': slug, 'description': description, 'color': color}
        for name, slug, description, color in LIFECYCLES
    ]
    data['plugins/service-specification/slas/'] = [
        {'name': name, 'slug': slug, 'sla_definition': name} for name, slug in SLAS
    ]
    data['plugins/service-specification/operation-times/'] = [
        {'name': name, 'slug': slug, 'description': name} for name, slug in OPERATION_TIMES
    ]
    data['plugins/service-specification/availabilities/'] = [
        {'name': name, 'slug': slug, 'description': name} for name, slug in AVAILABILITIES
    ]
    data['plugins/service-specification/criticalities/'] = [
        {'name': name, 'slug': slug, 'description': name} for name, slug in CRITICALITIES
    ]
    data['plugins/service-specification/environments/'] = [
        {'name': name, 'slug': slug, 'description': name} for name, slug in ENVIRONMENTS
    ]
    data['plugins/service-specification/mtats/'] = [
        {'name': name, 'slug': slug, 'description': name, 'value': value, 'unit': 'hours'}
        for name, slug, value in MTATS
    ]
    data['plugins/service-specification/ci-functions/'] = [
        {'name': name, 'slug': slug, 'description': name} for name, slug in CI_FUNCTIONS
    ]


def build_hierarchy(data, tenant_slugs):
    lifecycle_slugs = [slug for _name, slug, _desc, _color in LIFECYCLES]
    sla_slugs = [slug for _name, slug in SLAS]
    op_time_slugs = [slug for _name, slug in OPERATION_TIMES]
    availability_slugs = [slug for _name, slug in AVAILABILITIES]
    criticality_slugs = [slug for _name, slug in CRITICALITIES]
    environment_slugs = [slug for _name, slug in ENVIRONMENTS]
    mtat_slugs = [slug for _name, slug, _value in MTATS]
    ci_function_slugs = [slug for _name, slug in CI_FUNCTIONS]

    shared_business_unit = ['app1-business-unit']
    shared_support_group = ['app-support-group']
    shared_change_group = ['app-change-group']

    portfolios = []
    services = []
    offerings = []
    app_services = []

    offering_counter = 0

    for p in range(1, NUM_PORTFOLIOS + 1):
        portfolio_name = f'Portfolio {p:02d}'
        portfolios.append(
            {
                'name': portfolio_name,
                'description': portfolio_name,
                'lifecycle': lifecycle_slugs[p % len(lifecycle_slugs)],
                'portfolio_owner_contacts': ['Alice Johnson'],
                'portfolio_owner_contact_groups': ['portfolio-owners'],
                'portfolio_manager_contacts': ['Brian Smith'],
                'portfolio_manager_contact_groups': ['portfolio-managers'],
            }
        )

        for s in range(1, SERVICES_PER_PORTFOLIO + 1):
            service_name = f'Portfolio {p:02d} / Service {s:02d}'
            services.append(
                {
                    'name': service_name,
                    'description': service_name,
                    'lifecycle': lifecycle_slugs[(p + s) % len(lifecycle_slugs)],
                    'ci_function': ci_function_slugs[(p + s) % len(ci_function_slugs)],
                    'service_owner_contacts': ['David Kim'],
                    'service_owner_contact_groups': ['service-owners'],
                    'service_manager_contacts': ['Carla Nguyen'],
                    'service_manager_contact_groups': ['service-managers'],
                    'service_portfolio': [portfolio_name],
                    'business_unit': shared_business_unit,
                    'support_group': shared_support_group,
                    'change_group': shared_change_group,
                }
            )

            for o in range(1, OFFERINGS_PER_SERVICE + 1):
                offering_name = f'Portfolio {p:02d} / Service {s:02d} / Offering {o:02d}'
                tenant_slug = tenant_slugs[offering_counter % len(tenant_slugs)]
                offerings.append(
                    {
                        'name': offering_name,
                        'description': offering_name,
                        'contract_number': f'CN-{p:02d}{s:02d}{o:02d}',
                        'lifecycle': lifecycle_slugs[(p + s + o) % len(lifecycle_slugs)],
                        'service': [service_name],
                        'service_offering_owner_contacts': ['Elena Petrova'],
                        'service_offering_owner_contact_groups': ['service-offering-owners'],
                        'service_offering_manager_contacts': ['Franklin Diaz'],
                        'service_offering_manager_contact_groups': ['service-offering-managers'],
                        'business_unit': shared_business_unit,
                        'support_group': shared_support_group,
                        'change_group': shared_change_group,
                        'tenant': [tenant_slug],
                    }
                )

                app_service_name = f'Portfolio {p:02d} / Service {s:02d} / Offering {o:02d} / App'
                app_services.append(
                    {
                        'name': app_service_name,
                        'description': app_service_name,
                        'environment': environment_slugs[offering_counter % len(environment_slugs)],
                        'lifecycle': lifecycle_slugs[(p + s + o + 1) % len(lifecycle_slugs)],
                        'service_offering': offering_name,
                        'business_unit': shared_business_unit,
                        'support_group': shared_support_group,
                        'change_group': shared_change_group,
                        'sla': [sla_slugs[offering_counter % len(sla_slugs)]],
                        'owned_by_contact_group': 'app1-owner-group',
                        'operation_time': [op_time_slugs[offering_counter % len(op_time_slugs)]],
                        'availability': [availability_slugs[offering_counter % len(availability_slugs)]],
                        'mtat': [mtat_slugs[offering_counter % len(mtat_slugs)]],
                        'service_criticality': [criticality_slugs[offering_counter % len(criticality_slugs)]],
                        'accepted_downtime': 1 + (offering_counter % 4),
                        'ttr': 1 + (offering_counter % 3),
                        'rpo': 2 + (offering_counter % 3),
                        'rto': 2 + (offering_counter % 4),
                        'bcm': 1 + (offering_counter % 3),
                    }
                )

                offering_counter += 1

    data['plugins/service-specification/portfolios/'] = portfolios
    data['plugins/service-specification/services/'] = services
    data['plugins/service-specification/service-offerings/'] = offerings
    data['plugins/service-specification/app-services/'] = app_services

    return [a['name'] for a in app_services]


def build_ci_assignments(data, device_pool, cluster_pool, vm_pool, app_service_names):
    """Spreads every Application Service across the pool of devices,
    clusters and VMs created for the 20 customers: cycling through the
    combined pool assigns each Application Service to exactly one
    Technical CI, so — since the pool is much smaller than the number of
    Application Services — each CI ends up backing several of them
    (application_services is a ManyToMany on each *ServiceInfo row, one
    row per Device/Cluster/VirtualMachine, so every one of their
    assignments has to be collected before emitting a single row per CI,
    not one row per assignment).
    """
    pool = [('device', name) for name in device_pool]
    pool += [('cluster', name) for name in cluster_pool]
    pool += [('virtual_machine', name) for name in vm_pool]

    assignments = {ci_ref: [] for ci_ref in pool}
    for i, app_service_name in enumerate(app_service_names):
        ci_ref = pool[i % len(pool)]
        assignments[ci_ref].append(app_service_name)

    endpoint_by_kind = {
        'device': 'plugins/service-specification/device-service-infos/',
        'cluster': 'plugins/service-specification/cluster-service-infos/',
        'virtual_machine': 'plugins/service-specification/virtual-machine-service-infos/',
    }
    field_by_kind = {'device': 'device', 'cluster': 'cluster', 'virtual_machine': 'virtual_machine'}

    for endpoint in endpoint_by_kind.values():
        data.setdefault(endpoint, [])

    for (kind, name), assigned in assignments.items():
        if not assigned:
            continue
        data[endpoint_by_kind[kind]].append({field_by_kind[kind]: name, 'application_services': assigned})


def main():
    data = {}

    build_lookups(data)
    device_pool, cluster_pool, vm_pool = build_tenants_and_infra(data)
    tenant_slugs = [t['slug'] for t in data['tenancy/tenants/']]
    app_service_names = build_hierarchy(data, tenant_slugs)
    build_ci_assignments(data, device_pool, cluster_pool, vm_pool, app_service_names)

    # Re-declare in dependency order: build_* above populated `data` in
    # convenient-for-generation order, not necessarily the order
    # test-deployment.py needs to see them in (an object referenced by a
    # later entry must be listed earlier — see that script's own
    # docstring).
    ordered = {}
    for key in (
        'tenancy/tenants/',
        'tenancy/contact-groups/',
        'tenancy/contacts/',
        'dcim/sites/',
        'dcim/manufacturers/',
        'dcim/device-roles/',
        'dcim/device-types/',
        'dcim/devices/',
        'virtualization/cluster-groups/',
        'virtualization/cluster-types/',
        'virtualization/clusters/',
        'virtualization/virtual-machines/',
        'plugins/service-specification/lifecycles/',
        'plugins/service-specification/slas/',
        'plugins/service-specification/operation-times/',
        'plugins/service-specification/availabilities/',
        'plugins/service-specification/criticalities/',
        'plugins/service-specification/environments/',
        'plugins/service-specification/mtats/',
        'plugins/service-specification/ci-functions/',
        'plugins/service-specification/portfolios/',
        'plugins/service-specification/services/',
        'plugins/service-specification/service-offerings/',
        'plugins/service-specification/app-services/',
        'plugins/service-specification/device-service-infos/',
        'plugins/service-specification/cluster-service-infos/',
        'plugins/service-specification/virtual-machine-service-infos/',
    ):
        ordered[key] = data[key]

    with OUTPUT_FILE.open('w') as f:
        json.dump(ordered, f, indent=2)
        f.write('\n')

    total = sum(len(v) for v in ordered.values())
    print(f'Wrote {OUTPUT_FILE} — {len(ordered)} endpoints, {total} objects total.')
    for key, values in ordered.items():
        print(f'  {key}: {len(values)}')


if __name__ == '__main__':
    main()
