import pytest
import asyncio.coroutines
import asyncio
from unittest.mock import MagicMock
import time
import uuid
import traceback
import pdb

from gssa.server import GoSmartSimulationServerComponent
import gssa.comparator


known_guid   = str(uuid.uuid4()).upper()
unknown_guid = str(uuid.uuid4()).upper()


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
def gsssc(definition, monkeypatch, event_loop):
    server_id = 'test-000000'
    database = MagicMock()
    publish_cb = MagicMock()
    use_observant = False
    ignore_development = True

    mkdir = MagicMock()
    monkeypatch.setattr("os.mkdir", mkdir)
    mkdir.return_value = True
    chdir = MagicMock()
    monkeypatch.setattr("os.chdir", chdir)
    chdir.return_value = True
    
    GoSmartSimulationServerComponent._write_identity = MagicMock()
    
    gsssc = GoSmartSimulationServerComponent(
        server_id,
        database,
        publish_cb,
        ignore_development,
        use_observant
    )

    # In theory, this is redundant but ensures that we are not thinking
    # about the thread callback timing
    gsssc._db = MagicMock()
    fd, fd_coro = magic_coro()
    gsssc._fetch_definition = fd_coro
    fd.side_effect = lambda g: (g, (definition if g == known_guid else False))
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
    definition.push_files.assert_called_with(files, transferrer=None)

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
    definition.push_files.assert_called_with(files, transferrer=None)

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
    #xml1 = MagicMock(spec=dict)    # produces 1st random xml file dict ??? who knows....
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
    gsssc._db = MagicMock()
    result = yield from gsssc.doFinalize(random_guid,"/home56") # as previously
    yield from wait() # as always...
    definition.finalize.assert_called_with()
    definition.set_remote_dir.assert_called_with("/home56")
    gsssc._db.addOrUpdate.assert_called_with(definition)
    #the result is derived from current.finalize()
    assert ( result == 1983 ) # or maybe false ? not sure...
    


@pytest.mark.asyncio
def test_doProperties(gsssc , definition):
    #simulate, sc = magic_coro()
    random_guid = known_guid
    getProperties, gsssc.getProperties = magic_coro()
    getProperties.return_value = 1983
    result = yield from gsssc.doProperties(random_guid)
    yield from wait()
    # we have set in line 228 that getProperties is a MagicMock
    # e.g. a random object. 
    # Therefore, once doProperties is called, instead of 
    # invoking the original getProperties function
    # (as stated in server.py
    # it will invoke our own self-made random object
    getProperties.assert_called_with(random_guid) 
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
    assert ( result000 == 1983  )            



@pytest.mark.asyncio
def test_doRequestDiagnostic ( gsssc , monkeypatch , definition ):  
    random_guid     = known_guid
    random_target   = MagicMock()
    result = yield from gsssc.doRequestDiagnostic ( random_guid, random_target)
    definition.gather_diagnostic.assert_called_with()   
    definition.push_files.assert_called_with({definition.gather_diagnostic(): random_target}, transferrer=None)   
    assert ( result is definition.push_files({definition.gather_diagnostic(): random_target}, transferrer=None)   )   
    
    

@pytest.mark.asyncio
def test_handle_simulation_done ( gsssc , monkeypatch , definition ):
    random_guid = known_guid
    random_fut  = MagicMock()
    #gsssc.guid  = random_guid
    #gsssc.fut  = random_fut
    gsssc.success = True
    gsssc.eventComplete = MagicMock()
    yield from gsssc._handle_simulation_done(random_fut , random_guid)
    gsssc.eventComplete.assert_called_with(random_guid)
    result000 = 1983
    assert ( result000 == 1983  )           
    


