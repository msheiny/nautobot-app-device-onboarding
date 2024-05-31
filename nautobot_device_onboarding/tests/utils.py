"""Testing utilites."""

from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.choices import InterfaceTypeChoices
from nautobot.dcim.models import Device, DeviceType, Interface, Location, LocationType, Manufacturer, Platform
from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices
from nautobot.extras.models import Role, Secret, SecretsGroup, SecretsGroupAssociation, Status
from nautobot.ipam.choices import IPAddressTypeChoices, PrefixTypeChoices
from nautobot.ipam.models import IPAddress, IPAddressToInterface, Namespace, Prefix


def sync_network_data_ensure_required_nautobot_objects():
    """Ensure the requied Nautobot objects needed for testing exist."""
    testing_objects = {}

    status, _ = Status.objects.get_or_create(name="Active")
    status.content_types.add(ContentType.objects.get_for_model(Device))
    status.content_types.add(ContentType.objects.get_for_model(Prefix))
    status.content_types.add(ContentType.objects.get_for_model(IPAddress))
    status.content_types.add(ContentType.objects.get_for_model(Location))
    status.content_types.add(ContentType.objects.get_for_model(Interface))
    status.content_types.add(ContentType.objects.get_for_model(Interface))
    status.validated_save()

    username_secret, _ = Secret.objects.get_or_create(
        name="username", provider="environment-variable", parameters={"variable": "DEVICE_USER"}
    )
    password_secret, _ = Secret.objects.get_or_create(
        name="password", provider="environment-variable", parameters={"variable": "DEVICE_PASS"}
    )
    secrets_group, _ = SecretsGroup.objects.get_or_create(name="test secrets group")
    SecretsGroupAssociation.objects.get_or_create(
        secrets_group=secrets_group,
        secret=username_secret,
        access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
        secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME,
    )
    SecretsGroupAssociation.objects.get_or_create(
        secrets_group=secrets_group,
        secret=password_secret,
        access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
        secret_type=SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
    )

    namespace, _ = Namespace.objects.get_or_create(name="Global")

    prefix, _ = Prefix.objects.get_or_create(
        prefix="10.1.1.0/24",
        namespace=namespace,
        type=PrefixTypeChoices.TYPE_NETWORK,
        status=status,
    )
    ip_address_1, _ = IPAddress.objects.get_or_create(
        host="10.1.1.10", mask_length=24, type=IPAddressTypeChoices.TYPE_HOST, status=status
    )
    ip_address_2, _ = IPAddress.objects.get_or_create(
        host="10.1.1.11", mask_length=24, type=IPAddressTypeChoices.TYPE_HOST, status=status
    )
    ip_address_3, _ = IPAddress.objects.get_or_create(
        host="10.1.1.15", mask_length=24, type=IPAddressTypeChoices.TYPE_HOST, status=status
    )
    location_type, _ = LocationType.objects.get_or_create(name="Site")
    location_type.content_types.add(ContentType.objects.get_for_model(Device))
    location_type.validated_save()
    location, _ = Location.objects.get_or_create(name="Site A", location_type=location_type, status=status)

    device_role, _ = Role.objects.get_or_create(name="Network")
    device_role.content_types.add(ContentType.objects.get_for_model(Device))
    device_role.validated_save()

    manufacturer, _ = Manufacturer.objects.get_or_create(name="Cisco")

    platform_1, _ = Platform.objects.get_or_create(
        name="cisco_ios", network_driver="cisco_ios", manufacturer=manufacturer
    )
    platform_2, _ = Platform.objects.get_or_create(
        name="cisco_xe", network_driver="cisco_xe", manufacturer=manufacturer
    )

    device_type, _ = DeviceType.objects.get_or_create(model="CSR1000V17", manufacturer=manufacturer)
    device_1, _ = Device.objects.get_or_create(
        name="demo-cisco-xe1",
        serial="9ABUXU581111",
        device_type=device_type,
        status=status,
        location=location,
        role=device_role,
        platform=platform_1,
        secrets_group=secrets_group,
    )
    device_2, _ = Device.objects.get_or_create(
        name="demo-cisco-xe2",
        serial="9ABUXU5882222",
        device_type=device_type,
        status=status,
        location=location,
        role=device_role,
        platform=platform_2,
        secrets_group=secrets_group,
    )
    device_3, _ = Device.objects.get_or_create(
        name="demo-cisco-xe3",
        serial="9ABUXU5883333",
        device_type=device_type,
        status=status,
        location=location,
        role=device_role,
        platform=platform_2,
        secrets_group=secrets_group,
    )
    interface_1, _ = Interface.objects.get_or_create(
        device=device_1, name="GigabitEthernet1", status=status, type=InterfaceTypeChoices.TYPE_VIRTUAL
    )
    interface_2, _ = Interface.objects.get_or_create(
        device=device_2, name="GigabitEthernet1", status=status, type=InterfaceTypeChoices.TYPE_VIRTUAL
    )
    interface_3, _ = Interface.objects.get_or_create(
        device=device_3, name="GigabitEthernet1", status=status, type=InterfaceTypeChoices.TYPE_VIRTUAL
    )
    IPAddressToInterface.objects.get_or_create(interface=interface_1, ip_address=ip_address_1)
    device_1.primary_ip4 = ip_address_1
    device_1.validated_save()

    IPAddressToInterface.objects.get_or_create(interface=interface_2, ip_address=ip_address_2)
    device_2.primary_ip4 = ip_address_2
    device_2.validated_save()

    IPAddressToInterface.objects.get_or_create(interface=interface_3, ip_address=ip_address_3)
    device_3.primary_ip4 = ip_address_3
    device_3.validated_save()

    testing_objects["status"] = status
    testing_objects["secrets_group"] = secrets_group
    testing_objects["namespace"] = namespace
    testing_objects["location"] = location
    testing_objects["manufacturer"] = manufacturer
    testing_objects["device_role"] = device_role
    testing_objects["device_type"] = device_type
    testing_objects["platform_1"] = platform_1
    testing_objects["platform_2"] = platform_2
    testing_objects["prefix"] = prefix
    testing_objects["ip_address_1"] = ip_address_1
    testing_objects["ip_address_2"] = ip_address_2
    testing_objects["ip_address_3"] = ip_address_3
    testing_objects["device_1"] = device_1
    testing_objects["device_2"] = device_2
    testing_objects["device_3"] = device_3

    return testing_objects


