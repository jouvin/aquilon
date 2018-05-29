# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Contains the logic for `aq update room`."""

from aquilon.aqdb.model import Room
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location, update_location


class CommandUpdateRoom(BrokerCommand):

    required_parameters = ["room"]

    def render(self, session, room, fullname, uri, comments, floor, user,
               justification, reason, logger, **arguments):
        dbroom = Room.get_unique(session, room, compel=True)
        if floor is not None:
            dbroom.floor = floor

        update_location(dbroom, fullname=fullname, comments=comments,
                        uri=uri)