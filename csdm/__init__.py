from netbox.plugins import PluginConfig


class CSDMConfig(PluginConfig):
    name = 'csdm'
    verbose_name = 'CSDM'
    description = 'Business and Technical Service Offerings (CSDM) for NetBox'
    version = '1.0.0'
    author = 'ThaseG'
    base_url = 'csdm'
    min_version = '4.6.0'


config = CSDMConfig
