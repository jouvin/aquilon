# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2016  Contributor
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
"""Contains the logic for `aq manage --hostname`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.manage_list import CommandManageList
from aquilon.worker.dbwrappers.host import hostname_to_host


class CommandManageHostname(CommandManageList):

    required_parameters = ["hostname"]

    def get_objects(self, session, hostname, **_):
        dbhost = hostname_to_host(session, hostname)
        if dbhost.cluster:
            raise ArgumentError("Cluster nodes must be managed at the "
                                "cluster level; this host is a member of "
                                "{0}.".format(dbhost.cluster))

        return (dbhost.branch, dbhost.sandbox_author, [dbhost])
