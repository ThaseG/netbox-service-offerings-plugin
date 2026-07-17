from netbox.api.routers import NetBoxRouter

from . import views

app_name = 'service_specification'

router = NetBoxRouter()
router.register('portfolio', views.PortfolioViewSet)
router.register('service', views.ServiceViewSet)
router.register('service-offering', views.ServiceOfferingViewSet)
router.register('app-service', views.AppServiceViewSet)
router.register('lifecycle', views.LifecycleViewSet)
router.register('sla', views.SLAViewSet)
router.register('operation-time', views.OperationTimeViewSet)
router.register('availability', views.AvailabilityViewSet)
router.register('mtat', views.MTATViewSet)
router.register('criticality', views.CriticalityViewSet)
router.register('environment', views.EnvironmentViewSet)
router.register('ci-function', views.CIFunctionViewSet)

urlpatterns = router.urls
