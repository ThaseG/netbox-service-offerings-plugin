from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from tenancy.models import Tenant
from utilities.testing import APITestCase

from service_specification.choices import ThreeCConditionChoices, ThreeCKPIChoices, ThreeCRuleTypeChoices
from service_specification.models import ThreeCFinding, ThreeCRule, ThreeCSettings
from service_specification.three_c import (
    aggregate_breakdown,
    health_score,
    kpi_scores,
    run_health_check,
    threshold_state,
)


class ThreeCScoringTestCase(TestCase):
    def test_health_score_rounds_half_up_and_is_none_without_data(self):
        self.assertIsNone(health_score(0, 0))
        self.assertEqual(health_score(0, 10), 100)
        # 1/3 = 33.3% failure -> 67; 1/8 = 12.5% failure -> rounds up to 13 -> 87
        self.assertEqual(health_score(1, 3), 67)
        self.assertEqual(health_score(1, 8), 87)

    def test_kpi_failures_are_pooled_and_composite_averages_kpis(self):
        scores = kpi_scores(
            {
                'required': [1, 4],
                'recommended': [3, 4],  # completeness pooled: 4/8 -> 50
                'stale': [0, 10],
                'orphan': [0, 10],  # correctness: 0/20 -> 100
            }
        )
        self.assertEqual(scores[ThreeCKPIChoices.KPI_COMPLETENESS], 50)
        self.assertEqual(scores[ThreeCKPIChoices.KPI_CORRECTNESS], 100)
        self.assertIsNone(scores[ThreeCKPIChoices.KPI_COMPLIANCE])
        # N/A KPIs are left out of the average, not counted as 0.
        self.assertEqual(scores['composite'], 75)

    def test_threshold_state_uses_failure_rate(self):
        self.assertEqual(threshold_state(96, 5, 10), 'best')  # 4% failing
        self.assertEqual(threshold_state(95, 5, 10), 'at_risk')  # 5% failing
        self.assertEqual(threshold_state(90, 5, 10), 'at_risk')  # 10% failing
        self.assertEqual(threshold_state(89, 5, 10), 'critical')  # 11% failing
        self.assertIsNone(threshold_state(None, 5, 10))


class ThreeCRuleTestCase(TestCase):
    def test_parameter_must_belong_to_ci_class(self):
        rule = ThreeCRule(name='Bad', rule_type=ThreeCRuleTypeChoices.TYPE_REQUIRED, ci_type='device', parameter='nope')
        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_completeness_rule_is_normalized_to_not_empty(self):
        rule = ThreeCRule(
            name='Serial',
            rule_type=ThreeCRuleTypeChoices.TYPE_REQUIRED,
            ci_type='device',
            parameter='serial',
            condition=ThreeCConditionChoices.CONDITION_EQUALS,
            value='x',
        )
        rule.full_clean()
        self.assertEqual(rule.condition, ThreeCConditionChoices.CONDITION_NOT_EMPTY)
        self.assertEqual(rule.value, '')

    def test_compliance_rule_needs_a_value_and_a_valid_regex(self):
        rule = ThreeCRule(
            name='Status',
            rule_type=ThreeCRuleTypeChoices.TYPE_COMPLIANCE,
            ci_type='device',
            parameter='status',
            condition=ThreeCConditionChoices.CONDITION_EQUALS,
        )
        with self.assertRaises(ValidationError):
            rule.full_clean()
        rule.condition, rule.value = ThreeCConditionChoices.CONDITION_REGEX, '('
        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_service_info_and_custom_field_parameters_are_offered(self):
        rule = ThreeCRule(
            name='Support group',
            rule_type=ThreeCRuleTypeChoices.TYPE_RECOMMENDED,
            ci_type='clustergroup',
            parameter='service_info__support_group',
        )
        rule.full_clean()


class ThreeCHealthCheckTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        site = Site.objects.create(name='Site 1', slug='site-1')
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        role = DeviceRole.objects.create(name='Role 1', slug='role-1')
        cls.tenant = Tenant.objects.create(name='Tenant 1', slug='tenant-1')
        common = {'site': site, 'device_type': device_type, 'role': role}

        cls.device_ok = Device.objects.create(name='dev-ok', serial='SN-1', tenant=cls.tenant, **common)
        cls.device_no_serial = Device.objects.create(name='dev-no-serial', **common)
        # Same serial as dev-ok (a duplicate), and offline (stale + non-compliant).
        cls.device_offline = Device.objects.create(
            name='dev-offline', serial='SN-1', status='offline', tenant=cls.tenant, **common
        )

        ThreeCRule.objects.create(
            name='Serial is filled in',
            rule_type=ThreeCRuleTypeChoices.TYPE_REQUIRED,
            ci_type='device',
            parameter='serial',
        )
        ThreeCRule.objects.create(
            name='Must be active',
            rule_type=ThreeCRuleTypeChoices.TYPE_COMPLIANCE,
            ci_type='device',
            parameter='status',
            condition=ThreeCConditionChoices.CONDITION_EQUALS,
            value='Active',
        )
        ThreeCRule.objects.create(
            name='Disabled rule',
            rule_type=ThreeCRuleTypeChoices.TYPE_REQUIRED,
            ci_type='device',
            parameter='asset_tag',
            enabled=False,
        )

    def _finding(self, kpi, device):
        return ThreeCFinding.objects.get(kpi=kpi, ci_type='device', ci_id=device.pk)

    def test_scores_and_findings(self):
        snapshot = run_health_check()

        self.assertEqual(snapshot.ci_count, 3)
        # Required: 1 of 3 devices missing a serial (the disabled asset_tag rule is ignored).
        self.assertEqual(snapshot.completeness, 67)
        # Compliance: 1 of 3 devices not active.
        self.assertEqual(snapshot.compliance, 67)
        # Correctness pools stale (1/3), orphan (3/3 — no Application Service
        # on any of them) and duplicate (1/3): 5/9 failing -> 44.
        self.assertEqual(snapshot.correctness, 44)
        self.assertEqual(snapshot.composite, 59)

        self.assertEqual(
            self._finding(ThreeCKPIChoices.KPI_COMPLETENESS, self.device_no_serial).failures,
            ['Missing (required): Serial number'],
        )
        self.assertFalse(ThreeCFinding.objects.filter(kpi=ThreeCKPIChoices.KPI_COMPLETENESS, ci_id=self.device_ok.pk))

        compliance = self._finding(ThreeCKPIChoices.KPI_COMPLIANCE, self.device_offline)
        self.assertIn('actual: Offline', compliance.failures[0])

        correctness = self._finding(ThreeCKPIChoices.KPI_CORRECTNESS, self.device_offline)
        self.assertEqual(correctness.sub_metrics, ['stale', 'orphan', 'duplicate'])
        self.assertIn('Duplicate of dev-ok (same serial)', correctness.failures)
        # The oldest of a duplicate set is the original, not a failure.
        self.assertNotIn('duplicate', self._finding(ThreeCKPIChoices.KPI_CORRECTNESS, self.device_ok).sub_metrics)

    def test_breakdown_can_be_filtered_by_tenant(self):
        snapshot = run_health_check()
        totals = aggregate_breakdown(snapshot.breakdown, tenant_ids=[str(self.tenant.pk)])
        # Only dev-ok and dev-offline belong to the tenant; both have a serial.
        self.assertEqual(totals['required'], [0, 2])
        self.assertEqual(totals['audit'], [1, 2])
        self.assertEqual(aggregate_breakdown(snapshot.breakdown, ci_types=['cluster']), {})

    def test_only_latest_snapshot_keeps_findings(self):
        first = run_health_check()
        second = run_health_check()
        self.assertFalse(first.findings.exists())
        self.assertTrue(second.findings.exists())


class ThreeCViewsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(username='admin', email='admin@example.com', password='x')
        site = Site.objects.create(name='Site 1', slug='site-1')
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        role = DeviceRole.objects.create(name='Role 1', slug='role-1')
        Device.objects.create(name='dev-1', site=site, device_type=device_type, role=role)
        ThreeCRule.objects.create(
            name='Serial', rule_type=ThreeCRuleTypeChoices.TYPE_REQUIRED, ci_type='device', parameter='serial'
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_report_without_and_with_snapshot(self):
        url = reverse('plugins:service_specification:three_c_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No 3C snapshot yet')

        run_health_check()
        response = self.client.get(url, {'ci_type': 'device'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Relationship Health')
        self.assertContains(response, 'Export CSV')

    def test_findings_list_and_export(self):
        run_health_check()
        url = reverse('plugins:service_specification:threecfinding_list')
        self.assertEqual(self.client.get(url, {'kpi': 'completeness'}).status_code, 200)
        response = self.client.get(url, {'kpi': 'completeness', 'export': 'table'})
        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content) if response.streaming else response.content
        self.assertIn('dev-1', content.decode())

    def test_settings_and_rule_forms(self):
        response = self.client.get(reverse('plugins:service_specification:three_c_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ThreeCSettings.objects.count(), 1)

        # Picking a CI class fills the Parameter dropdown with that class's parameters.
        response = self.client.get(reverse('plugins:service_specification:threecrule_add'), {'ci_type': 'device'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="serial"')
        self.assertContains(response, 'value="service_info__support_group"')


class ThreeCAPITestCase(APITestCase):
    model = ThreeCFinding
    view_namespace = 'plugins-api:service_specification'
    user_permissions = (
        'service_specification.view_threecfinding',
        'service_specification.view_threecsnapshot',
        'service_specification.view_threecsettings',
        'service_specification.change_threecsettings',
    )

    @classmethod
    def setUpTestData(cls):
        site = Site.objects.create(name='Site 1', slug='site-1')
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        role = DeviceRole.objects.create(name='Role 1', slug='role-1')
        Device.objects.create(name='dev-1', site=site, device_type=device_type, role=role)
        ThreeCRule.objects.create(
            name='Serial', rule_type=ThreeCRuleTypeChoices.TYPE_REQUIRED, ci_type='device', parameter='serial'
        )
        run_health_check()

    def test_findings_and_snapshots_are_readable(self):
        url = reverse('plugins-api:service_specification-api:threecfinding-list')
        response = self.client.get(f'{url}?kpi=completeness&sub_metric=required', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        finding = response.data['results'][0]
        self.assertEqual(finding['ci_name'], 'dev-1')
        self.assertEqual(finding['failures'], ['Missing (required): Serial number'])
        self.assertTrue(finding['ci_url'].endswith(f'/dcim/devices/{finding["ci_id"]}/'))

        url = reverse('plugins-api:service_specification-api:threecsnapshot-list')
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['completeness'], 0)

    def test_settings_singleton_can_be_patched_but_not_created(self):
        url = reverse('plugins-api:service_specification-api:threecsettings-list')
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        detail_url = reverse('plugins-api:service_specification-api:threecsettings-detail', args=[1])
        response = self.client.patch(detail_url, {'completeness_lower': 3}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(ThreeCSettings.load().completeness_lower, 3)

        # No create endpoint (405) — or 403 first, since DRF checks the
        # missing add permission before the method.
        response = self.client.post(url, {}, format='json', **self.header)
        self.assertIn(response.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED))
        self.assertEqual(ThreeCSettings.objects.count(), 1)
