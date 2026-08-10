import django_tables2 as tables
from django.utils.html import format_html, format_html_join
from netbox.tables import NetBoxTable, columns
from tenancy.models import Tenant

from .models import (
    MTAT,
    SLA,
    AppService,
    Availability,
    CIFunction,
    Contract,
    ContractRateCard,
    Criticality,
    Environment,
    Lifecycle,
    OperationTime,
    Portfolio,
    Service,
    ServiceOffering,
)

__all__ = (
    'ContractTable',
    'ContractRateCardTable',
    'PortfolioTable',
    'ServiceTable',
    'ServiceOfferingTable',
    'AppServiceTable',
    'LifecycleTable',
    'SLATable',
    'OperationTimeTable',
    'AvailabilityTable',
    'CriticalityTable',
    'EnvironmentTable',
    'MTATTable',
    'CIFunctionTable',
    'TenantReportTable',
)


class LookupTable(NetBoxTable):
    """Shared columns for the simple name/description/comments lookup models.
    Each subclass below re-declares `tags` with its own url_name — django-tables2
    fields can't be templated, so this base intentionally leaves it unset."""

    name = tables.Column(linkify=True)
    comments = columns.MarkdownColumn()

    class Meta(NetBoxTable.Meta):
        fields = ('pk', 'id', 'name', 'description', 'comments', 'tags', 'created', 'last_updated', 'actions')
        default_columns = ('pk', 'name', 'description')


class LifecycleTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:service_specification:lifecycle_list')
    color = columns.ColorColumn()

    class Meta(LookupTable.Meta):
        model = Lifecycle
        fields = LookupTable.Meta.fields + ('color',)
        default_columns = ('pk', 'name', 'color', 'description')


class SLATable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:service_specification:sla_list')

    class Meta(LookupTable.Meta):
        model = SLA
        fields = LookupTable.Meta.fields + ('sla_definition',)
        default_columns = ('pk', 'name', 'sla_definition', 'description')


class OperationTimeTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:service_specification:operationtime_list')

    class Meta(LookupTable.Meta):
        model = OperationTime


class AvailabilityTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:service_specification:availability_list')

    class Meta(LookupTable.Meta):
        model = Availability


class CriticalityTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:service_specification:criticality_list')

    class Meta(LookupTable.Meta):
        model = Criticality


class EnvironmentTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:service_specification:environment_list')

    class Meta(LookupTable.Meta):
        model = Environment


class MTATTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:service_specification:mtat_list')

    class Meta(LookupTable.Meta):
        model = MTAT
        fields = LookupTable.Meta.fields + ('value', 'unit')
        default_columns = ('pk', 'name', 'value', 'unit', 'description')


class CIFunctionTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:service_specification:cifunction_list')

    class Meta(LookupTable.Meta):
        model = CIFunction


