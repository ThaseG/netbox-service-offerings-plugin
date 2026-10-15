import datetime
import re

from dcim.models import Device, Manufacturer
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse
from netbox.choices import ColorChoices
from netbox.models import NetBoxModel, OrganizationalModel, PrimaryModel
from tenancy.models import Contact, ContactGroup, Tenant, TenantGroup
from utilities.fields import ColorField
from virtualization.models import Cluster, ClusterGroup, VirtualMachine

from .choices import (
    RateCardIntervalChoices,
    ThreeCCITypeChoices,
    ThreeCConditionChoices,
    ThreeCKPIChoices,
    ThreeCRuleTypeChoices,
    TimeUnitChoices,
)

# Every FK/M2M field below uses related_name='+': many of these models point
# at the same core NetBox models (ContactGroup in particular is targeted by
# several M2M fields on the same source model), so distinct reverse
# accessors would need inventing for every one of them. '+' disables the
# reverse relation; querying the other direction (e.g. "services with this
# lifecycle") is still done via Service.objects.filter(lifecycle=...).
#
# Every model below also explicitly re-declares the `owner` field it
# inherits from NetBoxModel's OwnerMixin, again with related_name='+'.
# OwnerMixin's own definition has no related_name, defaulting to
# `<model>_set` on users.Owner — which is only unique *within* an app.
# service_specification.Service silently collided with NetBox core's own ipam.Service this
# way (both wanting `Owner.service_set`), and Django refused to boot until
# it was fixed. Overriding it here on every model, not just Service,
# closes off the same failure mode against any future name collision.

__all__ = (
    'Contract',
    'ContractRateCard',
    'Portfolio',
    'Service',
    'ServiceOffering',
    'AppService',
    'Lifecycle',
    'SLA',
    'OperationTime',
    'Availability',
    'Criticality',
    'Environment',
    'MTAT',
    'CIFunction',
    'DeviceServiceInfo',
    'VirtualMachineServiceInfo',
    'ClusterServiceInfo',
    'ClusterGroupServiceInfo',
    'ThreeCRule',
    'ThreeCSettings',
    'ThreeCSnapshot',
    'ThreeCFinding',
)


#
# Support / lookup models
#


