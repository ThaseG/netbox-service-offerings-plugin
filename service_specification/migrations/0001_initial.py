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
#   manage.py makemigrations service_specification --check --dry-run
# on a live instance. If it reports drift, regenerate this file from that
# environment and replace it.
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models


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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Lifecycle',
                'verbose_name_plural': 'Service Lifecycle Managements',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'MTAT',
                'verbose_name_plural': 'MTATs',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='CIFunction',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
                    ),
                ),
            ],
            options={
                'verbose_name': 'CI Function',
                'verbose_name_plural': 'CI Functions',
                'ordering': ('name',),
            },
        ),
        #
        # Core Service Specification models
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.lifecycle',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.lifecycle',
                    ),
                ),
                (
                    'ci_function',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.cifunction',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.lifecycle',
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
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='users.owner',
                    ),
                ),
                (
                    'environment',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.environment',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.lifecycle',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Application Service',
                'verbose_name_plural': 'Application Services',
                'ordering': ('name',),
            },
        ),
        #
        # Service Specification info attached directly to core NetBox
        # infrastructure objects (see models.py's ServiceSpecificationInfoBase
        # docstring for why these are separate 1:1 tables rather than fields
        # added directly to dcim.Device / virtualization.*).
        #
        migrations.CreateModel(
            name='DeviceServiceInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'ci_function',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.cifunction',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.lifecycle',
                    ),
                ),
                (
                    'device',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='service_specification_info',
                        to='dcim.device',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Device Service Info',
                'verbose_name_plural': 'Device Service Info',
            },
        ),
        migrations.CreateModel(
            name='VirtualMachineServiceInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'ci_function',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.cifunction',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.lifecycle',
                    ),
                ),
                (
                    'virtual_machine',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='service_specification_info',
                        to='virtualization.virtualmachine',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Virtual Machine Service Info',
                'verbose_name_plural': 'Virtual Machine Service Info',
            },
        ),
        migrations.CreateModel(
            name='ClusterServiceInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'ci_function',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.cifunction',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.lifecycle',
                    ),
                ),
                (
                    'cluster',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='service_specification_info',
                        to='virtualization.cluster',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Cluster Service Info',
                'verbose_name_plural': 'Cluster Service Info',
            },
        ),
        migrations.CreateModel(
            name='ClusterGroupServiceInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
                (
                    'ci_function',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.cifunction',
                    ),
                ),
                (
                    'lifecycle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='service_specification.lifecycle',
                    ),
                ),
                (
                    'cluster_group',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='service_specification_info',
                        to='virtualization.clustergroup',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Cluster Group Service Info',
                'verbose_name_plural': 'Cluster Group Service Info',
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
            field=models.ManyToManyField(related_name='services', to='service_specification.portfolio'),
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
            field=models.ManyToManyField(related_name='service_offerings', to='service_specification.service'),
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
            field=models.ManyToManyField(related_name='app_services', to='service_specification.serviceoffering'),
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
            field=models.ManyToManyField(related_name='+', to='service_specification.sla'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='owned_by',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='operation_time',
            field=models.ManyToManyField(related_name='+', to='service_specification.operationtime'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='availability',
            field=models.ManyToManyField(related_name='+', to='service_specification.availability'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='mtat',
            field=models.ManyToManyField(related_name='+', to='service_specification.mtat'),
        ),
        migrations.AddField(
            model_name='appservice',
            name='service_criticality',
            field=models.ManyToManyField(related_name='+', to='service_specification.criticality'),
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
        # DeviceServiceInfo / VirtualMachineServiceInfo / ClusterServiceInfo / ClusterGroupServiceInfo
        migrations.AddField(
            model_name='deviceserviceinfo',
            name='business_unit',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='deviceserviceinfo',
            name='support_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='deviceserviceinfo',
            name='change_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='virtualmachineserviceinfo',
            name='business_unit',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='virtualmachineserviceinfo',
            name='support_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='virtualmachineserviceinfo',
            name='change_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='clusterserviceinfo',
            name='business_unit',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='clusterserviceinfo',
            name='support_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='clusterserviceinfo',
            name='change_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='clustergroupserviceinfo',
            name='business_unit',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='clustergroupserviceinfo',
            name='support_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
        migrations.AddField(
            model_name='clustergroupserviceinfo',
            name='change_group',
            field=models.ManyToManyField(related_name='+', to='tenancy.contactgroup'),
        ),
    ]
