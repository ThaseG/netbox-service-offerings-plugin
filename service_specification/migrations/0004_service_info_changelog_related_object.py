# Data-only: backfills the CI as the related object on change log entries
# recorded before ServiceSpecificationInfoBase.to_objectchange() started
# setting it, so past Service Specification edits also show up in the CI's
# own Changelog tab. The CI's id is read from the entry's own snapshot data
# (post- or pre-change), so it also works for side-table rows deleted since.
from django.db import migrations

# side-table model -> (its FK field to the CI, the CI's app label, model name)
SERVICE_INFO_PARENTS = {
    'deviceserviceinfo': ('device', 'dcim', 'device'),
    'virtualmachineserviceinfo': ('virtual_machine', 'virtualization', 'virtualmachine'),
    'clusterserviceinfo': ('cluster', 'virtualization', 'cluster'),
    'clustergroupserviceinfo': ('cluster_group', 'virtualization', 'clustergroup'),
    'virtualdevicecontextserviceinfo': ('virtual_device_context', 'dcim', 'virtualdevicecontext'),
}


def link_changes_to_ci(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ObjectChange = apps.get_model('core', 'ObjectChange')

    for info_model, (fk_name, ci_app_label, ci_model) in SERVICE_INFO_PARENTS.items():
        info_type = ContentType.objects.filter(app_label='service_specification', model=info_model).first()
        if info_type is None:
            continue
        ci_type, _ = ContentType.objects.get_or_create(app_label=ci_app_label, model=ci_model)
        changes = ObjectChange.objects.filter(changed_object_type=info_type, related_object_id__isnull=True)
        for change in changes.iterator():
            ci_id = (change.postchange_data or {}).get(fk_name) or (change.prechange_data or {}).get(fk_name)
            if ci_id:
                ObjectChange.objects.filter(pk=change.pk).update(related_object_type=ci_type, related_object_id=ci_id)


class Migration(migrations.Migration):
    dependencies = [
        ('service_specification', '0003_virtual_device_context'),
        ('core', '0024_job_notifications'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(link_changes_to_ci, migrations.RunPython.noop),
    ]
