#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""The main class here is ResponsePage, which contains all the methods
for implementing the various aq commands.

To implement a command, define a transport for it in input.xml and
then add a command_<name>[_trigger] method to the ResponsePage class.
Any variables in the URL itself will be available as
request.args["varname"][0] where "varname" is the name of the
option.  (Any normal query/post variables will also be in this dict.)

The pages are built up at server start time based on the definitions in
the server's input.xml.  The RestServer class (which itself inherits
from ResponsePage for serving requests) contains this magic.  This
class builds out all the ResponsePage children as part of its __init__.

For any given ResponsePage, all methods (including all the command_
methods) are available, but only the expected methods for that relative
URL will be assigned to render_GET, render_POST, etc.  The rest will be
dormant.

As the request comes in (and passes through the various
getChildWithDefault() calls) it will be checked for extensions that
match the available format functions.  A request for location.html,
for example, will retrieve 'location' and format it with format_html().

ToDo:
    - Possibly massage the incoming data - simplify lists back to
        single variables, handle put content, etc.
    - Add some sort of interface that can be implemented for
        objects to give hints on how they should be rendered.
    - Add other output formats (csv, xml, etc.).

"""

import re
import sys
import os
import xml.etree.ElementTree as ET

from twisted.web import server, resource, http, static
from twisted.internet import defer, threads
from twisted.python import log

from aquilon.exceptions_ import ArgumentError, AuthorizationException, \
        NotFoundException, UnimplementedError, PartialError
from aquilon.server.formats.formatters import ResponseFormatter
from aquilon.server.broker import BrokerCommand
from aquilon.server import commands


class ResponsePage(resource.Resource):

    def __init__(self, path, formatter, path_variable=None):
        self.path = path
        self.path_variable = path_variable
        self.dynamic_child = None
        resource.Resource.__init__(self)
        self.formatter = formatter
        self.handlers = {}

    def getChildWithDefault(self, path, request):
        """Overriding this method to parse formatting requests out
        of the incoming resource request."""

        # A good optimization here would be to have the resource store
        # a compiled regular expression to use instead of this loop.
        for style in self.formatter.formats:
            #log.msg("Checking style: %s" % style)
            extension = "." + style
            if path.endswith(extension):
                #log.msg("Retrieving formatted child for dynamic page: %s" % path)
                request.output_format = style
                # Chop off the extension when searching for children
                path = path[:-len(extension)]
                break
        return resource.Resource.getChildWithDefault(self, path, request)

    def getChild(self, path, request):
        """Typically in twisted.web, a dynamic child would be created...
        dynamically.  However, to make the command_* mappings possible,
        they were all created at start time.

        This is an issue because the path cannot be handed to the
        constructor for it to deal with variable path names.  Instead,
        the request object is abused - the variable path names are
        crammed into the data structure used for query and post
        arguments before handing back the child that is being
        requested.

        This method also checks to see if a format has been requested,
        and tucks that info away in the request object as well.  This
        is done for the static objects simply by replicating them at
        creation time - one for each style.
        """

        if not self.dynamic_child:
            return resource.Resource.getChild(self, path, request)

        #log.msg("Retrieving child for dynamic page: %s" % path)
        request.args[self.dynamic_child.path_variable] = [path]
        return self.dynamic_child

    def render(self, request):
        """This is based on the default implementation from
        resource.Resource that checks for the appropriate method to
        delegate to.

        It adds a default handler for arguments in a PUT request and
        delegation of argument parsing.
        The processing is pushed off onto a thread and wrapped with
        error handling.

        """
        if request.method == 'PUT':
            # For now, assume all put requests use a simple urllib encoding.
            request.content.seek(0)
            # Since these are both lists, there is a theoretical case where
            # one might want to merge the lists, instead of overwriting with
            # the new.  Not sure if that matters right now.
            request.args.update( http.parse_qs(request.content.read()) )
        # FIXME: This breaks HEAD and OPTIONS handling...
        handler = self.handlers.get(request.method, None)
        if not handler:
            # FIXME: This may be broken, if it is supposed to get a useful
            # message based on available render_ methods.
            raise server.UnsupportedMethod(getattr(self, 'allowedMethods', ()))
        # Default render would just call the method here.
        # This is expanded to do argument checking, finish the request, 
        # and do some error handling.
        d = self.check_arguments(request,
                handler.required_parameters, handler.optional_parameters)
        style = getattr(self, "output_format", None)
        if style is None:
            style = getattr(request, "output_format", None)
        if style is None:
            style = getattr(handler, "default_style", "raw")
        d = d.addCallback(lambda arguments: threads.deferToThread(
                handler.render, style=style, request=request, **arguments))
        d = d.addCallback(self.finishRender, request)
        d = d.addErrback(self.wrapNonInternalError, request)
        d = d.addErrback(self.wrapError, request)
        return server.NOT_DONE_YET

    def check_arguments(self, request, required = [], optional = []):
        """Check for the required and optional arguments.

        Returns a Deferred that will have a dictionary of the arguments
        found.  Any unsupplied optional arguments will have a value of 
        None.  If there are any problems, the Deferred will errback with
        a failure.
        
        This should probably rely on the input.xml file for the list
        of required and optional arguments.  For now, it is just a 
        utility function.
        """

        required_map = {}
        for arg in optional or []:
            required_map[arg] = False
        for arg in required or []:
            required_map[arg] = True

        arguments = {}
        for (arg, req) in required_map.items():
            #log.msg("Checking for arg %s with required=%s" % (arg, req))
            if not request.args.has_key(arg):
                if req:
                    return defer.fail(ArgumentError(
                        "Missing mandatory argument %s" % arg))
                else:
                    arguments[arg] = None
                    continue
            values = request.args[arg]
            if not isinstance(values, list):
                # FIXME: This should be something that raises a 500
                # (Internal Server Error)... this is handled internally.
                return defer.fail(ArgumentError(
                    "Internal Error: Expected list for %s, got '%s'"
                    % (arg, str(values))))
            arguments[arg] = values[0]
        return defer.succeed(arguments)

    def format(self, result, request):
        style = getattr(self, "output_format", None)
        if style is None:
            style = getattr(request, "output_format", "raw")
        return self.formatter.format(style, result, request)

    def finishRender(self, result, request):
        if result:
            request.setHeader('content-length', str(len(result)))
            request.write(result)
        else:
            request.setHeader('content-length', 0)
        request.finish()
        return

    def wrapNonInternalError(self, failure, request):
        """This takes care of 'expected' problems, like NotFoundException."""
        r = failure.trap(NotFoundException, AuthorizationException,
                ArgumentError, UnimplementedError, PartialError)
        if r == NotFoundException:
            request.setResponseCode(http.NOT_FOUND)
        elif r == AuthorizationException:
            request.setResponseCode(http.UNAUTHORIZED)
        elif r == ArgumentError:
            request.setResponseCode(http.BAD_REQUEST)
        elif r == UnimplementedError:
            request.setResponseCode(http.NOT_IMPLEMENTED)
        elif r == PartialError:
            request.setResponseCode(http.MULTI_STATUS)
        formatted = self.format(failure.value, request)
        return self.finishRender(formatted, request)

    # TODO: Something should go into both the logs and back to the client...
    def wrapError(self, failure, request):
        """This is generally the final stop for errors - anything will be
        caught, logged, and a 500 error passed back to the client."""
        log.err(failure.getBriefTraceback())
        msg = failure.getErrorMessage()
        log.err(failure.getErrorMessage())
        #failure.printDetailedTraceback()
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        return self.finishRender(msg, request)


class RestServer(ResponsePage):
    """The root resource is used to define the site as a whole."""
    def __init__(self, config):
        formatter = ResponseFormatter()
        ResponsePage.__init__(self, '', formatter)
        self.config = config

        # Regular Expression for matching variables in a path definition.
        # Currently only supports stuffing a single variable in a path
        # component.
        varmatch = re.compile(r'^%\((.*)\)s$')

        BINDIR = os.path.dirname( os.path.realpath(sys.argv[0]) )
        tree = ET.parse( os.path.join( BINDIR, '..', 'etc', 'input.xml' ) )

        for command in tree.getiterator("command"):
            for transport in command.getiterator("transport"):
                if not command.attrib.has_key("name") \
                        or not transport.attrib.has_key("method") \
                        or not transport.attrib.has_key("path"):
                    continue
                name = command.attrib["name"]
                method = transport.attrib["method"]
                path = transport.attrib["path"]
                trigger = transport.attrib.get("trigger")
                container = self
                relative = ""
                # Traverse down the resource tree, container will
                # end up pointing to the correct spot.
                # Create branches and leaves as necessary, continueing to
                # traverse downward.
                for component in path.split("/"):
                    relative = relative + "/" + component
                    #log.msg("Working with component '" + component + "' of '" + relative + "'.")
                    m = varmatch.match(component)
                    # Is this piece of the path dynamic?
                    if not m:
                        #log.msg("Component '" + component + "' is static.")
                        child = container.getStaticEntity(component)
                        if child is None:
                            #log.msg("Creating new static component '" + component + "'.")
                            child = ResponsePage(relative,
                                    formatter)
                            container.putChild(component, child)
                        container = child
                    else:
                        #log.msg("Component '" + component + "' is dynamic.")
                        path_variable = m.group(1)
                        if container.dynamic_child is not None:
                            #log.msg("Dynamic component '" + component + "' already exists.")
                            current_variable = container.dynamic_child.\
                                    path_variable
                            if current_variable != path_variable:
                                log.err("Could not use variable '"
                                        + path_variable + "', already have "
                                        + "dynamic variable '"
                                        + current_variable + "'.")
                                # XXX: Raise an error if they don't match
                                container = container.dynamic_child
                            else:
                                #log.msg("Dynamic component '" + component + "' had correct variable.")
                                container = container.dynamic_child
                        else:
                            #log.msg("Creating new dynamic component '" + component + "'.")
                            child = ResponsePage(relative,
                                    formatter, path_variable=path_variable)
                            container.dynamic_child = child
                            container = child

                fullcommand = name
                if trigger:
                    fullcommand = fullcommand + "_" + trigger
                mymodule = getattr(commands, fullcommand, None)
                if not mymodule:
                    log.msg("No module available in aquilon.server.commands " +
                            "for %s" % fullcommand)
                # See commands/__init__.py for more info here...
                myinstance = getattr(mymodule, "broker_command", None)
                if not myinstance:
                    log.msg("No class instance available for %s" % fullcommand)
                    myinstance = BrokerCommand()
                rendermethod = method.upper()
                if container.handlers.get(rendermethod, None):
                    log.err("Already have a %s here at %s..." %
                            (rendermethod, container.path))
                #log.msg("Setting 'command_" + fullcommand + "' as '" + rendermethod + "' for container '" + container.path + "'.")
                container.handlers[rendermethod] = myinstance

                # Since we are parsing input.xml anyway, record the possible
                # parameters...
                for option in command.getiterator("option"):
                    if not option.attrib.has_key("name"):
                        continue
                    option_name = option.attrib["name"]
                    if option_name not in myinstance.optional_parameters:
                        myinstance.optional_parameters.append(option_name)

        # FIXME: Only do this if needed...
        # Serve up a static templates directory for git...
        #log.msg("Checking on %s" % self.broker.templatesdir)
        templatesdir = config.get("broker", "templatesdir")
        if os.path.exists(templatesdir):
            self.putChild("templates", static.File(templatesdir))
        else:
            log.err("ERROR: templates directory '%s' not found, will not serve"
                    % templatesdir)

        self.make_required_dirs()

        def _logChildren(level, container):
            for (key, child) in container.listStaticEntities():
                log.msg("Resource at level %d for %s [key:%s]"
                        % (level, child.path, key))
                _logChildren(level+1, child)
            if getattr(container, "dynamic_child", None):
                log.msg("Resource at level %d for %s [dynamic]"
                        % (level, container.dynamic_child.path))
                _logChildren(level+1, container.dynamic_child)

        #_logChildren(0, self)

    def set_umask(self):
        os.umask(int(self.config.get("broker", "umask"), 8))

    def make_required_dirs(self):
        for d in ["basedir", "profilesdir", "depsdir", "hostsdir",
                "plenarydir", "rundir"]:
            dir = self.config.get("broker", d)
            if os.path.exists(dir):
                continue
            try:
                os.makedirs(dir)
            except OSError, e:
                log.err(e)

