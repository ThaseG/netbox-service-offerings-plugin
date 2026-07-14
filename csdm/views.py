from netbox.ui.layout import SimpleLayout
from netbox.views import generic
from utilities.views import register_model_view

from . import filtersets, forms, panels, tables
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


def _make_views(model, filterset_cls, filterset_form_cls, table_cls, form_cls, layout):
    """Builds the standard list/detail/edit/delete view set for a model,
    registering each with utilities.views.register_model_view so
    get_model_urls() can assemble the URL patterns in urls.py."""
    # Class bodies resolve names against their own (incrementally-built)
    # namespace before falling back to the enclosing scope, so a class-body
    # assignment that reuses the parameter's name (`layout = layout`) raises
    # NameError instead of reading the parameter. Bind it under a different
    # name first so the class body can see it via the closure.
    detail_layout = layout

    @register_model_view(model, 'list', path='', detail=False)
    class ListView(generic.ObjectListView):
        queryset = model.objects.all()
        filterset = filterset_cls
        filterset_form = filterset_form_cls
        table = table_cls

    @register_model_view(model)
    class DetailView(generic.ObjectView):
        queryset = model.objects.all()
        layout = detail_layout

    @register_model_view(model, 'add', detail=False)
    @register_model_view(model, 'edit')
    class EditView(generic.ObjectEditView):
        queryset = model.objects.all()
        form = form_cls

    @register_model_view(model, 'delete')
    class DeleteView(generic.ObjectDeleteView):
        queryset = model.objects.all()

    # Views are defined dynamically per model above, so every one is
    # literally named "ListView"/"DetailView"/etc. by default. Rename them
    # per model so tracebacks and Django's debug toolbar point at something
    # useful (e.g. "PortfolioListView") instead of 12 indistinguishable
    # "ListView" entries.
    for view_cls, suffix in (
        (ListView, 'ListView'),
        (DetailView, 'View'),
        (EditView, 'EditView'),
        (DeleteView, 'DeleteView'),
    ):
        view_cls.__name__ = view_cls.__qualname__ = f'{model.__name__}{suffix}'

    return ListView, DetailView, EditView, DeleteView


def _lookup_layout(panel_cls=panels.LookupPanel):
    return SimpleLayout(left_panels=[panel_cls()], bottom_panels=[panels.CommentsPanel()])


PortfolioListView, PortfolioView, PortfolioEditView, PortfolioDeleteView = _make_views(
    Portfolio,
    filtersets.PortfolioFilterSet,
    forms.PortfolioFilterForm,
    tables.PortfolioTable,
    forms.PortfolioForm,
    layout=SimpleLayout(
        left_panels=[panels.PortfolioPanel()],
        right_panels=[panels.PortfolioOwnershipPanel()],
        bottom_panels=[panels.CommentsPanel()],
    ),
)
ServiceListView, ServiceView, ServiceEditView, ServiceDeleteView = _make_views(
    Service,
    filtersets.ServiceFilterSet,
    forms.ServiceFilterForm,
    tables.ServiceTable,
    forms.ServiceForm,
    layout=SimpleLayout(
        left_panels=[panels.ServicePanel(), panels.ServiceOwnershipPanel()],
        right_panels=[panels.ServiceOrganizationPanel()],
        bottom_panels=[panels.CommentsPanel()],
    ),
)
ServiceOfferingListView, ServiceOfferingView, ServiceOfferingEditView, ServiceOfferingDeleteView = _make_views(
    ServiceOffering,
    filtersets.ServiceOfferingFilterSet,
    forms.ServiceOfferingFilterForm,
    tables.ServiceOfferingTable,
    forms.ServiceOfferingForm,
    layout=SimpleLayout(
        left_panels=[panels.ServiceOfferingPanel(), panels.ServiceOfferingOwnershipPanel()],
        right_panels=[panels.ServiceOfferingOrganizationPanel(), panels.ServiceOfferingCustomerPanel()],
        bottom_panels=[panels.CommentsPanel()],
    ),
)
AppServiceListView, AppServiceView, AppServiceEditView, AppServiceDeleteView = _make_views(
    AppService,
    filtersets.AppServiceFilterSet,
    forms.AppServiceFilterForm,
    tables.AppServiceTable,
    forms.AppServiceForm,
    layout=SimpleLayout(
        left_panels=[panels.AppServiceOverviewPanel(), panels.AppServiceRecoveryPanel()],
        right_panels=[panels.AppServiceLevelsPanel(), panels.AppServiceOrganizationPanel()],
        bottom_panels=[panels.AppServiceCustomerPanel(), panels.CommentsPanel()],
    ),
)
TechCIListView, TechCIView, TechCIEditView, TechCIDeleteView = _make_views(
    TechCI,
    filtersets.TechCIFilterSet,
    forms.TechCIFilterForm,
    tables.TechCITable,
    forms.TechCIForm,
    layout=SimpleLayout(
        left_panels=[panels.TechCIPanel(), panels.TechCIOrganizationPanel()],
        right_panels=[panels.TechCIInfrastructurePanel(), panels.TechCICustomerPanel()],
        bottom_panels=[panels.CommentsPanel()],
    ),
)
LifecycleListView, LifecycleView, LifecycleEditView, LifecycleDeleteView = _make_views(
    Lifecycle,
    filtersets.LifecycleFilterSet,
    forms.LifecycleFilterForm,
    tables.LifecycleTable,
    forms.LifecycleForm,
    layout=_lookup_layout(),
)
SLAListView, SLAView, SLAEditView, SLADeleteView = _make_views(
    SLA,
    filtersets.SLAFilterSet,
    forms.SLAFilterForm,
    tables.SLATable,
    forms.SLAForm,
    layout=_lookup_layout(panels.SLAPanel),
)
OperationTimeListView, OperationTimeView, OperationTimeEditView, OperationTimeDeleteView = _make_views(
    OperationTime,
    filtersets.OperationTimeFilterSet,
    forms.OperationTimeFilterForm,
    tables.OperationTimeTable,
    forms.OperationTimeForm,
    layout=_lookup_layout(),
)
AvailabilityListView, AvailabilityView, AvailabilityEditView, AvailabilityDeleteView = _make_views(
    Availability,
    filtersets.AvailabilityFilterSet,
    forms.AvailabilityFilterForm,
    tables.AvailabilityTable,
    forms.AvailabilityForm,
    layout=_lookup_layout(),
)
CriticalityListView, CriticalityView, CriticalityEditView, CriticalityDeleteView = _make_views(
    Criticality,
    filtersets.CriticalityFilterSet,
    forms.CriticalityFilterForm,
    tables.CriticalityTable,
    forms.CriticalityForm,
    layout=_lookup_layout(),
)
EnvironmentListView, EnvironmentView, EnvironmentEditView, EnvironmentDeleteView = _make_views(
    Environment,
    filtersets.EnvironmentFilterSet,
    forms.EnvironmentFilterForm,
    tables.EnvironmentTable,
    forms.EnvironmentForm,
    layout=_lookup_layout(),
)
MTATListView, MTATView, MTATEditView, MTATDeleteView = _make_views(
    MTAT,
    filtersets.MTATFilterSet,
    forms.MTATFilterForm,
    tables.MTATTable,
    forms.MTATForm,
    layout=_lookup_layout(panels.MTATPanel),
)
