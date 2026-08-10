#!/usr/bin/env python3
"""Regenerates ci/scripts/test-deployment.json — 20 tenants (realistic
company names), each with its own HQ/Branch sites (named after real
cities) and ~20 Technical CIs (devices/cluster/cluster group/VMs), plus 2
Service Portfolios each realizing 20 Service Offerings across two rounds
(two per tenant, covering all 20 tenants twice with different themes),
each with its own Application Service. Every one of a tenant's Application
Services is assigned the full set of Technical CIs belonging to that same
tenant.

This is a one-off *generator*, not part of the actual deploy pipeline:
ci/scripts/test-deployment.py itself stays a generic "read JSON, POST it,
resolve references" engine with zero knowledge of how the JSON was
produced. Run this script, by hand, whenever the seeded dataset's shape or
scale needs to change; commit the regenerated test-deployment.json.
"""

import json
from pathlib import Path

OUTPUT_FILE = Path(__file__).with_name('test-deployment.json')

# 20 recognizable, "nice" company names for tenants — this is a private
# CI/demo seed fixture, not anything published as or claiming to be these
# companies, same spirit as the original single-tenant dataset's "Coca
# Cola" placeholder.
COMPANIES = [
    'Coca Cola',
    'Cisco',
    'SAP',
    'Google',
    'Amazon',
    'Microsoft',
    'IBM',
    'Oracle',
    'Siemens',
    'BMW',
    'Volkswagen',
    'Deutsche Bank',
    'Allianz',
    'Adidas',
    'Puma',
    'Nike',
    'Samsung',
    'Sony',
    'Toyota',
    'Shell',
]

# 40 distinct cities — two per tenant (HQ + Branch) — kept globally unique
# across the whole dataset so city-derived names (sites, devices, clusters,
# VMs) never collide without needing to prefix everything with the tenant.
CITIES = [
    'Munich',
    'Hamburg',
    'Berlin',
    'Frankfurt',
    'Cologne',
    'Stuttgart',
    'Dusseldorf',
    'Leipzig',
    'Dortmund',
    'Essen',
    'Vienna',
    'Zurich',
    'Amsterdam',
    'Brussels',
    'Paris',
    'London',
    'Madrid',
    'Milan',
    'Rome',
    'Lisbon',
    'Warsaw',
    'Prague',
    'Budapest',
    'Copenhagen',
    'Stockholm',
    'Oslo',
    'Dublin',
    'Helsinki',
    'Athens',
    'Geneva',
    'Singapore',
    'Tokyo',
    'Sydney',
    'Toronto',
    'Chicago',
    'Dallas',
    'Seattle',
    'Boston',
    'Miami',
    'Denver',
]

# (role slug, device type slug, name suffix, count per site) — shared
# across every tenant's sites.
DEVICE_ROLES = [
    ('firewall', 'fortigate-100f', 'FW', 2),
    ('switch', 'c9300-24t', 'SW', 2),
    ('server', 'poweredge-r750', 'SRV', 1),
]
VMS_PER_CLUSTER = 4

# 2 Service Portfolios, each with its own 10 offering themes — the
# Portfolio/Service layer only exists because a Service Offering can't
# exist without a parent Service; one Service per Portfolio keeps that
# layer a simple pass-through rather than adding more scale of its own.
PORTFOLIOS = [
    {
        'name': 'Digital Workplace Portfolio',
        'service_name': 'Digital Workplace Services',
        'themes': [
            'Managed Email',
            'Unified Communications',
            'Endpoint Management',
            'Helpdesk Support',
            'Identity & Access Management',
            'Video Conferencing',
            'File Sharing & Collaboration',
            'Mobile Device Management',
            'Print Services',
            'Virtual Desktop Infrastructure',
        ],
    },
    {
        'name': 'Cloud Infrastructure Portfolio',
        'service_name': 'Cloud Infrastructure Services',
        'themes': [
            'Cloud Backup',
            'Disaster Recovery',
            'Network Security',
            'Database Hosting',
            'Load Balancing',
            'Container Orchestration',
            'Data Analytics Platform',
            'Storage as a Service',
            'Monitoring & Observability',
            'DNS & DHCP Management',
        ],
    },
]

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

# (first, last, group) — one contact per group, reused across both
# Portfolios/Services/all 20 Offerings/AppServices: ownership groups are an
# org-chart concept, not something that multiplies with the number of
# tenants or offerings.
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


