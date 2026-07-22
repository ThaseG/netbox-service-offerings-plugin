import django_filters
from dcim.models import Device
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from virtualization.models import Cluster, ClusterGroup, VirtualMachine

from .models import (
    MTAT,
    SLA,
    AppService,
    Availability,
    CIFunction,
    ClusterGroupServiceInfo,
    ClusterServiceInfo,
    Criticality,
    DeviceServiceInfo,
    Environment,
    Lifecycle,
    OperationTime,
    Portfolio,
    Service,
    ServiceOffering,
    VirtualMachineServiceInfo,
)

__all__ = (
    'PortfolioFilterSet',
    'ServiceFilterSet',
    'ServiceOfferingFilterSet',
    'AppServiceFilterSet',
    'LifecycleFilterSet',
    'SLAFilterSet',
    'OperationTimeFilterSet',
    'AvailabilityFilterSet',
    'CriticalityFilterSet',
    'EnvironmentFilterSet',
    'MTATFilterSet',
    'CIFunctionFilterSet',
    'DeviceServiceInfoFilterSet',
    'VirtualMachineServiceInfoFilterSet',
    'ClusterServiceInfoFilterSet',
    'ClusterGroupServiceInfoFilterSet',
)


class LifecycleFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Lifecycle
        fields = ('id', 'name', 'slug')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class SLAFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = SLA
        fields = ('id', 'name', 'slug', 'sla_definition')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value) | Q(sla_definition__icontains=value)
        )


class OperationTimeFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = OperationTime
        fields = ('id', 'name', 'slug')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class AvailabilityFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Availability
        fields = ('id', 'name', 'slug')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class CriticalityFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Criticality
        fields = ('id', 'name', 'slug')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class EnvironmentFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Environment
        fields = ('id', 'name', 'slug')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class MTATFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MTAT
        fields = ('id', 'name', 'slug', 'value', 'unit')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class CIFunctionFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = CIFunction
        fields = ('id', 'name', 'slug')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class PortfolioFilterSet(NetBoxModelFilterSet):
    lifecycle_id = django_filters.ModelMultipleChoiceFilter(
        field_name='lifecycle',
        queryset=Lifecycle.objects.all(),
        label='Lifecycle (ID)',
    )

    class Meta:
        model = Portfolio
        fields = ('id', 'name', 'lifecycle_id')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class ServiceFilterSet(NetBoxModelFilterSet):
    lifecycle_id = django_filters.ModelMultipleChoiceFilter(
        field_name='lifecycle',
        queryset=Lifecycle.objects.all(),
        label='Lifecycle (ID)',
    )
    service_portfolio_id = django_filters.ModelMultipleChoiceFilter(
        field_name='service_portfolio',
        queryset=Portfolio.objects.all(),
        label='Service Portfolio (ID)',
    )
    ci_function_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ci_function',
        queryset=CIFunction.objects.all(),
        label='CI Function (ID)',
    )

    class Meta:
        model = Service
        fields = ('id', 'name', 'lifecycle_id', 'service_portfolio_id', 'ci_function_id')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class ServiceOfferingFilterSet(NetBoxModelFilterSet):
    lifecycle_id = django_filters.ModelMultipleChoiceFilter(
        field_name='lifecycle',
        queryset=Lifecycle.objects.all(),
        label='Lifecycle (ID)',
    )
    service_id = django_filters.ModelMultipleChoiceFilter(
        field_name='service',
        queryset=Service.objects.all(),
        label='Service (ID)',
    )

    class Meta:
        model = ServiceOffering
        fields = ('id', 'name', 'contract_number', 'lifecycle_id', 'service_id')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value) | Q(contract_number__icontains=value)
        )


class AppServiceFilterSet(NetBoxModelFilterSet):
    lifecycle_id = django_filters.ModelMultipleChoiceFilter(
        field_name='lifecycle',
        queryset=Lifecycle.objects.all(),
        label='Lifecycle (ID)',
    )
    environment_id = django_filters.ModelMultipleChoiceFilter(
        field_name='environment',
        queryset=Environment.objects.all(),
        label='Environment (ID)',
    )
    service_offering_id = django_filters.ModelMultipleChoiceFilter(
        field_name='service_offering',
        queryset=ServiceOffering.objects.all(),
        label='Service Offering (ID)',
    )

    class Meta:
        model = AppService
        fields = ('id', 'name', 'lifecycle_id', 'environment_id', 'service_offering_id')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class DeviceServiceInfoFilterSet(NetBoxModelFilterSet):
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )
    ci_function_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ci_function',
        queryset=CIFunction.objects.all(),
        label='CI Function (ID)',
    )
    lifecycle_id = django_filters.ModelMultipleChoiceFilter(
        field_name='lifecycle',
        queryset=Lifecycle.objects.all(),
        label='Lifecycle (ID)',
    )

    class Meta:
        model = DeviceServiceInfo
        fields = ('id', 'device_id', 'ci_function_id', 'lifecycle_id')


class VirtualMachineServiceInfoFilterSet(NetBoxModelFilterSet):
    virtual_machine_id = django_filters.ModelMultipleChoiceFilter(
        field_name='virtual_machine',
        queryset=VirtualMachine.objects.all(),
        label='Virtual machine (ID)',
    )
    ci_function_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ci_function',
        queryset=CIFunction.objects.all(),
        label='CI Function (ID)',
    )
    lifecycle_id = django_filters.ModelMultipleChoiceFilter(
        field_name='lifecycle',
        queryset=Lifecycle.objects.all(),
        label='Lifecycle (ID)',
    )

    class Meta:
        model = VirtualMachineServiceInfo
        fields = ('id', 'virtual_machine_id', 'ci_function_id', 'lifecycle_id')


class ClusterServiceInfoFilterSet(NetBoxModelFilterSet):
    cluster_id = django_filters.ModelMultipleChoiceFilter(
        field_name='cluster',
        queryset=Cluster.objects.all(),
        label='Cluster (ID)',
    )
    ci_function_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ci_function',
        queryset=CIFunction.objects.all(),
        label='CI Function (ID)',
    )
    lifecycle_id = django_filters.ModelMultipleChoiceFilter(
        field_name='lifecycle',
        queryset=Lifecycle.objects.all(),
        label='Lifecycle (ID)',
    )

    class Meta:
        model = ClusterServiceInfo
        fields = ('id', 'cluster_id', 'ci_function_id', 'lifecycle_id')


class ClusterGroupServiceInfoFilterSet(NetBoxModelFilterSet):
    cluster_group_id = django_filters.ModelMultipleChoiceFilter(
        field_name='cluster_group',
        queryset=ClusterGroup.objects.all(),
        label='Cluster group (ID)',
    )
    ci_function_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ci_function',
        queryset=CIFunction.objects.all(),
        label='CI Function (ID)',
    )
    lifecycle_id = django_filters.ModelMultipleChoiceFilter(
        field_name='lifecycle',
        queryset=Lifecycle.objects.all(),
        label='Lifecycle (ID)',
    )

    class Meta:
        model = ClusterGroupServiceInfo
        fields = ('id', 'cluster_group_id', 'ci_function_id', 'lifecycle_id')
