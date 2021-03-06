#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016,2017,2018  Contributor
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
"""Build infrastructure for testing HA clusters"""

import unittest
import re

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from machinetest import MachineTestMixin

dnsdomain = "aqd-unittest.ms.com"

def host_fqdn(host):
    """ Return FQDN given a node name. """
    return "%s.%s" % (host, dnsdomain)


config = {
    # Buildings to add
    "building": {
        "utb1": {"address": "Unit 1 Test Park", "city": "ny", "next_rackid": "1"},
        "utb2": {"address": "Unit 2 Test Park", "city": "ny", "next_rackid": "1"},
        "utb3": {"address": "Unit 3 Test Park", "city": "ny", "next_rackid": "1"},
    },

    # Service mappings required (by service name and instance)
    "map": {
        "afs": "q.ny.ms.com",
        "bootserver": "unittest",
        "dns": "unittest",
    },

    # Racks to add
    "rack": {
        "utb11": {"row": "1", "column": "a", "building": "utb1", "fullname": "utb1-1a"},
        "utb12": {"row": "1", "column": "b", "building": "utb1", "fullname": "utb1-1b"},
        "utb21": {"row": "1", "column": "a", "building": "utb2", "fullname": "utb2-1a"},
        "utb31": {"row": "1", "column": "a", "building": "utb3", "fullname": "utb3-1a"},
    },

    # Hosts to add and cluster
    "host": {
        "utbhost01": {"cluster": "utbvcs1a", "rack": "utb11"},
        "utbhost02": {"cluster": "utbvcs1a", "rack": "utb12"},
        "utbhost03": {"cluster": "utbvcs1b", "rack": "utb11"},
        "utbhost04": {"cluster": "utbvcs1b", "rack": "utb12"},
        "utbhost05": {"cluster": "utbvcs1c", "rack": "utb11"},
        "utbhost06": {"cluster": "utbvcs1c", "rack": "utb12"},
        "utbhost07": {"cluster": "utbvcs1d", "rack": "utb11"},
        "utbhost08": {"cluster": "utbvcs1d", "rack": "utb12"},

        "utbhost09": {"cluster": "utbvcs2a", "rack": "utb11"},
        "utbhost10": {"cluster": "utbvcs2a", "rack": "utb21"},
        "utbhost11": {"cluster": "utbvcs2b", "rack": "utb11"},
        "utbhost12": {"cluster": "utbvcs2b", "rack": "utb21"},
        "utbhost13": {"cluster": "utbvcs2c", "rack": "utb11"},
        "utbhost14": {"cluster": "utbvcs2c", "rack": "utb21"},
        "utbhost15": {"cluster": "utbvcs2d", "rack": "utb11"},
        "utbhost16": {"cluster": "utbvcs2d", "rack": "utb21"},

        "utbhost17": {"cluster": "utbvcs3a", "rack": "utb21"},
        "utbhost18": {"cluster": "utbvcs3a", "rack": "utb31"},
        "utbhost19": {"cluster": "utbvcs3b", "rack": "utb21"},
        "utbhost20": {"cluster": "utbvcs3b", "rack": "utb31"},
        "utbhost21": {"cluster": "utbvcs3c", "rack": "utb21"},
        "utbhost22": {"cluster": "utbvcs3c", "rack": "utb31"},
        "utbhost23": {"cluster": "utbvcs3d", "rack": "utb21"},
        "utbhost24": {"cluster": "utbvcs3d", "rack": "utb31"},
        "utbhost25": {"cluster": "utbvcs3e", "rack": "utb21"},
        "utbhost26": {"cluster": "utbvcs3e", "rack": "utb31"},
        "utbhost27": {"cluster": "utbvcs3f", "rack": "utb21"},
        "utbhost28": {"cluster": "utbvcs3f", "rack": "utb31"},

        "utbhost29": {"cluster": "utbvcs4a", "rack": "utb11"},
        "utbhost30": {"cluster": "utbvcs4a", "rack": "utb31"},
        "utbhost31": {"cluster": "utbvcs4b", "rack": "utb11"},
        "utbhost32": {"cluster": "utbvcs4b", "rack": "utb31"},
        "utbhost33": {"cluster": "utbvcs4c", "rack": "utb11"},
        "utbhost34": {"cluster": "utbvcs4c", "rack": "utb31"},
        "utbhost35": {"cluster": "utbvcs4d", "rack": "utb11"},
        "utbhost36": {"cluster": "utbvcs4d", "rack": "utb31"},
        "utbhost37": {"cluster": "utbvcs4e", "rack": "utb11"},
        "utbhost38": {"cluster": "utbvcs4e", "rack": "utb31"},
        "utbhost39": {"cluster": "utbvcs4f", "rack": "utb11"},
        "utbhost40": {"cluster": "utbvcs4f", "rack": "utb31"},

        "utbhost41": {"cluster": "utbvcs5a", "rack": "utb11"},
        "utbhost42": {"cluster": "utbvcs5a", "rack": "utb21"},
        "utbhost43": {"cluster": "utbvcs5a", "rack": "utb31"},
        "utbhost44": {"cluster": "utbvcs5b", "rack": "utb11"},
        "utbhost45": {"cluster": "utbvcs5b", "rack": "utb21"},
        "utbhost46": {"cluster": "utbvcs5b", "rack": "utb31"},
        "utbhost47": {"cluster": "utbvcs5c", "rack": "utb11"},
        "utbhost48": {"cluster": "utbvcs5c", "rack": "utb21"},
        "utbhost49": {"cluster": "utbvcs5c", "rack": "utb31"},
        "utbhost50": {"cluster": "utbvcs5d", "rack": "utb11"},
        "utbhost51": {"cluster": "utbvcs5d", "rack": "utb21"},
        "utbhost52": {"cluster": "utbvcs5d", "rack": "utb31"},
    },
}