class Lifecycle(OrganizationalModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    color = ColorField(default=ColorChoices.COLOR_GREY, verbose_name='Color')

    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Lifecycle'
        verbose_name_plural = 'Service Lifecycle Managements'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class SLA(OrganizationalModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    sla_definition = models.CharField(
        max_length=500,
        verbose_name='SLA Definition',
    )

    class Meta(OrganizationalModel.Meta):
        verbose_name = 'SLA'
        verbose_name_plural = 'SLAs'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class OperationTime(OrganizationalModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)

    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Operation Time'
        verbose_name_plural = 'Operation Times'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class Availability(OrganizationalModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)

    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Availability'
        verbose_name_plural = 'Availabilities'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class Criticality(OrganizationalModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)

    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Criticality'
        verbose_name_plural = 'Criticalities'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class Environment(OrganizationalModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)

    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Environment'
        verbose_name_plural = 'Environments'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class MTAT(OrganizationalModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    value = models.PositiveIntegerField(
        verbose_name='Value',
    )
    unit = models.CharField(
        max_length=30,
        choices=TimeUnitChoices,
        verbose_name='Time Unit',
    )

    class Meta(OrganizationalModel.Meta):
        verbose_name = 'MTAT'
        verbose_name_plural = 'MTATs'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class CIFunction(OrganizationalModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)

    class Meta(OrganizationalModel.Meta):
        verbose_name = 'CI Function'
        verbose_name_plural = 'CI Functions'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


#
# Core Service Specification models
#


class Portfolio(PrimaryModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    name = models.CharField(max_length=150)
    portfolio_owner_contacts = models.ManyToManyField(
        to=Contact,
        related_name='+',
        blank=True,
        verbose_name='Portfolio Owner (Contacts)',
    )
    portfolio_owner_contact_groups = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=True,
        verbose_name='Portfolio Owner (Contact Groups)',
    )
    portfolio_manager_contacts = models.ManyToManyField(
        to=Contact,
        related_name='+',
        blank=True,
        verbose_name='Portfolio Manager (Contacts)',
    )
    portfolio_manager_contact_groups = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=True,
        verbose_name='Portfolio Manager (Contact Groups)',
    )
    lifecycle = models.ForeignKey(
        to=Lifecycle,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Service Lifecycle Management',
    )

    class Meta(PrimaryModel.Meta):
        ordering = ('name',)
        verbose_name = 'Service Portfolio'
        verbose_name_plural = 'Service Portfolios'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class Service(PrimaryModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    name = models.CharField(max_length=150)
    service_owner_contacts = models.ManyToManyField(
        to=Contact,
        related_name='+',
        blank=True,
        verbose_name='Service Owner (Contacts)',
    )
    service_owner_contact_groups = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=True,
        verbose_name='Service Owner (Contact Groups)',
    )
    service_manager_contacts = models.ManyToManyField(
        to=Contact,
        related_name='+',
        blank=True,
        verbose_name='Service Manager (Contacts)',
    )
    service_manager_contact_groups = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=True,
        verbose_name='Service Manager (Contact Groups)',
    )
    lifecycle = models.ForeignKey(
        to=Lifecycle,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Service Lifecycle Management',
    )
    service_portfolio = models.ManyToManyField(
        to=Portfolio,
        related_name='services',
        blank=False,
        verbose_name='Service Portfolios',
    )
    business_unit = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Business Unit',
    )
    support_group = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Support Group',
    )
    change_group = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Change Group',
    )
    ci_function = models.ForeignKey(
        to=CIFunction,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='CI Function',
    )

    class Meta(PrimaryModel.Meta):
        ordering = ('name',)
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class Contract(PrimaryModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    contract_number = models.CharField(max_length=100, verbose_name='Contract Number')
    external_reference = models.CharField(max_length=100, blank=True, verbose_name='External Reference')
    short_description = models.CharField(max_length=300, blank=True, verbose_name='Short Description')
    legacy_contract = models.CharField(max_length=100, blank=True, verbose_name='Legacy Contract')
    project = models.CharField(max_length=150, blank=True, verbose_name='Project')
    parent_contract = models.ForeignKey(
        to='self',
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Parent Contract',
    )
    vendor = models.ForeignKey(
        to=Manufacturer,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Vendor',
    )
    location = models.CharField(max_length=200, blank=True, verbose_name='Location')
    tenant = models.ForeignKey(
        to=Tenant,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Tenant',
    )
    tenant_group = models.ForeignKey(
        to=TenantGroup,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Tenant Group',
    )
    contact_person = models.ManyToManyField(
        to=Contact,
        related_name='+',
        blank=True,
        verbose_name='Contact Person',
    )
    primary_contact = models.ManyToManyField(
        to=Contact,
        related_name='+',
        blank=True,
        verbose_name='Primary Contact',
    )
    contract_manager = models.ManyToManyField(
        to=Contact,
        related_name='+',
        blank=True,
        verbose_name='Contract Manager',
    )
    approver = models.ForeignKey(
        to=Contact,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Approver',
    )
    business_unit = models.ForeignKey(
        to=ContactGroup,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Business Unit',
    )
    contract_starts = models.DateField(blank=True, null=True, verbose_name='Contract Starts')
    contract_ends = models.DateField(blank=True, null=True, verbose_name='Contract Ends')

    class Meta(PrimaryModel.Meta):
        ordering = ('contract_number',)
        verbose_name = 'Contract'
        verbose_name_plural = 'Contracts'

    def __str__(self):
        return self.contract_number

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])

    @property
    def status(self):
        # Deliberately not a stored field: a Contract with zero active Rate
        # Cards must always read as Inactive, including the instant the
        # last one is deleted or deactivated elsewhere — a stored field
        # would only get re-validated when the Contract itself is next
        # saved, and could otherwise sit stale. See ContractRateCard.active.
        if self.rate_cards.filter(active=True).exists():
            return 'Active'
        return 'Inactive'


