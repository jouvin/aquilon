#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add location`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon import const
from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.loc.location import Location
from aquilon.aqdb.loc.company import Company
from aquilon.aqdb.loc.hub import Hub
from aquilon.aqdb.loc.continent import Continent
from aquilon.aqdb.loc.country import Country
from aquilon.aqdb.loc.city import City
from aquilon.aqdb.loc.building import Building
from aquilon.aqdb.loc.rack import Rack
from aquilon.aqdb.loc.desk import Desk


# FIXME: This probably belongs in location.py
# It's also broken, as campus is not strictly between country and city.
const.location_types = ("company", "hub", "continent", "country", "campus",
                        "city", "building", "rack", "desk")


class CommandAddLocation(BrokerCommand):

    required_parameters = ["name", "fullname", "type",
            "parentname", "parenttype", "comments"]

    @add_transaction
    @az_check
    def render(self, session, name, fullname, type, 
            parentname, parenttype, comments, **arguments):
        newLocation = session.query(Location).filter_by(name=name,
                location_type=type).first()
        if newLocation:
            # FIXME: Technically this is coming in with an http PUT,
            # which should try to adjust state and succeed if everything
            # is alright.
            raise ArgumentError("%s '%s' already exists."
                    % (type.capitalize(), name))
        try:
            dbparent = session.query(Location).filter_by(name=parentname,
                    location_type=parenttype).one()
        except InvalidRequestError:
            raise ArgumentError(
                    "Parent %s %s not found."
                    % (parenttype.capitalize(), parentname))
        # Incoming looks like 'city', need the City class.
        location_type = globals()[type.capitalize()]
        if not issubclass(location_type, Location):
            raise ArgumentError("%s is not a known location type" % type)

        # Figure out if it is valid to add this type of child to the parent...
        found_parent = False
        found_new = False
        for t in const.location_types:
            if t == parenttype:
                # Great, found the parent type in the list before requested type
                found_parent = True
                continue
            if t != type:
                # This item is neither parent nor new, keep going...
                continue
            # Moment of truth.
            if found_parent:
                # We saw the parent earlier - life is good.
                found_new = True
                break
            raise ArgumentError("type %s cannot be a parent of %s" %
                    (parenttype, type))
        if not found_new:
            raise ArgumentError("unknown type %s" % type)

        optional_args = {}
        # XXX: The fullname used to be nullable... adding hack...
        if not fullname:
            fullname = name
        if comments:
            optional_args["comments"] = comments

        new_location = location_type(name=name, fullname=fullname,
                parent=dbparent, **optional_args)
        session.save(new_location)
        return


#if __name__=='__main__':