@pytest.mark.asyncio
def test_eventComplete ( gsssc , monkeypatch , definition ):
    random_guid = known_guid
    fetch_definition, fetch_definition_coro = magic_coro()
    gsssc._fetch_definition = fetch_definition_coro
    fetch_definition.return_value = random_guid, definition
    
    monkeypatch.setattr("time.time" , lambda: 1983 )
    threadsafe_call = MagicMock()
    monkeypatch.setattr("gssa.server._threadsafe_call", threadsafe_call )               
    gsssc.setStatus = MagicMock()
    yield from gsssc.eventComplete(random_guid) 
    yield from wait()
    #gsssc.setStatus.assert_called_with()
    #gsssc.assert_called_with(random_guid)
    #panos2.call_soon_threadsafe.assert_called_with ( 123456 ) 
    threadsafe_call.assert_called_with ( gsssc.setStatus, random_guid, "SUCCESS", "Success", "100", 1983 ) 
    result000 = 1983
    assert ( result000 == 1983  )  


    
@pytest.mark.asyncio
def test_updateStatus ( gsssc , monkeypatch , definition ):
    random_guid = known_guid
    random_message = MagicMock()
    random_percentage = 0.3 
    gsssc.setStatus = MagicMock()
    threadsafe_call = MagicMock()
    monkeypatch.setattr("gssa.server._threadsafe_call", threadsafe_call )    
    monkeypatch.setattr("time.time" , lambda: 1983 )    
    yield from gsssc.updateStatus ( random_guid , 0.3 , random_message ) 
    yield from wait()    
    threadsafe_call.assert_called_with ( gsssc.setStatus , random_guid , 'IN_PROGRESS' , random_message , 0.3 , 1983 )
    result000 = 1983
    assert ( result000 == 1983  )      



@pytest.mark.asyncio       
def test_onRequestIdentify( gsssc , monkeypatch , definition ):
    gsssc._db.active_count = MagicMock()
    gsssc._db.active_count.return_value = 1983
    gsssc.publish = MagicMock()
    monkeypatch.setattr( 'socket.gethostname' , lambda: 'panos3' )
    monkeypatch.setattr( 'multiprocessing.cpu_count' , lambda: 983 )
    random_name = MagicMock()
    gsssc.onRequestIdentify()       ########################
    yield from wait()
    gsssc._db.active_count.assert_called_with()    
    gsssc.publish.assert_called_with( u'com.gosmartsimulation.identify', gsssc.server_id , 'panos3' , -1000 )    
    result000 = 1983
    assert ( result000 == 1983  )      



@pytest.mark.asyncio       
def test_onRequestAnnounce ( gsssc , monkeypatch , definition ):
    random_guid = known_guid
    status1 = MagicMock()
    gsssc.onRequestIdentify = MagicMock()
    status1.return_value = 'unstable'
    gsssc._db.all = MagicMock()
    simulations = [ {   'exit_code'     : 'panos133'    , 
                        'status'        : 'panos134'    , 
                        'percentage'    :  0.3          , 
                        'guid'          :  random_guid  ,
                        'directory'     : 'home'        ,
                        'timestamp'     : 'zerohour'    ,
                        'validation'    : 'invalid'     
                        }  ]  
    gsssc._db.all.return_value = simulations
    monkeypatch.setattr( 'gssa.error.makeError' , status1 )
    gsssc.publish = MagicMock()
    random_serverid = MagicMock()
    gsssc.server_id = 123
    gsssc.onRequestAnnounce()
    yield from wait()
    gsssc.publish.assert_called_with( u'com.gosmartsimulation.announce' , 123 , random_guid , ( 0.3 , 'unstable' ) , 'home' ,  'zerohour'  , 'invalid' )
    result000 = 1983
    assert ( result000 == 1983  )   
    


@pytest.mark.asyncio     
def test_getProperties(gsssc , monkeypatch , definition):
    random_guid = known_guid
    random_definition   , random_coroutine = magic_coro()
    gsssc._fetch_definition = random_coroutine
    random_definition.return_value = random_guid , definition
    definition.get_dir.return_value =  1983 
    result = yield from gsssc.getProperties(random_guid) 
    yield from wait()
    random_definition.assert_called_with(random_guid)
    assert ( result == { "location" : 1983 } ) 



