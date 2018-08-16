#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the bind server command.

Note: This runs after make_aquilon and reconfigure tests.  If server
bindings are needed *before* those tests, they need to be in with
the TestPrebindServer tests.

"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestBindServer(TestBrokerCommand):

    def test_100_bind_utsi1_unittest02(self):
        self.noouttest(["bind", "server",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--service", "utsvc", "--instance", "utsi1"])

    # Test binding multiple servers to a single instance
    def test_110_bind_utsi1_unittest00(self):
        self.noouttest(["bind", "server",
                        "--hostname", "unittest00.one-nyp.ms.com",
                        "--service", "utsvc", "--instance", "utsi1"])

    def test_120_bind_utsi1_server1(self):
        self.statustest(["bind", "server", "--position", 1,
                         "--hostname", "server1.aqd-unittest.ms.com",
                         "--service", "utsvc", "--instance", "utsi1"])

    # Test binding a server to multiple instances
    def test_130_bind_utsi2_unittest00(self):
        self.noouttest(["bind", "server",
                        "--hostname", "unittest00.one-nyp.ms.com",
                        "--service", "utsvc", "--instance", "utsi2"])

    def test_140_add_alias(self):
        self.noouttest(["add_alias", "--fqdn", "srv-alias.one-nyp.ms.com",
                        "--target", "unittest00.one-nyp.ms.com"])
        self.noouttest(["add_alias", "--fqdn", "srv-alias2.one-nyp.ms.com",
                        "--target", "unittest00.one-nyp.ms.com"])

    def test_141_bind_aliased_server(self):
        command = ["bind_server", "--alias", "srv-alias.one-nyp.ms.com",
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"] + self.valid_just_tcm
        self.statustest(command)

    def test_145_bind_alias_alone(self):
        command = ["bind_server",
                   "--alias", "srv-alias2.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"] + self.valid_just_tcm
        self.noouttest(command)

    def test_150_bind_service_address(self):
        self.noouttest(["bind_server",
                        "--hostname", "unittest20.aqd-unittest.ms.com",
                        "--service_address", "zebra2",
                        "--service", "utsvc", "--instance", "utsi2"])

    def test_160_bind_auxiliary(self):
        ip = self.net["unknown0"].usable[3]
        self.noouttest(["bind_server", "--ip", ip,
                        "--hostname", "unittest00.one-nyp.ms.com",
                        "--service", "utsvc", "--instance", "utsi2"])

    def test_200_bind_utsi2_unittest00_again(self):
        command = ["bind", "server", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The server binding already exists.", command)

    def test_300_cat_utsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include "servicedata/utsvc/config";',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out,
                          r'"servers" = list\(\s*'
                          r'"unittest02.one-nyp.ms.com",\s*'
                          r'"server1.aqd-unittest.ms.com",\s*'
                          r'"unittest00.one-nyp.ms.com"\s*\);',
                          command)
        unittest02_ip = self.net["unknown0"].usable[0]
        server1_ip = self.net["hp_eth0"].usable[1]
        unittest00_ip = self.net["unknown0"].usable[2]
        self.searchoutput(out,
                          r'"server_ips" = list\(\s*'
                          r'"%s",\s*'
                          r'"%s",\s*'
                          r'"%s"\s*\);' %
                          (unittest02_ip, server1_ip, unittest00_ip),
                          command)

    def test_300_show_utsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        # Order is important
        self.searchoutput(out,
                          r'Server Binding: unittest02.one-nyp.ms.com\n\s*'
                          r'Server Binding: server1.aqd-unittest.ms.com\n\s*'
                          r'Server Binding: unittest00.one-nyp.ms.com\n\s*',
                          command)

    def test_300_show_utsi1_proto(self):
        command = "show service --service utsvc --instance utsi1 --format proto"
        svc = self.protobuftest(command.split(" "), expect=1)[0]
        self.assertEqual(svc.name, "utsvc",
                         "Service name mismatch: %s instead of utsvc\n" %
                         svc.name)
        si = svc.serviceinstances[0]
        self.assertEqual(si.name, "utsi1",
                         "Service name mismatch: %s instead of utsi1\n" %
                         si.name)
        servers = [srv.fqdn for srv in si.servers]
        expected = ["unittest02.one-nyp.ms.com",
                    "server1.aqd-unittest.ms.com",
                    "unittest00.one-nyp.ms.com"]
        self.assertEqual(servers, expected,
                         "Wrong list of servers for service utsvc "
                         "instance utsi1: %s\n" %
                         " ".join(list(servers)))

        self.assertEqual(len(si.provider), 3)
        self.assertEqual(si.provider[0].target_fqdn, "unittest02.one-nyp.ms.com")
        self.assertEqual(si.provider[0].host.fqdn, "unittest02.one-nyp.ms.com")
        self.assertEqual(si.provider[1].target_fqdn, "server1.aqd-unittest.ms.com")
        self.assertEqual(si.provider[1].host.fqdn, "server1.aqd-unittest.ms.com")
        self.assertEqual(si.provider[2].target_fqdn, "unittest00.one-nyp.ms.com")
        self.assertEqual(si.provider[2].host.fqdn, "unittest00.one-nyp.ms.com")

    def test_300_cat_utsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include "servicedata/utsvc/config";',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out,
                          r'"servers" = list\(\s*'
                          r'"unittest00.one-nyp.ms.com",\s*'
                          r'"srv-alias.one-nyp.ms.com",\s*'
                          r'"srv-alias2.one-nyp.ms.com",\s*'
                          r'"zebra2.aqd-unittest.ms.com",\s*'
                          r'"unittest00-e1.one-nyp.ms.com"\s*\);',
                          command)
        unittest00_ip = self.net["unknown0"].usable[2]
        unittest00_e1_ip = self.net["unknown0"].usable[3]
        zebra2_ip = self.net["zebra_vip"].usable[14]
        self.searchoutput(out,
                          r'"server_ips" = list\(\s*'
                          r'"%s",\s*'
                          r'"%s",\s*'
                          r'"%s"\s*\);' % (unittest00_ip, zebra2_ip,
                                           unittest00_e1_ip),
                          command)

    def test_300_show_utsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        zebra2_ip = self.net["zebra_vip"].usable[14]
        unittest00_e1_ip = self.net["unknown0"].usable[3]
        self.searchoutput(out,
                          r'Server Binding: unittest00.one-nyp.ms.com\n\s*'
                          r'Server Binding: srv-alias.one-nyp.ms.com \[alias, host: unittest00.one-nyp.ms.com\]\n\s*'
                          r'Server Binding: srv-alias2.one-nyp.ms.com \[alias\]\n\s*'
                          r'Server Binding: zebra2.aqd-unittest.ms.com \[host: unittest20.aqd-unittest.ms.com, service_address: zebra2, IP: %s\]\n\s*'
                          r'Server Binding: unittest00-e1.one-nyp.ms.com \[host: unittest00.one-nyp.ms.com, IP: %s\]\n\s*'
                          % (zebra2_ip, unittest00_e1_ip),
                          command)

    def test_300_show_utsi2_proto(self):
        unittest20_ip = self.net["zebra_vip"].usable[2]
        zebra2_ip = self.net["zebra_vip"].usable[14]
        unittest00_ip = self.net["unknown0"].usable[2]
        unittest00_e1_ip = self.net["unknown0"].usable[3]

        command = "show service --service utsvc --instance utsi2 --format proto"
        svc = self.protobuftest(command.split(" "), expect=1)[0]
        self.assertEqual(svc.name, "utsvc",
                         "Service name mismatch: %s instead of utsvc\n" %
                         svc.name)
        si = svc.serviceinstances[0]
        self.assertEqual(si.name, "utsi2",
                         "Service name mismatch: %s instead of utsi2\n" %
                         si.name)

        # Compat server list
        servers = [srv.fqdn for srv in si.servers]
        expected = ["unittest00.one-nyp.ms.com",
                    "unittest20.aqd-unittest.ms.com",
                    "unittest00.one-nyp.ms.com"]
        self.assertEqual(servers, expected,
                         "Wrong list of servers for service utsvc "
                         "instance utsi2: %s\n" %
                         " ".join(list(servers)))

        # New-style provider list
        self.assertEqual(len(si.provider), 5)
        self.assertEqual(si.provider[0].target_fqdn, "unittest00.one-nyp.ms.com")
        self.assertEqual(si.provider[0].target_ip, str(unittest00_ip))
        self.assertEqual(si.provider[0].host.fqdn, "unittest00.one-nyp.ms.com")
        self.assertEqual(si.provider[0].host.ip, str(unittest00_ip))
        self.assertEqual(si.provider[0].service_address.fqdn, "")
        self.assertEqual(si.provider[0].service_address.ip, "")

        self.assertEqual(si.provider[1].target_fqdn, "srv-alias.one-nyp.ms.com")
        self.assertEqual(si.provider[1].target_ip, "")
        self.assertEqual(si.provider[1].host.fqdn, "")
        self.assertEqual(si.provider[1].host.ip, "")
        self.assertEqual(si.provider[1].service_address.fqdn, "")
        self.assertEqual(si.provider[1].service_address.ip, "")

        self.assertEqual(si.provider[2].target_fqdn, "srv-alias2.one-nyp.ms.com")
        self.assertEqual(si.provider[2].target_ip, "")
        self.assertEqual(si.provider[2].host.fqdn, "")
        self.assertEqual(si.provider[2].host.ip, "")
        self.assertEqual(si.provider[2].service_address.fqdn, "")
        self.assertEqual(si.provider[2].service_address.ip, "")

        self.assertEqual(si.provider[3].target_fqdn, "zebra2.aqd-unittest.ms.com")
        self.assertEqual(si.provider[3].target_ip, str(zebra2_ip))
        self.assertEqual(si.provider[3].host.fqdn, "unittest20.aqd-unittest.ms.com")
        self.assertEqual(si.provider[3].host.ip, str(unittest20_ip))
        self.assertEqual(si.provider[3].service_address.fqdn, "zebra2.aqd-unittest.ms.com")
        self.assertEqual(si.provider[3].service_address.ip, str(zebra2_ip))

        self.assertEqual(si.provider[4].target_fqdn, "unittest00-e1.one-nyp.ms.com")
        self.assertEqual(si.provider[4].target_ip, str(unittest00_e1_ip))
        self.assertEqual(si.provider[4].host.fqdn, "unittest00.one-nyp.ms.com")
        self.assertEqual(si.provider[4].host.ip, str(unittest00_ip))
        self.assertEqual(si.provider[4].service_address.fqdn, "")
        self.assertEqual(si.provider[4].service_address.ip, "")

    def test_300_show_service_server(self):
        command = "show service --server unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server Binding: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi2", command)

    def test_300_show_service_name_server(self):
        command = "show service --service utsvc --server unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server Binding: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)

    def test_300_cat_unittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "object template unittest00.one-nyp.ms.com",
                         command)
        self.matchoutput(out,
                         'include "service/utsvc/utsi1/server/config";',
                         command)
        self.matchoutput(out,
                         'include "service/utsvc/utsi2/server/config";',
                         command)

    def test_300_show_unittest00(self):
        unittest00_e1_ip = self.net["unknown0"].usable[3]
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: unittest00.one-nyp.ms.com",
                         command)
        self.searchoutput(out,
                          r'Provides Service: utsvc Instance: utsi1\s*'
                          r'Server Binding: unittest00.one-nyp.ms.com',
                          command)
        self.searchoutput(out,
                          r'Provides Service: utsvc Instance: utsi2\s*'
                          r'Server Binding: unittest00.one-nyp.ms.com\n',
                          command)
        self.searchoutput(out,
                          r'Provides Service: utsvc Instance: utsi2\s*'
                          r'Server Binding: srv-alias.one-nyp.ms.com \[alias, host: unittest00.one-nyp.ms.com\]\n',
                          command)
        self.searchoutput(out,
                          r'Provides Service: utsvc Instance: utsi2\s*'
                          r'Server Binding: unittest00-e1.one-nyp.ms.com \[host: unittest00.one-nyp.ms.com, IP: %s\]\n\s*'
                          % unittest00_e1_ip,
                          command)
        self.searchclean(out,
                         r'Server Binding: srv-alias2.one-nyp.ms.com',
                         command)
        self.matchoutput(out, "Aliases: srv-alias.one-nyp.ms.com, srv-alias2.one-nyp.ms.com", command)

    def test_300_show_unittest00_proto(self):
        command = "show host --hostname unittest00.one-nyp.ms.com --format proto"
        host = self.protobuftest(command.split(" "), expect=1)[0]
        self.assertEqual(len(host.services_provided), 4)
        services = set()
        for svc_msg in host.services_provided:
            services.add("%s/%s" % (svc_msg.service, svc_msg.instance))
        for binding in ("utsvc/utsi1", "utsvc/utsi2"):
            self.assertTrue(binding in services,
                            "Service binding %s is missing from protobuf "
                            "message. All bindings: %s" %
                            (binding, ",".join(list(services))))

    def test_300_cat_unittest20(self):
        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         'include "service/utsvc/utsi2/server/config";',
                         command)

    def test_300_show_unittest20(self):
        zebra2_ip = self.net["zebra_vip"].usable[14]
        command = ["show_host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Provides Service: utsvc Instance: utsi2",
                         command)
        self.matchoutput(out, "Server Binding: zebra2.aqd-unittest.ms.com "
                         "[host: unittest20.aqd-unittest.ms.com, "
                         "service_address: zebra2, IP: %s]" % zebra2_ip,
                         command)

    def test_300_show_srv_alias(self):
        command = ["show_alias", "--fqdn", "srv-alias.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Provides Service: utsvc Instance: utsi2",
                         command)

    def test_400_alias_not_allowed(self):
        command = ['bind_server', '--service', 'utsvc2', '--instance', 'utsi1',
                   '--alias', 'srv-alias.one-nyp.ms.com']
        out = self.badrequesttest(command)
        self.matchoutput(out, "Service utsvc2 is not configured to allow "
                              "alias bindings.", command)

    def test_800_cleanup(self):
        self.statustest(["unbind_server",
                         "--hostname", "server1.aqd-unittest.ms.com",
                         "--service", "utsvc", "--instance", "utsi1"])

    def test_805_bind_to_network_device(self):
        # Test service bind to network device
        # Test @test_show_service_all.py: 'show service all --format=proto'
        command = ['add_service', '--service', 'test_network_dev']
        self.noouttest(command)
        command = ['add_service', '--service', 'test_network_dev', '--instance', 'test']
        self.noouttest(command)
        command = ['bind_server', '--service', 'test_network_dev', '--instance', 'test',
                   '--hostname', 'switchinbuilding.aqd-unittest.ms.com']
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)
