import pynetbox
import json
import os

NETBOX_URL = os.getenv('NETBOX_URL', 'http://localhost:8080')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN', 'your_netbox_token_here')

nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

devices = []

for device in nb.dcim.devices.all():
    device_data = {
        "name": device.name,
        "interfaces": [],
        "ip_addresses": [],
        "vlans": [],
        "ip_ranges": [],
        "prefixes": [],
        "cables": []
    }

    interfaces = nb.dcim.interfaces.filter(device=device.name)
    for iface in interfaces:
        device_data["interfaces"].append({
            "name": iface.name,
            "type": str(iface.type) if iface.type else None,
            "enabled": str(iface.enabled).lower() if iface.enabled is not None else "false",
            "description": iface.description,
            "mode": str(iface.mode) if iface.mode else None,
            "vlan": iface.untagged_vlan.vid if iface.untagged_vlan else None,
            "ip": None 
        })

    ip_addresses = nb.ipam.ip_addresses.filter(device=device.name)
    for ip in ip_addresses:
        device_data["ip_addresses"].append({
            "address": ip.address,
            "status": str(ip.status) if ip.status else None,
            "description": ip.description
        })

        if ip.assigned_object:
            iface_name = ip.assigned_object.name
            for iface in device_data["interfaces"]:
                if iface["name"] == iface_name:
                    iface["ip"] = ip.address

    site = device.site.name if device.site else None
    if site:
        vlans = nb.ipam.vlans.filter(site=site)
        for vlan in vlans:
            device_data["vlans"].append({
                "vlan_id": vlan.vid,
                "vlan_name": vlan.name
            })

        prefixes = nb.ipam.prefixes.filter(site=site)
        for prefix in prefixes:
            device_data["prefixes"].append({
                "prefix": prefix.prefix,
                "prefix_details": prefix.description
            })

        ip_ranges = nb.ipam.ip_ranges.filter(site=site)
        for rng in ip_ranges:
            device_data["ip_ranges"].append({
                "start_address": rng.start_address,
                "end_address": rng.end_address,
                "description": rng.description
            })

    cables = nb.dcim.cables.filter(device_id=device.id)
    for cable in cables:
        try:
            device_data["cables"].append({
                "type": str(cable.type) if cable.type else None,
                "side_a_devices": cable.a_terminations[0].device.name,
                "side_a_name": cable.a_terminations[0].name,
                "side_b_devices": cable.b_terminations[0].device.name,
                "side_b_name": cable.b_terminations[0].name
            })
        except Exception as e:
            print(f"Error parsing cable for device {device.name}: {e}")

    devices.append(device_data)

print(json.dumps(devices, indent=2))

        