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
import functools
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

import gssa.transferrer
import gssa.comparator
import gssa.definition
import gssa.translator
import gssa.error
import gssa.config
import gssa.utils


def _threadsafe_call(function, *args, **kwargs):
    loop = asyncio.get_event_loop()
    loop.call_soon_threadsafe(functools.partial(function, *args, **kwargs))

# FIXME: 18103 should be made configurable
_default_client_port = 18103


class GoSmartSimulationServerComponent(object):
    """This subclasses ApplicationSession, which runs inside an Autobahn WAMP session

    """
    current = None
    client = None
    _db = None

    def _write_identity(self, identity):
        """Provide a directory-internal way to find out our ID (i.e. without
           looking at the name in the directory above)

        """
        with open("identity", "w") as f:
            f.write(identity)

    def __init__(self, server_id, database, publish_cb, ignore_development=False, use_observant=use_observant, simdata_path='/tmp'):
        # This forwards exceptions to the client
        self.traceback_app = True

        self.server_id = server_id
        self.current = {}
        self.publish = publish_cb
        # Flag that tells the server to ignore anything with a parameter
        # `DEVELOPMENT` true
        self._ignore_development = ignore_development
        self._simdata_path = simdata_path

        # If we are using vigilant, do the relevant set-up
        if use_observant:
            config = CParser()
            config.read(os.path.join(gssa.config.etc_location, 'vigilant.cfg'))

            lock = str(config.get('daemon', 'lock'))
            sock = str(config.get('daemon', 'sock'))
            transport_type = str(config.get('transport', 'type'))
            host = str(config.get('transport', 'host'))
            port = int(config.get('transport', 'port'))
            transport_means = UDPStatsTransport if transport_type == 'udp' else TCPStatsTransport
            transport = transport_means(host=host, port=port)

            self.client = StatsCore.attachOrCreateStatsDaemon(transport, pid=lock, sock=sock)
            self.client.postWatchPid('go-smart-simulation-server', os.getpid())

        # Create a directory to hold information specific to this server ID
        if not os.path.exists(server_id):
            logger.debug("Creating server ID directory")
            os.mkdir(server_id)

        logger.debug("Changing to server ID directory")

        # Use this as the working directory
        os.chdir(server_id)

        logger.debug("Storing identity (%s)" % server_id)

        self._write_identity(server_id)

        logger.debug("Requesting DB setup")

        # Flag this up to be done, but don't wait for it
        _threadsafe_call(self.setDatabase, database())

    @asyncio.coroutine
    def _fetch_definition(self, guid, allow_many=False, resync=False):
        """Retrieve a definition, if not from the current set, from persistent storage.
           If resync is True then update the DB if it is inconsistent; set to False
           by default to avoid unnecessary DB hits.

        """
        guid = guid.upper()

        # We only resync DB if there is a full-length GUID match
        live_current = None

        if guid in self.current:
            if resync:
                live_current = self.current[guid]
            else:
                return guid, self.current[guid]

        guids = []
        if len(guid) < 32:
            guids = {k: v for k, v in self.current.items() if k.startswith(guid)}
            if len(guids) > 1:
                if not allow_many:
                    raise RuntimeError("More than one matching GUID")

        fut = asyncio.Future()

        _threadsafe_call(lambda: fut.set_result(self._db.retrieve(guid)))

        definition = yield from fut

        if len(guid) < 32:
            definition.update(guids)

            if len(definition) > 1:
                if allow_many:
                    return definition
                else:
                    raise RuntimeError("More than one matching GUID")
            elif not definition:
                return guid, False

            short_guid = guid
            guid, current = definition.popitem()
            logger.info("Matched {short_guid} to {guid}".format(short_guid=short_guid, guid=guid))

            if guid not in self.current:
                self.current[guid] = current
        elif definition:
            if live_current:
                self._resync(live_current, definition)
            else:
                self.current[guid] = definition
        else:
            return guid, False

        return guid, self.current[guid]

    @asyncio.coroutine
    def _resync(self, live_definition, db_definition):
        """Update the database based on the status of the live entry."""
        live_summary = live_definition.summary()
        db_summary = db_definition.summary()
        if live_summary != db_summary:
            logger.warning("Definitions do not match!\n%s\n%s\n(updating)" % (live_summary, db_summary))
            _threadsafe_call(self.addOrUpdate, live_definition)
            _threadsafe_call(
                self.setStatus,
                live_summary['guid'],
                live_summary['exit_status'],
                live_summary['status']['message'],
                live_summary['status']['percentage'],
                live_summary['status']['timestamp']
            )

    @asyncio.coroutine
    def doSearch(self, guid, limit=None):
        """``com.gosmartsimulation.search``

        Check for matching definitions

        """
        definitions = yield from self._fetch_definition(guid, allow_many=True)
        logging.info('Searching for %s' % guid)

        # If one or zero results are available, they are returned as a GUID/def pair
        if isinstance(definitions, tuple):
            if definitions[1]:
                definitions = {definitions[0]: definitions[1]}
            else:
                logging.info('Found no matches')
                return {}

        definitions = {k: d.summary() for k, d in definitions.items()}

        # Reduce total number of definitions to a manageable level, if requested
        # Note this is an arbitrary selection
        if limit:
            key_subset = list(definitions.keys())[:limit]
            definitions = {k: definitions[k] for k in key_subset}

        logging.info('Found %d matches' % len(definitions))
        return definitions

    @asyncio.coroutine
    def doApi(self):
        """``com.gosmartsimulation.api``

           Find the current API version in use.
           The API version only needs to be bumped when backward-incompatible changes
           occur on either side

        """
        return gssa.config.get_api_version()

    def setDatabase(self, database):
        """Update database backend.

        Mainly for start-up. Mark everything in-progress in the DB as not-in-progress/unfinished.

        """
        self._db = database
        self._db.markAllOld()
        logger.debug("DB set up")

    @asyncio.coroutine
    def doInit(self, guid):
        """``com.gosmartsimulation.init``

        Dummy call for the moment.

        """
        return True

    @asyncio.coroutine
    def doClean(self, guid):
        """``com.gosmartsimulation.clean``

        Remove anything in simulation working directory, for instance

        """
        guid, current = yield from self._fetch_definition(guid, resync=True)
        if not current:
            logger.warning("Definition %s not found" % guid)
            return False

        result = yield from current.clean()

        return result

    @asyncio.coroutine
    def doStart(self, guid):
        """``com.gosmartsimulation.start``

        Execute the simulation in a coro.

        """

        guid, current = yield from self._fetch_definition(guid)
        if not current:
            logger.warning("Definition %s not found" % guid)
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

        task.add_done_callback(lambda f: _threadsafe_call(self._db.updateValidation, guid, f.result()))

        return True

    @asyncio.coroutine
    def _handle_simulation_done(self, fut, guid):
        # This should be the return value of the simulate call
        outcome = fut.result()
        logger.info("Simulation exited [%s]" % guid)

        guid, current = yield from self._fetch_definition(guid)
        if not current:
            logger.warning("Definition %s not found" % guid)
            return False

        if outcome is True:
            yield from self.eventComplete(guid)
        elif isinstance(outcome, gssa.error.ErrorMessage):
            logger.warning("Failed simulation in %s" % current.get_dir())
            yield from self.eventFail(guid, outcome)
        elif outcome is None:
            # None indicates we've dealt with failure (errored) already
            pass
        else:
            # We know this did not succeed, but not why it failed
            code = gssa.error.Error.E_UNKNOWN
            error_message = "Unknown error occurred"
            logger.warning("Failed simulation in %s" % current.get_dir())
            yield from self.eventFail(guid, gssa.error.makeError(code, error_message))

        logger.info("Finished simulation")

    @asyncio.coroutine
    def doUpdateFiles(self, guid, files):
        """``com.gosmartsimulation.update_files``

        Add the passed files to the
        simulation's reference dictionary of required input files (available to be
        requested later)

        """
        guid, current = yield from self._fetch_definition(guid)
        if not current or not isinstance(files, dict):
            return False

        logger.debug("Update Files")
        for local, remote in files.items():
            logger.debug("remote" + remote)
            logger.debug("Local" + local)
        current.update_files(files)

        return True

    @asyncio.coroutine
    def doLogs(self, guid, only=None):
        """``com.gosmartsimulation.logs``

        Retrieve the container logs for a simulation.

        """
        guid, current = yield from self._fetch_definition(guid)
        if not current:
            logger.warning("Simulation [%s] not found" % guid)
            return False

        try:
            result = yield from current.logs(only)
        except Exception as e:
            logger.exception("Problem retrieving simulation container logs")
            raise e

        return result

    @asyncio.coroutine
    def doCancel(self, guid):
        """``com.gosmartsimulation.cancel``

        Prematurely stop the running simulation.

        """
        guid, current = yield from self._fetch_definition(guid)
        if not current:
            logger.warning("Simulation [%s] not found" % guid)
            return False

        try:
            result = yield from current.cancel()
        except Exception as e:
            logger.exception("Problem cancelling simulation")
            raise e

        return result

    @asyncio.coroutine
    def doRequestFiles(self, guid, files):
        """``com.gosmartsimulation.request_files``

        Push the requested output files
        through the transferrer and return the list that was sent.

        """
        logger.info("Files requested for [%s]" % guid)

        result = yield from self._request_files(guid, files)
        return result

    @asyncio.coroutine
    def doRequestResults(self, guid, target):
        """``com.gosmartsimulation.request_results``

        Push a bundle of output
        files through the transferrer. If target is None, assume gateway is
        running a temporary HTTP on default client port

        FIXME: this should be made asynchronous!

        """
        guid, current = yield from self._fetch_definition(guid)
        if not current:
            logger.warning("Simulation [%s] not found" % guid)
            return {}

        logger.info("Result bundle requested for [%s]" % guid)

        result_archive = current.gather_results()
        transferrer = None

        if target is None:
            gateway = gssa.utils.get_default_gateway()
            target = "http://%s:%d/receive" % (
                gateway,
                _default_client_port
            )
            transferrer = gssa.transferrer.transferrer_register['http']()

        files = {result_archive: target}

        result = yield from self._request_files(guid, files, transferrer=transferrer)
        return result

    @asyncio.coroutine
    def doRequestDiagnostic(self, guid, target):
        """``com.gosmartsimulation.request_diagnostic``

        Push a bundle of diagnostic
        files through the transferrer. If target is None, assume gateway is
        running a temporary HTTP on default client port

        FIXME: this should be made asynchronous!

        """
        guid, current = yield from self._fetch_definition(guid)
        if not current:
            logger.warning("Simulation [%s] not found" % guid)
            return {}

        logger.info("Diagnostic bundle requested for [%s]" % guid)

        diagnostic_archive = current.gather_diagnostic()
        transferrer = None

        if target is None:
            gateway = gssa.utils.get_default_gateway()
            target = "http://%s:%d/receive" % (
                gateway,
                _default_client_port
            )
            transferrer = gssa.transferrer.transferrer_register['http']()

        files = {diagnostic_archive: target}

        result = yield from self._request_files(guid, files, transferrer=transferrer)
        return result

    @asyncio.coroutine
    def _request_files(self, guid, files, transferrer=None):
        """Helper routine as several endpoints involve returning file requests."""
        guid, current = yield from self._fetch_definition(guid)
        if not current or not isinstance(files, dict):
            return {}

        try:
            uploaded_files = current.push_files(files, transferrer=transferrer)
        except Exception:
            logger.exception("Problem pushing files")
            return {}

        logger.info("Files sent")

        return uploaded_files

    @asyncio.coroutine
    def doCompare(self, this_xml, that_xml):
        """``com.gosmartsimulation.compare``

        Check whether two GSSA-XML files match
        and, if not, what their differences are.

        """
        comparator = gssa.comparator.Comparator(this_xml, that_xml)
        return comparator.diff()

    @asyncio.coroutine
    def doUpdateSettingsXml(self, guid, xml):
        """``com.gosmartsimulation.update_settings_xml``

        Set the GSSA-XML for a given
        simulation

        """
        guid = guid.upper()

        try:
            # Create a working directory for the simulation (this is needed even
            # if the tool runs elsewhere, as in the Docker case)
            tmpdir = tempfile.mkdtemp(prefix='%s/' % self._simdata_path)
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
                update_status_callback=lambda p, m: asyncio.async(self.updateStatus(guid, p, m))
            )

            # Announce that XML has been uploaded
            # TODO: why announce this? Surely the response is sufficient?
            self.publish(u'com.gosmartsimulation.announce', self.server_id, guid, [0, 'XML uploaded'], tmpdir, time.time())
        except Exception as e:
            logger.exception("Problem updating settings XML")
            raise e

        logger.debug("XML set")

        return True

    @asyncio.coroutine
    def doSimulate(self, guid):
        """Start the simulation

        This occurs in a separately scheduled coro from the
        RPC call so it will almost certainly have returned by time we do.
        This does not have an API endpoint as :py:func:`~gssa.server.doStart`
        is responsible for launching it asynchronously.

        """
        guid, current = yield from self._fetch_definition(guid)
        if not current:
            yield from self.eventFail(guid, gssa.error.makeError(gssa.error.Error.E_CLIENT, "Not fully prepared before launching - no current simulation set"))
            success = None

        logger.debug("Running simulation in %s" % current.get_dir())

        # Inform the user that we got this far
        yield from self.updateStatus(guid, 0, "Starting simulation...")
        # Start the socket server before simulating
        yield from current.init_percentage_socket_server()

        # Start the simulation. If we get an error, then blame the server side -
        # it should have returned False
        # FIXME: so how exactly does any non E_SERVER message get sent back?
        try:
            success = yield from current.simulate()
        except Exception as e:
            logger.exception("Simulation failed! {exc}".format(exc=e))
            yield from self.eventFail(guid, gssa.error.makeError(gssa.error.Error.E_SERVER, "[%s] %s" % (type(e), str(e))))
            success = None

        return success

    @asyncio.coroutine
    def doFinalize(self, guid, client_directory_prefix):
        """``com.gosmartsimulation.finalize``

        Do any remaining preparation before the
        simulation can start.

        """
        logger.debug("Converting the Xml")
        guid, current = yield from self._fetch_definition(guid)
        if not current:
            logger.warning("Simulation [%s] not found" % guid)
            return False

        current.set_remote_dir(client_directory_prefix)

        # Make sure the simulation is in the DB
        self._db.addOrUpdate(current)

        # Execute the finalization
        result = current.finalize()

        return result

    @asyncio.coroutine
    def doProperties(self, guid):
        """``com.gosmartsimulation.properties``

        Return important server-side simulation
        properties.

        """
        result = yield from self.getProperties(guid)
        return result

    @asyncio.coroutine
    def getProperties(self, guid):
        """Server-specific properties for this simulation

        At present, just working directory location.

        """

        guid, current = yield from self._fetch_definition(guid)
        if not current:
            raise RuntimeError("Simulation not found: %s" % guid)

        return {"location": current.get_dir()}

    @asyncio.coroutine
    def eventComplete(self, guid):
        """Called when simulation completes

        Publishes a completion event: ``com.gosmartsimulation.complete``

        """
        logger.debug("Completed [%s]" % guid)
        guid, current = yield from self._fetch_definition(guid)
        if not current:
            logger.warning("Tried to send simulation-specific completion event with no current simulation definition")

        current.set_exit_status(True)

        # Record the finishing time, as we see it
        timestamp = time.time()

        logger.debug(timestamp)
        try:
            # Tell the database we have finished
            _threadsafe_call(self.setStatus, guid, "SUCCESS", "Success", "100", timestamp)
            # Run validation (if req)
            validation = None
            # validation = yield from self.current[guid].validation()
            # if validation:
            #    loop.call_soon_threadsafe(lambda: self._db.updateValidation(guid, validation))
        except:
            validation = None
            logger.exception("Problem with completion/validation")

        logger.info('Success [%s]' % guid)

        # Notify any subscribers
        self.publish(u'com.gosmartsimulation.complete', guid, gssa.error.makeError('SUCCESS', 'Success'), current.get_dir(), timestamp, validation)

    @asyncio.coroutine
    def eventFail(self, guid, message):
        """Called when simulation fails

        Publishes a failure event: ``com.gosmartsimulation.failed``

        """
        guid, current = yield from self._fetch_definition(guid)
        if not current:
            logger.warning("Tried to send simulation-specific failure event with no current simulation definition")

        current.set_exit_status(False, message)

        # Record the failure time as we see it
        timestamp = time.time()

        try:
            # Update the database
            _threadsafe_call(self.setStatus, guid, message["code"], message["message"], None, timestamp)
        except:
            logger.exception("Problem saving failure status")

        logger.warning('Failure [%s]: %s' % (guid, repr(message)))

        # Notify any subscribers
        self.publish(u'com.gosmartsimulation.fail', guid, message, current.get_dir(), timestamp, None)

    @asyncio.coroutine
    def doRetrieveStatus(self, guid, allow_resync=True):
        """``com.gosmartsimulation.retrieve_status``

        Get the latest status for a
        simulation. allow_resync permits the server to update the DB if it finds
        an inconsistency.

        """
        # Get this from the DB, not current, as the DB should give a consistent
        # answer even after restart (unless marked unfinished)
        if allow_resync:
            guid, simulation = yield from self._fetch_definition(guid, resync=True)
        else:
            simulation = self._db.retrieve(guid)

        if not simulation:
            logger.error('Simulation not found')
            return None

        try:
            summary = simulation.summary()

            exit_code = summary['exit_status']

            if exit_code is None:
                if summary['guid'] in self.current:
                    exit_code = ('IN_PROGRESS', '...')
                else:
                    exit_code = ('E_UNKNOWN', '...')

            # NB: makeError can return SUCCESS or IN_PROGRESS
            status = gssa.error.makeError(exit_code[0], summary['status']['message'])
            percentage = summary['status']['percentage']
            timestamp = summary['status']['timestamp']

            # This format matches the fail/status/complete events
            return {
                "server_id": self.server_id,
                "summary_id": summary['guid'],
                "exit_code": exit_code,
                "status": (percentage, status, timestamp),
                "directory": summary['directory']
            }
        except Exception as e:
            logging.exception('Could not show status')
            raise e

    def onRequestAnnounce(self):
        """``com.gosmartsimulation.request_announce``

        Release a status report on each
        simulation in the database

        TODO: this gets unwieldy, perhaps it should have an earliest simulation
        timestamp argument?

        """

        # Go through /every/ simulation
        simulations = self._db.all()
        for simulation in simulations:
            exit_code = simulation['exit_code']

            # If it hasn't exited, it should be running...
            if exit_code is None:
                if simulation['guid'] in self.current:
                    exit_code = 'IN_PROGRESS'
                else:
                    exit_code = 'E_UNKNOWN'

            status = gssa.error.makeError(exit_code, simulation['status'])
            percentage = simulation['percentage']

            # Tell the world
            self.publish(u'com.gosmartsimulation.announce', self.server_id, simulation['guid'], (percentage, status), simulation['directory'], simulation['timestamp'], simulation['validation'])
            logger.debug("Announced: %s %s %r" % (simulation['guid'], simulation['directory'], simulation['validation'] is not None))

        # Follow up with an identify event
        self.onRequestIdentify()

    def setStatus(self, id, key, message, percentage, timestamp):
        """Record a status change in the database and on the filesystem.

        Note that,
        for both those reasons, this could be slow and so should always be run
        with call_soon_threadsafe

        FIXME: we need some sort of rate limiting here, or producer-consumer
        pattern with ability to skip once getting behind

        """
        # Write this message to the database
        self._db.setStatus(id, key, message, percentage, timestamp)

        try:
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
        except OSError:
            # This may because the simulation was from a previous server process
            logger.warning("Tried to update simulation status on filesystem but simulation gone.")

    @asyncio.coroutine
    def updateStatus(self, guid, percentage, message):
        """Update the status.

        Sets up a callback for asyncio to update database.

        """
        progress = "%.2lf" % percentage if percentage else '##'

        guid, current = yield from self._fetch_definition(guid)
        if current:
            directory = current.get_dir()
        else:
            logger.warning("Simulation [%s] not found" % guid)

        if current.get_exit_status():
            logger.warning("Got status message [%s%%:%s] for [%s], which has already exited." % (progress, message, guid))
            return

        timestamp = time.time()

        # Write out to the command line for debug
        # TODO: switch to `logger` and `vigilant`
        logger.debug("%s [%r] ---- %s%%: %s" % (guid, timestamp, progress, message))

        try:
            # Call the setStatus method asynchronously
            _threadsafe_call(self.setStatus, guid, 'IN_PROGRESS', message, percentage, timestamp)
        except:
            logger.exception("Problem saving status")

        directory = None
        # Publish a status update for the WAMP clients to see
        self.publish('com.gosmartsimulation.status', guid, (percentage, gssa.error.makeError('IN_PROGRESS', message)), directory, timestamp, None)

    def onRequestIdentify(self):
        """``com.gosmartsimulation.request_identify``

        Publish basic server information.

        $$ score = #cores - #active_simulations $$

        This gives an availability estimate, the higher the better

        """
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
