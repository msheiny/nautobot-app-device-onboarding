"""Test Cisco Support adapter."""

from unittest.mock import patch

from diffsync.exceptions import ObjectNotFound
from nautobot.core.testing import TransactionTestCase
from nautobot.dcim.models import Device, DeviceType, Manufacturer, Platform
from nautobot.extras.models import JobResult, JobLogEntry

from nautobot_device_onboarding.diffsync.adapters.sync_network_data_adapters import (
    SyncNetworkDataNautobotAdapter,
    SyncNetworkDataNetworkAdapter,
)
from nautobot_device_onboarding.jobs import SSOTSyncDevices
from nautobot_device_onboarding.tests import utils
from nautobot_device_onboarding.tests.fixtures import sync_network_data_fixture


class SyncNetworkDataNetworkAdapterTestCase(TransactionTestCase):
    """Test SyncNetworkDataNetworkAdapter class."""

    databases = ("default", "job_logs")

    def setUp(self):  # pylint: disable=invalid-na
        """Initialize test case."""
        # Setup Nautobot Objects
        self.testing_objects = utils.sync_network_data_ensure_required_nautobot_objects()

        # Setup Job
        self.job = SSOTSyncDevices()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, user=None, task_name="fake task", worker="default"
        )
        self.job.command_getter_result = sync_network_data_fixture.sync_network_mock_data_valid

        # Form inputs
        self.job.interface_status = self.testing_objects["status"]
        self.job.ip_address_status = self.testing_objects["status"]
        self.job.location = self.testing_objects["location"]
        self.job.sync_vlans = True
        self.job.sync_vrfs = True
        self.job.debug = True
        self.job.devices_to_load = None

        self.sync_network_data_adapter = SyncNetworkDataNetworkAdapter(job=self.job, sync=None)

    def test_handle_failed_devices(self):
        """Devices that failed to returned pardsed data should be removed from results."""
        # Add a failed device to the mock returned data
        self.job.command_getter_result.update(sync_network_data_fixture.failed_device)

        self.sync_network_data_adapter._handle_failed_devices(device_data=self.job.command_getter_result)
        self.assertNotIn("demo-cisco-xe3", self.job.command_getter_result.keys())

    @patch("nautobot_device_onboarding.diffsync.adapters.sync_network_data_adapters.sync_network_data_command_getter")
    def test_execute_command_getter(self, command_getter_result):
        """Test execute command getter."""
        command_getter_result.return_value = sync_network_data_fixture.sync_network_mock_data_valid
        command_getter_result.update(sync_network_data_fixture.failed_device)
        self.sync_network_data_adapter.execute_command_getter()
        self.assertIn(
            self.testing_objects["device_1"].name, list(self.job.devices_to_load.values_list("name", flat=True))
        )
        self.assertIn(
            self.testing_objects["device_2"].name, list(self.job.devices_to_load.values_list("name", flat=True))
        )

    def test_load_devices(self):
        """Test loading device data returned from command getter into the diffsync store."""
        self.sync_network_data_adapter.load_devices()

        # test loaded devices
        for hostname, device_data in self.job.command_getter_result.items():
            unique_id = f"{hostname}__{device_data['serial']}"
            diffsync_obj = self.sync_network_data_adapter.get("device", unique_id)
            self.assertEqual(hostname, diffsync_obj.name)
            self.assertEqual(device_data["serial"], diffsync_obj.serial)

        # test child interfaces which are loaded along with devices
        for hostname, device_data in self.job.command_getter_result.items():
            for interface_name, interface_data in device_data["interfaces"].items():
                unique_id = f"{hostname}__{interface_name}"
                diffsync_obj = self.sync_network_data_adapter.get("interface", unique_id)
                self.assertEqual(hostname, diffsync_obj.device__name)
                self.assertEqual(interface_name, diffsync_obj.name)
                self.assertEqual(self.testing_objects["status"].name, diffsync_obj.status__name)
                self.assertEqual(
                    self.sync_network_data_adapter._process_mac_address(mac_address=interface_data["mac_address"]),
                    diffsync_obj.mac_address,
                )
                self.assertEqual(interface_data["802.1Q_mode"], diffsync_obj.mode)
                self.assertEqual(interface_data["link_status"], diffsync_obj.enabled)
                self.assertEqual(interface_data["description"], diffsync_obj.description)

    def test_load_ip_addresses(self):
        """Test loading ip address data returned from command getter into the diffsync store."""
        self.sync_network_data_adapter.load_ip_addresses()

        for _, device_data in self.job.command_getter_result.items():
            for _, interface_data in device_data["interfaces"].items():
                if interface_data["ip_addresses"]:
                    for ip_address in interface_data["ip_addresses"]:
                        if ip_address["ip_address"]:
                            unique_id = ip_address["ip_address"]
                            diffsync_obj = self.sync_network_data_adapter.get("ip_address", unique_id)
                            self.assertEqual(ip_address["ip_address"], diffsync_obj.host)
                            self.assertEqual(4, diffsync_obj.ip_version)
                            self.assertEqual(int(ip_address["prefix_length"]), diffsync_obj.mask_length)
                            self.assertEqual(self.job.ip_address_status.name, diffsync_obj.status__name)

    def test_load_vlans(self):
        """Test loading vlan data returned from command getter into the diffsync store."""
        self.job.devices_to_load = Device.objects.filter(name__in=["demo-cisco-xe1", "demo-cisco-xe2"])
        self.sync_network_data_adapter.load_vlans()

        for _, device_data in self.job.command_getter_result.items():
            for _, interface_data in device_data["interfaces"].items():
                for tagged_vlan in interface_data["tagged_vlans"]:
                    unique_id = f"{tagged_vlan['id']}__{tagged_vlan['name']}__{self.job.location.name}"
                    diffsync_obj = self.sync_network_data_adapter.get("vlan", unique_id)
                    self.assertEqual(int(tagged_vlan["id"]), diffsync_obj.vid)
                    self.assertEqual(tagged_vlan["name"], diffsync_obj.name)
                    self.assertEqual(self.job.location.name, diffsync_obj.location__name)
                if interface_data["untagged_vlan"]:
                    unique_id = f"{interface_data['untagged_vlan']['id']}__{interface_data['untagged_vlan']['name']}__{self.job.location.name}"
                    diffsync_obj = self.sync_network_data_adapter.get("vlan", unique_id)
                    self.assertEqual(int(interface_data['untagged_vlan']["id"]), diffsync_obj.vid)
                    self.assertEqual(interface_data['untagged_vlan']["name"], diffsync_obj.name)
                    self.assertEqual(self.job.location.name, diffsync_obj.location__name)


# TODO: SyncNetworkDataNautobotAdapterTestCase
