PLUGINS = [
    "netbox_topology_views",
    "netbox_lifecycle",
    "service_specification",
]

PLUGINS_CONFIG = {
    "netbox_topology_views": {
        "allow_coordinates_saving": True,
        "always_save_coordinates": False,
    },
    "netbox_lifecycle": {
        "lifecycle_card_position": "right_page",
        "contract_card_position": "right_page",
    },
}
