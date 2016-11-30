# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2016  Contributor
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
"""Contains the logic for `aq del campus`."""

from aquilon.aqdb.model import Campus
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.del_location import CommandDelLocation


class CommandDelCampus(CommandDelLocation):

    required_parameters = ["campus"]

    def render(self, session, logger, campus, **arguments):
        dbcampus = Campus.get_unique(session, campus, compel=True)
        name = dbcampus.name

        result = CommandDelLocation.render(self, session=session, name=name,
                                           type='campus', **arguments)
        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.del_campus(name)
        dsdb_runner.commit_or_rollback()

        return result
