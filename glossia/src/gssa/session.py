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


class GoSmartSimulationServerSession(ApplicationSession):
    """This subclasses ApplicationSession, which runs inside an Autobahn WAMP session.

    .. inheritance-diagram:: gssa.session.GoSmartSimulationServerSession

    """
    _component = None

    def __init__(self, x, server_id, database, ignore_development=False, simdata_path='/tmp'):
        self.server_id = server_id
        self._component = GoSmartSimulationServerComponent(
            server_id,
            database,
            self.publish,
            ignore_development=ignore_development,
            simdata_path=simdata_path
        )
        ApplicationSession.__init__(self, x)

    @asyncio.coroutine
    def doSearch(self, guid, limit=None):
        """``com.gosmartsimulation.search``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doSearch`

        Check for matching definitions.

        """
        return self._component.doSearch(guid, limit)

    @asyncio.coroutine
    def doInit(self, guid):
        """``com.gosmartsimulation.init``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doInit`

        Dummy call for the moment.

        """
        return self._component.doInit(guid)

    @asyncio.coroutine
    def doApi(self):
        """``com.gosmartsimulation.api``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doApi`

        Find the current API version in use. The API version only needs to be
        bumped when backward-incompatible changes occur on either side.

        """
        return self._component.doApi()

    @asyncio.coroutine
    def doClean(self, guid):
        """``com.gosmartsimulation.clean``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doClean`

        Remove anything in simulation directory, for instance.

        """
        return self._component.doClean(guid)

    @asyncio.coroutine
    def doStart(self, guid):
        """``com.gosmartsimulation.start``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doStart`

        Execute the simulation in a coro.

        """
        return self._component.doStart(guid)

    @asyncio.coroutine
    def doTmpValidation(self, guid, directory):
        # RMV: This is hacky
        return self._component.doTmpValidation(directory)

    @asyncio.coroutine
    def doUpdateFiles(self, guid, files):
        """``com.gosmartsimulation.update_files``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doUpdateFiles`

        Add the passed files to simulation's reference dictionary of required
        input files (available to be requested later).

        """
        return self._component.doUpdateFiles(guid, files)

    @asyncio.coroutine
    def doCancel(self, guid):
        """``com.gosmartsimulation.cancel``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doCancel`

        Prematurely stop a running simulation but bear in mind that no request for
        confirmation exists!

        """
        return self._component.doCancel(guid)

    @asyncio.coroutine
    def doRequestFiles(self, guid, files):
        """``com.gosmartsimulation.request_files``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doRequestFiles`

        Push the requested output files through the transferrer and return the
        list that was sent.

        """
        return self._component.doRequestFiles(guid, files)

    @asyncio.coroutine
    def doCompare(self, this_xml, that_xml):
        """``com.gosmartsimulation.compare``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doCompare`

        Check whether two GSSA-XML files match and, if not, what their
        differences are.

        """
        return self._component.doCompare(this_xml, that_xml)

    @asyncio.coroutine
    def doUpdateSettingsXml(self, guid, xml):
        """``com.gosmartsimulation.update_settings_xml``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doUpdateSettingsXml`

        Set the GSSA-XML for a given simulation.

        """
        return self._component.doUpdateSettingsXml(guid, xml)

    @asyncio.coroutine
    def doFinalize(self, guid, client_directory_prefix):
        """``com.gosmartsimulation.finalize``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doFinalize`

        Do any remaining preparation before the simulation can start.

        """
        return self._component.doFinalize(guid, client_directory_prefix)

    @asyncio.coroutine
    def doProperties(self, guid):
        """``com.gosmartsimulation.properties``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doProperties`

        Return important server-side simulation properties.

        """
        return self._component.doProperties(guid)

    @asyncio.coroutine
    def doRequestResults(self, guid, target):
        """``com.gosmartsimulation.request_results``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doRequestResults`

        Push a bundle of result files through the transferrer.

        """
        return self._component.doRequestResults(guid, target)

    @asyncio.coroutine
    def doRequestDiagnostic(self, guid, target):
        """``com.gosmartsimulation.request_diagnostic``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doRequestDiagnostic`

        Push a bundle of diagnostic files through the transferrer.

        """
        return self._component.doRequestDiagnostic(guid, target)

    @asyncio.coroutine
    def doRetrieveStatus(self, guid):
        """``com.gosmartsimulation.retrieve_status``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.doRetrieveStatus`

        Get the latest status for a simulation.

        """
        return self._component.doRetrieveStatus(guid)

    @asyncio.coroutine
    def onRequestAnnounce(self):
        """``com.gosmartsimulation.request_announce``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.onRequestAnnounce`

        Release a status report on each simulation in the database. TODO: this
        gets unwieldy, perhaps it should have an earliest simulation timestamp
        argument?.

        """
        self._component.onRequestAnnounce()

    @asyncio.coroutine
    def onRequestIdentify(self):
        """``com.gosmartsimulation.request_identify``

        :py:func:`gssa.server.GoSmartSimulationServerComponent.onRequestIdentify`

        Publish basic server information.

        """
        self._component.onRequestIdentify()

    def onJoin(self, details):
        """Register methods and subscribes.

        Fired when we first join the router - this gives us a chance to
        register everything.

        """
        logger.info("session ready")

        # Register an us-specific set of RPC calls. Also attempts to do the same
        # for the generic set, if we haven't been beaten to the punch
        try:
            for i in ('.' + self.server_id, ''):
                self.subscribe(self.onRequestAnnounce, u'com.gosmartsimulation%s.request_announce' % i)
                self.subscribe(self.onRequestIdentify, u'com.gosmartsimulation%s.request_identify' % i)

                self.register(self.doSearch, u'com.gosmartsimulation%s.search' % i)
                self.register(self.doInit, u'com.gosmartsimulation%s.init' % i)
                self.register(self.doStart, u'com.gosmartsimulation%s.start' % i)
                self.register(self.doUpdateSettingsXml, u'com.gosmartsimulation%s.update_settings_xml' % i)
                self.register(self.doUpdateFiles, u'com.gosmartsimulation%s.update_files' % i)
                self.register(self.doCancel, u'com.gosmartsimulation%s.cancel' % i)
                self.register(self.doRequestFiles, u'com.gosmartsimulation%s.request_files' % i)
                self.register(self.doRequestDiagnostic, u'com.gosmartsimulation%s.request_diagnostic' % i)
                self.register(self.doRequestResults, u'com.gosmartsimulation%s.request_results' % i)
                self.register(self.doTmpValidation, u'com.gosmartsimulation%s.tmp_validation' % i)
                self.register(self.doFinalize, u'com.gosmartsimulation%s.finalize' % i)
                self.register(self.doClean, u'com.gosmartsimulation%s.clean' % i)
                self.register(self.doCompare, u'com.gosmartsimulation%s.compare' % i)
                self.register(self.doProperties, u'com.gosmartsimulation%s.properties' % i)
                self.register(self.doRetrieveStatus, u'com.gosmartsimulation%s.retrieve_status' % i)
                self.register(self.doApi, u'com.gosmartsimulation%s.api' % i)
            logger.info("procedure registered")
        except Exception as e:
            logger.warning("could not register procedure: {0}".format(e))
