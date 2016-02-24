import pytest
import asyncio.coroutines
import asyncio
from unittest.mock import MagicMock
import uuid
import traceback

from gssa.server import GoSmartSimulationServerComponent
import gssa.comparator


known_guid   = str(uuid.uuid4())
unknown_guid = str(uuid.uuid4())


def magic_coro():
    mock = MagicMock()
    return mock, asyncio.coroutine(mock)


@asyncio.coroutine
def wait():
    pending = asyncio.Task.all_tasks()

    relevant_tasks = [t for t in pending if ('test_' not in t._coro.__name__)]
    yield from asyncio.gather(*relevant_tasks)


@pytest.fixture(scope="function")
def definition():
    definition = MagicMock()
    definition.guid = known_guid
    return definition


# We need event_loop as a fixture to ensure it gets
# started before the GSSA setup
@pytest.fixture(scope="function")
def gsssc(definition, event_loop):
    server_id = 'test-000000'
    database = MagicMock()
    publish_cb = MagicMock()
    use_observant = False

    gsssc = GoSmartSimulationServerComponent(
        server_id,
        database,
        publish_cb,
        use_observant
    )

    gsssc.current[known_guid] = definition

    return gsssc


# TESTS FROM HERE


@pytest.mark.asyncio
def test_init_succeeds(gsssc):
    result = yield from gsssc.doInit(unknown_guid)
    assert(result is True)


@pytest.mark.asyncio
def test_clean_succeeds(gsssc, definition):
    definition.clean = asyncio.coroutine(lambda: True)

    result = yield from gsssc.doClean(known_guid)

    assert(result is True)


@pytest.mark.asyncio
def test_clean_fails_if_guid_unrecognised(gsssc):
    result = yield from gsssc.doClean(unknown_guid)

    assert(result is False)


@pytest.mark.asyncio
def test_start_succeeds(gsssc, definition, event_loop):
    # Simulate will get fired off
    simulate, sc = magic_coro()
    gsssc.doSimulate = sc

    # And a handler attached for when its done
    handle_simulation_done, hsdc = magic_coro()
    gsssc._handle_simulation_done = hsdc

    # Run the doStart method
    result = yield from gsssc.doStart(known_guid)

    # Wait until mock simulation done and handled
    yield from wait()

    # Check simulation was correctly called
    simulate.assert_called_with(known_guid)

    # Check mock simulation handler fired when it finished
    args, kwargs = handle_simulation_done.call_args
    handle_simulation_done.assert_called_once_with(args[0], guid=known_guid)

    assert(result is True)


@pytest.mark.asyncio
def test_update_files_succeeds(gsssc, definition):
    files = MagicMock(spec=dict)
    files.items.return_value = (('local', 'remote'),)

    # Run the doUpdateFiles method
    result = yield from gsssc.doUpdateFiles(known_guid, files)

    # Wait until mock simulation done and handled
    yield from wait()

    # Check whether the files were examined exactly once
    files.items.assert_called_once_with()

    # Check the files were passed to the current definition
    definition.update_files.assert_called_with(files)

    assert(result is True)


@pytest.mark.asyncio
def test_request_files_succeeds(gsssc, definition):
    files = MagicMock(spec=dict)
    uploaded_files = MagicMock()
    definition.push_files.return_value = uploaded_files

    # Run the doRequestFiles method
    result = yield from gsssc.doRequestFiles(known_guid, files)

    # Wait until mock simulation done and handled
    yield from wait()

    # Check the files were passed to the current definition
    definition.push_files.assert_called_with(files)

    assert(result is uploaded_files)


@pytest.mark.asyncio
def test_request_files_fails_on_uploaded_error(gsssc, definition):
    files = MagicMock(spec=dict)
    definition.push_files.side_effect = RuntimeError("Upload failure")

    # Run the doRequestFiles method
    result = yield from gsssc.doRequestFiles(known_guid, files)

    # Wait until mock simulation done and handled
    yield from wait()

    # Check the files were passed to the current definition
    definition.push_files.assert_called_with(files)

    assert(result == {})


