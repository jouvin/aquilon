#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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

""" tests create and delete of a machine through the session """
from utils import load_classpath, add, commit

load_classpath()

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import (Vendor, Model, Machine, Cpu, Building, Domain,
                                DnsDomain, Status, Personality, Archetype, Host,
                                Cluster, EsxCluster, HostClusterMember, Service,
                                ServiceInstance, Tld, CfgPath,
                                MachineClusterMember)

from sqlalchemy import and_
from sqlalchemy.orm import join
from sqlalchemy.exc import IntegrityError

#from nose.plugins.attrib import attr
from nose.tools import raises

db = DbFactory()
sess = db.Session()

VM_NAME = 'test_vm'
MACHINE_NAME = 'test_esx_machine'
HOST_NAME = 'test_esx_host'
CLUSTER_NAME = 'test_esx_cluster'
NUM_MACHINES = 30
NUM_HOSTS = 30

#TODO: clean_up with an argument of setup/teardown if setup and you delete,
#      raise a warning that tear_down may not have worked as expected?

#TODO: have del_cluster_member raise a warning or error that cascaded deletion
#      doesn't work?

#TODO: __init__ method check for valid/invalid archetypes/os/personality of
#the host members per cluster_type???

def clean_up():
    del_hosts()
    del_cluster_member() #if you delete the host, it should be handled...
    del_machines()
    del_clusters()

def setup():
    print 'set up'
    clean_up()

def teardown():
    print 'tear down'
    clean_up()

def del_machines():
    machines = sess.query(Machine).filter(
        Machine.name.like(MACHINE_NAME+'%')).all()
    if machines:
        for machine in machines:
            sess.delete(machine)
        commit(sess)
        print 'deleted %s esx machines'%(len(machines))

    machines = sess.query(Machine).filter(Machine.name.like(VM_NAME+'%')).all()
    if machines:
        for vm in machines:
            sess.delete(vm)
        commit(sess)
        print 'deleted %s virtual machines'%(len(machines))

def del_hosts():
    hosts = sess.query(Host).filter(Host.name.like(HOST_NAME+'%')).all()
    if hosts:
        for host in hosts:
            sess.delete(host)
        commit(sess)
        print 'deleted %s hosts'% (len(hosts))

def del_clusters():
    clist = sess.query(Cluster).all()
    if len(clist) > 0:
        for c in clist:
            sess.delete(c)
        commit(sess)
        print 'deleted %s cluster(s)'%(len(clist))

def del_cluster_member():
    ech = sess.query(HostClusterMember).filter(Host.name==HOST_NAME).first()
    if ech:
        sess.delete(ech)
        commit(sess)
        print 'deleted cluster host'

def test_create_vm():
    vend = Vendor.get_unique(sess, 'virtual')
    mod = Model.get_unique(sess, 'vm', vendor_id=vend.id)
    proc = Cpu.get_unique(sess, 'virtual_cpu', vendor_id=vend.id, speed=0)
    np = Building.get_by('name', 'np', sess)[0]

    for i in xrange(NUM_MACHINES):
        vm = Machine(name='%s%s'%(VM_NAME, i), location=np, model = mod,
                     cpu=proc, cpu_quantity=1, memory=4196)
        add(sess, vm)
    commit(sess)

    machines = sess.query(Machine).filter(Machine.name.like(VM_NAME+'%')).all()

    assert len(machines) is NUM_MACHINES
    print 'created %s machines'%(len(machines))

def test_create_machines_for_hosts():
    np = Building.get_by('name', 'np', sess)[0]
    am = Model.get_by('name', 'vm', sess)[0]
    a_cpu = Cpu.get_by('name', 'aurora_cpu', sess)[0]

    for i in xrange(NUM_HOSTS):
        machine = Machine(name='%s%s'% (MACHINE_NAME, i), location=np, model=am,
                          cpu=a_cpu, cpu_quantity=8, memory=32768)
        add(sess, machine)
    commit(sess)

    machines = sess.query(Machine).filter(
        Machine.name.like(MACHINE_NAME+'%')).all()

    assert len(machines) is NUM_MACHINES
    print 'created %s esx machines'%(len(machines))

def esx_machine_factory():
    machines = sess.query(Machine).filter(
        Machine.name.like(MACHINE_NAME+'%')).all()
    size = len(machines)
    for machine in machines:
        yield machine

m_factory = esx_machine_factory()

