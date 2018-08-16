#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015,2016,2017  Contributor
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
"""Module for testing the unbind server command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

instance_servers = {
    "aqd": {
        "ny-prod": ["nyaqd1.ms.com"],
    },
    "bootserver": {
        "unittest": ["infra1.aqd-unittest.ms.com", "infra2.aqd-unittest.ms.com"],
        "one-nyp": ["infra1.one-nyp.ms.com", "infra2.one-nyp.ms.com"],
    },
    "chooser1": {
        "ut.a": ["server1.aqd-unittest.ms.com"],
        "ut.b": ["server2.aqd-unittest.ms.com"],
        "ut.c": ["server3.aqd-unittest.ms.com"],
    },
    "chooser2": {
        "ut.a": ["server1.aqd-unittest.ms.com"],
        "ut.c": ["server3.aqd-unittest.ms.com"],
    },
    "chooser3": {
        "ut.a": ["server1.aqd-unittest.ms.com"],
        "ut.b": ["server2.aqd-unittest.ms.com"],
    },
    "dns": {
        "one-nyp": ["infra1.one-nyp.ms.com"],
    },
    "ips": {
        "northamerica": ["infra1.aqd-unittest.ms.com"],
    },
    "lemon": {
        "ny-prod": ["nyaqd1.ms.com"],
    },
    "ntp": {
        "pa.ny.na": ["nyaqd1.ms.com"],
    },
    "syslogng": {
        "ny-prod": ["nyaqd1.ms.com"],
    },
}


class TestUnbindServer(TestBrokerCommand):
    def check_last_server_msg(self, out, command, service, instance):
        self.matchoutput(out,
                         "Warning: Service Instance %s/%s was left "
                         "without servers, but it still has clients." %
                         (service, instance),
                         command)

    def test_100_check_initial_plenary(self):
        # This test must use the same regular expressions as
        # testverifycatunittest02() does, to verify that the success of
        # searchclean() is not due to errors in the expressions
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r'/utsvc/[^/]+/server', command)

    def test_110_unbind_utsi1_unittest02(self):
        command = ["unbind", "server",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "utsvc", "--all"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "utsvc", "utsi1")

    def test_115_verify_cat_utsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include "servicedata/utsvc/config";',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def test_115_verify_cat_unittest02(self):
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.searchclean(out, r'/utsvc/[^/]+/server', command)

    def test_115_verify_show_utsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def test_120_unbind_utsi2_unittest00(self):
        command = ["unbind_server",
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"]
        self.noouttest(command)

    def test_121_unbind_utsi2_aliased(self):
        self.noouttest(["unbind_server", "--alias", "srv-alias.one-nyp.ms.com",
                        "--hostname", "unittest00.one-nyp.ms.com",
                        "--service", "utsvc", "--instance", "utsi2"])

    def test_122_unbind_alias_alone(self):
        self.noouttest(["unbind_server", "--alias", "srv-alias2.one-nyp.ms.com",
                        "--service", "utsvc", "--instance", "utsi2"])

    def test_123_unbind_service_address(self):
        self.noouttest(["unbind_server",
                        "--hostname", "unittest20.aqd-unittest.ms.com",
                        "--service_address", "zebra2",
                        "--service", "utsvc", "--instance", "utsi2"])

    def test_124_unbind_auxiliary(self):
        ip = self.net["unknown0"].usable[3]
        command = ["unbind_server", "--ip", ip,
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "utsvc", "utsi2")

    def test_129_verify_cat_utsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include "servicedata/utsvc/config";',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)
        self.searchoutput(out, r'"server_ips" = list\(\s*\);', command)

    def test_129_verify_show_utsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def test_130_unbind_pollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.statustest(["unbind", "server", "--hostname", "nyaqd1.ms.com",
                         "--service", service, "--instance", "unittest"] + self.valid_just_tcm)

    def test_140_verify_pre_unbind(self):
        command = ["show_service", "--service", "dns", "--instance", "unittest"]
        out = self.commandtest(command)
        # We only care about the order of the servers here
        self.searchoutput(out,
                          r"Server Binding: infra1\.aqd-unittest\.ms\.com\s*"
                          r"Server Binding: nyaqd1\.ms\.com",
                          command)

    def test_141_unbind_by_position(self):
        command = ["unbind_server", "--service", "dns",
                   "--instance", "unittest", "--position", 1] + self.valid_just_tcm
        self.statustest(command)

    def test_142_verify_unbind(self):
        command = ["show_service", "--service", "dns", "--instance", "unittest"]
        out = self.commandtest(command)
        self.matchoutput(out, "Server Binding: infra1.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "nyaqd1.ms.com", command)

    def test_143_unbind_bad_position(self):
        command = ["unbind_server", "--service", "dns",
                   "--instance", "unittest", "--position", 1] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "Invalid server position.", command)

    def test_144_unbind_last_by_position(self):
        command = ["unbind_server", "--service", "dns",
                   "--instance", "unittest", "--position", 0] + self.valid_just_tcm
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "dns", "unittest")

    def test_145_verify_unbind_last(self):
        command = ["show_service", "--service", "dns", "--instance", "unittest"]
        out = self.commandtest(command)
        self.matchclean(out, "Server Binding:", command)
        self.matchclean(out, "infra1.aqd-unittest.ms.com", command)
        self.matchclean(out, "nyaqd1.ms.com", command)

    def test_150_unbind_all(self):
        for service, instances in instance_servers.items():
            for instance, servers in instances.items():
                for server in servers:
                    command = ["unbind_server", "--hostname", server,
                               "--service", service, "--instance", instance] + self.valid_just_tcm
                    self.statustest(command)

            command = ["show_service", "--service", service]
            out = self.commandtest(command)
            for instance, servers in instances.items():
                for server in servers:
                    self.matchclean(out, server, command)

    def test_155_unbind_to_network_device(self):
        command = ['unbind_server', '--service', 'test_network_dev', '--instance', 'test',
                   '--hostname', 'switchinbuilding.aqd-unittest.ms.com']
        self.noouttest(command)
        command = ['del_service', '--service', 'test_network_dev', '--instance', 'test']
        self.noouttest(command)
        command = ['del_service', '--service', 'test_network_dev']
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)
