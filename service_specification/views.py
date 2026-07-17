from dcim.models import Device
from django.shortcuts import get_object_or_404
from netbox.ui.layout import SimpleLayout
from netbox.ui.panels import ObjectsTablePanel
from netbox.views import generic
from utilities.views import ViewTab, register_model_view
from virtualization.models import Cluster, ClusterGroup, VirtualMachine

from . import filtersets, forms, panels, tables
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


def _make_service_info_views(parent_model, info_model, form_cls, fk_name):
    """Registers a read-only 'Service Specification' tab plus a matching
    edit view directly on `parent_model`'s own detail page (Device,
    VirtualMachine, Cluster or ClusterGroup — all core NetBox models).

    Plugins can't add real database fields to NetBox's own models, so
    `info_model` (see models.py's ServiceSpecificationInfoBase) is a
    separate table in a OneToOne relationship with `parent_model`.

    The read-only tab's `queryset` is deliberately `parent_model`, not
    `info_model`: NetBox derives the page's breadcrumbs, title and — via
    `{% model_view_tabs %}` in generic/object.html — the tab bar itself
    from `context['object']`, which has to be the Device/VM/Cluster/
    ClusterGroup being viewed for this to render as a tab on *its* page
    rather than as a standalone info_model detail page. The actual
    service-info data is supplied separately via get_extra_context() and
    rendered through ServiceSpecificationInfoPanel's accessor='service_info',
    falling back to an unsaved in-memory info_model instance when no row
    exists yet — so the tab always renders something sensible instead of
    404ing on first visit, and no row is persisted until the user actually
    saves the edit form.
    """

    def _get_info(parent):
        return info_model.objects.filter(**{fk_name: parent}).first() or info_model(**{fk_name: parent})

    @register_model_view(parent_model, 'service_specification', path='service-specification')
    class ServiceInfoView(generic.ObjectView):
        queryset = parent_model.objects.all()
        template_name = 'service_specification/service_info_tab.html'
        layout = SimpleLayout(left_panels=[panels.ServiceSpecificationInfoPanel(accessor='service_info')])
        tab = ViewTab(
            label='Service Specification',
            permission=f'service_specification.view_{info_model._meta.model_name}',
        )
        actions = ()

        def get_extra_context(self, request, instance):
            return {'service_info': _get_info(instance)}

    @register_model_view(parent_model, 'service_specification_edit', path='service-specification/edit')
    class ServiceInfoEditView(generic.ObjectEditView):
        queryset = info_model.objects.all()
        form = form_cls

        def get_object(self, **kwargs):
            parent = get_object_or_404(parent_model.objects.all(), pk=kwargs['pk'])
            return _get_info(parent)

    ServiceInfoView.__name__ = ServiceInfoView.__qualname__ = f'{parent_model.__name__}ServiceSpecificationView'
    ServiceInfoEditView.__name__ = ServiceInfoEditView.__qualname__ = (
        f'{parent_model.__name__}ServiceSpecificationEditView'
    )

    return ServiceInfoView, ServiceInfoEditView


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
        bottom_panels=[
            # Read-only rollup of the parent Service(s)' own parameters —
            # editing the relationship still happens on this same
            # ServiceOffering form via the `service` field; this just saves
            # a click to see what's on the other end of it.
            ObjectsTablePanel(
                model='service_specification.service',
                title='Parent Services',
                filters={'id': lambda ctx: list(ctx['object'].service.values_list('pk', flat=True))},
            ),
            panels.CommentsPanel(),
        ],
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
        bottom_panels=[
            panels.AppServiceCustomerPanel(),
            # Read-only rollups: the Service Offering(s) this app service
            # realizes, and — one hop further — the Service(s) behind those
            # offerings. Editing still happens via the `service_offering`
            # field on this same form.
            ObjectsTablePanel(
                model='service_specification.serviceoffering',
                title='Service Offerings',
                filters={'id': lambda ctx: list(ctx['object'].service_offering.values_list('pk', flat=True))},
            ),
            ObjectsTablePanel(
                model='service_specification.service',
                title='Parent Services',
                filters={
                    'id': lambda ctx: list(
                        Service.objects.filter(service_offerings__in=ctx['object'].service_offering.all())
                        .values_list('pk', flat=True)
                        .distinct()
                    )
                },
            ),
            panels.CommentsPanel(),
        ],
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
CIFunctionListView, CIFunctionView, CIFunctionEditView, CIFunctionDeleteView = _make_views(
    CIFunction,
    filtersets.CIFunctionFilterSet,
    forms.CIFunctionFilterForm,
    tables.CIFunctionTable,
    forms.CIFunctionForm,
    layout=_lookup_layout(),
)

DeviceServiceSpecificationView, DeviceServiceSpecificationEditView = _make_service_info_views(
    Device, DeviceServiceInfo, forms.DeviceServiceInfoForm, 'device'
)
VirtualMachineServiceSpecificationView, VirtualMachineServiceSpecificationEditView = _make_service_info_views(
    VirtualMachine, VirtualMachineServiceInfo, forms.VirtualMachineServiceInfoForm, 'virtual_machine'
)
ClusterServiceSpecificationView, ClusterServiceSpecificationEditView = _make_service_info_views(
    Cluster, ClusterServiceInfo, forms.ClusterServiceInfoForm, 'cluster'
)
ClusterGroupServiceSpecificationView, ClusterGroupServiceSpecificationEditView = _make_service_info_views(
    ClusterGroup, ClusterGroupServiceInfo, forms.ClusterGroupServiceInfoForm, 'cluster_group'
)
