from netbox.choices import ButtonColorChoices
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem


def _item(model_name, link_text):
    return PluginMenuItem(
        link=f'plugins:csdm:{model_name}_list',
        link_text=link_text,
        permissions=[f'csdm.view_{model_name}'],
        buttons=(
            PluginMenuButton(
                link=f'plugins:csdm:{model_name}_add',
                title=f'Add {link_text}',
                icon_class='mdi mdi-plus-thick',
                color=ButtonColorChoices.GREEN,
                permissions=[f'csdm.add_{model_name}'],
            ),
        ),
    )


data_model_items = (
    _item('portfolio', 'Service Portfolios'),
    _item('service', 'Services'),
    _item('serviceoffering', 'Service Offerings'),
    _item('appservice', 'Application Services'),
    _item('techci', 'Technical CIs'),
)

support_items = (
    _item('lifecycle', 'Lifecycle Managements'),
    _item('sla', 'SLAs'),
    _item('operationtime', 'Operation Times'),
    _item('availability', 'Availabilities'),
    _item('criticality', 'Criticalities'),
    _item('environment', 'Environments'),
    _item('mtat', 'MTATs'),
)

menu = PluginMenu(
    label='CSDM',
    icon_class='mdi mdi-briefcase-outline',
    groups=(
        ('Data Model', data_model_items),
        ('Support', support_items),
    ),
)
