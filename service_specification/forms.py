from django.core.exceptions import ValidationError
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm, OrganizationalModelForm, PrimaryModelForm
from tenancy.models import Contact, ContactGroup, Tenant, TenantGroup
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField
from utilities.forms.rendering import FieldSet

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

__all__ = (
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
)


#
# Support / lookup model forms
#


class LifecycleForm(OrganizationalModelForm):
    class Meta:
        model = Lifecycle
        fields = ('name', 'slug', 'description', 'tags', 'comments')


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
    lifecycle = DynamicModelChoiceField(queryset=Lifecycle.objects.all(), required=True)
    portfolio_owner_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    portfolio_owner_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={'group_id': '$portfolio_owner_contact_groups'},
        help_text='Required: select at least one Contact or Contact Group.',
    )
    portfolio_manager_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    portfolio_manager_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={'group_id': '$portfolio_manager_contact_groups'},
        help_text='Required: select at least one Contact or Contact Group.',
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
    lifecycle = DynamicModelChoiceField(queryset=Lifecycle.objects.all(), required=True)
    service_portfolio = DynamicModelMultipleChoiceField(queryset=Portfolio.objects.all(), required=True)
    service_owner_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    service_owner_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    service_manager_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    service_manager_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    business_unit = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    support_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    change_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    ci_function = DynamicModelChoiceField(queryset=CIFunction.objects.all(), required=False)

    fieldsets = (
        FieldSet('name', 'lifecycle', 'service_portfolio', 'description', 'tags', name='Service'),
        FieldSet('service_owner_contacts', 'service_owner_contact_groups', name='Owner'),
        FieldSet('service_manager_contacts', 'service_manager_contact_groups', name='Manager'),
        FieldSet('business_unit', 'support_group', 'change_group', name='Organization'),
        FieldSet('ci_function', name='CI Function'),
    )

    class Meta:
        model = Service
        fields = (
            'name',
            'lifecycle',
            'service_portfolio',
            'service_owner_contacts',
            'service_owner_contact_groups',
            'service_manager_contacts',
            'service_manager_contact_groups',
            'business_unit',
            'support_group',
            'change_group',
            'ci_function',
            'description',
            'tags',
            'comments',
        )

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


class ServiceOfferingForm(PrimaryModelForm):
    lifecycle = DynamicModelChoiceField(queryset=Lifecycle.objects.all(), required=True)
    service = DynamicModelMultipleChoiceField(queryset=Service.objects.all(), required=True)
    service_offering_owner_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    service_offering_owner_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    service_offering_manager_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    service_offering_manager_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        help_text='Required: select at least one Contact or Contact Group.',
    )
    business_unit = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    support_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    change_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    tenant = DynamicModelMultipleChoiceField(queryset=Tenant.objects.all(), required=False)
    tenant_group = DynamicModelMultipleChoiceField(queryset=TenantGroup.objects.all(), required=False)

    fieldsets = (
        FieldSet(
            'name',
            'contract_number',
            'lifecycle',
            'service',
            'description',
            'tags',
            name='Service Offering',
        ),
        FieldSet(
            'service_offering_owner_contacts',
            'service_offering_owner_contact_groups',
            name='Owner',
        ),
        FieldSet(
            'service_offering_manager_contacts',
            'service_offering_manager_contact_groups',
            name='Manager',
        ),
        FieldSet('business_unit', 'support_group', 'change_group', name='Organization'),
        FieldSet('tenant', 'tenant_group', name='Customer'),
    )

    class Meta:
        model = ServiceOffering
        fields = (
            'name',
            'contract_number',
            'lifecycle',
            'service',
            'service_offering_owner_contacts',
            'service_offering_owner_contact_groups',
            'service_offering_manager_contacts',
            'service_offering_manager_contact_groups',
            'business_unit',
            'support_group',
            'change_group',
            'tenant',
            'tenant_group',
            'description',
            'tags',
            'comments',
        )

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
    environment = DynamicModelChoiceField(queryset=Environment.objects.all(), required=True)
    lifecycle = DynamicModelChoiceField(queryset=Lifecycle.objects.all(), required=True)
    service_offering = DynamicModelMultipleChoiceField(queryset=ServiceOffering.objects.all(), required=True)
    business_unit = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    support_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    change_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    sla = DynamicModelMultipleChoiceField(queryset=SLA.objects.all(), required=True)
    owned_by = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    operation_time = DynamicModelMultipleChoiceField(queryset=OperationTime.objects.all(), required=True)
    availability = DynamicModelMultipleChoiceField(queryset=Availability.objects.all(), required=True)
    mtat = DynamicModelMultipleChoiceField(queryset=MTAT.objects.all(), required=True, label='MTAT')
    service_criticality = DynamicModelMultipleChoiceField(queryset=Criticality.objects.all(), required=True)
    tenant = DynamicModelMultipleChoiceField(queryset=Tenant.objects.all(), required=False)
    tenant_group = DynamicModelMultipleChoiceField(queryset=TenantGroup.objects.all(), required=False)

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
        FieldSet('business_unit', 'support_group', 'change_group', 'owned_by', name='Organization'),
        FieldSet('sla', 'operation_time', 'availability', 'mtat', 'service_criticality', name='Service Levels'),
        FieldSet('accepted_downtime', 'ttr', 'rpo', 'rto', 'bcm', name='Recovery & Continuity'),
        FieldSet('tenant', 'tenant_group', name='Customer'),
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
            'owned_by',
            'operation_time',
            'availability',
            'mtat',
            'ttr',
            'service_criticality',
            'rpo',
            'rto',
            'bcm',
            'tenant',
            'tenant_group',
            'description',
            'tags',
            'comments',
        )


#
# Service Specification info forms — one per core NetBox object type
# (Device/VirtualMachine/Cluster/ClusterGroup), built off a shared factory
# since the editable fields are identical across all four; only the model
# (and its non-editable parent-object field, set by the view rather than
# this form) differs. See models.py's ServiceSpecificationInfoBase.
#


def _make_service_info_form(model):
    class ServiceInfoForm(NetBoxModelForm):
        ci_function = DynamicModelChoiceField(queryset=CIFunction.objects.all(), required=True)
        lifecycle = DynamicModelChoiceField(queryset=Lifecycle.objects.all(), required=True)
        business_unit = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
        support_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
        change_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)

        fieldsets = (
            FieldSet('ci_function', 'lifecycle', 'tags', name='Service Specification'),
            FieldSet('business_unit', 'support_group', 'change_group', name='Organization'),
        )

        class Meta:
            fields = ('ci_function', 'lifecycle', 'business_unit', 'support_group', 'change_group', 'tags')

    ServiceInfoForm.Meta.model = model
    ServiceInfoForm.__name__ = ServiceInfoForm.__qualname__ = f'{model.__name__}Form'
    return ServiceInfoForm


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


class PortfolioFilterForm(NetBoxModelFilterSetForm):
    model = Portfolio
    lifecycle_id = DynamicModelMultipleChoiceField(
        queryset=Lifecycle.objects.all(),
        required=False,
        label='Lifecycle',
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


class ServiceOfferingFilterForm(NetBoxModelFilterSetForm):
    model = ServiceOffering
    lifecycle_id = DynamicModelMultipleChoiceField(
        queryset=Lifecycle.objects.all(),
        required=False,
        label='Lifecycle',
    )
    service_id = DynamicModelMultipleChoiceField(
        queryset=Service.objects.all(),
        required=False,
        label='Service',
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
