from dcim.models import Device, Manufacturer
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm, OrganizationalModelForm, PrimaryModelForm
from tenancy.models import Contact, ContactGroup, Tenant, TenantGroup
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField
from utilities.forms.rendering import FieldSet
from virtualization.models import Cluster, ClusterGroup, VirtualMachine

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

__all__ = (
    'ContractForm',
    'ContractRateCardForm',
    'PortfolioForm',
    'ServiceForm',
    'ServiceOfferingForm',
    'AppServiceForm',
    'LifecycleForm',
    'SLAForm',
    'OperationTimeForm',
    'AvailabilityForm',
    'CriticalityForm',
    'EnvironmentForm',
    'MTATForm',
    'CIFunctionForm',
    'DeviceServiceInfoForm',
    'VirtualMachineServiceInfoForm',
    'ClusterServiceInfoForm',
    'ClusterGroupServiceInfoForm',
    'ContractFilterForm',
    'ContractRateCardFilterForm',
    'PortfolioFilterForm',
    'ServiceFilterForm',
    'ServiceOfferingFilterForm',
    'AppServiceFilterForm',
    'LifecycleFilterForm',
    'SLAFilterForm',
    'OperationTimeFilterForm',
    'AvailabilityFilterForm',
    'CriticalityFilterForm',
    'EnvironmentFilterForm',
    'MTATFilterForm',
    'CIFunctionFilterForm',
    'OfferingsTreeFilterForm',
)


#
# Support / lookup model forms
#


class LifecycleForm(OrganizationalModelForm):
    class Meta:
        model = Lifecycle
        fields = ('name', 'slug', 'color', 'description', 'tags', 'comments')
        help_texts = {
            'name': (
                'Standard lifecycle statuses: Draft (created but still being defined, not yet approved); '
                'Design (planning/design phase); Build (being developed or configured, not yet ready for '
                'production); Available (ready for deployment, not yet actively in production); Operational '
                '(deployed and actively supporting business/IT services); In Maintenance (temporarily '
                'undergoing maintenance, upgrades, or repairs); End of Support (support has ended or is '
                'scheduled to end, though it may still be operational); End of Life (reached the end of its '
                'intended lifecycle, should no longer be used for production); Expired (no longer valid due '
                'to expiration of a license, certificate, contract, or subscription); Decommissioned '
                '(permanently removed from service, retained for audit purposes); Cancelled (planned but '
                'never deployed).'
            ),
        }


class SLAForm(OrganizationalModelForm):
    class Meta:
        model = SLA
        fields = ('name', 'slug', 'sla_definition', 'description', 'tags', 'comments')


class OperationTimeForm(OrganizationalModelForm):
    class Meta:
        model = OperationTime
        fields = ('name', 'slug', 'description', 'tags', 'comments')


class AvailabilityForm(OrganizationalModelForm):
    class Meta:
        model = Availability
        fields = ('name', 'slug', 'description', 'tags', 'comments')


class CriticalityForm(OrganizationalModelForm):
    class Meta:
        model = Criticality
        fields = ('name', 'slug', 'description', 'tags', 'comments')


class EnvironmentForm(OrganizationalModelForm):
    class Meta:
        model = Environment
        fields = ('name', 'slug', 'description', 'tags', 'comments')


class MTATForm(OrganizationalModelForm):
    class Meta:
        model = MTAT
        fields = ('name', 'slug', 'value', 'unit', 'description', 'tags', 'comments')


class CIFunctionForm(OrganizationalModelForm):
    class Meta:
        model = CIFunction
        fields = ('name', 'slug', 'description', 'tags', 'comments')


#
# Core model forms
#