def sync_devices_ensure_required_nautobot_objects():
    """Ensure the requied Nautobot objects needed for testing exist."""
    testing_objects = {}

    status, _ = Status.objects.get_or_create(name="Active")
    status.content_types.add(ContentType.objects.get_for_model(Device))
    status.content_types.add(ContentType.objects.get_for_model(Prefix))
    status.content_types.add(ContentType.objects.get_for_model(IPAddress))
    status.content_types.add(ContentType.objects.get_for_model(Location))
    status.content_types.add(ContentType.objects.get_for_model(Interface))
    status.content_types.add(ContentType.objects.get_for_model(Interface))
    status.validated_save()

    username_secret, _ = Secret.objects.get_or_create(
        name="username", provider="environment-variable", parameters={"variable": "DEVICE_USER"}
    )
    password_secret, _ = Secret.objects.get_or_create(
        name="password", provider="environment-variable", parameters={"variable": "DEVICE_PASS"}
    )
    secrets_group, _ = SecretsGroup.objects.get_or_create(name="test secrets group")
    SecretsGroupAssociation.objects.get_or_create(
        secrets_group=secrets_group,
        secret=username_secret,
        access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
        secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME,
    )
    SecretsGroupAssociation.objects.get_or_create(
        secrets_group=secrets_group,
        secret=password_secret,
        access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
        secret_type=SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
    )

    namespace, _ = Namespace.objects.get_or_create(name="Global")

    prefix, _ = Prefix.objects.get_or_create(
        prefix="192.1.1.0/24",
        namespace=namespace,
        type=PrefixTypeChoices.TYPE_NETWORK,
        status=status,
    )
    ip_address_1, _ = IPAddress.objects.get_or_create(
        host="192.1.1.10", mask_length=24, type=IPAddressTypeChoices.TYPE_HOST, status=status
    )
    ip_address_2, _ = IPAddress.objects.get_or_create(
        host="192.1.1.11", mask_length=24, type=IPAddressTypeChoices.TYPE_HOST, status=status
    )

    location_type, _ = LocationType.objects.get_or_create(name="Site")
    location_type.content_types.add(ContentType.objects.get_for_model(Device))
    location_type.validated_save()
    location, _ = Location.objects.get_or_create(name="Site A", location_type=location_type, status=status)

    device_role, _ = Role.objects.get_or_create(name="Network")
    device_role.content_types.add(ContentType.objects.get_for_model(Device))
    device_role.validated_save()

    manufacturer, _ = Manufacturer.objects.get_or_create(name="Cisco")

    platform, _ = Platform.objects.get_or_create(
        name="cisco_nxos", network_driver="cisco_nxos", manufacturer=manufacturer
    )

    device_type, _ = DeviceType.objects.get_or_create(
        model="CSR1000V17", part_number="CSR1000V17", manufacturer=manufacturer
    )
    device_1, _ = Device.objects.get_or_create(
        name="test device 1",
        serial="test-serial-abc",
        device_type=device_type,
        status=status,
        location=location,
        role=device_role,
        platform=platform,
        secrets_group=secrets_group,
    )
    device_2, _ = Device.objects.get_or_create(
        name="test device",
        serial="test-serial-123",
        device_type=device_type,
        status=status,
        location=location,
        role=device_role,
        platform=platform,
        secrets_group=secrets_group,
    )
    interface_1, _ = Interface.objects.get_or_create(
        device=device_1, name="GigabitEthernet1", status=status, type=InterfaceTypeChoices.TYPE_VIRTUAL
    )
    IPAddressToInterface.objects.get_or_create(interface=interface_1, ip_address=ip_address_1)
    device_1.primary_ip4 = ip_address_1
    device_1.validated_save()

    interface_2, _ = Interface.objects.get_or_create(
        device=device_2, name="GigabitEthernet1", status=status, type=InterfaceTypeChoices.TYPE_VIRTUAL
    )
    IPAddressToInterface.objects.get_or_create(interface=interface_2, ip_address=ip_address_2)
    device_2.primary_ip4 = ip_address_2
    device_2.validated_save()

    testing_objects["status"] = status
    testing_objects["secrets_group"] = secrets_group
    testing_objects["namespace"] = namespace
    testing_objects["location"] = location
    testing_objects["manufacturer"] = manufacturer
    testing_objects["device_role"] = device_role
    testing_objects["device_type"] = device_type
    testing_objects["platform"] = platform
    testing_objects["prefix"] = prefix
    testing_objects["ip_address_1"] = ip_address_1
    testing_objects["ip_address_2"] = ip_address_2
    testing_objects["device_1"] = device_1
    testing_objects["device_2"] = device_2

    return testing_objects
