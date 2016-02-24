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

import os
import socket
import multiprocessing
import logging
import tempfile
import time
from . import family as families

logger = logging.getLogger(__name__)

# Try to hook into vigilant if present
try:
    import StatsCore
    from StatsCore.SimpleTransports import UDPStatsTransport, TCPStatsTransport
    from configparser import RawConfigParser as CParser
    use_observant = True
except:
    use_observant = False

import gssa.comparator
import gssa.definition
import gssa.translator
from gssa.error import Error, makeError
from gssa.config import etc_location
import gssa.utils


# FIXME: 18103 should be made configurable
_default_client_port = 18103


# This subclasses ApplicationSession, which runs inside an Autobahn WAMP session
class GoSmartSimulationServerComponent(object):
    current = None
    client = None
    _db = None

    def __init__(self, server_id, database, publish_cb, ignore_development=False, use_observant=use_observant):
        # This forwards exceptions to the client
        self.traceback_app = True

        self.server_id = server_id
        self.current = {}
        self.publish = publish_cb
        # Flag that tells the server to ignore anything with a parameter
        # `DEVELOPMENT` true
        self._ignore_development = ignore_development

        # If we are using vigilant, do the relevant set-up
        if use_observant:
            config = CParser()
            config.read(os.path.join(etc_location, 'vigilant.cfg'))

            lock = str(config.get('daemon', 'lock'))
            sock = str(config.get('daemon', 'sock'))
            transport_type = str(config.get('transport', 'type'))
            host = str(config.get('transport', 'host'))
            port = int(config.get('transport', 'port'))
            transport_means = UDPStatsTransport if transport_type == 'udp' else TCPStatsTransport
            transport = transport_means(host=host, port=port)

            self.client = StatsCore.attachOrCreateStatsDaemon(transport, pid=lock, sock=sock)
            self.client.postWatchPid('go-smart-simulation-server', os.getpid())

        # Convert this to a zope interface
        loop = asyncio.get_event_loop()

        # Create a directory to hold information specific to this server ID
        if not os.path.exists(server_id):
            logger.debug("Creating server ID directory")
            os.mkdir(server_id)

        logger.debug("Changing to server ID directory")

        # Use this as the working directory
        os.chdir(server_id)

        logger.debug("Storing identity (%s)" % server_id)

        # Provide a directory-internal way to find out our ID (i.e. without
        # looking at the name in the directory above)
        with open("identity", "w") as f:
            f.write(server_id)

        logger.debug("Requesting DB setup")

        # Flag this up to be done, but don't wait for it
        loop.call_soon_threadsafe(lambda: self.setDatabase(database()))

    # Retrieve a definition, if not from the current set, from persistent storage
    @asyncio.coroutine
    def _fetch_definition(self, guid):
        if guid in self.current:
            return self.current[guid]

        fut = asyncio.Future()
        loop = asyncio.get_event_loop()

        loop.call_soon_threadsafe(lambda: fut.set_result(self._db.retrieve(guid)))

        definition = yield from fut.result()

        if definition:
            self.current[guid] = definition
            return definition

        return False

    # For start-up, mark everything in-progress in the DB as not-in-progress/unfinished
    def setDatabase(self, database):
        self._db = database
        self._db.markAllOld()
        logger.debug("DB set up")

    # com.gosmartsimulation.init - dummy call for the moment
    @asyncio.coroutine
    def doInit(self, guid):
        return True

    # com.gosmartsimulation.clean - remove anything in simulation working
    # directory, for instance
    @asyncio.coroutine
    def doClean(self, guid):
        current = self._fetch_definition(guid)
        if not current:
            return False

        result = yield from current.clean()

        return result

    # com.gosmartsimulation.start - execute the simulation in a coro
    @asyncio.coroutine
    def doStart(self, guid):
        current = self._fetch_definition(guid)
        if not current:
            return False

        loop = asyncio.get_event_loop()
        coro = self.doSimulate(guid)
        task = loop.create_task(coro)

        # Once the simulation has completed, we must handle it
        task.add_done_callback(lambda f: asyncio.async(self._handle_simulation_done(f, guid=guid)))

        return True

    # DEPRECATED
    def doTmpValidation(self, guid, directory):
        # RMV: This is hacky
        loop = asyncio.get_event_loop()
        coro = families.register["elmer-libnuma"].validation(None, directory)
        try:
            task = loop.create_task(coro)
        except AttributeError:
            task = asyncio.async(coro, loop=loop)

        task.add_done_callback(lambda f: loop.call_soon_threadsafe(lambda: self._db.updateValidation(guid, f.result())))

        return True

    @asyncio.coroutine
    def _handle_simulation_done(self, fut, guid):
        # This should be the return value of the simulate call
        success = fut.result()
        logger.info("Simulation exited [%s]" % guid)

        current = self._fetch_definition(guid)
        if not current:
            return False

        if success:
            yield from self.eventComplete(guid)
        elif success is None:
            # None indicates we've dealt with failure (errored) already
            pass
        else:
            # We know this did not succeed, but not why it failed
            code = Error.E_UNKNOWN
            error_message = "Unknown error occurred"

            # In theory, an error message should have been written here, in any
            # case
            error_message_path = os.path.join(current.get_dir(), 'error_message')

            if (os.path.exists(error_message_path)):
                with open(error_message_path, 'r') as f:
                    code = f.readline().strip()
                    error_message = f.read().strip()
                    error_message.encode('ascii', 'xmlcharrefreplace')
                    error_message.encode('utf-8')

            logger.warning("Failed simulation in %s" % current.get_dir())
            yield from self.eventFail(guid, makeError(code, error_message))

        logger.info("Finished simulation")

    # com.gosmartsimulation.update_files - add the passed files to the
    # simulation's reference dictionary of required input files (available to be
    # requested later)
    @asyncio.coroutine
    def doUpdateFiles(self, guid, files):
        current = self._fetch_definition(guid)
        if not current or not isinstance(files, dict):
            return False

        logger.debug("Update Files")
        for local, remote in files.items():
            logger.debug("remote" + remote)
            logger.debug("Local" + local)
        current.update_files(files)

        return True

    # com.gosmartsimulation.request_files - push the requested output files
    # through the transferrer and return the list that was sent
    @asyncio.coroutine
    def doRequestFiles(self, guid, files):
        logger.info("Files requested for [%s]" % guid)

        return self.request_files(guid, files)

    # com.gosmartsimulation.request_results - push a bundle of output
    # files through the transferrer. If target is None, assume gateway is
    # running a temporary HTTP on default client port
    # FIXME: this should be made asynchronous!
    @asyncio.coroutine
    def doRequestResults(self, guid, target):
        current = self._fetch_definition(guid)
        if not current:
            logger.info("Simulation [%s] not found" % guid)
            return {}

        logger.info("Result bundle requested for [%s]" % guid)

        result_archive = current.gather_results()

        if target is None:
            gateway = gssa.utils.get_default_gateway()
            target = "http://%s:%d/%s.tgz" % (
                gateway,
                _default_client_port,
                guid
            )

        files = {result_archive: target}

        return self.request_files(guid, files)

    # com.gosmartsimulation.request_diagnostic - push a bundle of diagnostic
    # files through the transferrer. If target is None, assume gateway is
    # running a temporary HTTP on default client port
    # FIXME: this should be made asynchronous!
    @asyncio.coroutine
    def doRequestDiagnostic(self, guid, target):
        current = self._fetch_definition(guid)
        if not current:
            logger.info("Simulation [%s] not found" % guid)
            return {}

        logger.info("Diagnostic bundle requested for [%s]" % guid)

        diagnostic_archive = current.gather_diagnostic()

        if target is None:
            gateway = gssa.utils.get_default_gateway()
            target = "http://%s:%d/%s.tgz" % (
                gateway,
                _default_client_port,
                guid
            )

        files = {diagnostic_archive: target}

        return self.request_files(guid, files)

    # Helper routine as several endpoints involve returning file requests
    def _request_files(self, guid, files, target):
        current = self._fetch_definition(guid)
        if not current or not isinstance(files, dict):
            return {}

        try:
            uploaded_files = current.push_files(files)
        except Exception:
            logger.exception("Problem pushing files")
            return {}

        logger.info("Files sent")

        return uploaded_files

    # com.gosmartsimulation.compare - check whether two GSSA-XML files match
    # and, if not, what their differences are
    @asyncio.coroutine
    def doCompare(self, this_xml, that_xml):
        comparator = gssa.comparator.Comparator(this_xml, that_xml)
        return comparator.diff()

    # com.gosmartsimulation.update_settings_xml - set the GSSA-XML for a given
    # simulation
    @asyncio.coroutine
    def doUpdateSettingsXml(self, guid, xml):
        try:
            # Create a working directory for the simulation (this is needed even
            # if the tool runs elsewhere, as in the Docker case)
            tmpdir = tempfile.mkdtemp(prefix='/simdata/')
            os.chmod(tmpdir, 0o770)
            logger.debug("Changed permissions")

            # Set up the translator to parse the standard bits of GSSA-XML
            translator = gssa.translator.GoSmartSimulationTranslator()
            self.current[guid] = gssa.definition.GoSmartSimulationDefinition(
                guid,
                xml,
                tmpdir,
                translator,
                finalized=False,
                ignore_development=self._ignore_development,
                update_status_callback=lambda p, m: self.updateStatus(guid, p, m)
            )

            # Announce that XML has been uploaded
            # TODO: why announce this? Surely the response is sufficient?
            self.publish(u'com.gosmartsimulation.announce', self.server_id, guid, [0, 'XML uploaded'], tmpdir, time.time())
        except Exception as e:
            logger.exception("Problem updating settings XML")
            raise e

        logger.debug("XML set")

        return True

    # Start the simulation. This occurs in a separately scheduled coro from the
    # RPC call so it will almost certainly have returned by time we do
    @asyncio.coroutine
    def doSimulate(self, guid):
        current = self._fetch_definition(guid)
        if not current:
            yield from self.eventFail(guid, makeError(Error.E_CLIENT, "Not fully prepared before launching - no current simulation set"))
            success = None

        logger.debug("Running simulation in %s" % current.get_dir())

        # Inform the user that we got this far
        self.updateStatus(guid, 0, "Starting simulation...")
        # Start the socket server before simulating
        yield from current.init_percentage_socket_server()

        # Start the simulation. If we get an error, then blame the server side -
        # it should have returned False
        # FIXME: so how exactly does any non E_SERVER message get sent back?
        try:
            success = yield from current.simulate()
        except Exception as e:
            logger.exception("Simulation failed! {exc}".format(exc=e))
            yield from self.eventFail(guid, makeError(Error.E_SERVER, "[%s] %s" % (type(e), str(e))))
            success = None

        return success

    # com.gosmartsimulation.finalize - do any remaining preparation before the
    # simulation can start
    @asyncio.coroutine
    def doFinalize(self, guid, client_directory_prefix):
        logger.debug("Converting the Xml")
        current = self._fetch_definition(guid)
        if not current:
            return False

        current.set_remote_dir(client_directory_prefix)

        # Make sure the simulation is in the DB
        self._db.addOrUpdate(current)

        # Execute the finalization
        result = current.finalize()

        return result

    # com.gosmartsimulation.properties - return important server-side simulation
    # properties
    @asyncio.coroutine
    def doProperties(self, guid):
        return self.getProperties(guid)

    # Server-specific properties for this simulation (at present, just wd location)
    def getProperties(self, guid):
        current = self._fetch_definition(guid)
        if not current:
            raise RuntimeError("Simulation not found: %s" % guid)

        return {"location": current.get_dir()}

    # Called when simulation completes - publishes a completion event
    @asyncio.coroutine
    def eventComplete(self, guid):
        logger.debug("Completed [%s]" % guid)
        current = self._fetch_definition(guid)
        if not current:
            logger.warning("Tried to send simulation-specific completion event with no current simulation definition")

        # Record the finishing time, as we see it
        timestamp = time.time()

        logger.debug(timestamp)
        try:
            # Tell the database we have finished
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(lambda: self.setStatus(guid, "SUCCESS", "Success", "100", timestamp))
            # Run validation (if req)
            validation = None
            #validation = yield from self.current[guid].validation()
            #if validation:
            #    loop.call_soon_threadsafe(lambda: self._db.updateValidation(guid, validation))
        except:
            validation = None
            logger.exception("Problem with completion/validation")

        current.set_exit_status(True)
        logger.info('Success [%s]' % guid)

        # Notify any subscribers
        self.publish(u'com.gosmartsimulation.complete', guid, makeError('SUCCESS', 'Success'), current.get_dir(), timestamp, validation)

    # Called when simulation fails - publishes a failure event
    @asyncio.coroutine
    def eventFail(self, guid, message):
        current = self._fetch_definition(guid)
        if not current:
            logger.warning("Tried to send simulation-specific failure event with no current simulation definition")

        # Record the failure time as we see it
        timestamp = time.time()

        try:
            loop = asyncio.get_event_loop()
            # Update the database
            loop.call_soon_threadsafe(lambda: self.setStatus(guid, message["code"], message["message"], None, timestamp))
        except:
            logger.exception("Problem saving failure status")

        current.set_exit_status(False, message)
        logger.warning('Failure [%s]: %s' % (guid, repr(message)))

        # Notify any subscribers
        self.publish(u'com.gosmartsimulation.fail', guid, message, current.get_dir(), timestamp, None)

    # com.gosmartsimulation.retrieve_status - get the latest status for a
    # simulation
    @asyncio.coroutine
    def doRetrieveStatus(self, guid):
        # Get this from the DB, not current, as the DB should give a consistent
        # answer even after restart (unless marked unfinished)
        simulation = self._db.retrieve(guid)
        exit_code = simulation['exit_code']

        if exit_code is None:
            if simulation['guid'] in self.current:
                exit_code = 'IN_PROGRESS'
            else:
                exit_code = 'E_UNKNOWN'

        # NB: makeError can return SUCCESS or IN_PROGRESS
        status = makeError(exit_code, simulation['status'])
        percentage = simulation['percentage']

        # This format matches the fail/status/complete events
        return {
            "server_id": self.server_id,
            "simulation_id": simulation['guid'],
            "status": (percentage, status),
            "directory": simulation['directory'],
            "timestamp": simulation['timestamp'],
            "validation": simulation['validation']
        }

    # com.gosmartsimulation.request_announce - release a status report on each
    # simulation in the database
    # TODO: this gets unwieldy, perhaps it should have an earliest simulation
    # timestamp argument?
    def onRequestAnnounce(self):
        # Go through /every/ simulation
        return 1
        simulations = self._db.all()
        for simulation in simulations:
            exit_code = simulation['exit_code']

            # If it hasn't exited, it should be running...
            if exit_code is None:
                if simulation['guid'] in self.current:
                    exit_code = 'IN_PROGRESS'
                else:
                    exit_code = 'E_UNKNOWN'

            status = makeError(exit_code, simulation['status'])
            percentage = simulation['percentage']

            # Tell the world
            self.publish(u'com.gosmartsimulation.announce', self.server_id, simulation['guid'], (percentage, status), simulation['directory'], simulation['timestamp'], simulation['validation'])
            logger.debug("Announced: %s %s %r" % (simulation['guid'], simulation['directory'], simulation['validation'] is not None))

        # Follow up with an identify event
        self.onRequestIdentify()

    # Record a status change in the database and on the filesystem. Note that,
    # for both those reasons, this could be slow and so should always be run
    # with call_soon_threadsafe
    # FIXME: we need some sort of rate limiting here, or producer-consumer
    # pattern with ability to skip once getting behind
    def setStatus(self, id, key, message, percentage, timestamp):
        # Write this message to the database
        self._db.setStatus(id, key, message, percentage, timestamp)

        # Write the last message in a format that the status can be easily
        # re-read
        with open(os.path.join(self.current[id].get_dir(), 'last_message'), 'w') as f:
            f.write("%s\n" % id)
            f.write("%s\n" % key.strip())
            if percentage:
                f.write("%lf\n" % float(percentage))
            else:
                f.write("\n")
            if message:
                f.write(message.strip())

    # Update the status, setting up a callback for asyncio
    def updateStatus(self, guid, percentage, message):
        timestamp = time.time()

        # Write out to the command line for debug
        # TODO: switch to `logger` and `vigilant`
        progress = "%.2lf" % percentage if percentage else '##'
        logger.debug("%s [%r] ---- %s%%: %s" % (guid, timestamp, progress, message))

        try:
            # Call the setStatus method asynchronously
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(lambda: self.setStatus(guid, 'IN_PROGRESS', message, percentage, timestamp))
        except:
            logger.exception("Problem saving status")

        directory = None
        current = self._fetch_definition(guid)
        if current:
            directory = current.get_dir()

        # Publish a status update for the WAMP clients to see
        self.publish('com.gosmartsimulation.status', guid, (percentage, makeError('IN_PROGRESS', message)), directory, timestamp, None)

    # com.gosmartsimulation.request_identify - publish basic server information
    def onRequestIdentify(self):
        # score = #cores - #active_simulations
        # this gives an availability estimate, the higher the better
        # FIXME: this seems to give a wrong number consistently, needs checked
        try:
            active_simulations = self._db.active_count()
            score = multiprocessing.cpu_count() - active_simulations
            server_name = socket.gethostname()

            self.publish(
                u'com.gosmartsimulation.identify',
                self.server_id,
                server_name,
                score
            )
            logger.info("Announced score: %d [%s]" % (score, self.server_id))
        except Exception as e:
            logger.error("Didn't send score!")
            raise e