class PortfolioForm(PrimaryModelForm):
    lifecycle = DynamicModelChoiceField(
        queryset=Lifecycle.objects.all(),
        required=True,
        help_text='Current phase of the portfolio (e.g., Draft, Operational). Use the standard lifecycle status list.',
    )
    portfolio_owner_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text=(
            "Executive accountable for the portfolio's strategic content. This is a senior leadership role. "
            'Required: select at least one Contact or Contact Group.'
        ),
    )
    portfolio_owner_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={'group_id': '$portfolio_owner_contact_groups'},
        help_text=(
            "Executive accountable for the portfolio's strategic content. This is a senior leadership role. "
            'Required: select at least one Contact or Contact Group.'
        ),
    )
    portfolio_manager_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text=(
            'Operational manager handling daily portfolio oversight and updates. Acts as the primary point of '
            'contact. Required: select at least one Contact or Contact Group.'
        ),
    )
    portfolio_manager_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={'group_id': '$portfolio_manager_contact_groups'},
        help_text=(
            'Operational manager handling daily portfolio oversight and updates. Acts as the primary point of '
            'contact. Required: select at least one Contact or Contact Group.'
        ),
    )

    fieldsets = (
        FieldSet('name', 'lifecycle', 'description', 'tags', name='Portfolio'),
        FieldSet(
            'portfolio_owner_contact_groups',
            'portfolio_owner_contacts',
            name='Service Portfolio Owner',
        ),
        FieldSet(
            'portfolio_manager_contact_groups',
            'portfolio_manager_contacts',
            name='Service Portfolio Manager',
        ),
    )

    class Meta:
        model = Portfolio
        fields = (
            'name',
            'lifecycle',
            'portfolio_owner_contact_groups',
            'portfolio_owner_contacts',
            'portfolio_manager_contact_groups',
            'portfolio_manager_contacts',
            'description',
            'tags',
            'comments',
        )
        help_texts = {
            'name': 'Unique identifier for the portfolio. Keep it concise and business-meaningful.',
            'description': "Brief summary of the portfolio's scope and purpose. Aim for one to two sentences.",
        }

    def clean(self):
        # Deliberately not using super().clean()'s return value: NetBoxModelForm's
        # own base mixins include CheckLastUpdatedMixin, which returns None
        # (bare `return`) for any new/unsaved object — a valid, documented
        # Django pattern (clean() doesn't have to return anything; Django
        # falls back to self.cleaned_data if it doesn't), but one that
        # breaks `cleaned_data = super().clean()` for every create form.
        # self.cleaned_data is always populated by this point regardless.
        super().clean()
        cleaned_data = self.cleaned_data
        if not (cleaned_data.get('portfolio_owner_contacts') or cleaned_data.get('portfolio_owner_contact_groups')):
            raise ValidationError('Select at least one Portfolio Owner (a contact or a contact group).')
        if not (cleaned_data.get('portfolio_manager_contacts') or cleaned_data.get('portfolio_manager_contact_groups')):
            raise ValidationError('Select at least one Portfolio Manager (a contact or a contact group).')
        return cleaned_data


class ServiceForm(PrimaryModelForm):
    lifecycle = DynamicModelChoiceField(
        queryset=Lifecycle.objects.all(),
        required=True,
        help_text='Current lifecycle state of the service (e.g., Operational, Retired). Use the standard status list.',
    )
    service_portfolio = DynamicModelMultipleChoiceField(
        queryset=Portfolio.objects.all(),
        required=True,
        help_text=(
            'Reference to the parent portfolio that contains this service. Links the service to its strategic context.'
        ),
    )
    service_owner_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text=(
            'Business stakeholder accountable for overall service outcomes and value. Has decision authority. '
            'Required: select at least one Contact or Contact Group.'
        ),
    )
    service_owner_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={'group_id': '$service_owner_contact_groups'},
        help_text=(
            'Business stakeholder accountable for overall service outcomes and value. Has decision authority. '
            'Required: select at least one Contact or Contact Group.'
        ),
    )
    service_manager_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text=(
            'Operational lead responsible for day-to-day service delivery and performance. Manages the support '
            'teams. Required: select at least one Contact or Contact Group.'
        ),
    )
    service_manager_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={'group_id': '$service_manager_contact_groups'},
        help_text=(
            'Operational lead responsible for day-to-day service delivery and performance. Manages the support '
            'teams. Required: select at least one Contact or Contact Group.'
        ),
    )
    business_unit = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=True,
        help_text='Organizational unit that consumes or funds the service. Helps with cost and ownership tracking.',
    )
    support_group = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=True,
        help_text='Team assigned to handle incidents, requests, and user issues. Typically a helpdesk or L2/L3 team.',
    )
    change_group = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=True,
        help_text=(
            'Team responsible for reviewing and executing changes for this service. Ensures proper change control.'
        ),
    )
    ci_function = DynamicModelChoiceField(
        queryset=CIFunction.objects.all(),
        required=False,
        label='CI Function',
        help_text=(
            'Primary capability or role this service provides (e.g., identity management). Describes what it '
            'does technically.'
        ),
    )

    fieldsets = (
        FieldSet('name', 'lifecycle', 'service_portfolio', 'description', 'tags', name='Service'),
        FieldSet('service_owner_contact_groups', 'service_owner_contacts', name='Owner'),
        FieldSet('service_manager_contact_groups', 'service_manager_contacts', name='Manager'),
        FieldSet('business_unit', 'support_group', 'change_group', name='Organization'),
        FieldSet('ci_function', name='CI Function'),
    )

    class Meta:
        model = Service
        fields = (
            'name',
            'lifecycle',
            'service_portfolio',
            'service_owner_contact_groups',
            'service_owner_contacts',
            'service_manager_contact_groups',
            'service_manager_contacts',
            'business_unit',
            'support_group',
            'change_group',
            'ci_function',
            'description',
            'tags',
            'comments',
        )
        help_texts = {
            'name': 'Unique identifier for the service. Should be clear and recognizable to stakeholders.',
            'description': (
                "Concise statement of the service's primary function. Keep it to one or two business-friendly lines."
            ),
        }

    def clean(self):
        # See PortfolioForm.clean() for why this doesn't use super().clean()'s
        # return value.
        super().clean()
        cleaned_data = self.cleaned_data
        if not (cleaned_data.get('service_owner_contacts') or cleaned_data.get('service_owner_contact_groups')):
            raise ValidationError('Select at least one Service Owner (a contact or a contact group).')
        if not (cleaned_data.get('service_manager_contacts') or cleaned_data.get('service_manager_contact_groups')):
            raise ValidationError('Select at least one Service Manager (a contact or a contact group).')
        return cleaned_data


