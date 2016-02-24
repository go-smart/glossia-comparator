# This file is part of the Go-Smart Simulation Architecture (GSSA).
# Go-Smart is an EU-FP7 project, funded by the European Commission.
#
# Copyright (C) 2013-  NUMA Engineering Ltd. (see AUTHORS file)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# This is a workaround for syntastic lack of Py3 recognition

import asyncio
from autobahn.asyncio.wamp import ApplicationSession

import logging

logger = logging.getLogger(__name__)

from .server import GoSmartSimulationServerComponent


# This subclasses ApplicationSession, which runs inside an Autobahn WAMP session
class GoSmartSimulationServerSession(ApplicationSession):
    _component = None

    def __init__(self, x, server_id, database, ignore_development=False):
        self.server_id = server_id
        self._component = GoSmartSimulationServerComponent(
            server_id,
            database,
            self.publish,
            ignore_development=ignore_development,
        )
        ApplicationSession.__init__(self, x)

    # com.gosmartsimulation.init - dummy call for the moment
    @asyncio.coroutine
    def doInit(self, guid):
        return self._component.doInit(guid)

    # com.gosmartsimulation.clean - remove anything in simulation working
    # directory, for instance
    @asyncio.coroutine
    def doClean(self, guid):
        return self._component.doClean(guid)

    # com.gosmartsimulation.start - execute the simulation in a coro
    @asyncio.coroutine
    def doStart(self, guid):
        return self._component.doStart(guid)

    @asyncio.coroutine
    def doTmpValidation(self, guid, directory):
        # RMV: This is hacky
        return self._component.doTmpValidation(directory)

    # com.gosmartsimulation.update_files - add the passed files to the
    # simulation's reference dictionary of required input files (available to be
    # requested later)
    @asyncio.coroutine
    def doUpdateFiles(self, guid, files):
        return self._component.doUpdateFiles(guid, files)

    # com.gosmartsimulation.request_files - push the requested output files
    # through the transferrer and return the list that was sent
    @asyncio.coroutine
    def doRequestFiles(self, guid, files):
        return self._component.doRequestFiles(guid, files)

    # com.gosmartsimulation.compare - check whether two GSSA-XML files match
    # and, if not, what their differences are
    @asyncio.coroutine
    def doCompare(self, this_xml, that_xml):
        return self._component.doCompare(this_xml, that_xml)

    # com.gosmartsimulation.update_settings_xml - set the GSSA-XML for a given
    # simulation
    @asyncio.coroutine
    def doUpdateSettingsXml(self, guid, xml):
        return self._component.doUpdateSettingsXml(guid, xml)

    # com.gosmartsimulation.finalize - do any remaining preparation before the
    # simulation can start
    @asyncio.coroutine
    def doFinalize(self, guid, client_directory_prefix):
        return self._component.doFinalize(guid, client_directory_prefix)

    # com.gosmartsimulation.properties - return important server-side simulation
    # properties
    @asyncio.coroutine
    def doProperties(self, guid):
        return self._component.doProperties(guid)

    # com.gosmartsimulation.request_diagnostic - push a bundle of diagnostic
    # files through the transferrer
    @asyncio.coroutine
    def doRequestDiagnostic(self, guid, target):
        return self._component.doRequestDiagnostic(guid, target)

    # com.gosmartsimulation.retrieve_status - get the latest status for a
    # simulation
    @asyncio.coroutine
    def doRetrieveStatus(self, guid):
        return self._component.doRetrieveStatus(guid)

    # com.gosmartsimulation.request_announce - release a status report on each
    # simulation in the database
    # TODO: this gets unwieldy, perhaps it should have an earliest simulation
    # timestamp argument?
    @asyncio.coroutine
    def onRequestAnnounce(self):
        self._component.doRequestAnnounce()

    # com.gosmartsimulation.request_identify - publish basic server information
    @asyncio.coroutine
    def onRequestIdentify(self):
        self._component.onRequestIdentify()

    # Fired when we first join the router - this gives us a chance to register
    # everything
    def onJoin(self, details):
        logger.info("session ready")

        # Register an us-specific set of RPC calls. Also attempts to do the same
        # for the generic set, if we haven't been beaten to the punch
        try:
            for i in ('.' + self.server_id, ''):
                self.subscribe(self.onRequestAnnounce, u'com.gosmartsimulation%s.request_announce' % i)
                self.subscribe(self.onRequestIdentify, u'com.gosmartsimulation%s.request_identify' % i)

                self.register(self.doInit, u'com.gosmartsimulation%s.init' % i)
                self.register(self.doStart, u'com.gosmartsimulation%s.start' % i)
                self.register(self.doUpdateSettingsXml, u'com.gosmartsimulation%s.update_settings_xml' % i)
                self.register(self.doUpdateFiles, u'com.gosmartsimulation%s.update_files' % i)
                self.register(self.doRequestFiles, u'com.gosmartsimulation%s.request_files' % i)
                self.register(self.doRequestDiagnostic, u'com.gosmartsimulation%s.request_diagnostic' % i)
                self.register(self.doTmpValidation, u'com.gosmartsimulation%s.tmp_validation' % i)
                self.register(self.doFinalize, u'com.gosmartsimulation%s.finalize' % i)
                self.register(self.doClean, u'com.gosmartsimulation%s.clean' % i)
                self.register(self.doCompare, u'com.gosmartsimulation%s.compare' % i)
                self.register(self.doProperties, u'com.gosmartsimulation%s.properties' % i)
                self.register(self.doRetrieveStatus, u'com.gosmartsimulation%s.retrieve_status' % i)
            logger.info("procedure registered")
        except Exception as e:
            logger.warning("could not register procedure: {0}".format(e))
