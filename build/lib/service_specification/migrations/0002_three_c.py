# Hand-written, same as 0001_initial.py (see its header): field kwargs
# follow NetBox's custom_deconstruct (utilities/migration.py), which drops
# `choices`, `help_text` and `verbose_name` from every field.
#
# A separate migration rather than an edit to 0001: unlike 0001's own
# drift fixes, these are new tables that existing installs must gain.
import datetime

import django.core.validators
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models


def _netbox_model_fields():
    return [
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
        ('created', models.DateTimeField(auto_now_add=True, null=True)),
        ('last_updated', models.DateTimeField(auto_now=True, null=True)),
        (
            'custom_field_data',
            models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
        ),
    ]


def _threshold(default):
    return models.PositiveSmallIntegerField(default=default, validators=[django.core.validators.MaxValueValidator(100)])


class Migration(migrations.Migration):
    dependencies = [
        ('service_specification', '0001_initial'),
        ('extras', '0140_imageattachment_image_size'),
        ('tenancy', '0024_default_ordering_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThreeCRule',
            fields=[
                *_netbox_model_fields(),
                ('name', models.CharField(max_length=100)),
                ('rule_type', models.CharField(max_length=30)),
                ('ci_type', models.CharField(max_length=30)),
                ('parameter', models.CharField(max_length=100)),
                ('condition', models.CharField(default='not_empty', max_length=30)),
                ('value', models.CharField(blank=True, max_length=500)),
                ('enabled', models.BooleanField(default=True)),
                ('description', models.CharField(blank=True, max_length=200)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
            ],
            options={
                'verbose_name': '3C Rule',
                'verbose_name_plural': '3C Rules',
                'ordering': ('ci_type', 'rule_type', 'name'),
            },
        ),
        migrations.CreateModel(
            name='ThreeCSettings',
            fields=[
                *_netbox_model_fields(),
                ('completeness_lower', _threshold(5)),
                ('completeness_upper', _threshold(10)),
                ('correctness_lower', _threshold(5)),
                ('correctness_upper', _threshold(10)),
                ('compliance_lower', _threshold(5)),
                ('compliance_upper', _threshold(10)),
                ('composite_lower', _threshold(5)),
                ('composite_upper', _threshold(10)),
                ('relationship_lower', _threshold(5)),
                ('relationship_upper', _threshold(10)),
                ('job_time', models.TimeField(default=datetime.time(2, 0))),
                ('snapshot_retention_days', models.PositiveIntegerField(default=400)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
            ],
            options={
                'verbose_name': '3C Settings',
                'verbose_name_plural': '3C Settings',
                'ordering': ('pk',),
            },
        ),
        migrations.CreateModel(
            name='ThreeCSnapshot',
            fields=[
                *_netbox_model_fields(),
                ('completeness', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('correctness', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('compliance', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('composite', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('relationship_health', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('ci_count', models.PositiveIntegerField(default=0)),
                ('breakdown', models.JSONField(default=dict)),
                ('relationship_breakdown', models.JSONField(default=dict)),
                ('lifecycle_checks', models.BooleanField(default=False)),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
            ],
            options={
                'verbose_name': '3C Snapshot',
                'verbose_name_plural': '3C Snapshots',
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='ThreeCFinding',
            fields=[
                *_netbox_model_fields(),
                ('kpi', models.CharField(max_length=30)),
                ('ci_type', models.CharField(max_length=30)),
                ('ci_id', models.PositiveBigIntegerField()),
                ('ci_name', models.CharField(max_length=255)),
                ('support_group', models.CharField(blank=True, max_length=500)),
                ('ci_last_updated', models.DateTimeField(blank=True, null=True)),
                ('sub_metrics', models.JSONField(default=list)),
                ('failures', models.JSONField(default=list)),
                (
                    'snapshot',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='findings',
                        to='service_specification.threecsnapshot',
                    ),
                ),
                (
                    'tenant',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='+',
                        to='tenancy.tenant',
                    ),
                ),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
            ],
            options={
                'verbose_name': '3C Finding',
                'verbose_name_plural': '3C Findings',
                'ordering': ('kpi', 'ci_type', 'ci_name'),
            },
        ),
    ]
