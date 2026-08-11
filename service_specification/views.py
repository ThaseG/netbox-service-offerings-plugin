import json
from dataclasses import dataclass

from dcim.models import Device
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from netbox.ui.layout import SimpleLayout
from netbox.ui.panels import ObjectsTablePanel
from netbox.views import generic
from tenancy.models import Tenant, TenantGroup
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
    VirtualMachineServiceInfo,
)
from .utils import tenant_offering_filter


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


ContractListView, ContractView, ContractEditView, ContractDeleteView = _make_views(
    Contract,
    filtersets.ContractFilterSet,
    forms.ContractFilterForm,
    tables.ContractTable,
    forms.ContractForm,
    layout=SimpleLayout(
        left_panels=[panels.ContractPanel(), panels.ContractContactsPanel()],
        right_panels=[panels.ContractCustomerPanel()],
        bottom_panels=[
            ObjectsTablePanel(
                model='service_specification.contractratecard',
                title='Contract Rate Cards',
                filters={'id': lambda ctx: _rollup_ids(ctx['object'].rate_cards.all())},
            ),
            panels.CommentsPanel(),
        ],
    ),
)
ContractRateCardListView, ContractRateCardView, ContractRateCardEditView, ContractRateCardDeleteView = _make_views(
    ContractRateCard,
    filtersets.ContractRateCardFilterSet,
    forms.ContractRateCardFilterForm,
    tables.ContractRateCardTable,
    forms.ContractRateCardForm,
    layout=SimpleLayout(
        left_panels=[panels.ContractRateCardPanel()],
        right_panels=[panels.ContractRateCardCostsPanel()],
        bottom_panels=[
            # Customer/Customer Group aren't set on the Rate Card itself
            # (removed — see models.py) — they live on the parent Contract
            # and are shown here read-only, one hop further, the same
            # pattern as AppService's "Customer (from Service Offering)"
            # rollups below.
            ObjectsTablePanel(
                model='tenancy.tenant',
                title='Customer (from Contract)',
                filters={'id': lambda ctx: _rollup_ids(Tenant.objects.filter(pk=ctx['object'].contract.tenant_id))},
            ),
            ObjectsTablePanel(
                model='tenancy.tenantgroup',
                title='Customer Group (from Contract)',
                filters={
                    'id': lambda ctx: _rollup_ids(TenantGroup.objects.filter(pk=ctx['object'].contract.tenant_group_id))
                },
            ),
            panels.CommentsPanel(),
        ],
    ),
)
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


@dataclass
class _TenantOfferingRow:
    """One row of TenantReportView's table: a Tenant paired with one of its
    related Service Offerings (or None, if it has none — the tenant still
    gets a row rather than being dropped from the report)."""

    tenant: Tenant
    service_offering: ServiceOffering | None = None

    @property
    def application_service(self):
        # A ServiceOffering backs at most one AppService (OneToOneField —
        # see models.py). Reverse accessor raises <Model>.DoesNotExist when
        # unset, but Django deliberately makes that exception also an
        # AttributeError so getattr()'s default kicks in.
        if self.service_offering is None:
            return None
        return getattr(self.service_offering, 'app_service', None)