def build_tenants_and_infra(data):
    """One tenant per COMPANIES entry, each with an HQ + Branch site (a
    distinct real city each — see CITIES — so device/cluster/VM names
    derived from the city stay globally unique without a tenant prefix)
    and ~21 Technical CIs: 10 devices (5 per site), 1 tenant-level Cluster
    Group, 2 Clusters (1 per site) and 8 VMs (4 per cluster).

    Returns {tenant_slug: [(kind, name), ...]} — every Technical CI that
    belongs to that tenant, for build_ci_assignments() to hand to that
    tenant's one Application Service.
    """
    data['tenancy/tenants/'] = []
    data['dcim/sites/'] = []
    data['dcim/devices/'] = []
    data['virtualization/cluster-groups/'] = []
    data['virtualization/clusters/'] = []
    data['virtualization/virtual-machines/'] = []

    cis_by_tenant = {}

    for i, company in enumerate(COMPANIES):
        tenant_slug = slugify(company)
        data['tenancy/tenants/'].append({'name': company, 'slug': tenant_slug})
        tenant_cis = []

        hq_city, branch_city = CITIES[2 * i], CITIES[2 * i + 1]
        cluster_group_slug = f'{tenant_slug}-infra'
        data['virtualization/cluster-groups/'].append({'name': f'{company} Infrastructure', 'slug': cluster_group_slug})
        # Referenced by slug, not name: ClusterGroup has a slug field, and
        # the engine's REFERENCE_FIELDS resolves cluster_group references
        # against virtualization/cluster-groups/ keyed by slug-else-name —
        # since this model has a slug, using the name here would 400 with
        # "not found" the same way an earlier lifecycle/name mixup did.
        tenant_cis.append(('cluster_group', cluster_group_slug))

        for site_label, city in (('HQ', hq_city), ('Branch', branch_city)):
            site_name = f'{site_label}-{city}'
            site_slug = slugify(site_name)
            data['dcim/sites/'].append(
                {
                    'name': site_name,
                    'slug': site_slug,
                    'physical_address': f'{city} Business District',
                    'tenant': tenant_slug,
                }
            )

            for role_slug, device_type_slug, suffix, count in DEVICE_ROLES:
                for n in range(1, count + 1):
                    device_name = f'{city}-{suffix}-{n:02d}'
                    data['dcim/devices/'].append(
                        {'name': device_name, 'role': role_slug, 'device_type': device_type_slug, 'site': site_slug}
                    )
                    tenant_cis.append(('device', device_name))

            cluster_name = f'{city} Cluster'
            data['virtualization/clusters/'].append(
                {
                    'name': cluster_name,
                    'type': 'proxmox',
                    'group': cluster_group_slug,
                    'scope_type': 'dcim.site',
                    'scope_id': site_slug,
                }
            )
            tenant_cis.append(('cluster', cluster_name))

            for n in range(1, VMS_PER_CLUSTER + 1):
                vm_name = f'{city.lower()}-vm-{n:02d}'
                data['virtualization/virtual-machines/'].append({'name': vm_name, 'cluster': cluster_name})
                tenant_cis.append(('virtual_machine', vm_name))

        cis_by_tenant[tenant_slug] = tenant_cis

    return cis_by_tenant


