from netbox.api.routers import NetBoxRouter

from . import views

app_name = 'service_specification'

router = NetBoxRouter()
# Prefixes are deliberately plural, matching urls.py's UI paths exactly
# (e.g. 'portfolios' here <-> 'portfolios/' there) — the whole point is
# that swapping between the UI and its REST API is just adding/removing
# "/api" right after the hostname, nothing else in the path changes. The
# four *-service-info entries have no UI list page of their own (they're
# only reachable via a tab on their parent Device/VM/Cluster/ClusterGroup),
# but are still named as plural collections for consistency with the rest.
router.register('portfolios', views.PortfolioViewSet)
router.register('services', views.ServiceViewSet)
router.register('service-offerings', views.ServiceOfferingViewSet)
router.register('app-services', views.AppServiceViewSet)
router.register('lifecycles', views.LifecycleViewSet)
router.register('slas', views.SLAViewSet)
router.register('operation-times', views.OperationTimeViewSet)
router.register('availabilities', views.AvailabilityViewSet)
router.register('mtats', views.MTATViewSet)
router.register('criticalities', views.CriticalityViewSet)
router.register('environments', views.EnvironmentViewSet)
router.register('ci-functions', views.CIFunctionViewSet)
router.register('device-service-infos', views.DeviceServiceInfoViewSet)
router.register('virtual-machine-service-infos', views.VirtualMachineServiceInfoViewSet)
router.register('cluster-service-infos', views.ClusterServiceInfoViewSet)
router.register('cluster-group-service-infos', views.ClusterGroupServiceInfoViewSet)

urlpatterns = router.urls
