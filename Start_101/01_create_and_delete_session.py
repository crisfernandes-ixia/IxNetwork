"""
01_create_and_delete_session.py
================================
Lesson 1 - The smallest useful IxNetwork script.

What you learn
  * How RestPy talks to the IxNetwork API server (Windows GUI, Linux API server
    or Web Edition - the code is the same).
  * How to create a session with a UNIQUE, identifiable name.
  * How to ALWAYS delete the session when the script ends (even on errors),
    so you never leak licenses.
  * How to navigate the object tree: ixnetwork -> Vport / Topology / Traffic ...

Run
  python 01_create_and_delete_session.py
"""
import traceback

from ixnetwork_restpy import SessionAssistant

import lab_config as cfg
from common import unique_session_name

session = None
try:
    # 1. Create (or connect to) a session ------------------------------------
    # SessionAssistant does all the plumbing: finds the REST port, logs in,
    # creates the session (Linux/Web Edition) and returns helper objects.
    session = SessionAssistant(
        IpAddress=cfg.API_SERVER,
        RestPort=cfg.REST_PORT,
        UserName=cfg.USERNAME,
        Password=cfg.PASSWORD,
        SessionName=unique_session_name('lesson01'),
        ClearConfig=True,          # start with an empty config
        LogLevel=cfg.LOG_LEVEL,    # try 'request' to see every REST call
    )

    # 2. The three objects you will use all the time -------------------------
    test_platform = session.TestPlatform   # the API server itself
    ixn_session = session.Session          # this session (id, name, state)
    ixnetwork = session.Ixnetwork          # ROOT of the IxNetwork object tree

    print('API server platform : {}'.format(test_platform.Platform))
    print('Session id / name   : {} / {}'.format(ixn_session.Id, ixn_session.Name))
    print('IxNetwork build     : {}'.format(ixnetwork.Globals.BuildNumber))

    # 3. Explore the tree - every node supports find(), add(), update(), remove()
    print('Virtual ports       : {}'.format(len(ixnetwork.Vport.find())))
    print('Topologies          : {}'.format(len(ixnetwork.Topology.find())))
    print('Traffic items       : {}'.format(len(ixnetwork.Traffic.TrafficItem.find())))

    # ixnetwork.info() writes to the RestPy log AND the IxNetwork event log.
    ixnetwork.info('Hello from Start_101 lesson 1')

except Exception:
    print(traceback.format_exc())

finally:
    # 4. Clean up -----------------------------------------------------------
    # Linux API server / Web Edition: delete the session -> frees the license.
    # Windows GUI: there is exactly one session and it cannot be deleted.
    if session is not None:
        if session.TestPlatform.Platform != 'windows':
            print('Deleting session {}'.format(session.Session.Name))
            session.Session.remove()
