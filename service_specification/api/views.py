from netbox.api.viewsets import NetBoxModelViewSet

from service_specification import filtersets, models

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
