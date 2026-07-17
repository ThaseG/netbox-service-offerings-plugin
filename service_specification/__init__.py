from netbox.plugins import PluginConfig


class ServiceSpecificationConfig(PluginConfig):
    name = 'service_specification'
    verbose_name = 'Service Specification'
    description = 'Business and Technical Service Offerings (Service Specification) for NetBox'
    version = '1.0.2'
    author = 'ThaseG'
    base_url = 'service-specification'
    min_version = '4.6.0'


config = ServiceSpecificationConfig
