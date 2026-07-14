# Hand-written (this sandbox has no NetBox/Django runtime available to run
# `manage.py makemigrations` for real). Field definitions were verified
# field-by-field against netbox-community/netbox @ v4.6.4 source
# (netbox/netbox/models/{__init__,features,mixins}.py) and cross-checked
# against real generated migrations in that same tree (e.g. vpn/migrations/
# 0001_initial.py, dcim/migrations/0201_add_power_outlet_status.py) for
# exact field/kwarg serialization conventions — notably that ChoiceSet
# `choices=` kwargs and `ManyToManyField(blank=False)` (the Django default)
# are omitted from migrations even though they're set in models.py.
#
# Verification step before/after first deploy: run
#   manage.py makemigrations csdm --check --dry-run
# on a live instance. If it reports drift, regenerate this file from that
# environment and replace it.
import django.db.models.deletion
import taggit.managers
from django.db import migrations, models

import utilities.json


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('extras', '0140_imageattachment_image_size'),
        ('users', '0016_default_ordering_indexes'),
        ('tenancy', '0024_default_ordering_indexes'),
        ('dcim', '0237_module_remove_local_context_data'),
        ('virtualization', '0056_virtualmachine_render_config_permission'),
    ]

    operations = [
        #
        # Support / lookup models
        #
        migrations.CreateModel(
            name='Lifecycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Lifecycle',
                'verbose_name_plural': 'Lifecycle Managements',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='SLA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('sla_definition', models.CharField(max_length=500)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'SLA',
                'verbose_name_plural': 'SLAs',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='OperationTime',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Operation Time',
                'verbose_name_plural': 'Operation Times',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Availability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Availability',
                'verbose_name_plural': 'Availabilities',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Criticality',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Criticality',
                'verbose_name_plural': 'Criticalities',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Environment',
                'verbose_name_plural': 'Environments',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='MTAT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('value', models.PositiveIntegerField()),
                ('unit', models.CharField(max_length=30)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'MTAT',
                'verbose_name_plural': 'MTATs',
                'ordering': ('name',),
            },
        ),

        #
        # Core CSDM models
        #
        migrations.CreateModel(
            name='Portfolio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=150)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name='+', to='csdm.lifecycle',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Service Portfolio',
                'verbose_name_plural': 'Service Portfolios',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=150)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name='+', to='csdm.lifecycle',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Service',
                'verbose_name_plural': 'Services',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ServiceOffering',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=150)),
                ('contract_number', models.CharField(max_length=100)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name='+', to='csdm.lifecycle',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Service Offering',
                'verbose_name_plural': 'Service Offerings',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='AppService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=150)),
                ('accepted_downtime', models.PositiveIntegerField()),
                ('ttr', models.PositiveIntegerField()),
                ('rpo', models.PositiveIntegerField()),
                ('rto', models.PositiveIntegerField()),
                ('bcm', models.PositiveIntegerField()),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
                (
                    'environment',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name='+', to='csdm.environment',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name='+', to='csdm.lifecycle',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Application Service',
                'verbose_name_plural': 'Application Services',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='TechCI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('name', models.CharField(max_length=150)),
                ('function', models.CharField(max_length=200)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'owner',
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                        related_name='+', to='users.owner',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name='+', to='csdm.lifecycle',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Technical CI',
                'verbose_name_plural': 'Technical CIs',
                'ordering': ('name',),
            },
        ),

        #
        # Many-to-many fields (added after every involved model exists, to
        # avoid ordering issues from the extensive cross-references below)
        #

        # Portfolio
        migrations.AddField(
            model_name='portfolio',
            name='portfolio_owner_contacts',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contact'),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='portfolio_owner_contact_groups',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='portfolio_manager_contacts',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contact'),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='portfolio_manager_contact_groups',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contactgroup'),
        ),

        # Service
        migrations.AddField(
            model_name='service',
            name='service_owner_contacts',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contact'),
        ),
        migrations.AddField(
            model_name='service',
            name='service_owner_contact_groups',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='service',
            name='service_manager_contacts',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contact'),
        ),
        migrations.AddField(
            model_name='service',
            name='service_manager_contact_groups',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='service',
            name='service_portfolio',
            field=models.ManyToManyField(related_name='services', to='csdm.portfolio'),
        ),
        migrations.AddField(
            model_name='service',
            name='business_unit',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='service',
            name='support_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='service',
            name='change_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='service',
            name='ci_function',
            field=models.ManyToManyField(blank=True, related_name='services', to='csdm.techci'),
        ),

        # ServiceOffering
        migrations.AddField(
            model_name='serviceoffering',
            name='service_offering_owner_contacts',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contact'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='service_offering_owner_contact_groups',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='service_offering_manager_contacts',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contact'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='service_offering_manager_contact_groups',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='service',
            field=models.ManyToManyField(related_name='service_offerings', to='csdm.service'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='business_unit',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='support_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='change_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='ci_function',
            field=models.ManyToManyField(blank=True, related_name='service_offerings', to='csdm.techci'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='tenant',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.tenant'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='tenant_group',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.tenantgroup'),
        ),

        # AppService
        migrations.AddField(
            model_name='appservice',
            name='service_offering',
            field=models.ManyToManyField(related_name='app_services', to='csdm.serviceoffering'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='business_unit',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='support_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='change_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='sla',
            field=models.ManyToManyField(related_name='+', to='csdm.sla'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='owned_by',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='operation_time',
            field=models.ManyToManyField(related_name='+', to='csdm.operationtime'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='availability',
            field=models.ManyToManyField(related_name='+', to='csdm.availability'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='mtat',
            field=models.ManyToManyField(related_name='+', to='csdm.mtat'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='service_criticality',
            field=models.ManyToManyField(related_name='+', to='csdm.criticality'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='ci_function',
            field=models.ManyToManyField(blank=True, related_name='app_services', to='csdm.techci'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='tenant',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.tenant'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='tenant_group',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.tenantgroup'),
        ),

        # TechCI
        migrations.AddField(
            model_name='techci',
            name='business_unit',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='techci',
            name='support_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='techci',
            name='change_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='techci',
            name='device',
            field=models.ManyToManyField(blank=True, related_name='+', to='dcim.device'),
        ),
        migrations.AddField(
            model_name='techci',
            name='virtual_machine',
            field=models.ManyToManyField(blank=True, related_name='+', to='virtualization.virtualmachine'),
        ),
        migrations.AddField(
            model_name='techci',
            name='cluster',
            field=models.ManyToManyField(blank=True, related_name='+', to='virtualization.cluster'),
        ),
        migrations.AddField(
            model_name='techci',
            name='cluster_group',
            field=models.ManyToManyField(blank=True, related_name='+', to='virtualization.clustergroup'),
        ),
        migrations.AddField(
            model_name='techci',
            name='tenant',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.tenant'),
        ),
        migrations.AddField(
            model_name='techci',
            name='tenant_group',
            field=models.ManyToManyField(blank=True, related_name='+', to='tenancy.tenantgroup'),
        ),
    ]
