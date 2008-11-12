#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq add aurora host`."""


import re

from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.add_host import CommandAddHost
from aquilon.server.processes import DSDBRunner, run_command
from aquilon.server.dbwrappers.machine import create_machine
from aquilon.server.dbwrappers.model import get_model
from aquilon.aqdb.loc.building import Building
from aquilon.aqdb.loc.rack import Rack
from aquilon.aqdb.sy.chassis import Chassis
from aquilon.aqdb.hw.chassis_hw import ChassisHw
from aquilon.aqdb.hw.chassis_slot import ChassisSlot
from aquilon.aqdb.hw.machine import Machine
from aquilon.aqdb.net.dns_domain import DnsDomain


class CommandAddAuroraHost(CommandAddHost):

    required_parameters = ["hostname"]
    # Look for node name like <building><rack_id>c<chassis_id>n<node_num>
    nodename_re = re.compile(r'^\s*([a-zA-Z]+)(\d+)c(\d+)n(\d+)\s*$')
    # Look for sys_loc output like "machine <building>.<city>.<region>",
    # but account for longer syslocs like "machine <extra>.<floor>.<b>.<c>.<r>"
    sys_loc_re = re.compile(
            r'^[-\.\w]+\s*(?:[-\.\w]*\.)?(\w+)\.(\w+)\.(\w+)\b$', re.M)

    @add_transaction
    @az_check
    def render(self, session, hostname, *args, **kwargs):
        # Pull relevant info out of dsdb...
        dsdb_runner = DSDBRunner()
        try:
            fields = dsdb_runner.show_host(hostname)
        except ProcessException, e:
            raise ArgumentError("Could not find %s in dsdb: %s" %
                                (hostname, e))

        fqdn = fields["fqdn"]
        dsdb_lookup = fields["dsdb_lookup"]
        if fields["node"]:
            machine = fields["node"]
        elif fields["primary_name"]:
            machine = fields["primary_name"]
        else:
            machine = dsdb_lookup

        # Create a machine
        dbmodel = get_model(session, "aurora_model")
        dbmachine = session.query(Machine).filter_by(name=machine).first()
        dbslot = None
        if not dbmachine:
            m = self.nodename_re.search(machine)
            if m:
                (building, rid, cid, nodenum) = m.groups()
                dbbuilding = session.query(Building).filter_by(
                        name=building).first()
                if not dbbuilding:
                    raise ArgumentError("Failed to find building %s for node %s, please add an Aurora machine manually and follow with add_host." %
                            building, machine)
                rack = building + rid
                dbrack = session.query(Rack).filter_by(name=rack).first()
                if not dbrack:
                    dbrack = Rack(name=rack, fullname=rack, parent=dbbuilding)
                    session.save(dbrack)
                dblocation = dbrack
                chassis = rack + "c" + cid
                dbdns_domain = session.query(DnsDomain).filter_by(
                        name="ms.com").first()
                dbchassis = session.query(Chassis).filter_by(
                        name=chassis, dns_domain=dbdns_domain).first()
                if not dbchassis:
                    dbchassis_model = get_model(session, 'aurora_chassis_model')
                    dbchassis_hw = ChassisHw(location=dbrack,
                                             model=dbchassis_model)
                    session.save(dbchassis_hw)
                    dbchassis = Chassis(name=chassis, dns_domain=dbdns_domain,
                                        chassis_hw=dbchassis_hw)
                    session.save(dbchassis)
                dbslot = session.query(ChassisSlot).filter_by(
                        chassis=dbchassis, slot_number=nodenum).first()
                # Note: Could be even more persnickity here and check that
                # the slot is currently empty.  Seems like overkill.
                if not dbslot:
                    dbslot = ChassisSlot(chassis=dbchassis,
                                         slot_number=nodenum)
                    session.save(dbslot)
            else:
                try:
                    out = run_command([self.config.get("broker", "sys_loc"),
                        dsdb_lookup])
                except ProcessException, e:
                    # Shouldn't happen, sys_loc returns 0 even for failures
                    raise ArgumentError("Using sys_loc to find a building for node %s failed, please add an Aurora machine manually and follow with add_host: %s" %
                            dsdb_lookup, e)
                m = self.sys_loc_re.search(out)
                if m:
                    (building, city, region) = m.groups()
                    dbbuilding = session.query(Building).filter_by(
                            name=building).first()
                    if not dbbuilding:
                        raise ArgumentError("Failed to find building %s for node %s, please add an Aurora machine manually and follow with add_host." %
                                (building, dsdb_lookup))
                else:
                    raise ArgumentError("Failed to determine building from sys_loc output for %s, please add an Aurora machine manually and follow with add_host: %s" %
                            (dsdb_lookup, out))
                dblocation = dbbuilding

            dbmachine = create_machine(session, machine, dblocation, dbmodel,
                    None, None, None, None, None, None)
            # create_machine already does a save and a flush
            if dbslot:
                dbslot.machine = dbmachine
                session.update(dbslot)
        # FIXME: Pull this from somewhere.
        buildstatus = 'ready'

        kwargs['skip_dsdb_check'] = True
        kwargs['session'] = session
        kwargs['hostname'] = fqdn
        kwargs['archetype'] = 'aurora'
        kwargs['domain'] = self.config.get("broker", "aurora_host_domain")
        kwargs['machine'] = dbmachine.name
        kwargs['buildstatus'] = buildstatus
        kwargs['ip'] = None
        # The superclass already contains the rest of the logic to handle this.
        return CommandAddHost.render(self, *args, **kwargs)


#if __name__=='__main__':
