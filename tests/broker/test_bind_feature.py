#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the bind feature command."""

import re
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand


class TestBindFeature(TestBrokerCommand):

    def verify_personality_flush(self, err, orig_command):
        command = ["search", "personality", "--archetype", "aquilon"]
        perslist = self.commandtest(command).splitlines()
        self.matchoutput(err, "Flushed %d/%d templates" %
                         (len(perslist), len(perslist)), orig_command)

    def test_100_bind_archetype(self):
        command = ["bind", "feature", "--feature", "pre_host",
                   "--archetype", "aquilon"] + self.valid_just_tcm
        err = self.statustest(command)
        self.verify_personality_flush(err, command)
        # We can't easily check the number of templates that got refreshed since
        # there's no easy way to query if "make" was run for a host or not

    def test_101_verify_show_archetype(self):
        command = ["show", "archetype", "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Host Feature: pre_host [pre_personality]", command)

    def test_101_verify_show_feature(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Archetype aquilon", command)

    def test_101_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the archetype
        # definition
        self.searchoutput(out,
                          r'^  Host Feature: pre_host \[pre_personality\]$',
                          command)

    def test_101_verify_cat_personality(self):
        command = ["cat", "--personality", "inventory"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'include "features/pre_host/config";\s*',
                          command)
        self.searchoutput(out,
                          r'"/metadata/features" = append\("features/pre_host/config"\);',
                          command)
        # Parameters should not be there yet
        self.matchclean(out, "system/features/pre_host", command)

    def test_110_bind_personality(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--personality", "inventory"]
        err = self.statustest(command)
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_111_verify_show_personality(self):
        command = ["show", "personality", "--personality", "inventory"]
        out = self.commandtest(command)
        self.matchoutput(out, "Host Feature: post_host [post_personality]",
                         command)

    def test_111_verify_show_personality_proto(self):
        command = ["show", "personality", "--personality", "inventory", "--format=proto"]
        personality = self.protobuftest(command, expect=1)[0]
        self.assertEqual(personality.name, "inventory")
        self.assertEqual(personality.stage, "")
        feature = personality.features[0]
        self.assertEqual(feature.name, "post_host")
        self.assertEqual(feature.type, "host")
        self.assertEqual(feature.post_personality, True)
        self.assertEqual(feature.interface_name, "")
        self.assertEqual(feature.model.name, "")
        self.assertEqual(feature.model.vendor, "")

    def test_111_verify_show_feature(self):
        command = ["show", "feature", "--feature", "post_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Personality aquilon/inventory", command)

    def test_111_verify_show_unittest17(self):
        command = ["show", "host", "--hostname", "unittest17.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the personality
        # definition
        self.matchoutput(out, "Host Personality: inventory", command)
        self.searchoutput(out, r'^  Host Feature: post_host', command)

    def test_111_verify_show_unittest00(self):
        command = ["show", "host", "--hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the personality
        # definition
        self.matchoutput(out, "Host Personality: compileserver", command)
        self.searchclean(out, r'^  Host Feature: post_host', command)

    def test_111_verify_cat_personality(self):
        command = ["cat", "--personality", "inventory"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'include "features/post_host/config";',
                          command)
        self.searchoutput(out,
                          r'"/metadata/features" = append\("features/post_host/config"\);',
                          command)

    def test_120_bind_personality_redundant(self):
        command = ["bind", "feature", "--feature", "pre_host",
                   "--personality", "inventory"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Warning: host feature pre_host is already bound to "
                         "archetype aquilon; binding it to personality "
                         "aquilon/inventory is redundant.",
                         command)
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_121_verify_show_feature(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Archetype aquilon", command)
        self.matchoutput(out, "Bound to: Personality aquilon/inventory", command)

    def test_121_verify_cat_personality(self):
        command = ["cat", "--personality", "inventory"]
        out = self.commandtest(command)
        # Default parameters should now be there
        self.matchoutput(out, '"/system/features/pre_host/', command)

    def test_125_bind_archetype_redundant(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--archetype", "aquilon"] + self.valid_just_tcm
        err = self.statustest(command)
        self.matchoutput(err,
                         "Warning: host feature post_host is bound to "
                         "personality aquilon/inventory which is now "
                         "redundant; consider removing it.",
                         command)
        matches = re.search(r"Flushed (\d+)/(\d+) templates", err, re.M)
        # The inventory personality should not have changed
        self.assertEqual(int(matches.group(1)) + 1, int(matches.group(2)))

    def test_126_verify_show_feature(self):
        command = ["show", "feature", "--feature", "post_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Archetype aquilon", command)
        self.matchoutput(out, "Bound to: Personality aquilon/inventory", command)

    def test_130_bind_model(self):
        hosts = self.commandtest(["search_host", "--archetype", "aquilon",
                                  "--model", "hs21-8853"]).splitlines()

        command = ["bind", "feature", "--feature", "bios_setup",
                   "--model", "hs21-8853",
                   "--archetype", "aquilon"] + self.valid_just_tcm
        err = self.statustest(command)
        # The actual number of templates written may be different, because not
        # all the hosts have services assigned, so sometimes only
        # PlenaryHostData gets written and not PlenaryHostObject.
        self.searchoutput(err, r"Flushed \d+/%d templates" % len(hosts),
                          command)

    def test_131_verify_show_model(self):
        command = ["show", "model", "--model", "hs21-8853"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Hardware Feature: bios_setup$\n'
                          r'^    Archetype: aquilon$',
                          command)

    def test_131_verify_show_archetype(self):
        command = ["show", "archetype", "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Hardware Feature: bios_setup$\n'
                          r'^    Vendor: ibm Model: hs21-8853$',
                          command)

    def test_131_verify_show_feature(self):
        command = ["show", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Model ibm/hs21-8853",
                         command)

    def test_131_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the model
        # definition (we don't do that now, but...)
        self.searchoutput(out, r'^  Hardware Feature: bios_setup$', command)

    def test_131_verify_cat_unittest02(self):
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         'include if_exists("features/hardware/bios_setup/config");',
                         command)
        self.matchoutput(out,
                         'include if_exists("features/hardware/bios_setup");',
                         command)

    def test_140_bind_nic_model_interface(self):
        command = ["bind", "feature", "--feature", "src_route",
                   "--model", "e1000", "--vendor", "intel",
                   "--personality", "compileserver", "--interface", "eth1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Personality and feature owners do not match and "
                              "feature visibility is set to 'owner_only'.", command)

        command_tmp = ["update", "feature", "--feature", "src_route", "--type",
                       "interface", "--visibility", "public"]
        out = self.commandtest(command_tmp)
        err = self.statustest(command)
        self.matchoutput(err, "Flush", command)

    def test_141_verify_show_model(self):
        command = ["show", "model", "--model", "e1000", "--vendor", "intel"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface Feature: src_route$\n'
                          r'^    Personality: compileserver Archetype: aquilon$\n'
                          r'^    Interface: eth1$',
                          command)

    def test_141_verify_show_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface Feature: src_route$\n'
                          r'^    Vendor: intel Model: e1000$\n'
                          r'^    Interface: eth1$',
                          command)

    def test_141_verify_show_personality_proto(self):
        command = ["show", "personality", "--personality", "compileserver", "--format=proto"]
        personality = self.protobuftest(command, expect=1)[0]
        feature = personality.features[0]
        self.assertEqual(feature.name, "src_route")
        self.assertEqual(feature.type, "interface")
        self.assertEqual(feature.post_personality, False)
        self.assertEqual(feature.interface_name, "eth1")
        self.assertEqual(feature.model.name, "e1000")
        self.assertEqual(feature.model.vendor, "intel")

    def test_141_verify_show_feature(self):
        command = ["show", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Bound to: Model intel/e1000, "
                         "Personality aquilon/compileserver, "
                         "Interface eth1",
                         command)

    def test_141_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchclean(out,
                         r'Interface: eth0 .*$\n'
                         r'(^    .*$\n)*'
                         r'^    Template: features/interface/src_route',
                         command)
        self.searchoutput(out,
                          r'Interface: eth1 .*$\n'
                          r'(^    .*$\n)*'
                          r'^    Template: features/interface/src_route',
                          command)

    def test_141_verify_cat_host(self):
        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchclean(out,
                         r'variable CURRENT_INTERFACE = "eth0";\s*'
                         r'include "features/interface/src_route/config";',
                         command)
        self.searchoutput(out,
                          r'variable CURRENT_INTERFACE = "eth1";\s*'
                          r'include "features/interface/src_route/config";',
                          command)

    def test_141_verify_cat_unittest00(self):
        command = ["cat", "--hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "src_route", command)

    def test_150_bind_interface_personality(self):
        command = ["update", "feature", "--feature", "src_route", "--type",
                   "interface", "--visibility", "public"]
        out = self.commandtest(command)
        command = ["bind", "feature", "--feature", "src_route",
                   "--personality", "compileserver", "--interface", "bond0"]
        err = self.statustest(command)
        self.matchoutput(err, "Flushed 2/1 templates.", command)

    def test_151_verify_show_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface Feature: src_route$\n'
                          r'^    Interface: bond0$',
                          command)

    def test_151_verify_show_personality_proto(self):
        command = ["show", "personality", "--personality", "compileserver", "--format=proto"]
        personality = self.protobuftest(command, expect=1)[0]
        features = {feature.interface_name: feature
                    for feature in personality.features}
        self.assertEqual(sorted(features.keys()), ["bond0", "eth1"])
        feature = features["eth1"]
        self.assertEqual(feature.name, "src_route")
        self.assertEqual(feature.type, "interface")
        self.assertEqual(feature.post_personality, False)
        self.assertEqual(feature.interface_name, "eth1")
        self.assertEqual(feature.model.name, "e1000")
        self.assertEqual(feature.model.vendor, "intel")
        feature = features["bond0"]
        self.assertEqual(feature.name, "src_route")
        self.assertEqual(feature.type, "interface")
        self.assertEqual(feature.post_personality, False)
        self.assertEqual(feature.interface_name, "bond0")
        self.assertEqual(feature.model.name, "")
        self.assertEqual(feature.model.vendor, "")

    def test_151_verify_show_feature(self):
        command = ["show", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         'Bound to: Personality aquilon/compileserver, '
                         'Interface bond0', command)

    def test_151_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest21.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface: bond0 .*$\n'
                          r'(^    .*$\n)*'
                          r'^    Template: features/interface/src_route',
                          command)

    def test_151_verify_cat_unittest21(self):
        command = ["cat", "--hostname", "unittest21.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'variable CURRENT_INTERFACE = "bond0";\s*'
                          r'include "features/interface/src_route/config";',
                          command)
        self.matchclean(out, 'CURRENT_INTERFACE = "eth0"', command)
        self.matchclean(out, 'CURRENT_INTERFACE = "eth1"', command)

    def test_160_bind_same_feature_name(self):
        for type in ["host", "hardware", "interface"]:
            command = ["bind_feature", "--feature", "shinynew",
                       "--personality", "inventory"]
            if type == "interface":
                command.extend(["--interface", "eth0"])
            if type == "hardware":
                command.extend(["--model", "hs21-8853"])
            self.statustest(command)

    def test_200_bind_archetype_again(self):
        command = ["bind", "feature", "--feature", "pre_host",
                   "--archetype", "aquilon"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "Host Feature pre_host is already bound to "
                         "archetype aquilon.", command)

    def test_200_bind_noncompilable_arch(self):
        command = ["bind", "feature", "--feature", "pre_host",
                   "--archetype", "windows"] + self.valid_just_tcm
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "Archetype windows is not compileable, "
                         "feature bindings are not supported.", command)

    def test_200_bind_model_again(self):
        command = ["bind", "feature", "--feature", "bios_setup",
                   "--model", "hs21-8853",
                   "--archetype", "aquilon"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Hardware Feature bios_setup is already bound to "
                         "archetype aquilon, model ibm/hs21-8853.",
                         command)

    def test_200_bind_not_iface(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--personality", "compileserver", "--interface", "bond0"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Interface Feature post_host not found.", command)

    def test_200_bind_not_host(self):
        command = ["bind", "feature", "--feature", "bios_setup",
                   "--personality", "compileserver"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Host Feature bios_setup not found.", command)

    def test_200_bind_not_hardware(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--model", "hs21-8853", "--personality", "compileserver"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Hardware Feature post_host not found.", command)

    def test_200_bind_archetype_no_justification(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--archetype", "aurora"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

    def test_200_missing_personality(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--personality", "personality-does-not-exist",
                   "--archetype", "aquilon"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality personality-does-not-exist, "
                         "archetype aquilon not found.",
                         command)

    def test_200_missing_personality_stage(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--personality", "nostage", "--archetype", "aquilon",
                   "--personality_stage", "previous"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality aquilon/nostage does not have stage "
                         "previous.",
                         command)

    def test_200_bad_personality_stage(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--personality", "nostage", "--archetype", "aquilon",
                   "--personality_stage", "no-such-stage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'no-such-stage' is not a valid personality "
                         "stage.", command)

    def test_200_bind_model_no_justification(self):
        command = ["bind", "feature", "--feature", "bios_setup",
                   "--model", "utmedium", "--archetype", "aurora"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

    def test_300_constraint_pre_host(self):
        command = ["del", "feature", "--feature", "pre_host",
                   "--type", "host"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host Feature pre_host is still in use and cannot be "
                         "deleted.",
                         command)

    def test_300_constraint_post_host(self):
        command = ["del", "feature", "--feature", "post_host",
                   "--type", "host"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host Feature post_host is still in use and cannot be "
                         "deleted.",
                         command)

    def test_300_constraint_bios_setup(self):
        command = ["del", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Hardware Feature bios_setup is still in use and cannot be "
                         "deleted.",
                         command)

    def test_300_constraint_src_route(self):
        command = ["del", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Interface Feature src_route is still in use and cannot be "
                         "deleted.",
                         command)

    def test_400_show_diff(self):
        command = ["show_diff", "--archetype", "aquilon",
                   "--personality", "compileserver", "--other", "inventory"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Differences for Features:\s*'
                          r'missing Features in Personality aquilon/compileserver:\s*'
                          r'post_host\s*'
                          r'pre_host\s*'
                          r'shinynew\s*'
                          r'missing Features in Personality aquilon/inventory:\s*'
                          r'src_route\s*',
                          command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
