# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Archetype formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Archetype


class ArchetypeFormatter(ObjectFormatter):
    template_raw = "archetype.mako"

    def format_proto(self, archetype, skeleton=None):
        # No ArchetypeList object yet...
        if not skeleton:
            return
        skeleton.name = str(archetype.name)
        # FIXME: Implement required services

ObjectFormatter.handlers[Archetype] = ArchetypeFormatter()