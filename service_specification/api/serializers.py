from netbox.api.serializers import NetBoxModelSerializer

from service_specification.models import (
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
    'PortfolioSerializer',
    'ServiceSerializer',
    'ServiceOfferingSerializer',
    'AppServiceSerializer',
    'LifecycleSerializer',
    'SLASerializer',
    'OperationTimeSerializer',
    'AvailabilitySerializer',
    'CriticalitySerializer',
    'EnvironmentSerializer',
    'MTATSerializer',
    'CIFunctionSerializer',
    'DeviceServiceInfoSerializer',
    'VirtualMachineServiceInfoSerializer',
    'ClusterServiceInfoSerializer',
    'ClusterGroupServiceInfoSerializer',
)


class LifecycleSerializer(NetBoxModelSerializer):
    class Meta:
        model = Lifecycle
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class SLASerializer(NetBoxModelSerializer):
    class Meta:
        model = SLA
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class OperationTimeSerializer(NetBoxModelSerializer):
    class Meta:
        model = OperationTime
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class AvailabilitySerializer(NetBoxModelSerializer):
    class Meta:
        model = Availability
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class CriticalitySerializer(NetBoxModelSerializer):
    class Meta:
        model = Criticality
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class EnvironmentSerializer(NetBoxModelSerializer):
    class Meta:
        model = Environment
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class MTATSerializer(NetBoxModelSerializer):
    class Meta:
        model = MTAT
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class CIFunctionSerializer(NetBoxModelSerializer):
    class Meta:
        model = CIFunction
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class PortfolioSerializer(NetBoxModelSerializer):
    class Meta:
        model = Portfolio
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class ServiceSerializer(NetBoxModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class ServiceOfferingSerializer(NetBoxModelSerializer):
    class Meta:
        model = ServiceOffering
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class AppServiceSerializer(NetBoxModelSerializer):
    class Meta:
        model = AppService
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name')


class DeviceServiceInfoSerializer(NetBoxModelSerializer):
    class Meta:
        model = DeviceServiceInfo
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'device')


class VirtualMachineServiceInfoSerializer(NetBoxModelSerializer):
    class Meta:
        model = VirtualMachineServiceInfo
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'virtual_machine')


class ClusterServiceInfoSerializer(NetBoxModelSerializer):
    class Meta:
        model = ClusterServiceInfo
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'cluster')


class ClusterGroupServiceInfoSerializer(NetBoxModelSerializer):
    class Meta:
        model = ClusterGroupServiceInfo
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'cluster_group')