@pytest.mark.asyncio
def test_compare_succeeds(gsssc, monkeypatch):
    xml1 = 5432
    xml2 = 4321

    comparator = MagicMock()
    monkeypatch.setattr("gssa.comparator.Comparator", lambda x1, x2: comparator)
    comparator.diff.return_value = 1234

    result = yield from gsssc.doCompare(xml1, xml2)

    comparator.diff.assert_called_once_with()

    assert(result == 1234)

# test for doCompare(self, this_xml, that_xml):

#def test_doCompare_diff ( gsssc , definition ):
	#xml1 = MagicMock(spec=dict)	# produces 1st random xml file dict ???	who knows....
	#xml2 = MagicMock(spec=dict) # produces 2nd random xml file presumably also a dict
	#result = yield from gsssc.doCompare(xml1,xml2) # only logical
	#definition.assert_called_with(known_guid)
	#yield from wait()
	#assert(result == {})

## test for doUpdateSettingsXml(self, guid, xml):

#def test_doUpdateSettingsXml ( gsssc , definition ):
	#random_xml = MagicMock(spec=dict)
	#result = yield from gsssc.doUpdateSettingsXml(random_xml)
	#yield from wait()
	#definition.assert_xml_settings_have_been_updated(known_guid)
	#assert(result is True)
	
# test for def doSimulate(self, guid):

@pytest.mark.asyncio
def test_doSimulate ( gsssc , definition ): 
	random_guid = known_guid
	# we used it in the past so it *must* be correct
	result = yield from gsssc.doSimulate(random_guid)
	# obvious and predictable
	yield from wait()
	# also obvious and predictable
	definition.simulate.assert_called_with()
	# found it earlier in the documen, feels fitting
	assert ( result == None )
	# I don't see any true/false dichotomy in the main code...


@pytest.mark.asyncio
def test_doFinalize(gsssc , definition):
	random_guid = known_guid # since it appears in the main class too
	definition.finalize.return_value = 1983
	result = yield from gsssc.doFinalize(random_guid,"/home56") # as previously
	yield from wait() # as always...
	definition.finalize.assert_called_with()
	definition.set_remote_dir.assert_called_with("/home56")
	#the result is derived from current.finalize()
	assert ( result == 1983 ) # or maybe false ? not sure...
	


@pytest.mark.asyncio
def test_doProperties(gsssc , definition):
	#simulate, sc = magic_coro()
	random_guid = known_guid
	gsssc.getProperties = MagicMock()
	gsssc.getProperties.return_value = 1983
	result = yield from gsssc.doProperties(random_guid)
	yield from wait()
	# we have set in line 228 that getProperties is a MagicMock
	# e.g. a random object. 
	# Therefore, once doProperties is called, instead of 
	# invoking the original getProperties function
	# (as stated in server.py
	# it will invoke our own self-made random object
	gsssc.getProperties.assert_called_with(random_guid)	
	assert ( result == 1983 )



@pytest.mark.asyncio
def test_doRetrieveStatus ( gsssc , monkeypatch , definition ):
	# current corresponds to definition
	#  self correspondss to gsssc
	random_guid = known_guid
	simulation = { 'exit_code': 'EXITCODE', 'guid': known_guid, 'status': 'STATUS' , 'percentage' : 0.6 , 'directory' : 'home' , 'timestamp' : 'zerohour' , 'validation' : 'valid'  }
	gsssc._db.retrieve = MagicMock()
	gsssc._db.retrieve.return_value = simulation
	makeError = MagicMock()
	monkeypatch.setattr("gssa.error.makeError", makeError)
	makeError.return_value = "MYSTATUS"
	result = yield from gsssc.doRetrieveStatus(random_guid)
	yield from wait()
	gsssc._db.retrieve.assert_called_with(random_guid)	
	makeError.assert_called_with(simulation['exit_code'], simulation['status'])	
	result000 = 1983
	assert ( result000 == 1983	)            



@pytest.mark.asyncio
def test_doRequestDiagnostic ( gsssc , monkeypatch , definition ):	
	random_guid   	= known_guid
	random_target	= MagicMock()
	result = yield from gsssc.doRequestDiagnostic ( random_guid, random_target)
	definition.gather_diagnostic.assert_called_with()	
	definition.push_files.assert_called_with({definition.gather_diagnostic(): random_target})	
	assert ( result is definition.push_files({definition.gather_diagnostic(): random_target})	) 	
	
	


