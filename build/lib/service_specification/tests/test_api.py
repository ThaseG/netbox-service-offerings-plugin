from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.urls import reverse
from rest_framework import status
from tenancy.models import Tenant
from utilities.testing import APITestCase
from utilities.testing.utils import disable_warnings
from virtualization.models import Cluster, ClusterGroup, ClusterType, VirtualMachine

from service_specification.models import (
    AppService,
    ClusterGroupServiceInfo,
    ClusterServiceInfo,
    DeviceServiceInfo,
    Environment,
    Lifecycle,
    ServiceOffering,
    VirtualMachineServiceInfo,
)


class LifecycleAPITestCase(APITestCase):
    """POST -> GET -> PATCH -> DELETE round trip against the plugin's REST
    API, using Lifecycle since it's the one model with no required related
    objects to create first. This exercises the real serializer/viewset/
    permission stack end to end, complementing test_models.py's plain ORM
    coverage.
    """

    model = Lifecycle
    # APITestCase._get_view_namespace() defaults to f'{app_label}-api',
    # which matches how *core* NetBox apps are mounted directly under
    # /api/. Plugins are mounted one level deeper (netbox/plugins/urls.py:
    # /api/plugins/ -> namespace 'plugins-api' -> namespace '<app_label>-api'),
    # so the default guess resolves to 'service_specification-api' when the real registered
    # namespace is 'plugins-api:service_specification-api'. Since view_namespace gets '-api'
    # appended automatically, 'plugins-api:service_specification' here becomes exactly that.
    view_namespace = 'plugins-api:service_specification'
    user_permissions = (
        'service_specification.add_lifecycle',
        'service_specification.view_lifecycle',
        'service_specification.change_lifecycle',
        'service_specification.delete_lifecycle',
    )

    def test_post_get_patch_delete(self):
        url = self._get_list_url()

        # POST: create a new Lifecycle
        response = self.client.post(url, {'name': 'Pilot', 'slug': 'pilot'}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        lifecycle_id = response.data['id']

        # GET: retrieve it back and confirm the data round-tripped
        detail_url = self._get_detail_url(Lifecycle.objects.get(pk=lifecycle_id))
        response = self.client.get(detail_url, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Pilot')
        self.assertEqual(response.data['slug'], 'pilot')

        # PATCH: change a field and confirm it actually persisted (not just
        # echoed back in the response)
        response = self.client.patch(
            detail_url,
            {'description': 'Pilot phase lifecycle stage'},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Pilot phase lifecycle stage')
        self.assertEqual(
            Lifecycle.objects.get(pk=lifecycle_id).description,
            'Pilot phase lifecycle stage',
        )

        # DELETE: clean up
        response = self.client.delete(detail_url, **self.header)
        self.assertHttpStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lifecycle.objects.filter(pk=lifecycle_id).exists())

    def test_create_without_permission_is_rejected(self):
        # Same POST as above, but as a user with no service_specification.add_lifecycle
        # permission — the base APITestCase.setUp() already grants
        # user_permissions, so this simulates the anonymous/unauthorized
        # case by clearing them first.
        self.user.object_permissions.all().delete()
        with disable_warnings('django.request'):
            response = self.client.post(
                self._get_list_url(),
                {'name': 'Should Not Be Created', 'slug': 'nope'},
                format='json',
                **self.header,
            )
        self.assertHttpStatus(response, status.HTTP_403_FORBIDDEN)


class TechnicalCIAPITestCase(APITestCase):
    """The technical-ci/* endpoints behind the Service Offering Tree /
    Product View's Technical CI filter dropdowns: each must narrow its CIs
    by the Customer / Service Offering / Application Service they're linked
    to through their Service Specification tab, and return everything when
    no such filter is given.
    """

    model = Device
    view_namespace = 'plugins-api:service_specification'
    user_permissions = (
        'dcim.view_device',
        'virtualization.view_virtualmachine',
        'virtualization.view_cluster',
        'virtualization.view_clustergroup',
    )

    # (endpoint basename, ServiceInfo model, its FK field to the CI)
    ENDPOINTS = (
        ('technical-ci-device', DeviceServiceInfo, 'device'),
        ('technical-ci-virtual-machine', VirtualMachineServiceInfo, 'virtual_machine'),
        ('technical-ci-cluster', ClusterServiceInfo, 'cluster'),
        ('technical-ci-cluster-group', ClusterGroupServiceInfo, 'cluster_group'),
    )

    @classmethod
    def setUpTestData(cls):
        lifecycle = Lifecycle.objects.create(name='Live', slug='live')
        environment = Environment.objects.create(name='Production', slug='production')
        site = Site.objects.create(name='Site 1', slug='site-1')
        manufacturer = Manufacturer.objects.create(name='Dell', slug='dell')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='R750', slug='r750')
        role = DeviceRole.objects.create(name='Server', slug='server')
        cluster_type = ClusterType.objects.create(name='VMware', slug='vmware')

        # Two fully separate Customer -> Offering -> AppService -> CI chains
        cls.chains = []
        for n in (1, 2):
            tenant = Tenant.objects.create(name=f'Tenant {n}', slug=f'tenant-{n}')
            offering = ServiceOffering.objects.create(name=f'Offering {n}', lifecycle=lifecycle)
            offering.tenant.add(tenant)
            app_service = AppService.objects.create(
                name=f'App Service {n}',
                environment=environment,
                lifecycle=lifecycle,
                service_offering=offering,
                accepted_downtime=1,
                ttr=1,
                rpo=1,
                rto=1,
                bcm=1,
            )
            group = ClusterGroup.objects.create(name=f'Group {n}', slug=f'group-{n}')
            cluster = Cluster.objects.create(name=f'Cluster {n}', type=cluster_type, group=group)
            cis = {
                'device': Device.objects.create(name=f'Device {n}', site=site, device_type=device_type, role=role),
                'virtual_machine': VirtualMachine.objects.create(name=f'VM {n}', cluster=cluster),
                'cluster': cluster,
                'cluster_group': group,
            }
            for _, info_model, field in cls.ENDPOINTS:
                info_model.objects.create(**{field: cis[field]}).application_services.add(app_service)
            cls.chains.append({'tenant': tenant, 'offering': offering, 'app_service': app_service, 'cis': cis})

        # A CI linked to no Application Service at all — must only show up unfiltered
        Device.objects.create(name='Unlinked Device', site=site, device_type=device_type, role=role)

    def _ids(self, basename, **params):
        url = reverse(f'plugins-api:service_specification-api:{basename}-list')
        response = self.client.get(url, {**params, 'brief': 1}, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        return {row['id'] for row in response.data['results']}

    def test_filters_by_customer_offering_and_app_service(self):
        chain = self.chains[0]
        for basename, _, field in self.ENDPOINTS:
            expected = {chain['cis'][field].pk}
            with self.subTest(endpoint=basename):
                self.assertEqual(self._ids(basename, offering_tenant_id=chain['tenant'].pk), expected)
                self.assertEqual(self._ids(basename, service_offering_id=chain['offering'].pk), expected)
                self.assertEqual(self._ids(basename, app_service_id=chain['app_service'].pk), expected)

    def test_unfiltered_returns_everything(self):
        self.assertEqual(self._ids('technical-ci-device'), set(Device.objects.values_list('pk', flat=True)))
