from django.utils.translation import gettext_lazy as _
from netbox.ui import attrs
from netbox.ui.actions import LinkAction
from netbox.ui.panels import CommentsPanel, ObjectAttributesPanel, OrganizationalObjectPanel

__all__ = (
    'LookupPanel',
    'SLAPanel',
    'MTATPanel',
    'ContractPanel',
    'ContractContactsPanel',
    'ContractCustomerPanel',
    'ContractRateCardPanel',
    'ContractRateCardCostsPanel',
    'PortfolioPanel',
    'PortfolioOwnershipPanel',
    'ServicePanel',
    'ServiceOwnershipPanel',
    'ServiceOrganizationPanel',
    'ServiceOfferingPanel',
    'ServiceOfferingOwnershipPanel',
    'ServiceOfferingOrganizationPanel',
    'ServiceOfferingCustomerPanel',
    'AppServiceOverviewPanel',
    'AppServiceLevelsPanel',
    'AppServiceRecoveryPanel',
    'AppServiceOrganizationPanel',
    'ServiceSpecificationInfoPanel',
    'CommentsPanel',
)


class LookupPanel(OrganizationalObjectPanel):
    """Reused as-is for Lifecycle, OperationTime, Availability, Criticality, Environment
    (identical shape: just name + description + tags)."""

    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class SLAPanel(LookupPanel):
    sla_definition = attrs.TextAttr('sla_definition', label=_('SLA Definition'))


class MTATPanel(LookupPanel):
    value = attrs.NumericAttr('value', label=_('Value'))
    unit = attrs.ChoiceAttr('unit', label=_('Time Unit'))


class ContractPanel(ObjectAttributesPanel):
    contract_number = attrs.TextAttr('contract_number', label=_('Contract Number'))
    external_reference = attrs.TextAttr('external_reference', label=_('External Reference'))
    legacy_contract = attrs.TextAttr('legacy_contract', label=_('Legacy Contract'))
    parent_contract = attrs.RelatedObjectAttr('parent_contract', label=_('Parent Contract'), linkify=True)
    project = attrs.TextAttr('project', label=_('Project'))
    # `status` is a computed property (see models.py), not a stored field —
    # TextAttr just displays whatever getattr(instance, 'status') returns,
    # which works the same for a property as for a real field.
    status = attrs.TextAttr('status', label=_('Status'))
    vendor = attrs.RelatedObjectAttr('vendor', label=_('Vendor'), linkify=True)
    location = attrs.TextAttr('location', label=_('Location'))
    contract_starts = attrs.TextAttr('contract_starts', label=_('Contract Starts'))
    contract_ends = attrs.TextAttr('contract_ends', label=_('Contract Ends'))
    short_description = attrs.TextAttr('short_description', label=_('Short Description'))
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class ContractContactsPanel(ObjectAttributesPanel):
    title = _('Contacts & Ownership')
    contact_person = attrs.RelatedObjectListAttr('contact_person', label=_('Contact Person'), linkify=True)
    primary_contact = attrs.RelatedObjectListAttr('primary_contact', label=_('Primary Contact'), linkify=True)
    contract_manager = attrs.RelatedObjectListAttr('contract_manager', label=_('Contract Manager'), linkify=True)
    approver = attrs.RelatedObjectAttr('approver', label=_('Approver'), linkify=True)
    business_unit = attrs.RelatedObjectAttr('business_unit', label=_('Business Unit'), linkify=True)


class ContractCustomerPanel(ObjectAttributesPanel):
    title = _('Customer')
    tenant = attrs.RelatedObjectAttr('tenant', label=_('Customer'), linkify=True)
    tenant_group = attrs.RelatedObjectAttr('tenant_group', label=_('Customer Group'), linkify=True)


