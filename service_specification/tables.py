import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import (
    MTAT,
    SLA,
    AppService,
    Availability,
    CIFunction,
    Criticality,
    Environment,
    Lifecycle,
    OperationTime,
    Portfolio,
    Service,
    ServiceOffering,
)

__all__ = (
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

    class Meta(LookupTable.Meta):
        model = Lifecycle


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


class PortfolioTable(NetBoxTable):
    name = tables.Column(linkify=True)
    lifecycle = tables.Column(linkify=True)
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
    lifecycle = tables.Column(linkify=True)
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
    lifecycle = tables.Column(linkify=True)
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:service_specification:serviceoffering_list')

    class Meta(NetBoxTable.Meta):
        model = ServiceOffering
        fields = (
            'pk',
            'id',
            'name',
            'contract_number',
            'lifecycle',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = ('pk', 'name', 'contract_number', 'lifecycle', 'description')


class AppServiceTable(NetBoxTable):
    name = tables.Column(linkify=True)
    environment = tables.Column(linkify=True)
    lifecycle = tables.Column(linkify=True)
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
        default_columns = ('pk', 'name', 'environment', 'lifecycle', 'description')
