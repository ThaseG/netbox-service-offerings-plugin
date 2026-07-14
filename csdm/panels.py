from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs
from netbox.ui.panels import CommentsPanel, ObjectAttributesPanel, OrganizationalObjectPanel

__all__ = (
    'LookupPanel',
    'SLAPanel',
    'MTATPanel',
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
    'AppServiceCustomerPanel',
    'TechCIPanel',
    'TechCIOrganizationPanel',
    'TechCIInfrastructurePanel',
    'TechCICustomerPanel',
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


class PortfolioPanel(ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Lifecycle Management'), linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class PortfolioOwnershipPanel(ObjectAttributesPanel):
    title = _('Ownership')
    portfolio_owner_contacts = attrs.RelatedObjectListAttr(
        'portfolio_owner_contacts', label=_('Owner (Contacts)'), linkify=True,
    )
    portfolio_owner_contact_groups = attrs.RelatedObjectListAttr(
        'portfolio_owner_contact_groups', label=_('Owner (Contact Groups)'), linkify=True,
    )
    portfolio_manager_contacts = attrs.RelatedObjectListAttr(
        'portfolio_manager_contacts', label=_('Manager (Contacts)'), linkify=True,
    )
    portfolio_manager_contact_groups = attrs.RelatedObjectListAttr(
        'portfolio_manager_contact_groups', label=_('Manager (Contact Groups)'), linkify=True,
    )


class ServicePanel(ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Lifecycle Management'), linkify=True)
    service_portfolio = attrs.RelatedObjectListAttr('service_portfolio', label=_('Service Portfolios'), linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class ServiceOwnershipPanel(ObjectAttributesPanel):
    title = _('Ownership')
    service_owner_contacts = attrs.RelatedObjectListAttr(
        'service_owner_contacts', label=_('Owner (Contacts)'), linkify=True,
    )
    service_owner_contact_groups = attrs.RelatedObjectListAttr(
        'service_owner_contact_groups', label=_('Owner (Contact Groups)'), linkify=True,
    )
    service_manager_contacts = attrs.RelatedObjectListAttr(
        'service_manager_contacts', label=_('Manager (Contacts)'), linkify=True,
    )
    service_manager_contact_groups = attrs.RelatedObjectListAttr(
        'service_manager_contact_groups', label=_('Manager (Contact Groups)'), linkify=True,
    )


class ServiceOrganizationPanel(ObjectAttributesPanel):
    title = _('Organization')
    business_unit = attrs.RelatedObjectListAttr('business_unit', label=_('Business Unit'), linkify=True)
    support_group = attrs.RelatedObjectListAttr('support_group', label=_('Support Group'), linkify=True)
    change_group = attrs.RelatedObjectListAttr('change_group', label=_('Change Group'), linkify=True)
    ci_function = attrs.RelatedObjectListAttr('ci_function', label=_('Technical CIs'), linkify=True)


class ServiceOfferingPanel(ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    contract_number = attrs.TextAttr('contract_number', label=_('Contract Number'))
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Lifecycle Management'), linkify=True)
    service = attrs.RelatedObjectListAttr('service', label=_('Services'), linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class ServiceOfferingOwnershipPanel(ObjectAttributesPanel):
    title = _('Ownership')
    service_offering_owner_contacts = attrs.RelatedObjectListAttr(
        'service_offering_owner_contacts', label=_('Owner (Contacts)'), linkify=True,
    )
    service_offering_owner_contact_groups = attrs.RelatedObjectListAttr(
        'service_offering_owner_contact_groups', label=_('Owner (Contact Groups)'), linkify=True,
    )
    service_offering_manager_contacts = attrs.RelatedObjectListAttr(
        'service_offering_manager_contacts', label=_('Manager (Contacts)'), linkify=True,
    )
    service_offering_manager_contact_groups = attrs.RelatedObjectListAttr(
        'service_offering_manager_contact_groups', label=_('Manager (Contact Groups)'), linkify=True,
    )


class ServiceOfferingOrganizationPanel(ObjectAttributesPanel):
    title = _('Organization')
    business_unit = attrs.RelatedObjectListAttr('business_unit', label=_('Business Unit'), linkify=True)
    support_group = attrs.RelatedObjectListAttr('support_group', label=_('Support Group'), linkify=True)
    change_group = attrs.RelatedObjectListAttr('change_group', label=_('Change Group'), linkify=True)
    ci_function = attrs.RelatedObjectListAttr('ci_function', label=_('Technical CIs'), linkify=True)


class ServiceOfferingCustomerPanel(ObjectAttributesPanel):
    title = _('Customer')
    tenant = attrs.RelatedObjectListAttr('tenant', label=_('Customer'), linkify=True)
    tenant_group = attrs.RelatedObjectListAttr('tenant_group', label=_('Customer Group'), linkify=True)


class AppServiceOverviewPanel(ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    environment = attrs.RelatedObjectAttr('environment', label=_('Environment'), linkify=True)
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Lifecycle Management'), linkify=True)
    service_offering = attrs.RelatedObjectListAttr('service_offering', label=_('Service Offerings'), linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class AppServiceLevelsPanel(ObjectAttributesPanel):
    title = _('Service Levels')
    sla = attrs.RelatedObjectListAttr('sla', label=_('SLAs'), linkify=True)
    operation_time = attrs.RelatedObjectListAttr('operation_time', label=_('Operation Time'), linkify=True)
    availability = attrs.RelatedObjectListAttr('availability', label=_('Availability'), linkify=True)
    mtat = attrs.RelatedObjectListAttr('mtat', label=_('MTAT'), linkify=True)
    service_criticality = attrs.RelatedObjectListAttr(
        'service_criticality', label=_('Service Criticality'), linkify=True,
    )


class AppServiceRecoveryPanel(ObjectAttributesPanel):
    title = _('Recovery & Continuity')
    accepted_downtime = attrs.NumericAttr('accepted_downtime', label=_('Accepted Downtime (hours)'))
    ttr = attrs.NumericAttr('ttr', label=_('TTR'))
    rpo = attrs.NumericAttr('rpo', label=_('RPO (hours)'))
    rto = attrs.NumericAttr('rto', label=_('RTO (hours)'))
    bcm = attrs.NumericAttr('bcm', label=_('BCM (hours)'))


class AppServiceOrganizationPanel(ObjectAttributesPanel):
    title = _('Organization')
    business_unit = attrs.RelatedObjectListAttr('business_unit', label=_('Business Unit'), linkify=True)
    support_group = attrs.RelatedObjectListAttr('support_group', label=_('Support Group'), linkify=True)
    change_group = attrs.RelatedObjectListAttr('change_group', label=_('Change Group'), linkify=True)
    owned_by = attrs.RelatedObjectListAttr('owned_by', label=_('Owned by'), linkify=True)
    ci_function = attrs.RelatedObjectListAttr('ci_function', label=_('Technical CIs'), linkify=True)


class AppServiceCustomerPanel(ObjectAttributesPanel):
    title = _('Customer')
    tenant = attrs.RelatedObjectListAttr('tenant', label=_('Customer'), linkify=True)
    tenant_group = attrs.RelatedObjectListAttr('tenant_group', label=_('Customer Group'), linkify=True)


class TechCIPanel(ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    function = attrs.TextAttr('function', label=_('CI Function'))
    lifecycle = attrs.RelatedObjectAttr('lifecycle', label=_('Lifecycle Management'), linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
    tags = attrs.RelatedObjectListAttr('tags', label=_('Tags'), linkify=True)


class TechCIOrganizationPanel(ObjectAttributesPanel):
    title = _('Organization')
    business_unit = attrs.RelatedObjectListAttr('business_unit', label=_('Business Unit'), linkify=True)
    support_group = attrs.RelatedObjectListAttr('support_group', label=_('Support Group'), linkify=True)
    change_group = attrs.RelatedObjectListAttr('change_group', label=_('Change Group'), linkify=True)


class TechCIInfrastructurePanel(ObjectAttributesPanel):
    title = _('Infrastructure')
    device = attrs.RelatedObjectListAttr('device', label=_('Devices'), linkify=True)
    virtual_machine = attrs.RelatedObjectListAttr('virtual_machine', label=_('Virtual Machines'), linkify=True)
    cluster = attrs.RelatedObjectListAttr('cluster', label=_('Clusters'), linkify=True)
    cluster_group = attrs.RelatedObjectListAttr('cluster_group', label=_('Cluster Groups'), linkify=True)


class TechCICustomerPanel(ObjectAttributesPanel):
    title = _('Customer')
    tenant = attrs.RelatedObjectListAttr('tenant', label=_('Customer'), linkify=True)
    tenant_group = attrs.RelatedObjectListAttr('tenant_group', label=_('Customer Group'), linkify=True)