class ContractForm(PrimaryModelForm):
    parent_contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        help_text='Parent contract this one is a sub-contract of, if any.',
    )
    vendor = DynamicModelChoiceField(
        queryset=Manufacturer.objects.all(),
        required=False,
        help_text='Manufacturer/vendor providing the contracted goods or services.',
    )
    tenant = DynamicModelChoiceField(queryset=Tenant.objects.all(), required=False, label='Customer')
    tenant_group = DynamicModelChoiceField(queryset=TenantGroup.objects.all(), required=False, label='Customer Group')
    contact_person = DynamicModelMultipleChoiceField(queryset=Contact.objects.all(), required=False)
    primary_contact = DynamicModelMultipleChoiceField(queryset=Contact.objects.all(), required=False)
    contract_manager = DynamicModelMultipleChoiceField(queryset=Contact.objects.all(), required=False)
    approver = DynamicModelChoiceField(queryset=Contact.objects.all(), required=False)
    business_unit = DynamicModelChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text='Unit that owns or funds this contract.',
    )

    fieldsets = (
        FieldSet(
            'contract_number',
            'external_reference',
            'legacy_contract',
            'parent_contract',
            'project',
            'short_description',
            'description',
            'tags',
            name='Contract',
        ),
        FieldSet('vendor', 'location', name='Vendor & Location'),
        FieldSet('tenant', 'tenant_group', name='Customer'),
        FieldSet(
            'contact_person',
            'primary_contact',
            'contract_manager',
            'approver',
            'business_unit',
            name='Contacts & Ownership',
        ),
        FieldSet('contract_starts', 'contract_ends', name='Term'),
    )

    class Meta:
        model = Contract
        fields = (
            'contract_number',
            'external_reference',
            'legacy_contract',
            'parent_contract',
            'project',
            'vendor',
            'location',
            'tenant',
            'tenant_group',
            'contact_person',
            'primary_contact',
            'contract_manager',
            'approver',
            'business_unit',
            'contract_starts',
            'contract_ends',
            'short_description',
            'description',
            'tags',
            'comments',
        )
        help_texts = {
            'contract_number': 'Reference number for the legal or commercial agreement. Use the actual contract ID.',
            'location': 'Free-text site/location description for this contract.',
        }