@pytest.mark.asyncio     
def test__request_files(gsssc , monkeypatch , definition):
    random_guid = known_guid
    random_files         = MagicMock(spec=dict)
    random_definition   , random_coroutine2 = magic_coro()
    # I only need magic_coro() if I am yielding from it
    definition.push_files   = random_coroutine2
    gsssc._fetch_definition = random_coroutine2
    random_files.return_value = 1945
    random_definition.return_value = random_guid , definition
    definition.push_files = MagicMock()
    definition.push_files.return_value = 'panos83'
    result = yield from gsssc._request_files( random_guid , random_files , transferrer=None )
    yield from wait()
    random_definition.assert_called_with(random_guid)
    definition.push_files.assert_called_with( random_files ,  transferrer=None)
    assert ( result ==  'panos83' ) 



@pytest.mark.asyncio     
def test_doRequestResults ( gsssc , monkeypatch , definition ) :
    random_guid = known_guid
    random_target = 1983
    random_definition , random_coroutine = magic_coro()
    # magic coro returns two things
    # 1. A magic Mock 
    # 2. A coroutine using it
    gsssc._fetch_definition = random_coroutine
    random_definition.return_value = random_guid , definition
    # we have set guid as random_guid (known_guid)
    # we already said current ~ definition 
    ############################################
    random_files , random_coroutine2 = magic_coro()
    gsssc._request_files = random_coroutine2
    random_files.return_value = 1945
    ################################################    
    definition.gather_results = MagicMock()
    definition.gather_results.return_value = 'panos13'
    result = yield from gsssc.doRequestResults ( random_guid , random_target )
    random_definition.assert_called_with(random_guid)    
    definition.gather_results.assert_called_with()
    random_files.assert_called_with ( random_guid , {'panos13': 1983} , transferrer=None )
    yield from wait()
    assert ( result == 1945 )



def test_setDatabase ( gsssc , monkeypatch , definition ) :
    random_database = MagicMock()
    gsssc.setDatabase ( random_database )
    random_database.markAllOld.assert_called_with()
    


@pytest.mark.asyncio     
def test_doSearch ( gsssc , monkeypatch , definition ) :
    random_guid = known_guid
    random_definitions , random_coroutine = magic_coro()
    gsssc._fetch_definition = random_coroutine
    random_definitions.return_value = random_guid , definition
    # random_definitions[0] = random_guid
    # random_definitions[1] = definition
    result = yield from gsssc.doSearch ( random_guid )
    yield from wait()
    random_definitions.assert_called_with( random_guid , allow_many=True )
    assert ( result == { random_guid : definition.summary() }  )
    
# TypeError: A Future or coroutine is required
# When I get that error check if there is any yield from

    
 
def test_setStatus ( gsssc , monkeypatch , definition ) :
    random_guid     = known_guid
    random_id       = known_guid
    random_message  = MagicMock()
    random_time     = MagicMock()
    random_key      = MagicMock()
    random_message.strip.return_value = 'panos123'
    random_status   , random_coroutine = magic_coro()
    gsssc.setStatus ( random_id , random_key, random_message, 0.3, random_time )
    gsssc._db.setStatus.assert_called_with( random_id , random_key , random_message , 0.3 , random_time )
        


@pytest.mark.asyncio     
def test_eventFail ( gsssc , monkeypatch , definition ) :
    random_guid     = known_guid
    random_message  = MagicMock()
    random_current , random_coroutine = magic_coro()
    gsssc._fetch_definition = random_coroutine
    random_current.return_value = random_guid , definition
    monkeypatch.setattr("time.time" , lambda: 1983 )
    yield from gsssc.eventFail ( random_guid , random_message )
    yield from wait()
    random_current.assert_called_with ( random_guid )
    # is event fail a mock ???