class TenantReportView(generic.ObjectListView):
    """Read-only rollup of every Tenant, reached from the plugin's own
    'Reports' menu (see navigation.py). One table row per (Tenant, Service
    Offering) pair: get_table() expands each filtered Tenant into its
    related offerings (see utils.tenant_offering_filter) before handing
    rows to TenantReportTable.
    """

    queryset = Tenant.objects.select_related('group').prefetch_related('sites', 'tags')
    filterset = filtersets.TenantReportFilterSet
    filterset_form = forms.TenantReportFilterForm
    table = tables.TenantReportTable
    actions = ()

    def get_table(self, data, request, bulk_actions=True):
        # filterset (applied earlier, in ObjectListView.get()) already
        # narrowed `data` down to Tenants with at least one matching
        # Offering — re-running the same form here additionally narrows
        # *which* of each qualifying Tenant's Offerings become rows, so a
        # Tenant that only qualifies because of one Offering doesn't also
        # drag in all its unrelated ones. Cheap: form validation has no
        # side effects, and this is only run once per request.
        form = forms.TenantReportFilterForm(request.GET)
        filters = form.cleaned_data if form.is_valid() else {}
        return super().get_table(self._expand_rows(data, filters), request, bulk_actions)

    @staticmethod
    def _expand_rows(tenants, filters=None):
        filters = filters or {}
        lifecycles = filters.get('service_offering_lifecycle_id')
        contracts = filters.get('contract_id')
        service_offerings = filters.get('service_offering_id')
        app_services = filters.get('application_service_id')

        rows = []
        for tenant in tenants:
            offerings_qs = ServiceOffering.objects.filter(tenant_offering_filter(tenant)).distinct()
            if lifecycles:
                offerings_qs = offerings_qs.filter(lifecycle__in=lifecycles)
            if contracts:
                offerings_qs = offerings_qs.filter(contract__in=contracts)
            if service_offerings:
                offerings_qs = offerings_qs.filter(pk__in=[o.pk for o in service_offerings])
            if app_services:
                offerings_qs = offerings_qs.filter(app_service__in=app_services)
            offerings = list(offerings_qs.select_related('lifecycle', 'app_service', 'contract'))

            if offerings:
                rows.extend(_TenantOfferingRow(tenant=tenant, service_offering=offering) for offering in offerings)
            else:
                rows.append(_TenantOfferingRow(tenant=tenant))
        return rows