class ContractRateCardPanel(ObjectAttributesPanel):
    contract = attrs.RelatedObjectAttr('contract', label=_('Contract'), linkify=True)
    contract_position_number = attrs.TextAttr('contract_position_number', label=_('Contract Position Number'))
    order_number = attrs.TextAttr('order_number', label=_('Order Number'))
    project = attrs.TextAttr('project', label=_('Project'))
    active = attrs.TextAttr('active', label=_('Active'))
    start_date = attrs.TextAttr('start_date', label=_('Start Date'))
    end_date = attrs.TextAttr('end_date', label=_('End Date'))
    short_description = attrs.TextAttr('short_description', label=_('Short Description'))
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class ContractRateCardCostsPanel(ObjectAttributesPanel):
    title = _('Costs & Billing')
    base_costs = attrs.NumericAttr('base_costs', label=_('Base Costs'))
    hourly_rate = attrs.NumericAttr('hourly_rate', label=_('Hourly Rate'))
    hours_spend = attrs.NumericAttr('hours_spend', label=_('Hours Spend'))
    # `total_costs` is a computed property (see models.py) — NumericAttr
    # reads it via the same getattr as any real numeric field.
    total_costs = attrs.NumericAttr('total_costs', label=_('Total Costs'))
    interval = attrs.ChoiceAttr('interval', label=_('Interval'))
    billing = attrs.TextAttr('billing', label=_('Billing'))


