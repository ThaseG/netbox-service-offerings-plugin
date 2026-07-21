# Hand-written, same reasoning as 0001_initial.py's header comment (no
# NetBox/Django runtime available in this sandbox to run makemigrations for
# real).
#
# Makes ci_function/lifecycle nullable on the four Service Specification
# "info" side-tables (DeviceServiceInfo, VirtualMachineServiceInfo,
# ClusterServiceInfo, ClusterGroupServiceInfo). They were originally NOT
# NULL, same as the rest of the plugin's required FKs — but these four
# tables are populated lazily: views.py persists an empty placeholder row
# the first time a Device/VM/Cluster/ClusterGroup's "Service Specification"
# tab is viewed, before the user has entered anything, and a NOT NULL FK
# makes that initial save fail outright. See models.py's
# ServiceSpecificationInfoBase for the full explanation.
#
# 0001_initial.py already reflects this as the correct schema for anyone
# deploying fresh, but on an instance where 0001_initial has already been
# applied, Django only tracks migrations by name — editing 0001_initial's
# text has no effect on that instance's actual columns. This migration is
# what actually alters them there.
#
# Verification step before/after deploying: run
#   manage.py makemigrations service_specification --check --dry-run
# on a live instance. If it reports drift, regenerate this file (or add a
# new one) from that environment and replace it.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('service_specification', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deviceserviceinfo',
            name='ci_function',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='service_specification.cifunction',
            ),
        ),
        migrations.AlterField(
            model_name='deviceserviceinfo',
            name='lifecycle',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='service_specification.lifecycle',
            ),
        ),
        migrations.AlterField(
            model_name='virtualmachineserviceinfo',
            name='ci_function',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='service_specification.cifunction',
            ),
        ),
        migrations.AlterField(
            model_name='virtualmachineserviceinfo',
            name='lifecycle',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='service_specification.lifecycle',
            ),
        ),
        migrations.AlterField(
            model_name='clusterserviceinfo',
            name='ci_function',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='service_specification.cifunction',
            ),
        ),
        migrations.AlterField(
            model_name='clusterserviceinfo',
            name='lifecycle',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='service_specification.lifecycle',
            ),
        ),
        migrations.AlterField(
            model_name='clustergroupserviceinfo',
            name='ci_function',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='service_specification.cifunction',
            ),
        ),
        migrations.AlterField(
            model_name='clustergroupserviceinfo',
            name='lifecycle',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='service_specification.lifecycle',
            ),
        ),
    ]