class ContractRateCardForm(PrimaryModelForm):
    contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=True,
        help_text='The contract this rate card is a position of.',
    )

    fieldsets = (
        FieldSet(
            'contract',
            'contract_position_number',
            'order_number',
            'project',
            'short_description',
            'description',
            'tags',
            name='Contract Rate Card',
        ),
        FieldSet('active', 'start_date', 'end_date', name='Term & Status'),
        FieldSet('base_costs', 'hourly_rate', 'hours_spend', 'interval', 'billing', name='Costs & Billing'),
    )

    class Meta:
        model = ContractRateCard
        fields = (
            'contract',
            'contract_position_number',
            'order_number',
            'project',
            'active',
            'start_date',
            'end_date',
            'base_costs',
            'hourly_rate',
            'hours_spend',
            'interval',
            'billing',
            'short_description',
            'description',
            'tags',
            'comments',
        )


class ServiceOfferingForm(PrimaryModelForm):
    lifecycle = DynamicModelChoiceField(
        queryset=Lifecycle.objects.all(),
        required=True,
        help_text='Current phase of the offering (e.g., Available, End of Life). Follows the standard lifecycle list.',
    )
    contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        help_text='Reference to the legal or commercial agreement governing this offering.',
    )
    service = DynamicModelMultipleChoiceField(
        queryset=Service.objects.all(),
        required=True,
        help_text='The core service on which this offering is based. Establishes the hierarchical relationship.',
    )
    service_offering_owner_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text=(
            "Business owner accountable for the offering's success and lifecycle. Has budget or P&L "
            'responsibility. Required: select at least one Contact or Contact Group.'
        ),
    )
    service_offering_owner_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={'group_id': '$service_offering_owner_contact_groups'},
        help_text=(
            "Business owner accountable for the offering's success and lifecycle. Has budget or P&L "
            'responsibility. Required: select at least one Contact or Contact Group.'
        ),
    )
    service_offering_manager_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text=(
            "Operational manager who runs the offering's daily activities. Coordinates delivery and "
            'improvements. Required: select at least one Contact or Contact Group.'
        ),
    )
    service_offering_manager_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={'group_id': '$service_offering_manager_contact_groups'},
        help_text=(
            "Operational manager who runs the offering's daily activities. Coordinates delivery and "
            'improvements. Required: select at least one Contact or Contact Group.'
        ),
    )
    business_unit = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=True,
        help_text=(
            'Unit that owns, funds, or is responsible for this offering. Aids in financial and organizational '
            'alignment.'
        ),
    )
    support_group = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=True,
        help_text=(
            "Team delivering support specifically for this offering. May differ from the parent service's "
            'support group.'
        ),
    )
    change_group = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=True,
        help_text="Team handling changes to this offering's configuration or content. Ensures change traceability.",
    )
    tenant = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        help_text=(
            'External or internal customer entity that subscribes to this offering. Links to the Foundation '
            'Information Form.'
        ),
    )
    tenant_group = DynamicModelMultipleChoiceField(queryset=TenantGroup.objects.all(), required=False)

    fieldsets = (
        FieldSet(
            'name',
            'contract',
            'lifecycle',
            'service',
            'description',
            'tags',
            name='Service Offering',
        ),
        FieldSet(
            'service_offering_owner_contact_groups',
            'service_offering_owner_contacts',
            name='Owner',
        ),
        FieldSet(
            'service_offering_manager_contact_groups',
            'service_offering_manager_contacts',
            name='Manager',
        ),
        FieldSet('business_unit', 'support_group', 'change_group', name='Organization'),
        FieldSet('tenant', 'tenant_group', name='Customer'),
    )

    class Meta:
        model = ServiceOffering
        fields = (
            'name',
            'contract',
            'lifecycle',
            'service',
            'service_offering_owner_contact_groups',
            'service_offering_owner_contacts',
            'service_offering_manager_contact_groups',
            'service_offering_manager_contacts',
            'business_unit',
            'support_group',
            'change_group',
            'tenant',
            'tenant_group',
            'description',
            'tags',
            'comments',
        )
        help_texts = {
            'name': (
                'Distinct name for the offering (e.g., Premium Support, Basic Plan). Differentiates it from '
                'other offerings.'
            ),
            'description': (
                'Summary of what the offering includes in terms of features or service levels. Keep it '
                'customer-friendly.'
            ),
        }

    def clean(self):
        # See PortfolioForm.clean() for why this doesn't use super().clean()'s
        # return value.
        super().clean()
        cleaned_data = self.cleaned_data
        if not (
            cleaned_data.get('service_offering_owner_contacts')
            or cleaned_data.get('service_offering_owner_contact_groups')
        ):
            raise ValidationError('Select at least one Service Offering Owner (a contact or a contact group).')
        if not (
            cleaned_data.get('service_offering_manager_contacts')
            or cleaned_data.get('service_offering_manager_contact_groups')
        ):
            raise ValidationError('Select at least one Service Offering Manager (a contact or a contact group).')
        return cleaned_data


