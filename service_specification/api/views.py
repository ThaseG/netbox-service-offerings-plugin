from core.api.serializers import JobSerializer
from dcim.api.views import DeviceViewSet, VirtualDeviceContextViewSet
from netbox.api.viewsets import NetBoxModelViewSet, NetBoxReadOnlyModelViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from virtualization.api.views import ClusterGroupViewSet, ClusterViewSet, VirtualMachineViewSet

from service_specification import filtersets, models
from service_specification.jobs import ThreeCHealthJob, ensure_scheduled

from . import serializers


class LifecycleViewSet(NetBoxModelViewSet):
    queryset = models.Lifecycle.objects.all()
    serializer_class = serializers.LifecycleSerializer
    filterset_class = filtersets.LifecycleFilterSet


class SLAViewSet(NetBoxModelViewSet):
    queryset = models.SLA.objects.all()
    serializer_class = serializers.SLASerializer
    filterset_class = filtersets.SLAFilterSet


class OperationTimeViewSet(NetBoxModelViewSet):
    queryset = models.OperationTime.objects.all()
    serializer_class = serializers.OperationTimeSerializer
    filterset_class = filtersets.OperationTimeFilterSet


class AvailabilityViewSet(NetBoxModelViewSet):
    queryset = models.Availability.objects.all()
    serializer_class = serializers.AvailabilitySerializer
    filterset_class = filtersets.AvailabilityFilterSet


class CriticalityViewSet(NetBoxModelViewSet):
    queryset = models.Criticality.objects.all()
    serializer_class = serializers.CriticalitySerializer
    filterset_class = filtersets.CriticalityFilterSet


class EnvironmentViewSet(NetBoxModelViewSet):
    queryset = models.Environment.objects.all()
    serializer_class = serializers.EnvironmentSerializer
    filterset_class = filtersets.EnvironmentFilterSet


class MTATViewSet(NetBoxModelViewSet):
    queryset = models.MTAT.objects.all()
    serializer_class = serializers.MTATSerializer
    filterset_class = filtersets.MTATFilterSet


class CIFunctionViewSet(NetBoxModelViewSet):
    queryset = models.CIFunction.objects.all()
    serializer_class = serializers.CIFunctionSerializer
    filterset_class = filtersets.CIFunctionFilterSet


class ContractViewSet(NetBoxModelViewSet):
    queryset = models.Contract.objects.all()
    serializer_class = serializers.ContractSerializer
    filterset_class = filtersets.ContractFilterSet


class ContractRateCardViewSet(NetBoxModelViewSet):
    queryset = models.ContractRateCard.objects.all()
    serializer_class = serializers.ContractRateCardSerializer
    filterset_class = filtersets.ContractRateCardFilterSet


class PortfolioViewSet(NetBoxModelViewSet):
    queryset = models.Portfolio.objects.all()
    serializer_class = serializers.PortfolioSerializer
    filterset_class = filtersets.PortfolioFilterSet


class ServiceViewSet(NetBoxModelViewSet):
    queryset = models.Service.objects.all()
    serializer_class = serializers.ServiceSerializer
    filterset_class = filtersets.ServiceFilterSet


class ServiceOfferingViewSet(NetBoxModelViewSet):
    queryset = models.ServiceOffering.objects.all()
    serializer_class = serializers.ServiceOfferingSerializer
    filterset_class = filtersets.ServiceOfferingFilterSet


class AppServiceViewSet(NetBoxModelViewSet):
    queryset = models.AppService.objects.all()
    serializer_class = serializers.AppServiceSerializer
    filterset_class = filtersets.AppServiceFilterSet


class DeviceServiceInfoViewSet(NetBoxModelViewSet):
    queryset = models.DeviceServiceInfo.objects.all()
    serializer_class = serializers.DeviceServiceInfoSerializer
    filterset_class = filtersets.DeviceServiceInfoFilterSet


class VirtualMachineServiceInfoViewSet(NetBoxModelViewSet):
    queryset = models.VirtualMachineServiceInfo.objects.all()
    serializer_class = serializers.VirtualMachineServiceInfoSerializer
    filterset_class = filtersets.VirtualMachineServiceInfoFilterSet