class ContractRateCard(PrimaryModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    # CASCADE, not PROTECT: a Rate Card has no independent existence outside
    # its Contract (unlike every other FK in this file, which points at a
    # shared/independent object). related_name is a real name, not '+' —
    # it's the only FK targeting Contract this way, and Contract.status /
    # the Contract detail page's rollup panel both read it directly.
    contract = models.ForeignKey(
        to=Contract,
        on_delete=models.CASCADE,
        related_name='rate_cards',
        verbose_name='Contract',
    )
    contract_position_number = models.CharField(max_length=100, verbose_name='Contract Position Number')
    # No tenant/tenant_group here: Customer is set once, on the parent
    # Contract, and shown read-only on this object's detail page (see
    # views.py's ContractRateCard layout) rather than duplicated here —
    # same reasoning as AppService's own Customer fields (see models.py's
    # AppService for the equivalent comment).
    active = models.BooleanField(default=True, verbose_name='Active')
    short_description = models.CharField(max_length=300, blank=True, verbose_name='Short Description')
    start_date = models.DateField(blank=True, null=True, verbose_name='Start Date')
    end_date = models.DateField(blank=True, null=True, verbose_name='End Date')
    order_number = models.CharField(max_length=100, blank=True, verbose_name='Order Number')
    base_costs = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Base Costs')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Hourly Rate')
    hours_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Hours Spend')
    interval = models.CharField(
        max_length=30,
        choices=RateCardIntervalChoices,
        default=RateCardIntervalChoices.INTERVAL_MONTHLY,
        verbose_name='Interval',
    )
    billing = models.BooleanField(default=False, verbose_name='Billing')
    project = models.CharField(max_length=150, blank=True, verbose_name='Project')

    class Meta(PrimaryModel.Meta):
        ordering = ('contract', 'contract_position_number')
        verbose_name = 'Contract Rate Card'
        verbose_name_plural = 'Contract Rate Cards'

    def __str__(self):
        return self.contract_position_number

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])

    @property
    def total_costs(self):
        return self.base_costs + self.hourly_rate * self.hours_spend


class ServiceOffering(PrimaryModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    name = models.CharField(max_length=150)
    contract = models.ForeignKey(
        to=Contract,
        on_delete=models.PROTECT,
        related_name='service_offerings',
        blank=True,
        null=True,
        verbose_name='Contract',
    )
    service_offering_owner_contacts = models.ManyToManyField(
        to=Contact,
        related_name='+',
        blank=True,
        verbose_name='Service Offering Owner (Contacts)',
    )
    service_offering_owner_contact_groups = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=True,
        verbose_name='Service Offering Owner (Contact Groups)',
    )
    service_offering_manager_contacts = models.ManyToManyField(
        to=Contact,
        related_name='+',
        blank=True,
        verbose_name='Service Offering Manager (Contacts)',
    )
    service_offering_manager_contact_groups = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=True,
        verbose_name='Service Offering Manager (Contact Groups)',
    )
    lifecycle = models.ForeignKey(
        to=Lifecycle,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Service Lifecycle Management',
    )
    service = models.ManyToManyField(
        to=Service,
        related_name='service_offerings',
        blank=False,
        verbose_name='Services',
    )
    business_unit = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Business Unit',
    )
    support_group = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Support Group',
    )
    change_group = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Change Group',
    )
    tenant = models.ManyToManyField(
        to=Tenant,
        related_name='+',
        blank=True,
        verbose_name='Customer',
    )
    tenant_group = models.ManyToManyField(
        to=TenantGroup,
        related_name='+',
        blank=True,
        verbose_name='Customer Group',
    )

    class Meta(PrimaryModel.Meta):
        ordering = ('name',)
        verbose_name = 'Service Offering'
        verbose_name_plural = 'Service Offerings'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class AppService(PrimaryModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    name = models.CharField(max_length=150)
    environment = models.ForeignKey(
        to=Environment,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Environment',
    )
    lifecycle = models.ForeignKey(
        to=Lifecycle,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Service Lifecycle Management',
    )
    # A ServiceOffering backs at most one AppService — enforced here (not
    # just filtered out of the form's dropdown) so it can't be bypassed via
    # the REST API/GraphQL either. See AppServiceForm for the matching
    # dropdown filter.
    service_offering = models.OneToOneField(
        to=ServiceOffering,
        on_delete=models.PROTECT,
        related_name='app_service',
        verbose_name='Service Offering',
    )
    business_unit = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Business Unit',
    )
    support_group = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Support Group',
    )
    change_group = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Change Group',
    )
    sla = models.ManyToManyField(
        to=SLA,
        related_name='+',
        blank=False,
        verbose_name='SLAs',
    )
    accepted_downtime = models.PositiveIntegerField(verbose_name='Accepted Downtime (hours)')
    # Owner is a single choice of *either* a Contact *or* a Contact Group,
    # not both — see AppServiceForm.clean() for the "exactly one" rule.
    # Modeled as two plain nullable FKs rather than a single polymorphic
    # (GenericForeignKey) field: much simpler to query/filter/serialize,
    # and a natural fit for a form with two independent single-select
    # dropdowns where exactly one is expected to be filled in.
    owned_by_contact = models.ForeignKey(
        to=Contact,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Owner (Contact)',
    )
    owned_by_contact_group = models.ForeignKey(
        to=ContactGroup,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Owner (Contact Group)',
    )
    operation_time = models.ManyToManyField(
        to=OperationTime,
        related_name='+',
        blank=False,
        verbose_name='Operation Time',
    )
    availability = models.ManyToManyField(
        to=Availability,
        related_name='+',
        blank=False,
        verbose_name='Availability',
    )
    mtat = models.ManyToManyField(
        to=MTAT,
        related_name='+',
        blank=False,
        verbose_name='MTAT',
    )
    ttr = models.PositiveIntegerField(verbose_name='TTR')
    service_criticality = models.ManyToManyField(
        to=Criticality,
        related_name='+',
        blank=False,
        verbose_name='Service Criticality',
    )
    rpo = models.PositiveIntegerField(verbose_name='RPO (hours)')
    rto = models.PositiveIntegerField(verbose_name='RTO (hours)')
    bcm = models.PositiveIntegerField(verbose_name='BCM -1')
    # No tenant/tenant_group here: Customer is set once, on the parent
    # ServiceOffering, and shown read-only on this object's detail page
    # (see views.py's AppService layout) rather than duplicated here.

    class Meta(PrimaryModel.Meta):
        ordering = ('name',)
        verbose_name = 'Application Service'
        verbose_name_plural = 'Application Services'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