class AppServiceForm(PrimaryModelForm):
    environment = DynamicModelChoiceField(
        queryset=Environment.objects.all(),
        required=True,
        help_text='Deployment context (e.g., Development, Test, Production). Critical for operational management.',
    )
    lifecycle = DynamicModelChoiceField(
        queryset=Lifecycle.objects.all(),
        required=True,
        help_text='Current phase (e.g., Build, Operational, Decommissioned). Use the standard status list.',
    )
    service_offering = DynamicModelChoiceField(
        queryset=ServiceOffering.objects.all(),
        required=True,
        query_params={'unassigned': 'true'},
        help_text=(
            'Parent offering that this application service supports or enables. Links to commercial agreements. '
            'A Service Offering can back only one Application Service.'
        ),
    )
    business_unit = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=True,
        help_text='Unit that owns or primarily uses the application. Helps with budgeting and governance.',
    )
    support_group = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=True,
        help_text=(
            'Team providing application-level support (e.g., App Support). Distinguish from infrastructure support.'
        ),
    )
    change_group = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=True,
        help_text='Team managing application changes and releases. Coordinates deployment and testing.',
    )
    sla = DynamicModelMultipleChoiceField(queryset=SLA.objects.all(), required=True, label='SLA')
    # Owner is a single choice of *either* a Contact *or* a Contact Group,
    # not both — see clean() below.
    owned_by_contact_group = DynamicModelChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Owner (Contact Group)',
        help_text=(
            'Person or team accountable for meeting the SLA targets. This is a managerial role. '
            'Select exactly one: either a Contact or a Contact Group, not both.'
        ),
    )
    owned_by_contact = DynamicModelChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={'group_id': '$owned_by_contact_group'},
        label='Owner (Contact)',
        help_text=(
            'Person or team accountable for meeting the SLA targets. This is a managerial role. '
            'Select exactly one: either a Contact or a Contact Group, not both.'
        ),
    )
    operation_time = DynamicModelMultipleChoiceField(
        queryset=OperationTime.objects.all(),
        required=True,
        help_text=(
            'Hours during which the service is measured (e.g., 24x7, 08:00-18:00 weekdays). Defines the '
            'measurement window.'
        ),
    )
    availability = DynamicModelMultipleChoiceField(
        queryset=Availability.objects.all(),
        required=True,
        help_text='Target uptime percentage (e.g., 99.9%). Calculated from the operation time.',
    )
    mtat = DynamicModelMultipleChoiceField(
        queryset=MTAT.objects.all(),
        required=True,
        label='MTAT',
        help_text=(
            'Mean Time to Acknowledge - target response time from incident creation to first response. '
            'Measured in minutes.'
        ),
    )
    service_criticality = DynamicModelMultipleChoiceField(
        queryset=Criticality.objects.all(),
        required=True,
        help_text=(
            'Priority level indicating business impact (e.g., Critical, High, Medium, Low). Drives response urgency.'
        ),
    )
    fieldsets = (
        FieldSet(
            'name',
            'environment',
            'lifecycle',
            'service_offering',
            'description',
            'tags',
            name='Application Service',
        ),
        FieldSet(
            'business_unit',
            'support_group',
            'change_group',
            'owned_by_contact_group',
            'owned_by_contact',
            name='Organization',
        ),
        FieldSet('sla', 'operation_time', 'availability', 'mtat', 'service_criticality', name='Service Levels'),
        FieldSet('accepted_downtime', 'ttr', 'rpo', 'rto', 'bcm', name='Recovery & Continuity'),
    )

    class Meta:
        model = AppService
        fields = (
            'name',
            'environment',
            'lifecycle',
            'service_offering',
            'business_unit',
            'support_group',
            'change_group',
            'sla',
            'accepted_downtime',
            'owned_by_contact_group',
            'owned_by_contact',
            'operation_time',
            'availability',
            'mtat',
            'ttr',
            'service_criticality',
            'rpo',
            'rto',
            'bcm',
            'description',
            'tags',
            'comments',
        )
        help_texts = {
            'name': 'Unique application service identifier. Use a recognizable application name or code.',
            'description': 'Purpose of the application service in business terms. Explain what it does for the user.',
            'accepted_downtime': (
                'Maximum allowable planned downtime within a given period (e.g., per month). Expressed in hours '
                'or minutes.'
            ),
            'ttr': 'Mean Time to Restore - target resolution or recovery time. Measured in hours or minutes.',
            'rpo': (
                'Recovery Point Objective - maximum tolerable data loss, measured in hours. Defines backup '
                'frequency needs.'
            ),
            'rto': (
                'Recovery Time Objective - maximum tolerable downtime, measured in hours. Defines recovery '
                'speed target.'
            ),
            'bcm': (
                'Business Continuity Management tier-1 recovery time target. Represents the first recovery milestone.'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A ServiceOffering backs at most one AppService (see models.py's
        # OneToOneField). query_params={'unassigned': 'true'} above already
        # keeps the live dropdown from suggesting already-claimed offerings;
        # this restricts the field's own queryset the same way so validation
        # (and any non-JS rendering) enforces the same rule — while still
        # allowing an existing AppService to keep its own current offering.
        self.fields['service_offering'].queryset = ServiceOffering.objects.filter(
            Q(app_service__isnull=True) | Q(pk=self.instance.service_offering_id)
        )

    def clean(self):
        # See PortfolioForm.clean() for why this doesn't use super().clean()'s
        # return value.
        super().clean()
        cleaned_data = self.cleaned_data
        owned_by_contact = cleaned_data.get('owned_by_contact')
        owned_by_contact_group = cleaned_data.get('owned_by_contact_group')
        if not (owned_by_contact or owned_by_contact_group):
            raise ValidationError('Select an Owner: either a Contact or a Contact Group.')
        if owned_by_contact and owned_by_contact_group:
            raise ValidationError('Select only one Owner: either a Contact or a Contact Group, not both.')
        return cleaned_data


#
# Service Specification info forms — one per core NetBox object type
# (Device/VirtualMachine/Cluster/ClusterGroup), built off a shared factory
# since the editable fields are identical across all four; only the model
# (and its non-editable parent-object field, set by the view rather than
# this form) differs. See models.py's ServiceSpecificationInfoBase.
#


def _make_service_info_form(model):
    # Built via type() rather than a nested `class ServiceInfoForm(...):`
    # statement so Meta.model is present in the class namespace *before*
    # ModelForm's metaclass runs — it reads Meta.model while the class is
    # being created to build the form's internal _meta, and never re-reads
    # it afterward. Assigning `ServiceInfoForm.Meta.model = model` post
    # hoc (the previous approach here) changes the Meta class's own
    # attribute but not the already-baked _meta.model, which stayed None;
    # BaseModelForm.__init__() then raises "ModelForm has no model class
    # specified." the moment the form is actually instantiated.
    meta = type(
        'Meta',
        (),
        {
            'model': model,
            'fields': (
                'application_services',
                'lifecycle',
                'business_unit',
                'support_group',
                'change_group',
                'tags',
            ),
        },
    )
    return type(
        f'{model.__name__}Form',
        (NetBoxModelForm,),
        {
            'application_services': DynamicModelMultipleChoiceField(
                queryset=AppService.objects.all(),
                required=True,
                label='Application Services',
                help_text='Application Service(s) this technical component supports. Used to derive its CI Function.',
            ),
            'lifecycle': DynamicModelChoiceField(
                queryset=Lifecycle.objects.all(),
                required=True,
                help_text='Current state (e.g., Operational, End of Support). Follows the standard lifecycle.',
            ),
            'business_unit': DynamicModelMultipleChoiceField(
                queryset=ContactGroup.objects.all(),
                required=True,
                help_text='Unit that owns or funds this technical component. Helps with cost allocation.',
            ),
            'support_group': DynamicModelMultipleChoiceField(
                queryset=ContactGroup.objects.all(),
                required=True,
                help_text='Team maintaining the component (e.g., Server Team, DBA). Handles incidents and maintenance.',
            ),
            'change_group': DynamicModelMultipleChoiceField(
                queryset=ContactGroup.objects.all(),
                required=True,
                help_text='Team executing changes on this CI (e.g., patching, upgrades). Ensures change compliance.',
            ),
            'fieldsets': (
                FieldSet('application_services', 'lifecycle', 'tags', name='Service Specification'),
                FieldSet('business_unit', 'support_group', 'change_group', name='Organization'),
            ),
            'Meta': meta,
        },
    )


DeviceServiceInfoForm = _make_service_info_form(DeviceServiceInfo)
VirtualMachineServiceInfoForm = _make_service_info_form(VirtualMachineServiceInfo)
ClusterServiceInfoForm = _make_service_info_form(ClusterServiceInfo)
ClusterGroupServiceInfoForm = _make_service_info_form(ClusterGroupServiceInfo)


#
# Filter forms
#


class LifecycleFilterForm(NetBoxModelFilterSetForm):
    model = Lifecycle


class SLAFilterForm(NetBoxModelFilterSetForm):
    model = SLA


class OperationTimeFilterForm(NetBoxModelFilterSetForm):
    model = OperationTime


class AvailabilityFilterForm(NetBoxModelFilterSetForm):
    model = Availability


class CriticalityFilterForm(NetBoxModelFilterSetForm):
    model = Criticality


class EnvironmentFilterForm(NetBoxModelFilterSetForm):
    model = Environment


class MTATFilterForm(NetBoxModelFilterSetForm):
    model = MTAT


class CIFunctionFilterForm(NetBoxModelFilterSetForm):
    model = CIFunction


class ContractFilterForm(NetBoxModelFilterSetForm):
    model = Contract
    parent_contract_id = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        label='Parent Contract',
    )
    vendor_id = DynamicModelMultipleChoiceField(
        queryset=Manufacturer.objects.all(),
        required=False,
        label='Vendor',
    )
    tenant_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        label='Customer',
    )
    tenant_group_id = DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        label='Customer Group',
    )
    contact_person_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Contact Person',
    )
    primary_contact_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Primary Contact',
    )
    contract_manager_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Contract Manager',
    )
    approver_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Approver',
    )
    business_unit_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Business Unit',
    )


