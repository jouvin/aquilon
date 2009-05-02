#!/usr/bin/env python2.5

# Twisted, the Framework of Your Internet
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

# This is an (almost) completely new version of the script from
# the original twisted distributed.
# hacked to understand the MS layout.
# It was then enhanced (marked with comments below) to handle 8.1.0.

import sys, os
sys.path.append( os.path.join(
                    os.path.dirname( os.path.realpath(sys.argv[0]) ),
                    "..", "lib", "python2.5" ) )

import aquilon.server.depends
import aquilon.aqdb.depends

from twisted.scripts import twistd

# This bit is taken from the twisted.application.app... we
# really want logging to start up before the app does.  This may need
# to be revisited on future twisted upgrades.  The below is a clone
# of 8.1.0, except that startLogging has been broken up to increase
# the rotate length and moved one line earlier to start before the app.
def updated_application_run(self):
    """
    Run the application.
    """
    self.preApplication()
    observer = self.getLogObserver()
    # Serious hack... should create hooks to make this sane.
    if hasattr(observer, 'im_self') and hasattr(observer.im_self, 'write') \
       and hasattr(observer.im_self.write, 'im_self') \
       and hasattr(observer.im_self.write.im_self, 'rotateLength'):
        # When logging to a file, observer is a FileLogObserver's emit
        # method.  So im_self gets us the FLO.  The write attribute
        # has been aliased from the FileLog's write attribute, so *that*
        # im_self gets us the FileLog.  Then we can set rotateLength.  Whew!
        observer.im_self.write.im_self.rotateLength = 10000000
    self.startLogging(observer)
    self.application = self.createOrGetApplication()
    self.postApplication()

# Install the updated method.  Again, may be 8.1.0 specific, and relies
# on the internals of twisted.scripts.twistd.
twistd._SomeApplicationRunner.run = updated_application_run

# Back to the original 2.5.0-based code.
twistd.run()
