from dcim.models import Device
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from netbox.ui.layout import SimpleLayout
from netbox.ui.panels import ObjectsTablePanel
from netbox.views import generic
from tenancy.filtersets import TenantFilterSet
from tenancy.forms import TenantFilterForm
from tenancy.models import Tenant
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


def _rollup_ids(queryset):
    """For use in an ObjectsTablePanel's `filters={'id': lambda ctx: ...}`.

    Passing an empty list as the 'id' filter value doesn't filter the
    rollup table to zero rows — it silently filters to *everything*.
    dict_to_querydict() (which builds the URL ObjectsTablePanel's table
    fetches) drops a key entirely when given an empty list, so the
    resulting URL carries no 'id' param at all, and the underlying list
    view falls back to its unfiltered default. Falling back to a sentinel
    PK that can never exist (0 — NetBox's auto-incrementing PKs start at 1)
    keeps a real, always-present 'id' param, so "nothing matches" reliably
    renders as an empty table instead of every object of that type.
    """
    ids = list(queryset.values_list('pk', flat=True))
    return ids or [0]


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
    rendered through ServiceSpecificationInfoPanel's accessor='service_info'.

    _get_info() persists an empty placeholder row (get_or_create) the first
    time it's called for a given parent, rather than handing back an unsaved
    in-memory instance: the panel reads business_unit/support_group/
    change_group, all ManyToManyFields, and Django refuses to query an M2M
    manager on an object with no primary key yet — a plain `info_model()`
    would 500 as soon as the panel tried to render. ci_function and
    lifecycle are nullable on ServiceSpecificationInfoBase specifically so
    this initial save (with nothing filled in) succeeds.
    """

    def _get_info(parent):
        obj, _created = info_model.objects.get_or_create(**{fk_name: parent})
        return obj

    @register_model_view(parent_model, 'service_specification', path='service-specification')
    class ServiceInfoView(generic.ObjectView):
        queryset = parent_model.objects.all()
        template_name = 'service_specification/service_info_tab.html'
        layout = SimpleLayout(
            left_panels=[panels.ServiceSpecificationInfoPanel(accessor='service_info')],
            bottom_panels=[
                # Read-only rollup: CI Function isn't set directly on this
                # side table any more (see models.py) — it's derived from
                # whichever AppService(s) `application_services` links to,
                # one hop further via each one's Service Offering -> Service.
                ObjectsTablePanel(
                    model='service_specification.cifunction',
                    title='CI Function (from Application Services)',
                    filters={
                        'id': lambda ctx: _rollup_ids(
                            CIFunction.objects.filter(
                                pk__in=_get_info(ctx['object']).application_services.values_list(
                                    'service_offering__service__ci_function', flat=True
                                )
                            )
                        )
                    },
                ),
            ],
        )
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
            # Read-only rollups of the parent Service(s)' own parameters,
            # and — one hop further — the CI Function(s) assigned to those
            # Services. Editing still happens on this same ServiceOffering
            # form via the `service` field; CI Function itself is only ever
            # set on Service, not here.
            ObjectsTablePanel(
                model='service_specification.service',
                title='Parent Services',
                filters={'id': lambda ctx: _rollup_ids(ctx['object'].service)},
            ),
            ObjectsTablePanel(
                model='service_specification.cifunction',
                title='CI Function (from Service)',
                filters={
                    'id': lambda ctx: _rollup_ids(
                        CIFunction.objects.filter(
                            pk__in=ctx['object']
                            .service.exclude(ci_function__isnull=True)
                            .values_list('ci_function', flat=True)
                        )
                    )
                },
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
            # Read-only rollups, one hop further than the (single)
            # `service_offering` field already shown in the overview panel
            # above: the Customer(s) and Service(s) behind that offering,
            # and — one hop further still — the CI Function(s) assigned to
            # those Services. Editing still happens via the
            # `service_offering` field on this same form — Customer is only
            # ever set on Service Offering, and CI Function only on
            # Service, not here.
            ObjectsTablePanel(
                model='tenancy.tenant',
                title='Customer (from Service Offering)',
                filters={'id': lambda ctx: _rollup_ids(ctx['object'].service_offering.tenant.all())},
            ),
            ObjectsTablePanel(
                model='tenancy.tenantgroup',
                title='Customer Group (from Service Offering)',
                filters={'id': lambda ctx: _rollup_ids(ctx['object'].service_offering.tenant_group.all())},
            ),
            ObjectsTablePanel(
                model='service_specification.service',
                title='Parent Services',
                filters={'id': lambda ctx: _rollup_ids(ctx['object'].service_offering.service.all())},
            ),
            ObjectsTablePanel(
                model='service_specification.cifunction',
                title='CI Function (from Service)',
                filters={
                    'id': lambda ctx: _rollup_ids(
                        CIFunction.objects.filter(
                            pk__in=ctx['object']
                            .service_offering.service.exclude(ci_function__isnull=True)
                            .values_list('ci_function', flat=True)
                        )
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
    layout=SimpleLayout(
        left_panels=[panels.LookupPanel()],
        bottom_panels=[
            # Read-only rollups of everything assigned this CI Function.
            # Service links to it directly (a plain FK). Devices/VMs/
            # Clusters/ClusterGroups have no direct CI Function of their
            # own any more — it's derived from whichever AppService(s)
            # their own ServiceSpecificationInfo side table (see models.py
            # — plugins can't add real fields to those core models) links
            # to, so those four traverse: reverse OneToOne accessor ->
            # application_services (M2M) -> service_offering ->
            # service (M2M) -> ci_function. .distinct() guards against
            # duplicate rows from that multi-hop M2M traversal.
            ObjectsTablePanel(
                model='service_specification.service',
                title='Services',
                filters={'id': lambda ctx: _rollup_ids(Service.objects.filter(ci_function=ctx['object']))},
            ),
            ObjectsTablePanel(
                model='dcim.device',
                title='Devices',
                filters={
                    'id': lambda ctx: _rollup_ids(
                        Device.objects.filter(
                            service_specification_info__application_services__service_offering__service__ci_function=ctx[
                                'object'
                            ]
                        ).distinct()
                    )
                },
            ),
            ObjectsTablePanel(
                model='virtualization.virtualmachine',
                title='Virtual Machines',
                filters={
                    'id': lambda ctx: _rollup_ids(
                        VirtualMachine.objects.filter(
                            service_specification_info__application_services__service_offering__service__ci_function=ctx[
                                'object'
                            ]
                        ).distinct()
                    )
                },
            ),
            ObjectsTablePanel(
                model='virtualization.cluster',
                title='Clusters',
                filters={
                    'id': lambda ctx: _rollup_ids(
                        Cluster.objects.filter(
                            service_specification_info__application_services__service_offering__service__ci_function=ctx[
                                'object'
                            ]
                        ).distinct()
                    )
                },
            ),
            ObjectsTablePanel(
                model='virtualization.clustergroup',
                title='Cluster Groups',
                filters={
                    'id': lambda ctx: _rollup_ids(
                        ClusterGroup.objects.filter(
                            service_specification_info__application_services__service_offering__service__ci_function=ctx[
                                'object'
                            ]
                        ).distinct()
                    )
                },
            ),
            panels.CommentsPanel(),
        ],
    ),
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


#
# Reports — neither of these is registered via register_model_view: Tenant
# is a core NetBox model already fully registered by NetBox itself
# (reusing that same registry here would collide with NetBox's own Tenant
# views), and the tree isn't tied to any single model's CRUD lifecycle at
# all. Both are wired directly to plain paths in urls.py instead.
#


class TenantReportView(generic.ObjectListView):
    """Read-only rollup of every Tenant, reached from the plugin's own
    'Reports' menu (see navigation.py).
    """

    queryset = Tenant.objects.select_related('group').prefetch_related('sites', 'tags')
    filterset = TenantFilterSet
    filterset_form = TenantFilterForm
    table = tables.TenantReportTable
    actions = ()


class OfferingsTreeView(TemplateView):
    """Read-only Portfolio -> Service -> Service Offering -> Application
    Service -> Technical CI tree, reached from the plugin's own 'Reports'
    menu (see navigation.py).
    """

    template_name = 'service_specification/offerings_tree.html'

    def get(self, request, *args, **kwargs):
        form = forms.OfferingsTreeFilterForm(request.GET or None)
        filters = form.cleaned_data if form.is_valid() else {}
        return self.render_to_response({'filter_form': form, 'portfolios': self._build_tree(filters)})

    @staticmethod
    def _filter_offerings_by_tenant(queryset, tenant):
        if not tenant:
            return queryset
        # Q(tenant_group=None) would match every offering with *no* group
        # set (Django translates field=None to __isnull=True), not just
        # ones tied to this specific ungrouped tenant — so the
        # tenant_group half only gets added when there's a group to match.
        offering_filter = Q(tenant=tenant)
        if tenant.group_id:
            offering_filter |= Q(tenant_group=tenant.group_id)
        return queryset.filter(offering_filter)

    @staticmethod
    def _technical_cis_for(app_service, device, virtual_machine, cluster, cluster_group):
        # If any Technical CI filter is set, only that type/instance is
        # shown for this AppService — the other three types are omitted
        # entirely rather than shown unfiltered alongside it.
        # (type label, mdi icon class) per Technical CI kind, for the tree
        # template's org-chart node styling.
        ci_filter_active = any((device, virtual_machine, cluster, cluster_group))
        cis = []
        if not ci_filter_active or device:
            qs = Device.objects.filter(service_specification_info__application_services=app_service)
            cis += [(obj, 'Device', 'mdi-server') for obj in (qs.filter(pk=device.pk) if device else qs)]
        if not ci_filter_active or virtual_machine:
            qs = VirtualMachine.objects.filter(service_specification_info__application_services=app_service)
            cis += [
                (obj, 'Virtual Machine', 'mdi-monitor')
                for obj in (qs.filter(pk=virtual_machine.pk) if virtual_machine else qs)
            ]
        if not ci_filter_active or cluster:
            qs = Cluster.objects.filter(service_specification_info__application_services=app_service)
            cis += [
                (obj, 'Cluster', 'mdi-hexagon-multiple-outline')
                for obj in (qs.filter(pk=cluster.pk) if cluster else qs)
            ]
        if not ci_filter_active or cluster_group:
            qs = ClusterGroup.objects.filter(service_specification_info__application_services=app_service)
            cis += [
                (obj, 'Cluster Group', 'mdi-hexagon-multiple')
                for obj in (qs.filter(pk=cluster_group.pk) if cluster_group else qs)
            ]
        return cis

    def _build_tree(self, filters):
        portfolio = filters.get('portfolio')
        service = filters.get('service')
        service_offering = filters.get('service_offering')
        app_service = filters.get('app_service')
        tenant = filters.get('tenant')
        device = filters.get('device')
        virtual_machine = filters.get('virtual_machine')
        cluster = filters.get('cluster')
        cluster_group = filters.get('cluster_group')
        ci_filter_active = any((device, virtual_machine, cluster, cluster_group))

        portfolios_qs = Portfolio.objects.all()
        if portfolio:
            portfolios_qs = portfolios_qs.filter(pk=portfolio.pk)

        tree = []
        for portfolio_obj in portfolios_qs:
            services_qs = portfolio_obj.services.all()
            if service:
                services_qs = services_qs.filter(pk=service.pk)

            service_nodes = []
            for service_obj in services_qs:
                offerings_qs = service_obj.service_offerings.all()
                if service_offering:
                    offerings_qs = offerings_qs.filter(pk=service_offering.pk)
                offerings_qs = self._filter_offerings_by_tenant(offerings_qs, tenant)

                offering_nodes = []
                for offering_obj in offerings_qs:
                    # Reverse OneToOneField accessor: raises <Model>.DoesNotExist
                    # when unset, but Django deliberately makes that exception
                    # also an AttributeError so getattr()'s default kicks in.
                    linked_app_service = getattr(offering_obj, 'app_service', None)
                    if app_service and (linked_app_service is None or linked_app_service.pk != app_service.pk):
                        continue

                    if linked_app_service is None:
                        if ci_filter_active:
                            continue
                        offering_nodes.append((offering_obj, None, []))
                        continue

                    technical_cis = self._technical_cis_for(
                        linked_app_service, device, virtual_machine, cluster, cluster_group
                    )
                    if ci_filter_active and not technical_cis:
                        continue
                    offering_nodes.append((offering_obj, linked_app_service, technical_cis))

                if offering_nodes:
                    service_nodes.append((service_obj, offering_nodes))

            if service_nodes:
                tree.append((portfolio_obj, service_nodes))

        return tree