class ContractRateCardFilterForm(NetBoxModelFilterSetForm):
    model = ContractRateCard
    contract_id = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        label='Contract',
    )


class PortfolioFilterForm(NetBoxModelFilterSetForm):
    model = Portfolio
    lifecycle_id = DynamicModelMultipleChoiceField(
        queryset=Lifecycle.objects.all(),
        required=False,
        label='Lifecycle',
    )
    portfolio_owner_contacts_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Portfolio Owner (Contact)',
    )
    portfolio_owner_contact_groups_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Portfolio Owner (Contact Group)',
    )
    portfolio_manager_contacts_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Portfolio Manager (Contact)',
    )
    portfolio_manager_contact_groups_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Portfolio Manager (Contact Group)',
    )


class ServiceFilterForm(NetBoxModelFilterSetForm):
    model = Service
    lifecycle_id = DynamicModelMultipleChoiceField(
        queryset=Lifecycle.objects.all(),
        required=False,
        label='Lifecycle',
    )
    service_portfolio_id = DynamicModelMultipleChoiceField(
        queryset=Portfolio.objects.all(),
        required=False,
        label='Service Portfolio',
    )
    ci_function_id = DynamicModelMultipleChoiceField(
        queryset=CIFunction.objects.all(),
        required=False,
        label='CI Function',
    )
    service_owner_contacts_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Service Owner (Contact)',
    )
    service_owner_contact_groups_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Service Owner (Contact Group)',
    )
    service_manager_contacts_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Service Manager (Contact)',
    )
    service_manager_contact_groups_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Service Manager (Contact Group)',
    )
    business_unit_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Business Unit',
    )
    support_group_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Support Group',
    )
    change_group_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Change Group',
    )


