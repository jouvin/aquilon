#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2015,2016,2017,2018  Contributor
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
"""Module for testing the del service address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelServiceAddress(TestBrokerCommand):

    def test_100_delzebra2(self):
        ip = self.net["zebra_vip"].usable[14]
        self.dsdb_expect_delete(ip)
        command = ["del", "service", "address", "--name", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_110_delzebra2again(self):
        command = ["del", "service", "address", "--name", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service Address zebra2, host "
                         "unittest20.aqd-unittest.ms.com not found.",
                         command)
        self.dsdb_verify(empty=True)

    def test_120_verifyzebra2(self):
        command = ["show", "address", "--fqdn", "zebra2.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Record zebra2.aqd-unittest.ms.com not "
                         "found.", command)

    def test_130_delzebra3(self):
        ip = self.net["zebra_vip"].usable[13]
        self.dsdb_expect_delete(ip)
        command = ["del", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--name", "zebra3"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_150_delzebra3again(self):
        command = ["del", "service", "address", "--name", "zebra3",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service Address zebra3, host "
                         "unittest20.aqd-unittest.ms.com not found.",
                         command)
        self.dsdb_verify(empty=True)

    def test_160_failhostname(self):
        command = ["del", "service", "address", "--name", "hostname",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The primary address of the host cannot be "
                         "deleted.", command)

    def test_170_del_extserviceaddress(self):
        # check that removing an external service address does not invoke DSDB
        command = ["del_service_address", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--name", "et-unittest20"]
        self.noouttest(command)
        self.dsdb_verify(empty=True)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelServiceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
