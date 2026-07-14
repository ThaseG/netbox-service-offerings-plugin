PLUGINS = [
    "netbox_topology_views",
    "netbox_lifecycle",
    "netbox_secrets",
    "csdm",
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
    "netbox_secrets": {
        # Objects that can have secrets attached. Extend as needed.
        "apps": [
            "dcim.device",
            "virtualization.virtualmachine",
        ],
    },
}
