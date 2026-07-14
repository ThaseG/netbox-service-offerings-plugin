from dcim.models import Device
from django.core.exceptions import ValidationError
from netbox.forms import NetBoxModelFilterSetForm, OrganizationalModelForm, PrimaryModelForm
from tenancy.models import Contact, ContactGroup, Tenant, TenantGroup
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField
from utilities.forms.rendering import FieldSet
from virtualization.models import Cluster, ClusterGroup, VirtualMachine

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

__all__ = (
    'PortfolioForm',
    'ServiceForm',
    'ServiceOfferingForm',
    'AppServiceForm',
    'TechCIForm',
    'LifecycleForm',
    'SLAForm',
    'OperationTimeForm',
    'AvailabilityForm',
    'CriticalityForm',
    'EnvironmentForm',
    'MTATForm',
    'PortfolioFilterForm',
    'ServiceFilterForm',
    'ServiceOfferingFilterForm',
    'AppServiceFilterForm',
    'TechCIFilterForm',
    'LifecycleFilterForm',
    'SLAFilterForm',
    'OperationTimeFilterForm',
    'AvailabilityFilterForm',
    'CriticalityFilterForm',
    'EnvironmentFilterForm',
    'MTATFilterForm',
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


#
# Core model forms
#


class PortfolioForm(PrimaryModelForm):
    lifecycle = DynamicModelChoiceField(queryset=Lifecycle.objects.all(), required=True)
    portfolio_owner_contacts = DynamicModelMultipleChoiceField(queryset=Contact.objects.all(), required=False)
    portfolio_owner_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
    )
    portfolio_manager_contacts = DynamicModelMultipleChoiceField(queryset=Contact.objects.all(), required=False)
    portfolio_manager_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
    )

    fieldsets = (
        FieldSet('name', 'lifecycle', 'description', 'tags', name='Portfolio'),
        FieldSet('portfolio_owner_contacts', 'portfolio_owner_contact_groups', name='Owner'),
        FieldSet('portfolio_manager_contacts', 'portfolio_manager_contact_groups', name='Manager'),
    )

    class Meta:
        model = Portfolio
        fields = (
            'name',
            'lifecycle',
            'portfolio_owner_contacts',
            'portfolio_owner_contact_groups',
            'portfolio_manager_contacts',
            'portfolio_manager_contact_groups',
            'description',
            'tags',
            'comments',
        )

    def clean(self):
        cleaned_data = super().clean()
        if not (cleaned_data.get('portfolio_owner_contacts') or cleaned_data.get('portfolio_owner_contact_groups')):
            raise ValidationError('Select at least one Portfolio Owner (a contact or a contact group).')
        if not (cleaned_data.get('portfolio_manager_contacts') or cleaned_data.get('portfolio_manager_contact_groups')):
            raise ValidationError('Select at least one Portfolio Manager (a contact or a contact group).')
        return cleaned_data


class ServiceForm(PrimaryModelForm):
    lifecycle = DynamicModelChoiceField(queryset=Lifecycle.objects.all(), required=True)
    service_portfolio = DynamicModelMultipleChoiceField(queryset=Portfolio.objects.all(), required=True)
    service_owner_contacts = DynamicModelMultipleChoiceField(queryset=Contact.objects.all(), required=False)
    service_owner_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
    )
    service_manager_contacts = DynamicModelMultipleChoiceField(queryset=Contact.objects.all(), required=False)
    service_manager_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
    )
    business_unit = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    support_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    change_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    ci_function = DynamicModelMultipleChoiceField(queryset=TechCI.objects.all(), required=False)

    fieldsets = (
        FieldSet('name', 'lifecycle', 'service_portfolio', 'description', 'tags', name='Service'),
        FieldSet('service_owner_contacts', 'service_owner_contact_groups', name='Owner'),
        FieldSet('service_manager_contacts', 'service_manager_contact_groups', name='Manager'),
        FieldSet('business_unit', 'support_group', 'change_group', name='Organization'),
        FieldSet('ci_function', name='Technical CIs'),
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
        cleaned_data = super().clean()
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
    )
    service_offering_owner_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
    )
    service_offering_manager_contacts = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
    )
    service_offering_manager_contact_groups = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
    )
    business_unit = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    support_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    change_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    ci_function = DynamicModelMultipleChoiceField(queryset=TechCI.objects.all(), required=False)
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
        FieldSet('ci_function', name='Technical CIs'),
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
            'ci_function',
            'tenant',
            'tenant_group',
            'description',
            'tags',
            'comments',
        )

    def clean(self):
        cleaned_data = super().clean()
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
    mtat = DynamicModelMultipleChoiceField(queryset=MTAT.objects.all(), required=True)
    service_criticality = DynamicModelMultipleChoiceField(queryset=Criticality.objects.all(), required=True)
    ci_function = DynamicModelMultipleChoiceField(queryset=TechCI.objects.all(), required=False)
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
        FieldSet('ci_function', name='Technical CIs'),
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
            'ci_function',
            'tenant',
            'tenant_group',
            'description',
            'tags',
            'comments',
        )


class TechCIForm(PrimaryModelForm):
    lifecycle = DynamicModelChoiceField(queryset=Lifecycle.objects.all(), required=True)
    business_unit = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    support_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    change_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=True)
    device = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), required=False)
    virtual_machine = DynamicModelMultipleChoiceField(queryset=VirtualMachine.objects.all(), required=False)
    cluster = DynamicModelMultipleChoiceField(queryset=Cluster.objects.all(), required=False)
    cluster_group = DynamicModelMultipleChoiceField(queryset=ClusterGroup.objects.all(), required=False)
    tenant = DynamicModelMultipleChoiceField(queryset=Tenant.objects.all(), required=False)
    tenant_group = DynamicModelMultipleChoiceField(queryset=TenantGroup.objects.all(), required=False)

    fieldsets = (
        FieldSet('name', 'function', 'lifecycle', 'description', 'tags', name='Technical CI'),
        FieldSet('business_unit', 'support_group', 'change_group', name='Organization'),
        FieldSet('device', 'virtual_machine', 'cluster', 'cluster_group', name='Infrastructure'),
        FieldSet('tenant', 'tenant_group', name='Customer'),
    )

    class Meta:
        model = TechCI
        fields = (
            'name',
            'function',
            'lifecycle',
            'business_unit',
            'support_group',
            'change_group',
            'device',
            'virtual_machine',
            'cluster',
            'cluster_group',
            'tenant',
            'tenant_group',
            'description',
            'tags',
            'comments',
        )


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


class TechCIFilterForm(NetBoxModelFilterSetForm):
    model = TechCI
    lifecycle_id = DynamicModelMultipleChoiceField(
        queryset=Lifecycle.objects.all(),
        required=False,
        label='Lifecycle',
    )