class ServiceOfferingFilterForm(NetBoxModelFilterSetForm):
    model = ServiceOffering
    lifecycle_id = DynamicModelMultipleChoiceField(
        queryset=Lifecycle.objects.all(),
        required=False,
        label='Lifecycle',
    )
    contract_id = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        label='Contract',
    )
    service_id = DynamicModelMultipleChoiceField(
        queryset=Service.objects.all(),
        required=False,
        label='Service',
    )
    service_offering_owner_contacts_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Owner (Contact)',
    )
    service_offering_owner_contact_groups_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Owner (Contact Group)',
    )
    service_offering_manager_contacts_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Manager (Contact)',
    )
    service_offering_manager_contact_groups_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Manager (Contact Group)',
    )
    business_unit_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Business Unit',
    )
    support_group_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Support Group',
    )
    change_group_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Change Group',
    )
    tenant_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        label='Customer',
    )
    tenant_group_id = DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        label='Customer Group',
    )


class AppServiceFilterForm(NetBoxModelFilterSetForm):
    model = AppService
    lifecycle_id = DynamicModelMultipleChoiceField(
        queryset=Lifecycle.objects.all(),
        required=False,
        label='Lifecycle',
    )
    environment_id = DynamicModelMultipleChoiceField(
        queryset=Environment.objects.all(),
        required=False,
        label='Environment',
    )
    service_offering_id = DynamicModelMultipleChoiceField(
        queryset=ServiceOffering.objects.all(),
        required=False,
        label='Service Offering',
    )
    business_unit_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Business Unit',
    )
    support_group_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Support Group',
    )
    change_group_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Change Group',
    )
    sla_id = DynamicModelMultipleChoiceField(
        queryset=SLA.objects.all(),
        required=False,
        label='SLA',
    )
    owned_by_contact_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label='Owner (Contact)',
    )
    owned_by_contact_group_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='Owner (Contact Group)',
    )
    operation_time_id = DynamicModelMultipleChoiceField(
        queryset=OperationTime.objects.all(),
        required=False,
        label='Operation Time',
    )
    availability_id = DynamicModelMultipleChoiceField(
        queryset=Availability.objects.all(),
        required=False,
        label='Availability',
    )
    mtat_id = DynamicModelMultipleChoiceField(
        queryset=MTAT.objects.all(),
        required=False,
        label='MTAT',
    )
    service_criticality_id = DynamicModelMultipleChoiceField(
        queryset=Criticality.objects.all(),
        required=False,
        label='Service Criticality',
    )
    tenant_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        label='Customer',
    )
    tenant_group_id = DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        label='Customer Group',
    )


