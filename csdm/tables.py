import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import (
    MTAT,
    SLA,
    AppService,
    Availability,
    Criticality,
    Environment,
    Lifecycle,
    OperationTime,
    Portfolio,
    Service,
    ServiceOffering,
    TechCI,
)

__all__ = (
    'PortfolioTable',
    'ServiceTable',
    'ServiceOfferingTable',
    'AppServiceTable',
    'TechCITable',
    'LifecycleTable',
    'SLATable',
    'OperationTimeTable',
    'AvailabilityTable',
    'CriticalityTable',
    'EnvironmentTable',
    'MTATTable',
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
    tags = columns.TagColumn(url_name='plugins:csdm:lifecycle_list')

    class Meta(LookupTable.Meta):
        model = Lifecycle


class SLATable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:csdm:sla_list')

    class Meta(LookupTable.Meta):
        model = SLA
        fields = LookupTable.Meta.fields + ('sla_definition',)
        default_columns = ('pk', 'name', 'sla_definition', 'description')


class OperationTimeTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:csdm:operationtime_list')

    class Meta(LookupTable.Meta):
        model = OperationTime


class AvailabilityTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:csdm:availability_list')

    class Meta(LookupTable.Meta):
        model = Availability


class CriticalityTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:csdm:criticality_list')

    class Meta(LookupTable.Meta):
        model = Criticality


class EnvironmentTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:csdm:environment_list')

    class Meta(LookupTable.Meta):
        model = Environment


class MTATTable(LookupTable):
    tags = columns.TagColumn(url_name='plugins:csdm:mtat_list')

    class Meta(LookupTable.Meta):
        model = MTAT
        fields = LookupTable.Meta.fields + ('value', 'unit')
        default_columns = ('pk', 'name', 'value', 'unit', 'description')


class PortfolioTable(NetBoxTable):
    name = tables.Column(linkify=True)
    lifecycle = tables.Column(linkify=True)
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:csdm:portfolio_list')

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
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:csdm:service_list')

    class Meta(NetBoxTable.Meta):
        model = Service
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


class ServiceOfferingTable(NetBoxTable):
    name = tables.Column(linkify=True)
    lifecycle = tables.Column(linkify=True)
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:csdm:serviceoffering_list')

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
    tags = columns.TagColumn(url_name='plugins:csdm:appservice_list')

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


class TechCITable(NetBoxTable):
    name = tables.Column(linkify=True)
    lifecycle = tables.Column(linkify=True)
    comments = columns.MarkdownColumn()
    tags = columns.TagColumn(url_name='plugins:csdm:techci_list')

    class Meta(NetBoxTable.Meta):
        model = TechCI
        fields = (
            'pk',
            'id',
            'name',
            'function',
            'lifecycle',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = ('pk', 'name', 'function', 'lifecycle', 'description')
