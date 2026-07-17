from django.urls import include, path
from utilities.urls import get_model_urls

app_name = 'service_specification'

# Importing views ensures every @register_model_view() decorator below has
# run (populating the registry get_model_urls() reads from) before this
# module builds urlpatterns.
from . import views  # noqa: E402,F401

urlpatterns = [
    path('portfolios/', include(get_model_urls('service_specification', 'portfolio', detail=False))),
    path('portfolios/<int:pk>/', include(get_model_urls('service_specification', 'portfolio'))),
    path('services/', include(get_model_urls('service_specification', 'service', detail=False))),
    path('services/<int:pk>/', include(get_model_urls('service_specification', 'service'))),
    path('service-offerings/', include(get_model_urls('service_specification', 'serviceoffering', detail=False))),
    path('service-offerings/<int:pk>/', include(get_model_urls('service_specification', 'serviceoffering'))),
    path('app-services/', include(get_model_urls('service_specification', 'appservice', detail=False))),
    path('app-services/<int:pk>/', include(get_model_urls('service_specification', 'appservice'))),
    path('lifecycles/', include(get_model_urls('service_specification', 'lifecycle', detail=False))),
    path('lifecycles/<int:pk>/', include(get_model_urls('service_specification', 'lifecycle'))),
    path('slas/', include(get_model_urls('service_specification', 'sla', detail=False))),
    path('slas/<int:pk>/', include(get_model_urls('service_specification', 'sla'))),
    path('operation-times/', include(get_model_urls('service_specification', 'operationtime', detail=False))),
    path('operation-times/<int:pk>/', include(get_model_urls('service_specification', 'operationtime'))),
    path('availabilities/', include(get_model_urls('service_specification', 'availability', detail=False))),
    path('availabilities/<int:pk>/', include(get_model_urls('service_specification', 'availability'))),
    path('criticalities/', include(get_model_urls('service_specification', 'criticality', detail=False))),
    path('criticalities/<int:pk>/', include(get_model_urls('service_specification', 'criticality'))),
    path('environments/', include(get_model_urls('service_specification', 'environment', detail=False))),
    path('environments/<int:pk>/', include(get_model_urls('service_specification', 'environment'))),
    path('mtats/', include(get_model_urls('service_specification', 'mtat', detail=False))),
    path('mtats/<int:pk>/', include(get_model_urls('service_specification', 'mtat'))),
    path('ci-functions/', include(get_model_urls('service_specification', 'cifunction', detail=False))),
    path('ci-functions/<int:pk>/', include(get_model_urls('service_specification', 'cifunction'))),
]