class OfferingsTreeView(TemplateView):
    """Read-only Portfolio -> Service -> Service Offering -> Application
    Service -> Technical CI graph, reached from the plugin's own 'Reports'
    menu (see navigation.py). Rendered client-side as a vis-network
    node-link diagram (see the template) rather than a DOM tree — that's
    the actual scalability fix over the previous CSS org-chart, so the
    heavy lifting here is just producing vis-network's nodes/edges JSON
    shape; the underlying tree traversal/filtering/pruning in _build_tree()
    is unchanged from before.
    """

    template_name = 'service_specification/offerings_tree.html'

    def get(self, request, *args, **kwargs):
        form = forms.OfferingsTreeFilterForm(request.GET or None)
        filters = form.cleaned_data if form.is_valid() else {}
        nodes, edges = self._flatten_to_graph(self._build_tree(filters))
        return self.render_to_response(
            {
                'filter_form': form,
                'has_results': bool(nodes),
                'nodes_json': json.dumps(nodes),
                'edges_json': json.dumps(edges),
            }
        )

    @staticmethod
    def _flatten_to_graph(tree):
        """Walk _build_tree()'s nested (portfolio, [(service, [(offering,
        app_service_or_None, [(ci, type_label, icon_class), ...]), ...]),
        ...]) structure into vis-network's flat nodes/edges lists, laying
        every node out ourselves (explicit pixel x/y, with y pinned via
        `fixed: {x: False, y: True}` — x is left free so users can still
        drag nodes sideways) rather than leaving positioning to
        vis-network's own hierarchical layout engine.

        That engine turned out not to be trustworthy here: giving every
        node an explicit `level` (needed so every node of a type lands on
        the same row) apparently short-circuits whatever internal pass
        vis-network normally uses to spread siblings out horizontally, so
        nodes were rendering stacked directly on top of each other rather
        than merely "too close". Computing positions ourselves sidesteps
        that entirely: `y` is just `level * LEVEL_HEIGHT`, and `x` is a
        classic bottom-up tree layout — lay out the leaves (Technical CIs)
        left to right with a fixed gap, then center each parent over the
        span of its own children, all the way up to Portfolio.

        Dedup by id is required, not optional: Service.service_portfolio
        and ServiceOffering.service are both ManyToMany, so a Service (and
        everything under it) can legally appear under more than one
        Portfolio branch of the same tree, and similarly an Offering under
        more than one Service. A shared node's position is computed once,
        the first time it's reached, and reused for every other parent
        that also points to it — vis.DataSet.add() would raise on a
        duplicate id if it were re-added, and repositioning it a second
        time makes no sense anyway since it's the same object on screen.
        """
        LEVEL_HEIGHT = 120
        NODE_GAP = 60
        LEVELS = {'portfolio': 0, 'service': 1, 'offering': 2, 'appservice': 3, 'technicalci': 4}

        nodes = []
        edges = []
        seen_edges = set()
        positions = {}  # node_id -> x (already-placed nodes, shared or not)
        occupied_x = {}  # group -> set of x already claimed by that row
        next_x = 0.0

        def estimate_width(name, type_label, extra_line):
            # Rough per-character pixel-width estimates for vis-network's
            # default arial rendering at our configured font sizes (14px
            # bold for the name line, 11px for the type/Customer lines) —
            # there's no way to measure real rendered text width from the
            # server, so this only needs to be generous enough that same
            # -row siblings don't visually overlap, not pixel-perfect.
            lines = [len(name) * 8.0]
            if type_label:
                lines.append(len(type_label) * 6.5)
            if extra_line:
                lines.append(len(extra_line) * 6.5)
            return max(120.0, max(lines)) + 24

        def place(node_id, name, group, obj, x, type_label=None, extra_line=None):
            # Two-line on-node label: object type on top, name below, plus
            # an optional third line (currently just Service Offering's
            # Customer). <code>/<b>/<i> are vis-network's own
            # font.multi='html' markup (see the template's
            # font.mono/font.bold/font.ital config, which style the three
            # lines differently) — rendered onto a <canvas>, not inserted
            # as real DOM/innerHTML, so there's no injection risk from an
            # object name containing '<' etc., only a cosmetic one.
            label = f'<code>{type_label}</code>\n<b>{name}</b>' if type_label else name
            if extra_line:
                label += f'\n<i>{extra_line}</i>'
            title = f'{type_label}: {name}' if type_label else name
            if extra_line:
                title += f' ({extra_line})'
            nodes.append(
                {
                    'id': node_id,
                    'label': label,
                    'group': group,
                    'url': obj.get_absolute_url(),
                    'title': title,
                    'x': x,
                    'y': LEVELS[group] * LEVEL_HEIGHT,
                    # y stays pinned — that's what keeps every node of a
                    # type on the same row — but x is left free so users
                    # can drag nodes sideways (vis-network's `fixed` blocks
                    # manual dragging on whichever axes it covers, not just
                    # physics, so this has to be per-axis rather than a
                    # blanket `fixed: True`).
                    'fixed': {'x': False, 'y': True},
                }
            )

        def add_edge(from_id, to_id):
            key = (from_id, to_id)
            if key not in seen_edges:
                seen_edges.add(key)
                edges.append({'from': from_id, 'to': to_id})

        def claim_x(group, x, name, type_label, extra_line):
            # A parent's x is normally the midpoint of its own children's
            # span — but two *different* parents on the same row (e.g. two
            # Application Services) can legitimately share the exact same
            # set of children (e.g. both of a tenant's Application Services
            # are assigned the same pool of Technical CIs — see
            # ci/scripts/generate_test_deployment_data.py's
            # build_ci_assignments), which makes their computed midpoints
            # identical too. Invisible in the full, ~40-offering tree (one
            # coincidental overlap lost among many spread-out siblings), but
            # glaring once a tenant filter narrows the tree down to just
            # that one pair — everything from Application Service upward
            # collapses onto a single x. Detect same-row collisions and
            # give the second (and any further) node its own fresh slot
            # instead of silently overlapping.
            claimed = occupied_x.setdefault(group, set())
            if x in claimed:
                x = take_slot(name, type_label, extra_line)
            claimed.add(x)
            return x

        def take_slot(name, type_label, extra_line):
            # Claim the next free horizontal slot for a node with no
            # children to center over (a true Technical CI leaf, or a
            # higher-level node whose own branch is otherwise empty — e.g.
            # a Service Offering with no Application Service attached
            # yet). One shared counter across every level: since only
            # same-row (same `level`, hence same y) placements can ever
            # visually collide, and this counter only ever increases,
            # nothing that gets its own slot this way can collide with
            # anything else that did too, regardless of which level either
            # one belongs to.
            nonlocal next_x
            width = estimate_width(name, type_label, extra_line)
            x = next_x + width / 2
            next_x += width + NODE_GAP
            return x

        def layout_ci(ci, type_label):
            ci_id = f'{ci.__class__.__name__.lower()}-{ci.pk}'
            if ci_id not in positions:
                x = take_slot(ci.name, type_label, None)
                positions[ci_id] = x
                place(ci_id, ci.name, 'technicalci', ci, x, type_label)
            return ci_id

        def layout_offering(offering, app_service, technical_cis):
            offering_id = f'offering-{offering.pk}'
            if offering_id in positions:
                return offering_id

            # Third label line: Customer. Falls back to Customer Group
            # name(s) when no Tenant is set directly (an offering can be
            # scoped to a whole Tenant Group instead — see
            # utils.tenant_offering_filter), and to nothing at all if
            # neither is set.
            tenant_names = ', '.join(t.name for t in offering.tenant.all())
            if not tenant_names:
                tenant_names = ', '.join(g.name for g in offering.tenant_group.all())
            tenant_names = tenant_names or None

            if app_service is None:
                x = take_slot(offering.name, 'Service Offering', tenant_names)
            else:
                app_service_id = f'appservice-{app_service.pk}'
                if app_service_id in positions:
                    x = positions[app_service_id]
                else:
                    if technical_cis:
                        ci_ids = [layout_ci(ci, type_label) for ci, type_label, _icon_class in technical_cis]
                        for ci_id in ci_ids:
                            add_edge(app_service_id, ci_id)
                        ci_xs = [positions[ci_id] for ci_id in ci_ids]
                        app_x = (min(ci_xs) + max(ci_xs)) / 2
                        app_x = claim_x('appservice', app_x, app_service.name, 'Application Service', None)
                    else:
                        app_x = take_slot(app_service.name, 'Application Service', None)
                    positions[app_service_id] = app_x
                    place(app_service_id, app_service.name, 'appservice', app_service, app_x, 'Application Service')
                x = positions[app_service_id]
                add_edge(offering_id, app_service_id)

            positions[offering_id] = x
            place(offering_id, offering.name, 'offering', offering, x, 'Service Offering', tenant_names)
            return offering_id

        def layout_service(service, offerings):
            service_id = f'service-{service.pk}'
            if service_id in positions:
                return service_id

            if offerings:
                offering_ids = [layout_offering(o, a, c) for o, a, c in offerings]
                for offering_id in offering_ids:
                    add_edge(service_id, offering_id)
                offering_xs = [positions[offering_id] for offering_id in offering_ids]
                x = (min(offering_xs) + max(offering_xs)) / 2
                x = claim_x('service', x, service.name, 'Service', None)
            else:
                x = take_slot(service.name, 'Service', None)

            positions[service_id] = x
            place(service_id, service.name, 'service', service, x, 'Service')
            return service_id

        def layout_portfolio(portfolio, services):
            portfolio_id = f'portfolio-{portfolio.pk}'
            if portfolio_id in positions:
                return portfolio_id

            if services:
                service_ids = [layout_service(s, o) for s, o in services]
                for service_id in service_ids:
                    add_edge(portfolio_id, service_id)
                service_xs = [positions[service_id] for service_id in service_ids]
                x = (min(service_xs) + max(service_xs)) / 2
                x = claim_x('portfolio', x, portfolio.name, 'Portfolio', None)
            else:
                x = take_slot(portfolio.name, 'Portfolio', None)

            positions[portfolio_id] = x
            place(portfolio_id, portfolio.name, 'portfolio', portfolio, x, 'Portfolio')
            return portfolio_id

        for portfolio, services in tree:
            layout_portfolio(portfolio, services)

        return nodes, edges

    @staticmethod
    def _filter_offerings_by_tenant(queryset, tenant):
        if not tenant:
            return queryset
        return queryset.filter(tenant_offering_filter(tenant))

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
                offerings_qs = service_obj.service_offerings.all().prefetch_related('tenant', 'tenant_group')
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