#
# Report forms
#


class OfferingsTreeFilterForm(forms.Form):
    """Filters for the read-only Portfolio -> Service -> Service Offering ->
    Application Service -> Technical CI tree (views.OfferingsTreeView). Not
    a ModelForm/FilterSet — this drives a hand-built tree, not a table.

    Every field is optional; picking one narrows the tree to whatever
    branch(es) it belongs to while still showing the full ancestor path
    down to it, rather than hiding everything else in isolation. There's no
    single combined "Technical CI" field: NetBox's DynamicModelChoiceField
    is bound to one model's API endpoint each, so a Device/VM/Cluster/
    Cluster Group picker can't be one literal dropdown — these four fields
    are grouped under one "Technical CI" heading in the template instead.
    """

    tenant = DynamicModelChoiceField(queryset=Tenant.objects.all(), required=False)
    portfolio = DynamicModelChoiceField(queryset=Portfolio.objects.all(), required=False, label='Service Portfolio')
    service = DynamicModelChoiceField(queryset=Service.objects.all(), required=False)
    service_offering = DynamicModelChoiceField(
        queryset=ServiceOffering.objects.all(),
        required=False,
        # Once a Tenant is picked, the live dropdown narrows to just that
        # tenant's own offerings instead of all of them — same
        # query_params cascading pattern as e.g. PortfolioForm's
        # portfolio_owner_contacts/portfolio_owner_contact_groups pair.
        query_params={'tenant_id': '$tenant'},
    )
    app_service = DynamicModelChoiceField(
        queryset=AppService.objects.all(), required=False, label='Application Service'
    )
    device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    virtual_machine = DynamicModelChoiceField(queryset=VirtualMachine.objects.all(), required=False)
    cluster = DynamicModelChoiceField(queryset=Cluster.objects.all(), required=False)
    cluster_group = DynamicModelChoiceField(queryset=ClusterGroup.objects.all(), required=False)