class ContractTable(NetBoxTable):
    contract_number = tables.Column(linkify=True)
    status = tables.Column(orderable=False)
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:service_specification:contract_list')

    class Meta(NetBoxTable.Meta):
        model = Contract
        fields = (
            'pk',
            'id',
            'contract_number',
            'external_reference',
            'tenant',
            'tenant_group',
            'vendor',
            'location',
            'status',
            'contract_starts',
            'contract_ends',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = ('pk', 'contract_number', 'tenant', 'vendor', 'status', 'contract_starts', 'contract_ends')


class ContractRateCardTable(NetBoxTable):
    contract_position_number = tables.Column(linkify=True)
    contract = tables.Column(linkify=True)
    total_costs = tables.Column(orderable=False)
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:service_specification:contractratecard_list')

    class Meta(NetBoxTable.Meta):
        model = ContractRateCard
        fields = (
            'pk',
            'id',
            'contract',
            'contract_position_number',
            'active',
            'start_date',
            'end_date',
            'order_number',
            'base_costs',
            'hourly_rate',
            'hours_spend',
            'total_costs',
            'interval',
            'billing',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = (
            'pk',
            'contract',
            'contract_position_number',
            'active',
            'base_costs',
            'hourly_rate',
            'hours_spend',
            'total_costs',
            'interval',
        )


class PortfolioTable(NetBoxTable):
    name = tables.Column(linkify=True)
    lifecycle = columns.ColoredLabelColumn()
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:service_specification:portfolio_list')

    class Meta(NetBoxTable.Meta):
        model = Portfolio
        fields = (
            'pk',
            'id',
            'name',
            'lifecycle',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = ('pk', 'name', 'lifecycle', 'description')


class ServiceTable(NetBoxTable):
    name = tables.Column(linkify=True)
    lifecycle = columns.ColoredLabelColumn()
    ci_function = tables.Column(linkify=True)
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:service_specification:service_list')

    class Meta(NetBoxTable.Meta):
        model = Service
        fields = (
            'pk',
            'id',
            'name',
            'lifecycle',
            'ci_function',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = ('pk', 'name', 'lifecycle', 'ci_function', 'description')


class ServiceOfferingTable(NetBoxTable):
    name = tables.Column(linkify=True)
    contract = tables.Column(linkify=True)
    lifecycle = columns.ColoredLabelColumn()
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:service_specification:serviceoffering_list')

    class Meta(NetBoxTable.Meta):
        model = ServiceOffering
        fields = (
            'pk',
            'id',
            'name',
            'contract',
            'lifecycle',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = ('pk', 'name', 'contract', 'lifecycle', 'description')


class AppServiceTable(NetBoxTable):
    name = tables.Column(linkify=True)
    environment = tables.Column(linkify=True)
    lifecycle = columns.ColoredLabelColumn()
    service_offering = tables.Column(linkify=True)
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:service_specification:appservice_list')

    class Meta(NetBoxTable.Meta):
        model = AppService
        fields = (
            'pk',
            'id',
            'name',
            'environment',
            'lifecycle',
            'service_offering',
            'accepted_downtime',
            'ttr',
            'rpo',
            'rto',
            'bcm',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = ('pk', 'name', 'environment', 'lifecycle', 'service_offering', 'description')


#
# Report tables
#


class TenantReportTable(NetBoxTable):
    """One row per (Tenant, Service Offering) pair — views.TenantReportView
    expands each filtered Tenant into its related offerings (see
    utils.tenant_offering_filter) before handing rows to this table, so a
    Tenant with no related offerings still gets exactly one row, with
    blank offering/application-service/lifecycle columns, rather than
    being silently dropped from the report.

    Rows are plain views._TenantOfferingRow objects, not Tenant instances
    — Tenant is still Meta.model (NetBoxTable.__init__ unconditionally
    looks up custom fields/links for it, and it's the closest "primary"
    entity this report has), but every column here is rendered manually
    against `record.tenant` / `record.service_offering` /
    `record.application_service` rather than relying on accessor
    auto-resolution. actions/pk/id are intentionally left out: this table
    has no edit/delete/bulk actions to offer.
    """

    name = tables.Column(empty_values=(), orderable=False, verbose_name='Tenant')
    group = tables.Column(empty_values=(), orderable=False, verbose_name='Tenant Group')
    service_offering_lifecycle = columns.ColoredLabelColumn(
        accessor='service_offering__lifecycle',
        orderable=False,
        verbose_name='Service Offering Lifecycle',
    )
    contract = tables.Column(empty_values=(), orderable=False, verbose_name='Contract')
    contract_location = tables.Column(empty_values=(), orderable=False, verbose_name='Contract Location')
    sites = tables.Column(empty_values=(), orderable=False)
    service_offering = tables.Column(empty_values=(), orderable=False, verbose_name='Service Offering')
    application_services = tables.Column(empty_values=(), orderable=False, verbose_name='Application Services')

    empty_text = 'No Tenants found.'

    class Meta(NetBoxTable.Meta):
        model = Tenant
        fields = (
            'name',
            'group',
            'service_offering_lifecycle',
            'contract',
            'contract_location',
            'sites',
            'service_offering',
            'application_services',
        )
        # 'group' (Tenant Group) is deliberately excluded here: still a
        # selectable column (it's in `fields` above), just not shown until
        # the user adds it themselves via the table's column picker.
        default_columns = tuple(f for f in fields if f != 'group')

    def render_name(self, record):
        return format_html('<a href="{}">{}</a>', record.tenant.get_absolute_url(), record.tenant.name)

    def render_group(self, record):
        if not record.tenant.group:
            return '—'
        return format_html('<a href="{}">{}</a>', record.tenant.group.get_absolute_url(), record.tenant.group.name)

    def render_sites(self, record):
        return format_html_join(
            ', ', '<a href="{}">{}</a>', ((s.get_absolute_url(), s.name) for s in record.tenant.sites.all())
        )

    def render_contract(self, record):
        if not record.service_offering or not record.service_offering.contract:
            return '—'
        contract = record.service_offering.contract
        return format_html('<a href="{}">{}</a>', contract.get_absolute_url(), contract.contract_number)

    def render_contract_location(self, record):
        if not record.service_offering or not record.service_offering.contract:
            return '—'
        return record.service_offering.contract.location or '—'

    def render_service_offering(self, record):
        if not record.service_offering:
            return '—'
        return format_html(
            '<a href="{}">{}</a>', record.service_offering.get_absolute_url(), record.service_offering.name
        )

    def render_application_services(self, record):
        app_service = record.application_service
        if not app_service:
            return '—'
        return format_html('<a href="{}">{}</a>', app_service.get_absolute_url(), app_service.name)