#
# Service Specification info attached directly to core NetBox infrastructure
# objects (Device, VirtualMachine, Cluster, ClusterGroup). Plugins can't add
# real database fields to NetBox's own models, so each of these is a
# separate table in a OneToOne relationship with its core object, surfaced
# as a "Service Specification" tab on that object's own detail page (see
# views.py) rather than as a top-level navigable model of its own.
#


class ServiceSpecificationInfoBase(NetBoxModel):
    # Every field here is blank=True (despite being required=True on the
    # form — see forms.py's _make_service_info_form) so a row can be created
    # or edited with only some fields filled in — e.g. views.py lazily
    # persisting an empty placeholder row the first time a Device/VM/
    # Cluster/ClusterGroup's "Service Specification" tab is viewed, or an
    # automation assigning just Business Unit up front and leaving the rest
    # for later. lifecycle also needs null=True (it's an FK — an unfilled FK
    # is a NOT NULL DB column otherwise, so even that initial empty save
    # would fail); application_services/business_unit/support_group/
    # change_group are ManyToManyFields, which are never DB-required
    # regardless of blank, but DRF's serializer (fields='__all__') still
    # marks a field required=True based on model-field blank unless it's
    # explicitly True.
    #
    # There's no direct CI Function field: it's derived read-only from
    # whichever AppService(s) this component supports (AppService ->
    # ServiceOffering -> Service -> CIFunction — see views.py's
    # _make_service_info_views rollup panel), rather than set directly here.
    application_services = models.ManyToManyField(
        to=AppService,
        related_name='+',
        blank=True,
        verbose_name='Application Services',
    )
    lifecycle = models.ForeignKey(
        to=Lifecycle,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Service Lifecycle Management',
    )
    business_unit = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=True,
        verbose_name='Business Unit',
    )
    support_group = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=True,
        verbose_name='Support Group',
    )
    change_group = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=True,
        verbose_name='Change Group',
    )

    class Meta:
        abstract = True


