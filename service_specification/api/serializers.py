from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from service_specification.models import (
    MTAT,
    SLA,
    AppService,
    Availability,
    CIFunction,
    ClusterGroupServiceInfo,
    ClusterServiceInfo,
    Contract,
    ContractRateCard,
    Criticality,
    DeviceServiceInfo,
    Environment,
    Lifecycle,
    OperationTime,
    Portfolio,
    Service,
    ServiceOffering,
    ThreeCFinding,
    ThreeCRule,
    ThreeCSettings,
    ThreeCSnapshot,
    VirtualDeviceContextServiceInfo,
    VirtualMachineServiceInfo,
)

__all__ = (
    'ContractSerializer',
    'ContractRateCardSerializer',
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
    'VirtualDeviceContextServiceInfoSerializer',
    'ThreeCRuleSerializer',
    'ThreeCSettingsSerializer',
    'ThreeCSnapshotSerializer',
    'ThreeCFindingSerializer',
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


class ContractSerializer(NetBoxModelSerializer):
    # Computed property (models.py), not a real column — '__all__' only
    # introspects model fields, so it needs an explicit declaration to be
    # included; DRF always includes declared fields regardless of '__all__'.
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Contract
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'contract_number')


class ContractRateCardSerializer(NetBoxModelSerializer):
    total_costs = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = ContractRateCard
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'contract_position_number')


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


class _NoDisplayURLMixin:
    """NetBoxModelSerializer always adds a `display_url` field pointing at
    the object's own web page, computed purely from NetBox's URL-naming
    convention (<app_label>:<model_name>) — it doesn't go through
    get_absolute_url(). The four *ServiceInfo models below have no such
    page (they're only reachable as a tab on their parent Device/VM/
    Cluster/ClusterGroup, by design — see models.py's
    ServiceSpecificationInfoBase), so that reverse() 500s. Their `url`
    field (the REST API link) is unaffected and still resolves fine, since
    the router registration below does provide a real API detail view.
    """

    def get_fields(self):
        fields = super().get_fields()
        fields.pop('display_url', None)
        return fields


class DeviceServiceInfoSerializer(_NoDisplayURLMixin, NetBoxModelSerializer):
    class Meta:
        model = DeviceServiceInfo
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'device')


class VirtualMachineServiceInfoSerializer(_NoDisplayURLMixin, NetBoxModelSerializer):
    class Meta:
        model = VirtualMachineServiceInfo
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'virtual_machine')


class ClusterServiceInfoSerializer(_NoDisplayURLMixin, NetBoxModelSerializer):
    class Meta:
        model = ClusterServiceInfo
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'cluster')


class ClusterGroupServiceInfoSerializer(_NoDisplayURLMixin, NetBoxModelSerializer):
    class Meta:
        model = ClusterGroupServiceInfo
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'cluster_group')


class VirtualDeviceContextServiceInfoSerializer(_NoDisplayURLMixin, NetBoxModelSerializer):
    class Meta:
        model = VirtualDeviceContextServiceInfo
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'virtual_device_context')


#
# 3C
#


class ThreeCRuleSerializer(NetBoxModelSerializer):
    class Meta:
        model = ThreeCRule
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'name', 'rule_type', 'ci_type')


# Neither the settings singleton nor findings have a detail page of their
# own (see _NoDisplayURLMixin).
class ThreeCSettingsSerializer(_NoDisplayURLMixin, NetBoxModelSerializer):
    class Meta:
        model = ThreeCSettings
        fields = '__all__'
        brief_fields = ('id', 'url', 'display')


class ThreeCSnapshotSerializer(NetBoxModelSerializer):
    class Meta:
        model = ThreeCSnapshot
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'created', 'composite')


class ThreeCFindingSerializer(_NoDisplayURLMixin, NetBoxModelSerializer):
    # The failing CI's own web page.
    ci_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ThreeCFinding
        fields = '__all__'
        brief_fields = ('id', 'url', 'display', 'kpi', 'ci_type', 'ci_id', 'ci_name')

    def get_ci_url(self, obj):
        request = self.context.get('request')
        url = obj.get_absolute_url()
        return request.build_absolute_uri(url) if request else url