def build_hierarchy(data, tenant_slugs):
    """2 Portfolios, each with one pass-through Service and 10 Service
    Offering themes. Every tenant gets 2 Service Offerings, not 1: the
    10-theme x 2-portfolio combination (20 combos) is walked twice, the
    second pass with tenant assignment rotated by half the tenant list
    (10 of 20) so each tenant's second Offering always lands on a
    different theme than its first — 40 Offerings total, each with its
    own 1:1 Application Service.
    """
    lifecycle_slugs = [slug for _name, slug, _desc, _color in LIFECYCLES]
    sla_slugs = [slug for _name, slug in SLAS]
    op_time_slugs = [slug for _name, slug in OPERATION_TIMES]
    availability_slugs = [slug for _name, slug in AVAILABILITIES]
    criticality_slugs = [slug for _name, slug in CRITICALITIES]
    environment_slugs = [slug for _name, slug in ENVIRONMENTS]
    mtat_slugs = [slug for _name, slug, _value in MTATS]

    shared_business_unit = ['app1-business-unit']
    shared_support_group = ['app-support-group']
    shared_change_group = ['app-change-group']

    portfolios = []
    services = []
    offerings = []
    app_services = []

    for portfolio in PORTFOLIOS:
        portfolios.append(
            {
                'name': portfolio['name'],
                'description': portfolio['name'],
                'lifecycle': 'operational',
                'portfolio_owner_contacts': ['Alice Johnson'],
                'portfolio_owner_contact_groups': ['portfolio-owners'],
                'portfolio_manager_contacts': ['Brian Smith'],
                'portfolio_manager_contact_groups': ['portfolio-managers'],
            }
        )
        services.append(
            {
                'name': portfolio['service_name'],
                'description': portfolio['service_name'],
                'lifecycle': 'operational',
                'ci_function': 'managed-exchange-service',
                'service_owner_contacts': ['David Kim'],
                'service_owner_contact_groups': ['service-owners'],
                'service_manager_contacts': ['Carla Nguyen'],
                'service_manager_contact_groups': ['service-managers'],
                'service_portfolio': [portfolio['name']],
                'business_unit': shared_business_unit,
                'support_group': shared_support_group,
                'change_group': shared_change_group,
            }
        )

    # global 0..39 across both rounds, also used to mix lifecycles/etc.
    offering_index = 0
    tenant_by_offering = {}

    for round_num in range(2):
        for portfolio in PORTFOLIOS:
            for theme in portfolio['themes']:
                # Position within this round's 20 (portfolio, theme) combos
                # maps directly to a tenant in round 0; round 1 shifts that
                # mapping by 10 tenants so every tenant's second Offering
                # uses a different theme than its first (see docstring).
                position_in_round = offering_index % len(tenant_slugs)
                tenant_slug = tenant_slugs[(position_in_round + round_num * 10) % len(tenant_slugs)]
                tenant_name = next(c for c in COMPANIES if slugify(c) == tenant_slug)
                offering_name = f'{theme} - {tenant_name}'
                # Mixed on purpose (not all "Available"): cycle through
                # every one of the 11 lifecycle statuses across the 40
                # offerings.
                lifecycle_slug = lifecycle_slugs[offering_index % len(lifecycle_slugs)]

                offerings.append(
                    {
                        'name': offering_name,
                        'description': offering_name,
                        'lifecycle': lifecycle_slug,
                        'service': [portfolio['service_name']],
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

                app_service_name = f'{theme} - {tenant_name} (Application Service)'
                app_services.append(
                    {
                        'name': app_service_name,
                        'description': app_service_name,
                        'environment': environment_slugs[offering_index % len(environment_slugs)],
                        'lifecycle': lifecycle_slugs[(offering_index + 1) % len(lifecycle_slugs)],
                        'service_offering': offering_name,
                        'business_unit': shared_business_unit,
                        'support_group': shared_support_group,
                        'change_group': shared_change_group,
                        'sla': [sla_slugs[offering_index % len(sla_slugs)]],
                        'owned_by_contact_group': 'app1-owner-group',
                        'operation_time': [op_time_slugs[offering_index % len(op_time_slugs)]],
                        'availability': [availability_slugs[offering_index % len(availability_slugs)]],
                        'mtat': [mtat_slugs[offering_index % len(mtat_slugs)]],
                        'service_criticality': [criticality_slugs[offering_index % len(criticality_slugs)]],
                        'accepted_downtime': 1 + (offering_index % 4),
                        'ttr': 1 + (offering_index % 3),
                        'rpo': 2 + (offering_index % 3),
                        'rto': 2 + (offering_index % 4),
                        'bcm': 1 + (offering_index % 3),
                    }
                )

                tenant_by_offering[app_service_name] = tenant_slug
                offering_index += 1

    data['plugins/service-specification/portfolios/'] = portfolios
    data['plugins/service-specification/services/'] = services
    data['plugins/service-specification/service-offerings/'] = offerings
    data['plugins/service-specification/app-services/'] = app_services

    return tenant_by_offering


def build_ci_assignments(data, cis_by_tenant, tenant_by_offering):
    """Each Technical CI belongs to exactly one tenant, but each tenant now
    has 2 Application Services (see build_hierarchy), not 1 — and every
    *ServiceInfo model is OneToOne with its Device/Cluster/ClusterGroup/
    VirtualMachine, so a CI can only ever get a single *ServiceInfo row.
    Both of a tenant's Application Services are therefore listed together
    in that one row's `application_services` (a ManyToMany field), rather
    than trying to create a second row for the same CI — which would 400
    on the OneToOne constraint.
    """
    endpoint_by_kind = {
        'device': 'plugins/service-specification/device-service-infos/',
        'cluster': 'plugins/service-specification/cluster-service-infos/',
        'cluster_group': 'plugins/service-specification/cluster-group-service-infos/',
        'virtual_machine': 'plugins/service-specification/virtual-machine-service-infos/',
    }
    field_by_kind = {
        'device': 'device',
        'cluster': 'cluster',
        'cluster_group': 'cluster_group',
        'virtual_machine': 'virtual_machine',
    }
    for endpoint in endpoint_by_kind.values():
        data[endpoint] = []

    app_services_by_tenant = {}
    for app_service_name, tenant_slug in tenant_by_offering.items():
        app_services_by_tenant.setdefault(tenant_slug, []).append(app_service_name)

    for tenant_slug, app_service_names in app_services_by_tenant.items():
        for kind, ci_name in cis_by_tenant[tenant_slug]:
            data[endpoint_by_kind[kind]].append(
                {field_by_kind[kind]: ci_name, 'application_services': app_service_names}
            )


def main():
    data = {}

    build_lookups(data)
    cis_by_tenant = build_tenants_and_infra(data)
    tenant_slugs = [t['slug'] for t in data['tenancy/tenants/']]
    tenant_by_offering = build_hierarchy(data, tenant_slugs)
    build_ci_assignments(data, cis_by_tenant, tenant_by_offering)

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
        'plugins/service-specification/cluster-group-service-infos/',
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