class DeviceServiceInfo(ServiceSpecificationInfoBase):
    device = models.OneToOneField(
        to=Device,
        on_delete=models.CASCADE,
        related_name='service_specification_info',
    )

    class Meta:
        verbose_name = 'Device Service Info'
        verbose_name_plural = 'Device Service Info'

    def __str__(self):
        return str(self.device)

    @property
    def parent(self):
        return self.device

    def get_absolute_url(self):
        return self.device.get_absolute_url()


class VirtualMachineServiceInfo(ServiceSpecificationInfoBase):
    virtual_machine = models.OneToOneField(
        to=VirtualMachine,
        on_delete=models.CASCADE,
        related_name='service_specification_info',
    )

    class Meta:
        verbose_name = 'Virtual Machine Service Info'
        verbose_name_plural = 'Virtual Machine Service Info'

    def __str__(self):
        return str(self.virtual_machine)

    @property
    def parent(self):
        return self.virtual_machine

    def get_absolute_url(self):
        return self.virtual_machine.get_absolute_url()


class ClusterServiceInfo(ServiceSpecificationInfoBase):
    cluster = models.OneToOneField(
        to=Cluster,
        on_delete=models.CASCADE,
        related_name='service_specification_info',
    )

    class Meta:
        verbose_name = 'Cluster Service Info'
        verbose_name_plural = 'Cluster Service Info'

    def __str__(self):
        return str(self.cluster)

    @property
    def parent(self):
        return self.cluster

    def get_absolute_url(self):
        return self.cluster.get_absolute_url()


class ClusterGroupServiceInfo(ServiceSpecificationInfoBase):
    cluster_group = models.OneToOneField(
        to=ClusterGroup,
        on_delete=models.CASCADE,
        related_name='service_specification_info',
    )

    class Meta:
        verbose_name = 'Cluster Group Service Info'
        verbose_name_plural = 'Cluster Group Service Info'

    def __str__(self):
        return str(self.cluster_group)

    @property
    def parent(self):
        return self.cluster_group

    def get_absolute_url(self):
        return self.cluster_group.get_absolute_url()


#
# 3C (CMDB health: Completeness, Correctness, Compliance)
#
# ThreeCRule and ThreeCSettings are the user-editable setup; ThreeCSnapshot
# and ThreeCFinding are written only by the scheduled health job (see
# jobs.py / three_c.py) and are read-only everywhere else. Snapshots are
# kept for the trend charts; findings (one row per failing CI per KPI) are
# only kept for the most recent snapshot.
#


def _three_c_rule_kpi(rule_type):
    if rule_type == ThreeCRuleTypeChoices.TYPE_COMPLIANCE:
        return ThreeCKPIChoices.KPI_COMPLIANCE
    return ThreeCKPIChoices.KPI_COMPLETENESS


class ThreeCRule(NetBoxModel):
    name = models.CharField(max_length=100, verbose_name='Name')
    rule_type = models.CharField(max_length=30, choices=ThreeCRuleTypeChoices, verbose_name='Rule Type')
    ci_type = models.CharField(max_length=30, choices=ThreeCCITypeChoices, verbose_name='CI Class')
    # A field path resolved by three_c.resolve_parameter() — a plain model
    # field name ('serial'), 'cf_<name>' for a custom field, or
    # 'service_info__<field>' for the CI's Service Specification tab.
    # Validated against three_c.get_parameter_choices() in clean() rather
    # than via static `choices`, since custom fields come and go at runtime.
    parameter = models.CharField(max_length=100, verbose_name='Parameter')
    condition = models.CharField(
        max_length=30,
        choices=ThreeCConditionChoices,
        default=ThreeCConditionChoices.CONDITION_NOT_EMPTY,
        verbose_name='Condition',
    )
    value = models.CharField(max_length=500, blank=True, verbose_name='Value')
    enabled = models.BooleanField(default=True, verbose_name='Enabled')
    description = models.CharField(max_length=200, blank=True, verbose_name='Description')

    class Meta:
        ordering = ('ci_type', 'rule_type', 'name')
        verbose_name = '3C Rule'
        verbose_name_plural = '3C Rules'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])

    @property
    def kpi(self):
        return _three_c_rule_kpi(self.rule_type)

    def get_rule_type_color(self):
        return ThreeCRuleTypeChoices.colors.get(self.rule_type)

    @property
    def parameter_label(self):
        # Imported here: three_c imports this module.
        from .three_c import get_parameter_label

        return get_parameter_label(self.ci_type, self.parameter)

    def clean(self):
        super().clean()
        from .three_c import get_parameter_choices

        if self.ci_type and self.parameter:
            valid = {key for key, _label in get_parameter_choices(self.ci_type)}
            if self.parameter not in valid:
                raise ValidationError(
                    {'parameter': f'"{self.parameter}" is not a parameter of {self.get_ci_type_display()}.'}
                )

        # Completeness rules only ever ask "is this filled in?" — any other
        # condition/value would silently be ignored, so normalize instead.
        if self.rule_type in (ThreeCRuleTypeChoices.TYPE_REQUIRED, ThreeCRuleTypeChoices.TYPE_RECOMMENDED):
            self.condition = ThreeCConditionChoices.CONDITION_NOT_EMPTY
            self.value = ''
            return

        if self.condition in ThreeCConditionChoices.VALUE_REQUIRED and not self.value:
            raise ValidationError({'value': 'This condition needs a value to compare against.'})
        if self.condition not in ThreeCConditionChoices.VALUE_REQUIRED:
            self.value = ''
        if self.condition == ThreeCConditionChoices.CONDITION_REGEX:
            try:
                re.compile(self.value)
            except re.error as e:
                raise ValidationError({'value': f'Invalid regular expression: {e}'})


