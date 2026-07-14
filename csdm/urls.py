from django.urls import include, path

from utilities.urls import get_model_urls

app_name = 'csdm'

# Importing views ensures every @register_model_view() decorator below has
# run (populating the registry get_model_urls() reads from) before this
# module builds urlpatterns.
from . import views  # noqa: E402,F401

urlpatterns = [
    path('portfolios/', include(get_model_urls('csdm', 'portfolio', detail=False))),
    path('portfolios/<int:pk>/', include(get_model_urls('csdm', 'portfolio'))),

    path('services/', include(get_model_urls('csdm', 'service', detail=False))),
    path('services/<int:pk>/', include(get_model_urls('csdm', 'service'))),

    path('service-offerings/', include(get_model_urls('csdm', 'serviceoffering', detail=False))),
    path('service-offerings/<int:pk>/', include(get_model_urls('csdm', 'serviceoffering'))),

    path('app-services/', include(get_model_urls('csdm', 'appservice', detail=False))),
    path('app-services/<int:pk>/', include(get_model_urls('csdm', 'appservice'))),

    path('tech-cis/', include(get_model_urls('csdm', 'techci', detail=False))),
    path('tech-cis/<int:pk>/', include(get_model_urls('csdm', 'techci'))),

    path('lifecycles/', include(get_model_urls('csdm', 'lifecycle', detail=False))),
    path('lifecycles/<int:pk>/', include(get_model_urls('csdm', 'lifecycle'))),

    path('slas/', include(get_model_urls('csdm', 'sla', detail=False))),
    path('slas/<int:pk>/', include(get_model_urls('csdm', 'sla'))),

    path('operation-times/', include(get_model_urls('csdm', 'operationtime', detail=False))),
    path('operation-times/<int:pk>/', include(get_model_urls('csdm', 'operationtime'))),

    path('availabilities/', include(get_model_urls('csdm', 'availability', detail=False))),
    path('availabilities/<int:pk>/', include(get_model_urls('csdm', 'availability'))),

    path('criticalities/', include(get_model_urls('csdm', 'criticality', detail=False))),
    path('criticalities/<int:pk>/', include(get_model_urls('csdm', 'criticality'))),

    path('environments/', include(get_model_urls('csdm', 'environment', detail=False))),
    path('environments/<int:pk>/', include(get_model_urls('csdm', 'environment'))),

    path('mtats/', include(get_model_urls('csdm', 'mtat', detail=False))),
    path('mtats/<int:pk>/', include(get_model_urls('csdm', 'mtat'))),
]
