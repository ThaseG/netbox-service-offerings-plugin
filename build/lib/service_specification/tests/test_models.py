from decimal import Decimal

from django.test import TestCase
from netbox.choices import ColorChoices
from tenancy.models import ContactGroup

from service_specification.choices import TimeUnitChoices
from service_specification.forms import PortfolioForm
from service_specification.models import MTAT, Contract, ContractRateCard, Lifecycle, Portfolio


class LifecycleModelTestCase(TestCase):
    def test_create_and_str(self):
        lifecycle = Lifecycle.objects.create(name='Live', slug='live')
        self.assertEqual(str(lifecycle), 'Live')
        self.assertIn(f'/{lifecycle.pk}/', lifecycle.get_absolute_url())

    def test_color_defaults_to_grey_and_can_be_overridden(self):
        # Regression coverage for the color field added so lifecycle
        # statuses can be shown as colored labels throughout the plugin's
        # tables (see tables.py's ColoredLabelColumn usage).
        default = Lifecycle.objects.create(name='Live', slug='live')
        self.assertEqual(default.color, ColorChoices.COLOR_GREY)

        available = Lifecycle.objects.create(name='Available', slug='available', color=ColorChoices.COLOR_GREEN)
        self.assertEqual(available.color, ColorChoices.COLOR_GREEN)


class MTATModelTestCase(TestCase):
    def test_value_and_unit_round_trip(self):
        # The one field this model exists to hold — regression coverage for
        # the value+unit split (previously a bare string field, changed
        # after review to an integer + separate unit ChoiceSet).
        mtat = MTAT.objects.create(name='Gold', slug='gold', value=15, unit=TimeUnitChoices.UNIT_MINUTES)
        self.assertEqual(mtat.value, 15)
        self.assertEqual(mtat.unit, 'minutes')


class ContractModelTestCase(TestCase):
    def test_status_computed_from_active_rate_cards(self):
        # Regression coverage for the "no manual status field" design: a
        # Contract with zero Rate Cards must read as Inactive, flip to
        # Active as soon as one active Rate Card exists, and flip back the
        # moment that Rate Card is deactivated — all without ever saving
        # the Contract itself (see models.py's Contract.status property).
        contract = Contract.objects.create(contract_number='CN-0001')
        self.assertEqual(contract.status, 'Inactive')

        rate_card = ContractRateCard.objects.create(
            contract=contract,
            contract_position_number='POS-0001',
        )
        self.assertEqual(contract.status, 'Active')

        rate_card.active = False
        rate_card.save()
        self.assertEqual(contract.status, 'Inactive')

    def test_create_and_str(self):
        contract = Contract.objects.create(contract_number='CN-0002')
        self.assertEqual(str(contract), 'CN-0002')
        self.assertIn(f'/{contract.pk}/', contract.get_absolute_url())


class ContractRateCardModelTestCase(TestCase):
    def test_total_costs_computed(self):
        # The one piece of arithmetic this model exists to hold — see the
        # spec's own "Total costs - Base cost + Hourly rate*Hours spend".
        contract = Contract.objects.create(contract_number='CN-0003')
        rate_card = ContractRateCard.objects.create(
            contract=contract,
            contract_position_number='POS-0001',
            base_costs=Decimal('100.00'),
            hourly_rate=Decimal('50.00'),
            hours_spend=Decimal('3.00'),
        )
        self.assertEqual(rate_card.total_costs, Decimal('250.00'))


class PortfolioModelTestCase(TestCase):
    def setUp(self):
        self.lifecycle = Lifecycle.objects.create(name='Live', slug='live')

    def test_create_and_str(self):
        portfolio = Portfolio.objects.create(name='Enterprise Portfolio', lifecycle=self.lifecycle)
        self.assertEqual(str(portfolio), 'Enterprise Portfolio')
        self.assertIn(f'/{portfolio.pk}/', portfolio.get_absolute_url())


class PortfolioFormOwnershipValidationTestCase(TestCase):
    """The owner/manager fields are each split into two plain M2M fields
    (contacts + contact_groups), both individually optional at the model
    level — the "at least one of the pair must be set" rule can't be a
    model-level constraint (M2M values aren't available on an unsaved
    instance), so it lives in PortfolioForm.clean() instead. This is the
    one piece of business logic here that specifically needs form-level
    coverage, not just a model round-trip.
    """

    def setUp(self):
        self.lifecycle = Lifecycle.objects.create(name='Live', slug='live')
        self.group = ContactGroup.objects.create(name='IT Ops', slug='it-ops')

    def test_rejects_when_neither_owner_nor_manager_set(self):
        form = PortfolioForm(data={'name': 'Test Portfolio', 'lifecycle': self.lifecycle.pk})
        self.assertFalse(form.is_valid())

    def test_rejects_when_owner_set_but_manager_missing(self):
        form = PortfolioForm(
            data={
                'name': 'Test Portfolio',
                'lifecycle': self.lifecycle.pk,
                'portfolio_owner_contact_groups': [self.group.pk],
            }
        )
        self.assertFalse(form.is_valid())

    def test_accepts_when_owner_and_manager_contact_groups_set(self):
        form = PortfolioForm(
            data={
                'name': 'Test Portfolio',
                'lifecycle': self.lifecycle.pk,
                'portfolio_owner_contact_groups': [self.group.pk],
                'portfolio_manager_contact_groups': [self.group.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
