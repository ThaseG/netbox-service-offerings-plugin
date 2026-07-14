from django.db import models
from django.urls import reverse

from dcim.models import Device
from netbox.models import OrganizationalModel, PrimaryModel
from tenancy.models import Contact, ContactGroup, Tenant, TenantGroup
from virtualization.models import Cluster, ClusterGroup, VirtualMachine

from .choices import TimeUnitChoices

# Every FK/M2M field below uses related_name='+': many of these models point
# at the same core NetBox models (ContactGroup in particular is targeted by
# several M2M fields on the same source model), so distinct reverse
# accessors would need inventing for every one of them. '+' disables the
# reverse relation; querying the other direction (e.g. "services with this
# lifecycle") is still done via Service.objects.filter(lifecycle=...).

__all__ = (
    'Portfolio',
    'Service',
    'ServiceOffering',
    'AppService',
    'TechCI',
    'Lifecycle',
    'SLA',
    'OperationTime',
    'Availability',
    'Criticality',
    'Environment',
    'MTAT',
)


#
# Support / lookup models
#

class Lifecycle(OrganizationalModel):
    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Lifecycle'
        verbose_name_plural = 'Lifecycle Managements'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class SLA(OrganizationalModel):
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
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class OperationTime(OrganizationalModel):
    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Operation Time'
        verbose_name_plural = 'Operation Times'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class Availability(OrganizationalModel):
    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Availability'
        verbose_name_plural = 'Availabilities'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class Criticality(OrganizationalModel):
    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Criticality'
        verbose_name_plural = 'Criticalities'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class Environment(OrganizationalModel):
    class Meta(OrganizationalModel.Meta):
        verbose_name = 'Environment'
        verbose_name_plural = 'Environments'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class MTAT(OrganizationalModel):
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
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


#
# Core CSDM models
#

