#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014,2015,2016,2017  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the update disk command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from eventstest import EventsTestMixin


class TestUpdateDisk(EventsTestMixin, TestBrokerCommand):

    def test_100_update_ut3c1n3_sda(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--size", "50", "--comments", "New disk comments",
                   "--controller", "sata", "--address", "0:0:0:0",
                   "--bus_address", "pci:0000:02:00.0"]
        self.noouttest(command)

    def test_101_update_ut3c1n3_c0d0(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "c0d0",
                   "--rename_to", "c0d1", "--boot"]
        self.noouttest(command)

    def test_102_update_ut3c1n3_c0d0_hostname(self):
        command = ["update_disk", "--hostname", "unittest00.one-nyp.ms.com", "--disk", "c0d1",
                   "--rename_to", "test", "--boot"]
        self.noouttest(command)
        command_verify = ["show_machine", "--machine", "ut3c1n3"]
        out = self.commandtest(command_verify)
        self.searchoutput(out,
                          r'Disk: test 34 GB cciss \(local\) \[boot\]\s*'
                          r'WWN: 600508b112233445566778899aabbccd\s*'
                          r'Controller Bus Address: pci:0000:01:00.0$',
                          command_verify)

    def test_103_update_ut3c1n3_c0d0_hostname_back(self):
        command = ["update_disk", "--hostname", "unittest00.one-nyp.ms.com", "--disk", "test",
                   "--rename_to", "c0d1", "--boot"]
        self.noouttest(command)
        command_verify = ["show_machine", "--machine", "ut3c1n3"]
        out = self.commandtest(command_verify)
        self.searchoutput(out,
                          r'Disk: c0d1 34 GB cciss \(local\) \[boot\]\s*'
                          r'WWN: 600508b112233445566778899aabbccd\s*'
                          r'Controller Bus Address: pci:0000:01:00.0$',
                          command_verify)

    def test_105_show_ut3c1n3(self):
        command = ["show_machine", "--machine", "ut3c1n3"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Disk: sda 50 GB sata \(local\)\s*'
                          r'Address: 0:0:0:0\s*'
                          r'Controller Bus Address: pci:0000:02:00.0\s*'
                          r'Comments: New disk comments$',
                          command)
        self.searchoutput(out,
                          r'Disk: c0d1 34 GB cciss \(local\) \[boot\]\s*'
                          r'WWN: 600508b112233445566778899aabbccd\s*'
                          r'Controller Bus Address: pci:0000:01:00.0$',
                          command)

    def test_105_show_ut3c1n3_proto(self):
        command = ["show_machine", "--machine", "ut3c1n3", "--format", "proto"]
        machine = self.protobuftest(command, expect=1)[0]
        self.assertEqual(machine.name, "ut3c1n3")
        self.assertEqual(len(machine.disks), 2)
        self.assertEqual(machine.disks[0].device_name, "c0d1")
        self.assertEqual(machine.disks[0].capacity, 34)
        self.assertEqual(machine.disks[0].disk_type, "cciss")
        self.assertEqual(machine.disks[0].wwn, "600508b112233445566778899aabbccd")
        self.assertEqual(machine.disks[0].bus_address, "pci:0000:01:00.0")
        self.assertEqual(machine.disks[1].device_name, "sda")
        self.assertEqual(machine.disks[1].capacity, 50)
        self.assertEqual(machine.disks[1].disk_type, "sata")
        self.assertEqual(machine.disks[1].address, "0:0:0:0")
        self.assertEqual(machine.disks[1].bus_address, "pci:0000:02:00.0")

    def test_105_cat_ut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"harddisks/{cciss/c0d1}" = '
                          r'create\("hardware/harddisk/generic/cciss",\s*'
                          r'"boot", true,\s*'
                          r'"bus", "pci:0000:01:00.0",\s*'
                          r'"capacity", 34\*GB,\s*'
                          r'"interface", "cciss",\s*'
                          r'"wwn", "600508b112233445566778899aabbccd"\s*\);',
                          command)
        self.searchoutput(out,
                          r'"harddisks/{sda}" = '
                          r'create\("hardware/harddisk/generic/sata",\s*'
                          r'"address", "0:0:0:0",\s*'
                          r'"bus", "pci:0000:02:00.0",\s*'
                          r'"capacity", 50\*GB,\s*'
                          r'"interface", "sata"\s*\);',
                          command)
        self.matchclean(out, "c0d0", command)

    def test_110_prepare_vm_test(self):
        self.noouttest(["add_filesystem", "--filesystem", "disk_update_test",
                        "--cluster", "utecl5", "--type", "ext3",
                        "--mountpoint", "/backend", "--blockdevice", "sdc",
                        "--bootmount"])

    def test_111_move_disk_to_fs(self):
        command = ["update_disk", "--machine", "evm10", "--disk", "sda",
                   "--filesystem", "disk_update_test", "--address", "0:1",
                   "--snapshot"]
        self.noouttest(command)

    def test_111_update_iops(self):
        command = ["update_disk", "--machine", "evm10", "--disk", "sda",
                   "--iops_limit", "15"]
        out = self.internalerrortest(command)
        self.matchoutput(out, "The value of iops_limit must be 16 or greater.", command)

        command = ["update_disk", "--machine", "evm10", "--disk", "sda",
                   "--iops_limit", "30"]
        self.statustest(command)

    def test_112_verify_utecl5_share(self):
        command = ["search_machine", "--share", "utecl5_share"]
        out = self.commandtest(command)
        self.matchclean(out, "evm10", command)

    def test_112_verify_fs(self):
        command = ["show_filesystem", "--filesystem", "disk_update_test",
                   "--cluster", "utecl5"]
        out = self.commandtest(command)
        self.matchoutput(out, "Virtual Disk Count: 1", command)

    def test_112_show_evm10(self):
        command = ["show", "machine", "--machine", "evm10"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Disk: sda 45 GB scsi (virtual_disk stored on "
                         "filesystem disk_update_test) [boot, snapshot]",
                         command)
        self.matchclean(out, "utecl5_share", command)

    def test_112_cat_evm10(self):
        command = ["cat", "--machine", "evm10"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"harddisks/{sda}" = nlist\(\s*'
                          r'"address", "0:1",\s*'
                          r'"boot", true,\s*'
                          r'"capacity", 45\*GB,\s*'
                          r'"filesystemname", "disk_update_test",\s*'
                          r'"interface", "scsi",\s*'
                          r'"iopslimit", 30,\s*'
                          r'"mountpoint", "/backend",\s*'
                          r'"path", "evm10/sda\.vmdk",\s*'
                          r'"snapshot", true\s*\);',
                          command)
        self.matchclean(out, "utecl5_share", command)

    def test_113_move_disk_to_share(self):
        command = ["update_disk", "--machine", "evm10", "--disk", "sda",
                   "--share", "utecl5_share", "--address", "0:0",
                   "--nosnapshot"]
        self.noouttest(command)

    def test_114_verify_utecl5_share(self):
        command = ["search_machine", "--share", "utecl5_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm10", command)

    def test_114_verify_fs(self):
        command = ["show_filesystem", "--filesystem", "disk_update_test",
                   "--cluster", "utecl5"]
        out = self.commandtest(command)
        self.matchoutput(out, "Virtual Disk Count: 0", command)

    def test_114_show_evm10(self):
        command = ["show", "machine", "--machine", "evm10"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Disk: sda 45 GB scsi (virtual_disk stored on "
                         "share utecl5_share) [boot]",
                         command)
        self.matchoutput(out, "IOPS Limit: 30", command)
        self.matchclean(out, "disk_update_test", command)

    def test_114_cat_evm10(self):
        command = ["cat", "--machine", "evm10"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"harddisks/{sda}" = nlist\(\s*'
                          r'"address", "0:0",\s*'
                          r'"boot", true,\s*'
                          r'"capacity", 45\*GB,\s*'
                          r'"interface", "scsi",\s*'
                          r'"iopslimit", 30,\s*'
                          r'"mountpoint", "/vol/lnn30f1v1/utecl5_share",\s*'
                          r'"path", "evm10/sda.vmdk",\s*'
                          r'"server", "lnn30f1",\s*'
                          r'"sharename", "utecl5_share",\s*'
                          r'"snapshot", false\s*\);',
                          command)
        self.matchclean(out, "disk_update_test", command)

    def test_119_cleanup_vm_test(self):
        self.noouttest(["del_filesystem", "--cluster", "utecl5",
                        "--filesystem", "disk_update_test"])

    def test_120_clear_wwn(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "c0d1",
                   "--wwn", ""]
        self.noouttest(command)

    def test_122_verify_no_wwn(self):
        command = ["show_machine", "--machine", "ut3c1n3"]
        out = self.commandtest(command)
        self.matchclean(out, "WWN", command)

        command = ["cat", "--machine", "ut3c1n3"]
        out = self.commandtest(command)
        self.matchclean(out, "wwn", command)

    def test_123_update_wwn(self):
        # Test the use of separators
        command = ["update_disk", "--machine", "ut3c5n10", "--disk", "sdb",
                   "--wwn", "60:05:08:b1:12:23:34:45-56:67:78:89:9a:ab:bc:cd"]
        self.noouttest(command)

    def test_124_verify_wwn_update(self):
        command = ["show_machine", "--machine", "ut3c5n10"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Disk: sdb.*$'
                          r'\s*Address: 0:0:1:0$'
                          r'\s*WWN: 600508b112233445566778899aabbccd$',
                          command)

        command = ["cat", "--machine", "ut3c5n10"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"harddisks/{sdb}" = '
                          r'create\("hardware/harddisk/generic/scsi",\s*'
                          r'"address", "0:0:1:0",\s*'
                          r'"capacity", 34\*GB,\s*'
                          r'"interface", "scsi",\s*'
                          r'"wwn", "600508b112233445566778899aabbccd"\s*\);',
                          command)

    def test_300_rename_exists(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--rename_to", "c0d1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "LocalDisk c0d1, machine "
                         "unittest00.one-nyp.ms.com already exists.", command)

    def test_300_bad_controller(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--controller", "bad-controller"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "bad-controller is not a valid controller type, "
                         "use one of: cciss, fibrechannel, flash, ide, "
                         "nvme, sas, sata, scsi.",
                         command)

    def test_300_bad_address(self):
        command = ["update_disk", "--machine", "evm10", "--disk", "sda",
                   "--address", "bad-address"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         r"Disk address 'bad-address' is not valid, "
                         r"it must match \d+:\d+$.",
                         command)

    def test_300_address_localdisk(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--address", "0:0"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         r"Disk address '0:0' is not valid, "
                         r"it must match (?:\d+:){3}\d+$.",
                         command)

    def test_300_snapshot_localdisk(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--snapshot"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Snapshot capability can only be set for "
                         "virtual disks.", command)

    def test_300_iops(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--iops_limit", "100"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "IOPS limit can only be set for virtual disks.", command)

    def test_300_share_localdisk(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--share", "test_share_1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Disk sda of machine unittest00.one-nyp.ms.com "
                         "is not a virtual disk, changing the backend store is "
                         "not possible.", command)

    def test_300_bad_wwn_syntax(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--wwn", "not-a-wwn"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The value of --wwn may contain hexadecimal "
                         "characters only.",
                         command)

    def test_300_bad_wwn_length(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--wwn", "00:11:22:33:44:55:66:77:88"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The value of --wwn must contain either 16 or 32 "
                         "hexadecimal digits.",
                         command)

    def test_300_bad_share(self):
        command = ["update_disk", "--disk", "sda", "--machine", "evm40",
                   "--share", "non_existent_share",
                   "--resourcegroup", "utmc8as1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl13 does not have share "
                         "non_existent_share assigned to it in "
                         "resourcegroup utmc8as1.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
