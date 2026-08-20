#!/usr/bin/env python3
"""Regenerates ci/scripts/test-deployment.json — 20 tenants (realistic
company names), each with its own site (named after a real city) and a
small, realistic network (see build_tenants_and_infra: 1 Firewall cabled
to 2 Switches, each cabled to 2 of 4 Servers, split into 2 Clusters in 1
Cluster Group, plus 6 VMs), plus 2 Service Portfolios each realizing 20
Service Offerings across two rounds (two per tenant, covering all 20
tenants twice with different themes), each with its own Application
Service, and its own 1:1 Contract (which in turn gets 2 Contract Rate
Cards of its own). VMs are the main Technical CI kind linked to
Application Services — each tenant's 6 VMs split 2-and-4 across its 2
Application Services — plus a couple of tenants' Firewalls/Switches are
also linked to one Application Service each, so those kinds have at least
one real example too (see build_ci_assignments).

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

# Device type per role, shared across every tenant's network (see
# build_tenants_and_infra): 1 Firewall, 2 Switches, 4 Servers.
DEVICE_TYPE_BY_ROLE = {
    'firewall': 'fortigate-100f',
    'switch': 'c9300-24t',
    'server': 'poweredge-r750',
}
INTERFACE_TYPE = '1000base-t'

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

# Slugs of the 3 manufacturers created in build_lookups() — reused as
# Contract.vendor below. RateCardIntervalChoices' 3 values (see choices.py),
# duplicated here rather than imported since this generator is otherwise
# fully standalone from the plugin package.
MANUFACTURER_SLUGS = ['cisco', 'fortinet', 'dell']
RATE_CARD_INTERVALS = ['monthly', 'one-time', 'others']

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
    data['virtualization/cluster-types/'] = [{'name': 'VMware', 'slug': 'vmware'}]

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
    """One tenant per COMPANIES entry, each with a single site (a distinct
    real city — see CITIES) and a small, realistic network:

      Firewall --- Switch A --- Server 1 (Cluster A)
               \\            \\- Server 2 (Cluster A)
                `- Switch B --- Server 3 (Cluster B)
                             \\- Server 4 (Cluster B)

    1 Firewall cabled to both Switches, each Switch cabled to 2 of the 4
    Servers, those Servers split 2-and-2 into 2 Clusters, both Clusters in
    1 Cluster Group (type VMware). The Firewall's first switch-facing
    interface gets an IP on its own /24 (10.<tenant index>.0.0/24 — a
    different one per tenant).

    6 VMs per tenant, not 4: one on each of the 4 Servers (named to match,
    both VirtualMachine.device and .cluster set to that Server/its
    Cluster) plus 2 extras (one per Cluster, cluster-scoped only, no
    specific host Server) — 6 so build_ci_assignments can split them
    2-and-4 across the tenant's 2 Application Services. Each Server also
    gets its own Device.cluster set to match, so Product View's
    "OtherServersInCluster"/Virtualization branches (see
    views._extend_ci_infra) have real sibling Devices to find.

    Devices/Clusters/Cluster Groups mostly aren't linked to Application
    Services — see build_ci_assignments — VMs are the only Technical CI
    kind assigned at scale. The Firewall/Switch names captured in
    network_by_tenant below exist so build_ci_assignments can additionally
    give a couple of tenants' Application Services a Firewall or Switch
    too (a small, deliberately limited exception — most tenants' Firewalls/
    Switches stay unassigned).

    Returns (vms_by_tenant, network_by_tenant): vms_by_tenant maps
    tenant_slug -> that tenant's 6 VM names, in creation order (Servers 1-4
    first, then the 2 extras); network_by_tenant maps tenant_slug ->
    {'firewall': fw_name, 'switches': [sw_name, sw_name]}.
    """
    data['tenancy/tenants/'] = []
    data['dcim/sites/'] = []
    data['dcim/devices/'] = []
    data['dcim/interfaces/'] = []
    data['dcim/cables/'] = []
    data['ipam/ip-addresses/'] = []
    data['virtualization/cluster-groups/'] = []
    data['virtualization/clusters/'] = []
    data['virtualization/virtual-machines/'] = []

    vms_by_tenant = {}
    network_by_tenant = {}

    for i, company in enumerate(COMPANIES):
        tenant_slug = slugify(company)
        data['tenancy/tenants/'].append({'name': company, 'slug': tenant_slug})

        # Only the first of each tenant's originally-allocated (HQ, Branch)
        # city pair is used now that there's a single site per tenant —
        # the second half of CITIES is simply unused spare capacity.
        city = CITIES[2 * i]
        site_name = f'HQ-{city}'
        site_slug = slugify(site_name)
        data['dcim/sites/'].append(
            {
                'name': site_name,
                'slug': site_slug,
                'physical_address': f'{city} Business District',
                'tenant': tenant_slug,
            }
        )

        cluster_group_slug = f'{tenant_slug}-infra'
        data['virtualization/cluster-groups/'].append({'name': f'{company} Infrastructure', 'slug': cluster_group_slug})

        fw_name = f'{city}-FW-01'
        data['dcim/devices/'].append(
            {'name': fw_name, 'role': 'firewall', 'device_type': DEVICE_TYPE_BY_ROLE['firewall'], 'site': site_slug}
        )
        fw_interfaces = [f'{fw_name} internal{n}' for n in (1, 2)]
        for fw_iface in fw_interfaces:
            data['dcim/interfaces/'].append({'name': fw_iface, 'device': fw_name, 'type': INTERFACE_TYPE})

        vm_names = []
        vm_n = 0
        cluster_names = []
        switch_names = []
        for sw_n, letter in ((1, 'A'), (2, 'B')):
            sw_name = f'{city}-SW-{sw_n:02d}'
            switch_names.append(sw_name)
            data['dcim/devices/'].append(
                {'name': sw_name, 'role': 'switch', 'device_type': DEVICE_TYPE_BY_ROLE['switch'], 'site': site_slug}
            )
            sw_uplink = f'{sw_name} uplink'
            data['dcim/interfaces/'].append({'name': sw_uplink, 'device': sw_name, 'type': INTERFACE_TYPE})
            data['dcim/cables/'].append(
                {
                    'a_terminations': [{'object_type': 'dcim.interface', 'name': fw_interfaces[sw_n - 1]}],
                    'b_terminations': [{'object_type': 'dcim.interface', 'name': sw_uplink}],
                }
            )

            cluster_name = f'{city} Cluster {letter}'
            cluster_names.append(cluster_name)
            data['virtualization/clusters/'].append(
                {
                    'name': cluster_name,
                    'type': 'vmware',
                    'group': cluster_group_slug,
                    'scope_type': 'dcim.site',
                    'scope_id': site_slug,
                }
            )

            for port_n in (1, 2):
                overall_srv_n = (sw_n - 1) * 2 + port_n
                srv_name = f'{city}-SRV-{overall_srv_n:02d}'
                data['dcim/devices/'].append(
                    {
                        'name': srv_name,
                        'role': 'server',
                        'device_type': DEVICE_TYPE_BY_ROLE['server'],
                        'site': site_slug,
                        # Host of this Cluster (Product View's "OtherServersInCluster"
                        # / Virtualization branches — see views._extend_ci_infra —
                        # depend on Device.cluster actually being set here, not
                        # just on the Cluster and VM sides).
                        'cluster': cluster_name,
                    }
                )
                srv_iface = f'{srv_name} nic1'
                sw_port = f'{sw_name} port{port_n}'
                data['dcim/interfaces/'].append({'name': srv_iface, 'device': srv_name, 'type': INTERFACE_TYPE})
                data['dcim/interfaces/'].append({'name': sw_port, 'device': sw_name, 'type': INTERFACE_TYPE})
                data['dcim/cables/'].append(
                    {
                        'a_terminations': [{'object_type': 'dcim.interface', 'name': sw_port}],
                        'b_terminations': [{'object_type': 'dcim.interface', 'name': srv_iface}],
                    }
                )

                # VM hosted on this Server — VirtualMachine.device is a real
                # NetBox field (verified against 4.6.5 source while building
                # Product View), not just a naming convention.
                vm_n += 1
                vm_name = f'{city.lower()}-vm-{vm_n:02d}'
                data['virtualization/virtual-machines/'].append(
                    {'name': vm_name, 'cluster': cluster_name, 'device': srv_name}
                )
                vm_names.append(vm_name)

        # 2 extra VMs (one per Cluster) so this tenant has 6 total, split
        # 2-and-4 across its 2 Application Services in build_ci_assignments.
        for cluster_name in cluster_names:
            vm_n += 1
            vm_name = f'{city.lower()}-vm-{vm_n:02d}'
            data['virtualization/virtual-machines/'].append({'name': vm_name, 'cluster': cluster_name})
            vm_names.append(vm_name)

        # Firewall's switch-facing IP — a distinct /24 per tenant.
        data['ipam/ip-addresses/'].append(
            {
                'address': f'10.{i}.0.1/24',
                'assigned_object_type': 'dcim.interface',
                'assigned_object_id': fw_interfaces[0],
            }
        )

        vms_by_tenant[tenant_slug] = vm_names
        network_by_tenant[tenant_slug] = {'firewall': fw_name, 'switches': switch_names}

    return vms_by_tenant, network_by_tenant


def build_hierarchy(data, tenant_slugs):
    """2 Portfolios, each with one pass-through Service and 10 Service
    Offering themes. Every tenant gets 2 Service Offerings, not 1: the
    10-theme x 2-portfolio combination (20 combos) is walked twice, the
    second pass with tenant assignment rotated by half the tenant list
    (10 of 20) so each tenant's second Offering always lands on a
    different theme than its first — 40 Offerings total, each with its
    own 1:1 Application Service. Each Offering also gets its own 1:1
    Contract, and each Contract gets 2 Contract Rate Cards.
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
    contracts = []
    rate_cards = []

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

                # One Contract per Offering, with 2 Contract Rate Cards of
                # its own — contract_number reuses the same CN-#### scheme
                # ServiceOffering.contract_number used before it became a
                # real reference (see models.py/forms.py's ServiceOffering).
                contract_number = f'CN-{offering_index + 1:04d}'
                start_year = 2022 + (offering_index % 3)
                contracts.append(
                    {
                        'contract_number': contract_number,
                        'external_reference': f'EXT-{offering_index + 1:04d}',
                        'short_description': f'Contract covering {theme} for {tenant_name}.',
                        'description': f'Commercial agreement backing {offering_name}.',
                        'project': theme,
                        'vendor': MANUFACTURER_SLUGS[offering_index % len(MANUFACTURER_SLUGS)],
                        'location': f'{tenant_name} Headquarters',
                        'tenant': tenant_slug,
                        'contact_person': ['Elena Petrova'],
                        'primary_contact': ['Franklin Diaz'],
                        'contract_manager': ['Jack Thompson'],
                        'approver': 'David Kim',
                        'business_unit': 'app1-business-unit',
                        'contract_starts': f'{start_year}-01-01',
                        'contract_ends': f'{start_year + 3}-12-31',
                    }
                )
                for position in (1, 2):
                    rate_cards.append(
                        {
                            'contract': contract_number,
                            'contract_position_number': f'{contract_number}-POS-{position:02d}',
                            'short_description': f'Rate card {position} for {contract_number}.',
                            'description': f'Position {position} of the {offering_name} contract.',
                            'order_number': f'PO-{offering_index + 1:04d}-{position}',
                            'project': theme,
                            'base_costs': 500 + (offering_index * 10) + (position * 100),
                            'hourly_rate': 50 + (position * 10),
                            'hours_spend': 10 + (position * 5),
                            'interval': RATE_CARD_INTERVALS[(offering_index + position) % len(RATE_CARD_INTERVALS)],
                            'billing': position == 1,
                            'start_date': f'{start_year}-01-01',
                            'end_date': f'{start_year + 3}-12-31',
                        }
                    )

                offerings.append(
                    {
                        'name': offering_name,
                        'description': offering_name,
                        'lifecycle': lifecycle_slug,
                        'contract': contract_number,
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
    data['plugins/service-specification/contracts/'] = contracts
    data['plugins/service-specification/contract-rate-cards/'] = rate_cards
    data['plugins/service-specification/service-offerings/'] = offerings
    data['plugins/service-specification/app-services/'] = app_services

    return tenant_by_offering


def build_ci_assignments(data, vms_by_tenant, tenant_by_offering, network_by_tenant):
    """VMs are the main Technical CI kind linked to Application Services —
    each tenant's 6 VMs (see build_tenants_and_infra) split 2-and-4 across
    its 2 Application Services, first Offering's Application Service
    getting the first 2 VMs, second Offering's getting the other 4.

    On top of that, a couple of tenants' Firewalls/Switches are *also*
    linked to an Application Service (cluster-service-infos/
    cluster-group-service-infos stay empty — nothing asked for those):
    FIREWALL_TENANT_COUNT tenants' first Application Service additionally
    gets that tenant's Firewall, and SWITCH_TENANT_COUNT tenants' second
    Application Service additionally gets one of that tenant's Switches —
    so there's at least one real example of each Technical CI kind besides
    VMs to look at, without doing it at the same scale as VMs.
    """
    FIREWALL_TENANT_COUNT = 2
    SWITCH_TENANT_COUNT = 2

    data['plugins/service-specification/virtual-machine-service-infos/'] = []
    data['plugins/service-specification/device-service-infos/'] = []
    data['plugins/service-specification/cluster-service-infos/'] = []
    data['plugins/service-specification/cluster-group-service-infos/'] = []

    app_services_by_tenant = {}
    for app_service_name, tenant_slug in tenant_by_offering.items():
        app_services_by_tenant.setdefault(tenant_slug, []).append(app_service_name)

    tenant_slugs_in_order = list(app_services_by_tenant)

    for tenant_slug, app_service_names in app_services_by_tenant.items():
        first_app_service, second_app_service = app_service_names
        for i, vm_name in enumerate(vms_by_tenant[tenant_slug]):
            app_service = first_app_service if i < 2 else second_app_service
            data['plugins/service-specification/virtual-machine-service-infos/'].append(
                {'virtual_machine': vm_name, 'application_services': [app_service]}
            )

    for tenant_slug in tenant_slugs_in_order[:FIREWALL_TENANT_COUNT]:
        first_app_service = app_services_by_tenant[tenant_slug][0]
        firewall_name = network_by_tenant[tenant_slug]['firewall']
        data['plugins/service-specification/device-service-infos/'].append(
            {'device': firewall_name, 'application_services': [first_app_service]}
        )

    for tenant_slug in tenant_slugs_in_order[:SWITCH_TENANT_COUNT]:
        second_app_service = app_services_by_tenant[tenant_slug][1]
        switch_name = network_by_tenant[tenant_slug]['switches'][0]
        data['plugins/service-specification/device-service-infos/'].append(
            {'device': switch_name, 'application_services': [second_app_service]}
        )


def main():
    data = {}

    build_lookups(data)
    vms_by_tenant, network_by_tenant = build_tenants_and_infra(data)
    tenant_slugs = [t['slug'] for t in data['tenancy/tenants/']]
    tenant_by_offering = build_hierarchy(data, tenant_slugs)
    build_ci_assignments(data, vms_by_tenant, tenant_by_offering, network_by_tenant)

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
        # Clusters (and what they depend on) now have to precede Devices:
        # Device.cluster (see build_tenants_and_infra) references a Cluster,
        # which itself only needs Sites (already above), not Devices.
        'virtualization/cluster-groups/',
        'virtualization/cluster-types/',
        'virtualization/clusters/',
        'dcim/devices/',
        'dcim/interfaces/',
        'dcim/cables/',
        'ipam/ip-addresses/',
        # ...and Virtual Machines now come after Devices too:
        # VirtualMachine.device (see build_tenants_and_infra) references a
        # Device.
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
        'plugins/service-specification/contracts/',
        'plugins/service-specification/contract-rate-cards/',
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
