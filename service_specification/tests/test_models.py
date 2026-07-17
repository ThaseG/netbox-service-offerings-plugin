from django.test import TestCase
from tenancy.models import ContactGroup

from service_specification.choices import TimeUnitChoices
from service_specification.forms import PortfolioForm
from service_specification.models import MTAT, Lifecycle, Portfolio


class LifecycleModelTestCase(TestCase):
    def test_create_and_str(self):
        lifecycle = Lifecycle.objects.create(name='Live', slug='live')
        self.assertEqual(str(lifecycle), 'Live')
        self.assertIn(f'/{lifecycle.pk}/', lifecycle.get_absolute_url())


class MTATModelTestCase(TestCase):
    def test_value_and_unit_round_trip(self):
        # The one field this model exists to hold — regression coverage for
        # the value+unit split (previously a bare string field, changed
        # after review to an integer + separate unit ChoiceSet).
        mtat = MTAT.objects.create(name='Gold', slug='gold', value=15, unit=TimeUnitChoices.UNIT_MINUTES)
        self.assertEqual(mtat.value, 15)
        self.assertEqual(mtat.unit, 'minutes')


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