class ClusterServiceInfoViewSet(NetBoxModelViewSet):
    queryset = models.ClusterServiceInfo.objects.all()
    serializer_class = serializers.ClusterServiceInfoSerializer
    filterset_class = filtersets.ClusterServiceInfoFilterSet


class ClusterGroupServiceInfoViewSet(NetBoxModelViewSet):
    queryset = models.ClusterGroupServiceInfo.objects.all()
    serializer_class = serializers.ClusterGroupServiceInfoSerializer
    filterset_class = filtersets.ClusterGroupServiceInfoFilterSet


class VirtualDeviceContextServiceInfoViewSet(NetBoxModelViewSet):
    queryset = models.VirtualDeviceContextServiceInfo.objects.all()
    serializer_class = serializers.VirtualDeviceContextServiceInfoSerializer
    filterset_class = filtersets.VirtualDeviceContextServiceInfoFilterSet


#
# Technical CI dropdown endpoints: NetBox's own Device/VM/Cluster/
# ClusterGroup/VirtualDeviceContext API viewsets (same serializers, brief mode, permissions),
# swapped onto filtersets that also understand the plugin's AppService/
# Service Offering/Customer links — see filtersets.TechnicalCIFilterSetMixin.
#


class TechnicalCIDeviceViewSet(DeviceViewSet):
    filterset_class = filtersets.TechnicalCIDeviceFilterSet


class TechnicalCIVirtualMachineViewSet(VirtualMachineViewSet):
    filterset_class = filtersets.TechnicalCIVirtualMachineFilterSet


class TechnicalCIClusterViewSet(ClusterViewSet):
    filterset_class = filtersets.TechnicalCIClusterFilterSet


class TechnicalCIClusterGroupViewSet(ClusterGroupViewSet):
    filterset_class = filtersets.TechnicalCIClusterGroupFilterSet


class TechnicalCIVirtualDeviceContextViewSet(VirtualDeviceContextViewSet):
    filterset_class = filtersets.TechnicalCIVirtualDeviceContextFilterSet


#
# 3C
#


class ThreeCRuleViewSet(NetBoxModelViewSet):
    queryset = models.ThreeCRule.objects.all()
    serializer_class = serializers.ThreeCRuleSerializer
    filterset_class = filtersets.ThreeCRuleFilterSet


class ThreeCSettingsViewSet(NetBoxModelViewSet):
    """The ThreeCSettings singleton: list/retrieve/update only (it always
    exists — the first request creates it with defaults)."""

    queryset = models.ThreeCSettings.objects.all()
    serializer_class = serializers.ThreeCSettingsSerializer
    filterset_class = filtersets.ThreeCSettingsFilterSet
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    def initial(self, request, *args, **kwargs):
        # After authentication/permission checks, so anonymous requests
        # can't create the row.
        super().initial(request, *args, **kwargs)
        models.ThreeCSettings.load()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        # Move the daily job if its run time changed. Best effort: the
        # report re-checks the schedule on every view anyway.
        try:
            ensure_scheduled(serializer.instance)
        except Exception:
            pass


class ThreeCSnapshotViewSet(NetBoxReadOnlyModelViewSet):
    queryset = models.ThreeCSnapshot.objects.all()
    serializer_class = serializers.ThreeCSnapshotSerializer
    filterset_class = filtersets.ThreeCSnapshotFilterSet

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Queue a 3C health calculation now (the report's "Run now"),
        requiring the add-snapshot permission. Returns the queued Job."""
        job = ThreeCHealthJob.enqueue(user=request.user)
        return Response(JobSerializer(job, context={'request': request}).data, status=status.HTTP_202_ACCEPTED)


class ThreeCFindingViewSet(NetBoxReadOnlyModelViewSet):
    queryset = models.ThreeCFinding.objects.select_related('tenant', 'snapshot')
    serializer_class = serializers.ThreeCFindingSerializer
    filterset_class = filtersets.ThreeCFindingFilterSet