def reset_config():
    """ Sets or resets additional keys in the config dict needed to
        support the test cases. """
    build_cluster_key()


def build_cluster_key():
    """ Create 'cluster' key based on entries in 'host' key in config dict,
       and create 'machine' if key is missing. """
    config["cluster"] = {}
    for host in config["host"]:
        config["cluster"].\
                    setdefault(config["host"][host]["cluster"], {}).\
                    setdefault("hosts", []).append(host)
        if "machine" not in config["host"][host]:
            config["host"][host]["machine"] = re.sub("host", "mach", host)

    for cluster in config["cluster"]:
        config["cluster"][cluster]["hosts"] = \
            tuple(sorted(config["cluster"][cluster]["hosts"]))



class TestBuildClusters(MachineTestMixin, TestBrokerCommand):

    @classmethod
    def setUpClass(cls):
        """ Fill in the computed bits of config dict prior to test execution """
        super(TestBuildClusters, cls).setUpClass()
        reset_config()

    def test_100_add_building(self):
        """ Add buildings needed for the use case """
        for building in config["building"]:
            args = config["building"][building]
            self.dsdb_expect("add_building_aq -building_name %s -city %s "
                             "-building_addr %s" % (building, args["city"],
                                                    args["address"]))
            self.dsdb_expect_add_campus_building("ny", building)
            self.noouttest(["add_building", "--building", building] +
                           ["--%s=%s" % (a, args[a]) for a in args])
            self.dsdb_verify()

            for service in config["map"]:
                command = ["map_service", "--service", service,
                           "--instance", config["map"][service],
                           "--building", building] + self.valid_just_tcm
                self.noouttest(command)

    def test_110_add_rack(self):
        """ Add racks needed for the use case """
        for rack in config["rack"]:
            args = config["rack"][rack]
            cmd = ["add_rack"] + ["--%s=%s" % (a, args[a]) for a in args]
            out = self.commandtest(cmd)
            self.matchoutput(out, rack, cmd)

    def test_120_add_host(self):
        """ Add hosts needed for the use case """
        ipidx = 0
        config["ip"] = {}
        for host in config["host"]:
            args = config["host"][host]
            ip = config["ip"][host] = self.net["aapb_net"].usable[ipidx]
            self.create_host(host_fqdn(host), ip, args["machine"],
                             model="utrackmount", memory=65536,
                             cpuname="utcpu", cpucount=2,
                             sda_size=500, sda_controller="sas",
                             rack=args["rack"], personality="utpers-prod",
                             osname="linux",
                             osversion=self.config.get("unittest",
                                                       "linux_version_curr"))
            ipidx += 1

    def test_130_add_cluster(self):
        """ Add clusters needed for the use case """
        for cluster in config["cluster"]:
            args = config["cluster"][cluster]
            self.noouttest(["add_cluster", "--cluster", cluster,
                            "--archetype", "hacluster",
                            "--personality", "hapersonality",
                            "--down_hosts_threshold", "0",
                            "--hub", "ny",
                            "--domain", "unittest",
                            "--max_members", len(args["hosts"])])

            for i in range(0, 2):
                rgname = "%sas%02d" % (cluster, i + 1)
                self.noouttest(["add_resourcegroup", "--resourcegroup", rgname,
                                "--cluster", cluster])
                self.noouttest(["add_filesystem", "--resourcegroup", rgname,
                                "--filesystem", rgname, "--type", "ext",
                                "--mountpoint", "/d/%s/d%d" % (cluster, i),
                                "--blockdevice",
                                "/dev/vx/dsk/%s.gnr.0/gnr.0" % rgname,
                                "--nobootmount"])

    def test_140_cluster(self):
        """ Add hosts to clusters needed for the use case """
        for cluster in config["cluster"]:
            for host in config["cluster"][cluster]["hosts"]:
                self.ignoreoutputtest(["cluster", "--cluster", cluster,
                                       "--hostn", host_fqdn(host)])
            self.noouttest(["update_cluster", "--cluster", cluster,
                            "--fix_location"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBuildClusters)
    unittest.TextTestRunner(verbosity=2).run(suite)
