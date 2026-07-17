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


data_model_items = (
    _item('portfolio', 'Service Portfolios'),
    _item('service', 'Services'),
    _item('serviceoffering', 'Service Offerings'),
    _item('appservice', 'Application Services'),
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

menu = PluginMenu(
    label='Service Specification',
    icon_class='mdi mdi-briefcase-outline',
    groups=(
        ('Data Model', data_model_items),
        ('Support', support_items),
    ),
)