class ThreeCSettings(NetBoxModel):
    """Singleton (always pk=1 — see load()). Thresholds are failure-rate
    percentages: below `lower` is Best, above `upper` is Critical, anything
    in between (inclusive) is At Risk."""

    completeness_lower = models.PositiveSmallIntegerField(
        default=5, validators=[MaxValueValidator(100)], verbose_name='Completeness: Lower Threshold (%)'
    )
    completeness_upper = models.PositiveSmallIntegerField(
        default=10, validators=[MaxValueValidator(100)], verbose_name='Completeness: Upper Threshold (%)'
    )
    correctness_lower = models.PositiveSmallIntegerField(
        default=5, validators=[MaxValueValidator(100)], verbose_name='Correctness: Lower Threshold (%)'
    )
    correctness_upper = models.PositiveSmallIntegerField(
        default=10, validators=[MaxValueValidator(100)], verbose_name='Correctness: Upper Threshold (%)'
    )
    compliance_lower = models.PositiveSmallIntegerField(
        default=5, validators=[MaxValueValidator(100)], verbose_name='Compliance: Lower Threshold (%)'
    )
    compliance_upper = models.PositiveSmallIntegerField(
        default=10, validators=[MaxValueValidator(100)], verbose_name='Compliance: Upper Threshold (%)'
    )
    composite_lower = models.PositiveSmallIntegerField(
        default=5, validators=[MaxValueValidator(100)], verbose_name='Composite: Lower Threshold (%)'
    )
    composite_upper = models.PositiveSmallIntegerField(
        default=10, validators=[MaxValueValidator(100)], verbose_name='Composite: Upper Threshold (%)'
    )
    relationship_lower = models.PositiveSmallIntegerField(
        default=5, validators=[MaxValueValidator(100)], verbose_name='Relationship Health: Lower Threshold (%)'
    )
    relationship_upper = models.PositiveSmallIntegerField(
        default=10, validators=[MaxValueValidator(100)], verbose_name='Relationship Health: Upper Threshold (%)'
    )
    job_time = models.TimeField(
        default=datetime.time(2, 0),
        verbose_name='Daily Run Time',
        help_text='Local time (NetBox TIME_ZONE) at which the 3C health job runs every day.',
    )
    snapshot_retention_days = models.PositiveIntegerField(
        default=400,
        verbose_name='Snapshot Retention (days)',
        help_text='Snapshots older than this are deleted by the health job. The report charts use the last 90 days.',
    )

    THRESHOLD_KEYS = ('completeness', 'correctness', 'compliance', 'composite', 'relationship')

    class Meta:
        ordering = ('pk',)
        verbose_name = '3C Settings'
        verbose_name_plural = '3C Settings'

    def __str__(self):
        return '3C Settings'

    def get_absolute_url(self):
        return reverse('plugins:service_specification:three_c_report')

    def clean(self):
        super().clean()
        errors = {}
        for key in self.THRESHOLD_KEYS:
            lower, upper = getattr(self, f'{key}_lower'), getattr(self, f'{key}_upper')
            if lower is not None and upper is not None and lower > upper:
                errors[f'{key}_upper'] = 'Upper threshold must be greater than or equal to the lower threshold.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    def thresholds(self, key):
        return getattr(self, f'{key}_lower'), getattr(self, f'{key}_upper')