class PortfolioPanel(ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Service Lifecycle Management'), linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class PortfolioOwnershipPanel(ObjectAttributesPanel):
    title = _('Ownership')
    portfolio_owner_contact_groups = attrs.RelatedObjectListAttr(
        'portfolio_owner_contact_groups',
        label=_('Owner (Contact Groups)'),
        linkify=True,
    )
    portfolio_owner_contacts = attrs.RelatedObjectListAttr(
        'portfolio_owner_contacts',
        label=_('Owner (Contacts)'),
        linkify=True,
    )
    portfolio_manager_contact_groups = attrs.RelatedObjectListAttr(
        'portfolio_manager_contact_groups',
        label=_('Manager (Contact Groups)'),
        linkify=True,
    )
    portfolio_manager_contacts = attrs.RelatedObjectListAttr(
        'portfolio_manager_contacts',
        label=_('Manager (Contacts)'),
        linkify=True,
    )


class ServicePanel(ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Service Lifecycle Management'), linkify=True)
    service_portfolio = attrs.RelatedObjectListAttr('service_portfolio', label=_('Service Portfolios'), linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class ServiceOwnershipPanel(ObjectAttributesPanel):
    title = _('Ownership')
    service_owner_contacts = attrs.RelatedObjectListAttr(
        'service_owner_contacts',
        label=_('Owner (Contacts)'),
        linkify=True,
    )
    service_owner_contact_groups = attrs.RelatedObjectListAttr(
        'service_owner_contact_groups',
        label=_('Owner (Contact Groups)'),
        linkify=True,
    )
    service_manager_contacts = attrs.RelatedObjectListAttr(
        'service_manager_contacts',
        label=_('Manager (Contacts)'),
        linkify=True,
    )
    service_manager_contact_groups = attrs.RelatedObjectListAttr(
        'service_manager_contact_groups',
        label=_('Manager (Contact Groups)'),
        linkify=True,
    )


class ServiceOrganizationPanel(ObjectAttributesPanel):
    title = _('Organization')
    business_unit = attrs.RelatedObjectListAttr('business_unit', label=_('Business Unit'), linkify=True)
    support_group = attrs.RelatedObjectListAttr('support_group', label=_('Support Group'), linkify=True)
    change_group = attrs.RelatedObjectListAttr('change_group', label=_('Change Group'), linkify=True)
    ci_function = attrs.RelatedObjectAttr('ci_function', label=_('CI Function'), linkify=True)


class ServiceOfferingPanel(ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    contract = attrs.RelatedObjectAttr('contract', label=_('Contract'), linkify=True)
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Service Lifecycle Management'), linkify=True)
    service = attrs.RelatedObjectListAttr('service', label=_('Services'), linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class ServiceOfferingOwnershipPanel(ObjectAttributesPanel):
    title = _('Ownership')
    service_offering_owner_contacts = attrs.RelatedObjectListAttr(
        'service_offering_owner_contacts',
        label=_('Owner (Contacts)'),
        linkify=True,
    )
    service_offering_owner_contact_groups = attrs.RelatedObjectListAttr(
        'service_offering_owner_contact_groups',
        label=_('Owner (Contact Groups)'),
        linkify=True,
    )
    service_offering_manager_contacts = attrs.RelatedObjectListAttr(
        'service_offering_manager_contacts',
        label=_('Manager (Contacts)'),
        linkify=True,
    )
    service_offering_manager_contact_groups = attrs.RelatedObjectListAttr(
        'service_offering_manager_contact_groups',
        label=_('Manager (Contact Groups)'),
        linkify=True,
    )


class ServiceOfferingOrganizationPanel(ObjectAttributesPanel):
    title = _('Organization')
    business_unit = attrs.RelatedObjectListAttr('business_unit', label=_('Business Unit'), linkify=True)
    support_group = attrs.RelatedObjectListAttr('support_group', label=_('Support Group'), linkify=True)
    change_group = attrs.RelatedObjectListAttr('change_group', label=_('Change Group'), linkify=True)


class ServiceOfferingCustomerPanel(ObjectAttributesPanel):
    title = _('Customer')
    tenant = attrs.RelatedObjectListAttr('tenant', label=_('Customer'), linkify=True)
    tenant_group = attrs.RelatedObjectListAttr('tenant_group', label=_('Customer Group'), linkify=True)


class AppServiceOverviewPanel(ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    environment = attrs.RelatedObjectAttr('environment', label=_('Environment'), linkify=True)
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Service Lifecycle Management'), linkify=True)
    service_offering = attrs.RelatedObjectAttr('service_offering', label=_('Service Offering'), linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class AppServiceLevelsPanel(ObjectAttributesPanel):
    title = _('Service Levels')
    sla = attrs.RelatedObjectListAttr('sla', label=_('SLAs'), linkify=True)
    operation_time = attrs.RelatedObjectListAttr('operation_time', label=_('Operation Time'), linkify=True)
    availability = attrs.RelatedObjectListAttr('availability', label=_('Availability'), linkify=True)
    mtat = attrs.RelatedObjectListAttr('mtat', label=_('MTAT'), linkify=True)
    service_criticality = attrs.RelatedObjectListAttr(
        'service_criticality',
        label=_('Service Criticality'),
        linkify=True,
    )


class AppServiceRecoveryPanel(ObjectAttributesPanel):
    title = _('Recovery & Continuity')
    accepted_downtime = attrs.NumericAttr('accepted_downtime', label=_('Accepted Downtime (hours)'))
    ttr = attrs.NumericAttr('ttr', label=_('TTR'))
    rpo = attrs.NumericAttr('rpo', label=_('RPO (hours)'))
    rto = attrs.NumericAttr('rto', label=_('RTO (hours)'))
    bcm = attrs.NumericAttr('bcm', label=_('BCM -1'))


class AppServiceOrganizationPanel(ObjectAttributesPanel):
    title = _('Organization')
    business_unit = attrs.RelatedObjectListAttr('business_unit', label=_('Business Unit'), linkify=True)
    support_group = attrs.RelatedObjectListAttr('support_group', label=_('Support Group'), linkify=True)
    change_group = attrs.RelatedObjectListAttr('change_group', label=_('Change Group'), linkify=True)
    owned_by_contact_group = attrs.RelatedObjectAttr(
        'owned_by_contact_group', label=_('Owner (Contact Group)'), linkify=True
    )
    owned_by_contact = attrs.RelatedObjectAttr('owned_by_contact', label=_('Owner (Contact)'), linkify=True)


class ServiceSpecificationInfoPanel(ObjectAttributesPanel):
    """Shared read-only panel for the Device/VirtualMachine/Cluster/ClusterGroup
    'Service Specification' tab (see views.py) — the editable fields are
    identical across all four side-info models, so one panel class covers
    all of them.

    The instance rendered here may be unsaved (pk=None) — the tab always
    resolves to either the existing side-info row or a fresh in-memory one
    bound to the parent object, so the very first visit shows blank fields
    plus an Edit link rather than a 404.
    """

    application_services = attrs.RelatedObjectListAttr(
        'application_services', label=_('Application Services'), linkify=True
    )
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Service Lifecycle Management'), linkify=True)
    business_unit = attrs.RelatedObjectListAttr('business_unit', label=_('Business Unit'), linkify=True)
    support_group = attrs.RelatedObjectListAttr('support_group', label=_('Support Group'), linkify=True)
    change_group = attrs.RelatedObjectListAttr('change_group', label=_('Change Group'), linkify=True)
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)

    def get_context(self, context):
        ctx = super().get_context(context)
        instance = ctx.get('object')
        parent = getattr(instance, 'parent', None)
        if parent is not None:
            ctx['actions'] = [
                LinkAction(
                    view_name=f'{parent._meta.app_label}:{parent._meta.model_name}_service_specification_edit',
                    view_kwargs={'pk': parent.pk},
                    label=_('Edit'),
                    button_icon='pencil',
                ),
            ]
        return ctx
