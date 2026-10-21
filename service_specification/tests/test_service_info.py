from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site, VirtualDeviceContext
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from tenancy.models import ContactGroup, Tenant, TenantGroup
from virtualization.models import Cluster, ClusterType, VirtualMachine

from service_specification.filtersets import AppServiceFilterSet
from service_specification.forms import (
    ClusterServiceInfoForm,
    DeviceServiceInfoForm,
    VirtualDeviceContextServiceInfoForm,
    VirtualMachineServiceInfoForm,
)
from service_specification.models import (
    AppService,
    ClusterServiceInfo,
    DeviceServiceInfo,
    Environment,
    Lifecycle,
    ServiceOffering,
    VirtualDeviceContextServiceInfo,
    VirtualMachineServiceInfo,
)


class ServiceInfoTenantRestrictionTestCase(TestCase):
    """A CI's Service Specification tab only offers Application Services of
    the CI's own tenant (directly, or via the tenant's Tenant Group)."""

    @classmethod
    def setUpTestData(cls):
        group = TenantGroup.objects.create(name='Group', slug='group')
        cls.tenant_a = Tenant.objects.create(name='Tenant A', slug='tenant-a', group=group)
        cls.tenant_b = Tenant.objects.create(name='Tenant B', slug='tenant-b')

        cls.lifecycle = Lifecycle.objects.create(name='Operational', slug='operational')
        environment = Environment.objects.create(name='Production', slug='production')

        def app_service(name, tenant=None, tenant_group=None):
            offering = ServiceOffering.objects.create(name=f'{name} offering', lifecycle=cls.lifecycle)
            if tenant:
                offering.tenant.add(tenant)
            if tenant_group:
                offering.tenant_group.add(tenant_group)
            return AppService.objects.create(
                name=name,
                environment=environment,
                lifecycle=cls.lifecycle,
                service_offering=offering,
                accepted_downtime=1,
                ttr=1,
                rpo=1,
                rto=1,
                bcm=1,
            )

        cls.app_a = app_service('App A', tenant=cls.tenant_a)
        cls.app_b = app_service('App B', tenant=cls.tenant_b)
        cls.app_group = app_service('App Group', tenant_group=group)

        site = Site.objects.create(name='Site', slug='site')
        manufacturer = Manufacturer.objects.create(name='Manufacturer', slug='manufacturer')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model', slug='model')
        role = DeviceRole.objects.create(name='Role', slug='role')
        cls.device = Device.objects.create(
            name='dev-a', site=site, device_type=device_type, role=role, tenant=cls.tenant_a
        )
        cluster_type = ClusterType.objects.create(name='Type', slug='type')
        cls.cluster = Cluster.objects.create(name='cluster-no-tenant', type=cluster_type)
        cls.vm = VirtualMachine.objects.create(name='vm-b', cluster=cls.cluster, tenant=cls.tenant_b)
        cls.contact_group = ContactGroup.objects.create(name='Team', slug='team')
        # A Tenant B context running on Tenant A's device: the VDC's own tenant counts.
        cls.vdc = VirtualDeviceContext.objects.create(device=cls.device, name='vdc-b', tenant=cls.tenant_b)

    def _form(self, form_cls, info, **data):
        return form_cls(instance=info, data=data or None)

    def test_device_offers_own_tenant_and_tenant_group_app_services(self):
        form = self._form(DeviceServiceInfoForm, DeviceServiceInfo.objects.create(device=self.device))
        field = form.fields['application_services']
        self.assertQuerySetEqual(field.queryset, [self.app_a, self.app_group], ordered=False)
        self.assertIn('available_for_tenant_id', str(field.widget.attrs))

    def test_vm_offers_only_its_tenant_app_services(self):
        info = VirtualMachineServiceInfo.objects.create(virtual_machine=self.vm)
        form = self._form(VirtualMachineServiceInfoForm, info)
        self.assertQuerySetEqual(form.fields['application_services'].queryset, [self.app_b], ordered=False)

    def test_ci_without_tenant_offers_every_app_service(self):
        form = self._form(ClusterServiceInfoForm, ClusterServiceInfo.objects.create(cluster=self.cluster))
        self.assertQuerySetEqual(
            form.fields['application_services'].queryset, [self.app_a, self.app_b, self.app_group], ordered=False
        )

    def test_other_tenants_app_service_is_rejected(self):
        info = DeviceServiceInfo.objects.create(device=self.device)
        common = {
            'lifecycle': self.lifecycle.pk,
            'business_unit': [self.contact_group.pk],
            'support_group': [self.contact_group.pk],
            'change_group': [self.contact_group.pk],
        }
        form = self._form(DeviceServiceInfoForm, info, application_services=[self.app_b.pk], **common)
        self.assertFalse(form.is_valid())
        self.assertIn('application_services', form.errors)

        form = self._form(DeviceServiceInfoForm, info, application_services=[self.app_a.pk], **common)
        self.assertTrue(form.is_valid(), form.errors)

    def test_available_for_tenant_filter(self):
        filtered = AppServiceFilterSet({'available_for_tenant_id': self.tenant_a.pk}, AppService.objects.all()).qs
        self.assertQuerySetEqual(filtered, [self.app_a, self.app_group], ordered=False)

    def test_edit_page_renders(self):
        user = get_user_model().objects.create_superuser(username='admin', email='admin@example.com', password='x')
        self.client.force_login(user)
        url = reverse('dcim:device_service_specification_edit', kwargs={'pk': self.device.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'available_for_tenant_id')

    def test_vdc_offers_its_own_tenant_app_services(self):
        info = VirtualDeviceContextServiceInfo.objects.create(virtual_device_context=self.vdc)
        form = self._form(VirtualDeviceContextServiceInfoForm, info)
        self.assertQuerySetEqual(form.fields['application_services'].queryset, [self.app_b], ordered=False)

    def test_vdc_tab_and_edit_page_render(self):
        user = get_user_model().objects.create_superuser(username='admin', email='admin@example.com', password='x')
        self.client.force_login(user)
        for name in (
            'dcim:virtualdevicecontext_service_specification',
            'dcim:virtualdevicecontext_service_specification_edit',
        ):
            response = self.client.get(reverse(name, kwargs={'pk': self.vdc.pk}))
            self.assertEqual(response.status_code, 200, name)
