from dcim.models import Device
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel, OrganizationalModel, PrimaryModel
from tenancy.models import Contact, ContactGroup, Tenant, TenantGroup
from virtualization.models import Cluster, ClusterGroup, VirtualMachine

from .choices import TimeUnitChoices

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
)


#
# Support / lookup models
#


class Lifecycle(OrganizationalModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)

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


class ServiceOffering(PrimaryModel):
    owner = models.ForeignKey(to='users.Owner', on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    name = models.CharField(max_length=150)
    contract_number = models.CharField(max_length=100, verbose_name='Contract Number')
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
    service_offering = models.ManyToManyField(
        to=ServiceOffering,
        related_name='app_services',
        blank=False,
        verbose_name='Service Offerings',
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
    owned_by = models.ManyToManyField(
        to=ContactGroup,
        related_name='+',
        blank=False,
        verbose_name='Owned by',
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
    # automation assigning just a CI Function up front and leaving the rest
    # for later. Two different mechanisms are involved: ci_function/
    # lifecycle also need null=True (they're FKs — an unfilled FK is a
    # NOT NULL DB column otherwise, so even that initial empty save would
    # fail); business_unit/support_group/change_group are ManyToManyFields,
    # which are never DB-required regardless of blank, but DRF's serializer
    # (fields='__all__') still marks a field required=True based on
    # model-field blank unless it's explicitly True.
    ci_function = models.ForeignKey(
        to=CIFunction,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='CI Function',
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
