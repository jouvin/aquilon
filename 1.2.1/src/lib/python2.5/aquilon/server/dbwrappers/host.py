#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrappers to make getting and using hosts simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.net.dns_domain import DnsDomain
from aquilon.aqdb.sy.host import Host


def hostname_to_domain_and_string(session, hostname):
    if not hostname:
        raise ArgumentError("No hostname specified.")
    (short, dot, dns_domain) = hostname.partition(".")
    if not dns_domain:
        raise ArgumentError(
                "'%s' invalid, hostname must be fully qualified." % hostname)
    if not short:
        raise ArgumentError("'%s' invalid, missing host name." % hostname)
    try:
        dbdns_domain = session.query(DnsDomain).filter_by(
                name=dns_domain).one()
    except InvalidRequestError, e:
        raise NotFoundException("DNS domain '%s' for '%s' not found: %s"
                % (dns_domain, hostname, e))
    return (short, dbdns_domain)

def hostname_to_host(session, hostname):
    (short, dbdns_domain) = hostname_to_domain_and_string(session, hostname)
    try:
        dball = session.query(Host).filter_by(name=short, dns_domain=dbdns_domain).all()
        if (len(dball) == 0):
            raise NotFoundException("Host '%s' not found" % hostname)
        return dball[0]
    except InvalidRequestError, e:
        raise ArgumentError("Failed to find host: %s" %e)

def get_host_build_item(self, dbhost, dbservice):
    for template in dbhost.templates:
        si = template.cfg_path.svc_inst
        if si and si.service == dbservice:
            return template
    return None

def get_host_dependencies(session, dbhost):
    """ returns a list of strings describing how a host is being used.
    If the host has no dependencies, then an empty list is returned
    """
    ret = []
    # XXX: Show any service instance which has dbhost as an element in host_list.hosts
    return ret


#if __name__=='__main__':
