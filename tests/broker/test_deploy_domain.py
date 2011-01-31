#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the deploy domain command."""


import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDeployDomain(TestBrokerCommand):

    def testdeploychangetest1domain(self):
        self.successtest(["deploy", "--source", "changetest1",
                          "--target", "deployable",
                          "--comments", "Test comment"])

    def testverifydeploy(self):
        domainsdir = self.config.get("broker", "domainsdir")
        ddir = os.path.join(domainsdir, "deployable")
        template = os.path.join(ddir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        self.failUnlessEqual(contents[-1], "#Added by unittest\n")

    def testverifygitlog(self):
        kingdir = self.config.get("broker", "kingdir")
        command = ["log", "--no-color", "-n", "1", "deployable"]
        (out, err) = self.gitcommand(command, cwd=kingdir)
        self.matchoutput(out, "User:", command)
        self.matchoutput(out, "Request ID:", command)
        self.matchoutput(out, "Comments: Test comment", command)

    def testdeploynosync(self):
        self.successtest(["deploy", "--source", "changetest1",
                          "--target", "prod", "--nosync"])

    def testverifynosync(self):
        domainsdir = self.config.get("broker", "domainsdir")
        # The change should be in prod...
        ddir = os.path.join(domainsdir, "prod")
        template = os.path.join(ddir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        self.failUnlessEqual(contents[-1], "#Added by unittest\n")
        # ...but not in the ut-prod tracking domain.
        ddir = os.path.join(domainsdir, "ut-prod")
        template = os.path.join(ddir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        self.failIfEqual(contents[-1], "#Added by unittest\n")


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeployDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