def test_create_hosts():
    dmn = Domain.get_by('name', 'daqscott', sess)[0]
    dns_dmn = DnsDomain.get_by('name', 'one-nyp.ms.com', sess)[0]
    stat = Status.get_by('name', 'build', sess)[0]

    pers = sess.query(Personality).select_from(
        join(Personality, Archetype)).filter(
        and_(Archetype.name=='vmhost', Personality.name=='generic')).one()

    sess.autoflush=False

    for i in xrange(NUM_HOSTS):
        machine = m_factory.next()
        vm_host = Host(machine=machine, name='%s%s'% (HOST_NAME, i), dns_domain=dns_dmn,
               domain=dmn, personality=pers, status=stat)
        add(sess, vm_host)

    sess.autoflush=True

    commit(sess)

    hosts = sess.query(Host).filter(
        Host.name.like(HOST_NAME+'%')).all()
    assert len(hosts) is NUM_HOSTS
    print 'created %s hosts'% (len(hosts))

def host_factory():
    hosts = sess.query(Host).filter(Host.name.like(HOST_NAME+'%')).all()
    size = len(hosts)
    for host in hosts:
        yield host

h_factory = host_factory()

def test_create_esx_cluster():
    """ tests the creation of an EsxCluster """
    dmn = Domain.get_by('name', 'ny-prod', sess)[0]
    np = sess.query(Building).filter_by(name='np').one()
    per = sess.query(Personality).select_from(
            join(Archetype, Personality)).filter(
            and_(Archetype.name=='windows', Personality.name=='generic')).one()

    ec = EsxCluster(name=CLUSTER_NAME, location_constraint=np, personality=per, domain=dmn)

    add(sess, ec)
    commit(sess)

    assert ec
    print ec

    assert ec.max_hosts is 8
    print 'esx cluster max members = %s'%(ec.max_hosts)

def test_add_cluster_host():
    """ test adding a host to the cluster """
    vm_host = h_factory.next()
    ec = EsxCluster.get_by('name', CLUSTER_NAME, sess)[0]

    sess.autoflush=False
    hcm = HostClusterMember(host=vm_host, cluster=ec)
    sess.autoflush=True

    add(sess, hcm)
    commit(sess)

    assert hcm
    print hcm

    assert ec.hosts
    assert len(ec.hosts) is 1
    print 'cluster members: %s'%(ec.hosts)

def test_add_machines():
    a = sess.query(MachineClusterMember).all()
    if a:
        print '%s machines are already in existence'

    machines = sess.query(Machine).filter(Machine.name.like(VM_NAME+'%')).all()
    ec = EsxCluster.get_unique(sess, CLUSTER_NAME)
    assert ec

    sess.autoflush=False
    for vm in machines[0:10]:
        mcm = MachineClusterMember(cluster=ec, machine=vm)
        add(sess, mcm)
    commit(sess)
    sess.autoflush=True

    assert len(ec.machines) is 10
    print 'there are %s machines in the cluster: %s'%(len(ec.machines), ec.machines)

def test_vm_append():
    machines = sess.query(Machine).filter(Machine.name.like(VM_NAME+'%')).all()
    ec = EsxCluster.get_unique(sess, CLUSTER_NAME)
    assert ec

    ec.machines.append(machines[12])
    commit(sess)
    assert len(ec.machines) is 11
    print 'now, there are %s machines in the cluster: %s'% (len(ec.machines),
                                                            ec.machines)

@raises(IntegrityError, AssertionError)
def test_host_in_two_clusters():
    """
        create 2 new clusters and add a host to both. check Host.cluster.
    """
    per = sess.query(Personality).select_from(
            join(Archetype, Personality)).filter(
            and_(Archetype.name=='windows', Personality.name=='generic')).one()

    for i in xrange(3):
        ec = EsxCluster(name='%s%s'% (CLUSTER_NAME, i), personality=per)
        add(sess, ec)
    commit(sess)

    c1 = sess.query(EsxCluster).filter_by(name='%s1'% (CLUSTER_NAME)).one()
    c2 = sess.query(EsxCluster).filter_by(name='%s2'% (CLUSTER_NAME)).one()

    assert c1
    assert c2
    print 'clusters in host in 2 cluster test are %s and %s'% (c1, c2)

    host = h_factory.next()


    sess.autoflush=False
    hcm1 = HostClusterMember(host=host, cluster=c1)
    add(sess, hcm1)
    commit(sess)
    assert host in c1.hosts
    print 'c1 hosts are %s'% (c1.hosts)

    c2.hosts.append(host)
    sess.autoflush=True
    commit(sess)


if __name__ == "__main__":
    import nose
    nose.runmodule()