class Portfolio(PrimaryModel):
    name = models.CharField(max_length=150)
    portfolio_owner_contacts = models.ManyToManyField(
        to=Contact, related_name='+', blank=True, verbose_name='Portfolio Owner (Contacts)',
    )
    portfolio_owner_contact_groups = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=True, verbose_name='Portfolio Owner (Contact Groups)',
    )
    portfolio_manager_contacts = models.ManyToManyField(
        to=Contact, related_name='+', blank=True, verbose_name='Portfolio Manager (Contacts)',
    )
    portfolio_manager_contact_groups = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=True, verbose_name='Portfolio Manager (Contact Groups)',
    )
    lifecycle = models.ForeignKey(
        to=Lifecycle, on_delete=models.PROTECT, related_name='+', verbose_name='Lifecycle Management',
    )

    class Meta(PrimaryModel.Meta):
        ordering = ('name',)
        verbose_name = 'Service Portfolio'
        verbose_name_plural = 'Service Portfolios'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class Service(PrimaryModel):
    name = models.CharField(max_length=150)
    service_owner_contacts = models.ManyToManyField(
        to=Contact, related_name='+', blank=True, verbose_name='Service Owner (Contacts)',
    )
    service_owner_contact_groups = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=True, verbose_name='Service Owner (Contact Groups)',
    )
    service_manager_contacts = models.ManyToManyField(
        to=Contact, related_name='+', blank=True, verbose_name='Service Manager (Contacts)',
    )
    service_manager_contact_groups = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=True, verbose_name='Service Manager (Contact Groups)',
    )
    lifecycle = models.ForeignKey(
        to=Lifecycle, on_delete=models.PROTECT, related_name='+', verbose_name='Lifecycle Management',
    )
    service_portfolio = models.ManyToManyField(
        to=Portfolio, related_name='services', blank=False, verbose_name='Service Portfolios',
    )
    business_unit = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Business Unit',
    )
    support_group = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Support Group',
    )
    change_group = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Change Group',
    )
    ci_function = models.ManyToManyField(
        to='csdm.TechCI', related_name='services', blank=True, verbose_name='Technical CIs',
    )

    class Meta(PrimaryModel.Meta):
        ordering = ('name',)
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class ServiceOffering(PrimaryModel):
    name = models.CharField(max_length=150)
    contract_number = models.CharField(max_length=100, verbose_name='Contract Number')
    service_offering_owner_contacts = models.ManyToManyField(
        to=Contact, related_name='+', blank=True, verbose_name='Service Offering Owner (Contacts)',
    )
    service_offering_owner_contact_groups = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=True, verbose_name='Service Offering Owner (Contact Groups)',
    )
    service_offering_manager_contacts = models.ManyToManyField(
        to=Contact, related_name='+', blank=True, verbose_name='Service Offering Manager (Contacts)',
    )
    service_offering_manager_contact_groups = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=True, verbose_name='Service Offering Manager (Contact Groups)',
    )
    lifecycle = models.ForeignKey(
        to=Lifecycle, on_delete=models.PROTECT, related_name='+', verbose_name='Lifecycle Management',
    )
    service = models.ManyToManyField(
        to=Service, related_name='service_offerings', blank=False, verbose_name='Services',
    )
    business_unit = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Business Unit',
    )
    support_group = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Support Group',
    )
    change_group = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Change Group',
    )
    ci_function = models.ManyToManyField(
        to='csdm.TechCI', related_name='service_offerings', blank=True, verbose_name='Technical CIs',
    )
    tenant = models.ManyToManyField(
        to=Tenant, related_name='+', blank=True, verbose_name='Customer',
    )
    tenant_group = models.ManyToManyField(
        to=TenantGroup, related_name='+', blank=True, verbose_name='Customer Group',
    )

    class Meta(PrimaryModel.Meta):
        ordering = ('name',)
        verbose_name = 'Service Offering'
        verbose_name_plural = 'Service Offerings'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class AppService(PrimaryModel):
    name = models.CharField(max_length=150)
    environment = models.ForeignKey(
        to=Environment, on_delete=models.PROTECT, related_name='+', verbose_name='Environment',
    )
    lifecycle = models.ForeignKey(
        to=Lifecycle, on_delete=models.PROTECT, related_name='+', verbose_name='Lifecycle Management',
    )
    service_offering = models.ManyToManyField(
        to=ServiceOffering, related_name='app_services', blank=False, verbose_name='Service Offerings',
    )
    business_unit = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Business Unit',
    )
    support_group = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Support Group',
    )
    change_group = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Change Group',
    )
    sla = models.ManyToManyField(
        to=SLA, related_name='+', blank=False, verbose_name='SLAs',
    )
    accepted_downtime = models.PositiveIntegerField(verbose_name='Accepted Downtime (hours)')
    owned_by = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Owned by',
    )
    operation_time = models.ManyToManyField(
        to=OperationTime, related_name='+', blank=False, verbose_name='Operation Time',
    )
    availability = models.ManyToManyField(
        to=Availability, related_name='+', blank=False, verbose_name='Availability',
    )
    mtat = models.ManyToManyField(
        to=MTAT, related_name='+', blank=False, verbose_name='MTAT',
    )
    ttr = models.PositiveIntegerField(verbose_name='TTR')
    service_criticality = models.ManyToManyField(
        to=Criticality, related_name='+', blank=False, verbose_name='Service Criticality',
    )
    rpo = models.PositiveIntegerField(verbose_name='RPO (hours)')
    rto = models.PositiveIntegerField(verbose_name='RTO (hours)')
    bcm = models.PositiveIntegerField(verbose_name='BCM (hours)')
    ci_function = models.ManyToManyField(
        to='csdm.TechCI', related_name='app_services', blank=True, verbose_name='Technical CIs',
    )
    tenant = models.ManyToManyField(
        to=Tenant, related_name='+', blank=True, verbose_name='Customer',
    )
    tenant_group = models.ManyToManyField(
        to=TenantGroup, related_name='+', blank=True, verbose_name='Customer Group',
    )

    class Meta(PrimaryModel.Meta):
        ordering = ('name',)
        verbose_name = 'Application Service'
        verbose_name_plural = 'Application Services'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])


class TechCI(PrimaryModel):
    name = models.CharField(max_length=150)
    function = models.CharField(max_length=200, verbose_name='CI Function')
    lifecycle = models.ForeignKey(
        to=Lifecycle, on_delete=models.PROTECT, related_name='+', verbose_name='Lifecycle Management',
    )
    business_unit = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Business Unit',
    )
    support_group = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Support Group',
    )
    change_group = models.ManyToManyField(
        to=ContactGroup, related_name='+', blank=False, verbose_name='Change Group',
    )
    device = models.ManyToManyField(
        to=Device, related_name='+', blank=True, verbose_name='Devices',
    )
    virtual_machine = models.ManyToManyField(
        to=VirtualMachine, related_name='+', blank=True, verbose_name='Virtual Machines',
    )
    cluster = models.ManyToManyField(
        to=Cluster, related_name='+', blank=True, verbose_name='Clusters',
    )
    cluster_group = models.ManyToManyField(
        to=ClusterGroup, related_name='+', blank=True, verbose_name='Cluster Groups',
    )
    tenant = models.ManyToManyField(
        to=Tenant, related_name='+', blank=True, verbose_name='Customer',
    )
    tenant_group = models.ManyToManyField(
        to=TenantGroup, related_name='+', blank=True, verbose_name='Customer Group',
    )

    class Meta(PrimaryModel.Meta):
        ordering = ('name',)
        verbose_name = 'Technical CI'
        verbose_name_plural = 'Technical CIs'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(f'plugins:csdm:{self._meta.model_name}', args=[self.pk])