class ThreeCSnapshot(NetBoxModel):
    # Health percentages (100 - failure rate), each null when nothing was
    # evaluated for that KPI (shown as N/A).
    completeness = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Completeness (%)')
    correctness = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Correctness (%)')
    compliance = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Compliance (%)')
    composite = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Composite (%)')
    relationship_health = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name='Relationship Health (%)'
    )
    ci_count = models.PositiveIntegerField(default=0, verbose_name='CIs Evaluated')
    # {ci_type: {tenant_id or '': {sub_metric: [failures, total]}}} — raw
    # counts, so the report can re-pool them for any CI class/tenant filter
    # (the stored percentages above are the unfiltered totals).
    breakdown = models.JSONField(default=dict, verbose_name='Breakdown')
    # {sub_metric: [failures, total]} for the plugin's own relationships.
    relationship_breakdown = models.JSONField(default=dict, verbose_name='Relationship Breakdown')
    lifecycle_checks = models.BooleanField(
        default=False,
        verbose_name='Lifecycle Checks',
        help_text='Whether netbox-lifecycle was installed, so the lifecycle and support contract checks ran.',
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = '3C Snapshot'
        verbose_name_plural = '3C Snapshots'

    def __str__(self):
        return f'3C Snapshot #{self.pk}'

    def get_absolute_url(self):
        return reverse(f'plugins:service_specification:{self._meta.model_name}', args=[self.pk])


class ThreeCFinding(NetBoxModel):
    """One failing CI for one KPI, with every failure for that KPI joined
    into a single row (e.g. "Missing (required): Serial number, Site")."""

    snapshot = models.ForeignKey(
        to=ThreeCSnapshot,
        on_delete=models.CASCADE,
        related_name='findings',
        verbose_name='Snapshot',
    )
    kpi = models.CharField(max_length=30, choices=ThreeCKPIChoices, verbose_name='KPI')
    ci_type = models.CharField(max_length=30, choices=ThreeCCITypeChoices, verbose_name='CI Class')
    # Plain id + type rather than a GenericForeignKey: the CI may be deleted
    # before the next run, and the row should still read sensibly until then.
    ci_id = models.PositiveBigIntegerField(verbose_name='CI ID')
    ci_name = models.CharField(max_length=255, verbose_name='CI')
    tenant = models.ForeignKey(
        to=Tenant,
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Tenant',
    )
    support_group = models.CharField(max_length=500, blank=True, verbose_name='Support Group')
    ci_last_updated = models.DateTimeField(blank=True, null=True, verbose_name='Last Updated')
    # e.g. ['required', 'recommended'] / ['stale', 'orphan'] / ['audit']
    sub_metrics = models.JSONField(default=list, verbose_name='Sub-metrics')
    failures = models.JSONField(default=list, verbose_name='Failures')

    CI_VIEW_NAMES = {
        ThreeCCITypeChoices.CI_DEVICE: 'dcim:device',
        ThreeCCITypeChoices.CI_VIRTUAL_MACHINE: 'virtualization:virtualmachine',
        ThreeCCITypeChoices.CI_CLUSTER: 'virtualization:cluster',
        ThreeCCITypeChoices.CI_CLUSTER_GROUP: 'virtualization:clustergroup',
    }

    class Meta:
        ordering = ('kpi', 'ci_type', 'ci_name')
        verbose_name = '3C Finding'
        verbose_name_plural = '3C Findings'

    def __str__(self):
        return f'{self.ci_name} ({self.get_kpi_display()})'

    def get_absolute_url(self):
        # Findings have no page of their own — they point at the failing CI.
        return reverse(self.CI_VIEW_NAMES[self.ci_type], args=[self.ci_id])

    def get_kpi_color(self):
        return ThreeCKPIChoices.colors.get(self.kpi)

    @property
    def failures_display(self):
        return '; '.join(self.failures)
