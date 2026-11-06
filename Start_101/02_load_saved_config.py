"""
02_load_saved_config.py
=======================
Lesson 2 - Re-use a configuration that was built in the IxNetwork GUI.

This is the fastest path to automation: build and debug the test interactively
in the GUI, File > Save As... <name>.ixncfg, then let a script do the
repetitive part (load, run, collect results).

What you learn
  * Upload + load an .ixncfg from your PC (the API server may be remote).
  * Re-map the config's virtual ports to the physical ports in YOUR lab.
  * Start protocols, verify sessions are up, run traffic, check loss.
  * Export statistic views to CSV.

Run
  python 02_load_saved_config.py configs/my_test.ixncfg
"""
import os
import sys

from ixnetwork_restpy import Files

import lab_config as cfg
from common import (CONFIGS_DIR, check_traffic_loss, connect_ports, ixnetwork_session,
                    run_traffic, start_protocols_and_wait, stat_view_to_csv,
                    verify_protocol_sessions)

config_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CONFIGS_DIR, 'sample.ixncfg')
if not os.path.isfile(config_file):
    sys.exit('Config file not found: {}\nUsage: python {} <file.ixncfg>'.format(config_file, sys.argv[0]))

with ixnetwork_session('lesson02') as session:
    ixnetwork = session.Ixnetwork

    # 1. Load the config ------------------------------------------------------
    # local_file=True -> RestPy uploads the file from this PC to the API server first.
    ixnetwork.info('Loading {}'.format(config_file))
    ixnetwork.LoadConfig(Files(config_file, local_file=True))

    # 2. Re-assign ports --------------------------------------------------------
    # Saved configs remember the chassis/ports they were saved with. Re-map the
    # existing vports (by name) to the ports listed in lab_config.py.
    vport_names = [vp.Name for vp in ixnetwork.Vport.find()]
    ixnetwork.info('Config has {} vports: {}'.format(len(vport_names), vport_names))
    connect_ports(session, cfg.PORTS[:len(vport_names)], names=vport_names)

    # 3. Protocols ----------------------------------------------------------------
    if len(ixnetwork.Topology.find()):
        start_protocols_and_wait(ixnetwork)
        verify_protocol_sessions(session)

    # 4. Traffic --------------------------------------------------------------------
    # The traffic items keep the rate / frame size / duration saved in the GUI.
    # Tip: save them as 'fixed frame count' or 'fixed duration' so run_traffic()
    # knows when the run is over.
    if len(ixnetwork.Traffic.TrafficItem.find()):
        run_traffic(ixnetwork)
        passed = check_traffic_loss(session)
        stat_view_to_csv(session, 'Traffic Item Statistics', 'lesson02_traffic_items.csv')
        stat_view_to_csv(session, 'Port Statistics', 'lesson02_ports.csv')
        print('\nRESULT: {}'.format('PASS' if passed else 'FAIL'))
