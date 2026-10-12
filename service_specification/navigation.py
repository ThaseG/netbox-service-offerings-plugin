from netbox.choices import ButtonColorChoices
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem


def _item(model_name, link_text):
    return PluginMenuItem(
        link=f'plugins:service_specification:{model_name}_list',
        link_text=link_text,
        permissions=[f'service_specification.view_{model_name}'],
        buttons=(
            PluginMenuButton(
                link=f'plugins:service_specification:{model_name}_add',
                title=f'Add {link_text}',
                icon_class='mdi mdi-plus-thick',
                color=ButtonColorChoices.GREEN,
                permissions=[f'service_specification.add_{model_name}'],
            ),
        ),
    )


def _report_item(url_name, link_text, permissions=None):
    # Reports are read-only (no backing model, nothing to add/edit/delete),
    # so unlike _item() above there's no PluginMenuButton, and usually no
    # model-specific permission — any authenticated user who can reach the
    # plugin can view them, the same as the data they're derived from. 3C
    # is the exception: it reads stored snapshots, so it needs their view
    # permission.
    return PluginMenuItem(
        link=f'plugins:service_specification:{url_name}',
        link_text=link_text,
        permissions=permissions or [],
    )


data_model_items = (
    _item('portfolio', 'Service Portfolios'),
    _item('service', 'Services'),
    _item('serviceoffering', 'Service Offerings'),
    _item('appservice', 'Application Services'),
)

contract_items = (
    _item('contract', 'Contracts'),
    _item('contractratecard', 'Contract Rate Cards'),
)

support_items = (
    _item('lifecycle', 'Service Lifecycle Managements'),
    _item('sla', 'SLAs'),
    _item('operationtime', 'Operation Times'),
    _item('availability', 'Availabilities'),
    _item('criticality', 'Criticalities'),
    _item('environment', 'Environments'),
    _item('mtat', 'MTATs'),
    _item('cifunction', 'CI Functions'),
)

reports_items = (
    _report_item('tenant_report', 'Service List'),
    _report_item('offerings_tree', 'Service View'),
    _report_item('product_view', 'Product View'),
    _report_item('three_c_report', '3C', permissions=['service_specification.view_threecsnapshot']),
)

three_c_items = (
    _item('threecrule', '3C Rules'),
    PluginMenuItem(
        link='plugins:service_specification:three_c_settings',
        link_text='3C Settings',
        permissions=['service_specification.change_threecsettings'],
    ),
    PluginMenuItem(
        link='plugins:service_specification:threecsnapshot_list',
        link_text='3C Snapshots',
        permissions=['service_specification.view_threecsnapshot'],
    ),
)

menu = PluginMenu(
    label='Service Specification',
    icon_class='mdi mdi-briefcase-outline',
    groups=(
        ('Data Model', data_model_items),
        ('Contracts', contract_items),
        ('Support', support_items),
        ('Reports', reports_items),
        ('3C Setup', three_c_items),
    ),
)
