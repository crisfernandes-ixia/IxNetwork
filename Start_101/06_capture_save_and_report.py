"""
06_capture_save_and_report.py
=============================
Lesson 6 - Keep the evidence: packet captures, the config, and the stats.

What you learn
  * Enable data-plane (hardware) and control-plane (software) capture on a port
  * Save the captures on the API server and download them to your PC (.cap -> Wireshark)
  * Save the running configuration (.ixncfg) and download it
  * Export statistic views to CSV

Uses any saved config (e.g. one written by this script, or from the GUI).

Run
  python 06_capture_save_and_report.py configs/my_test.ixncfg
"""
import os
import sys
import time

from ixnetwork_restpy import Files

import lab_config as cfg
from common import (CONFIGS_DIR, RESULTS_DIR, connect_ports, ixnetwork_session,
                    start_protocols_and_wait, stat_view_to_csv)

config_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CONFIGS_DIR, 'sample.ixncfg')
if not os.path.isfile(config_file):
    sys.exit('Config file not found: {}\nUsage: python {} <file.ixncfg>'.format(config_file, sys.argv[0]))

CAPTURE_SECONDS = 15

with ixnetwork_session('lesson06') as session:
    ixnetwork = session.Ixnetwork
    ixnetwork.LoadConfig(Files(config_file, local_file=True))
    vport_names = [vp.Name for vp in ixnetwork.Vport.find()]
    vports = connect_ports(session, cfg.PORTS[:len(vport_names)], names=vport_names)

    # 1. Configure capture on the LAST port (the receiver in most tests) ------------
    rx_port = vports[-1]
    rx_port.RxMode = 'captureAndMeasure'         # capture without losing statistics
    rx_port.Capture.HardwareEnabled = True       # data plane (traffic)
    rx_port.Capture.SoftwareEnabled = True       # control plane (ARP, MKA, BGP ...)

    # 2. Start protocols + traffic, then capture ---------------------------------
    start_protocols_and_wait(ixnetwork)
    if len(ixnetwork.Traffic.TrafficItem.find()):
        for ti in ixnetwork.Traffic.TrafficItem.find():
            ti.Generate()
        ixnetwork.Traffic.Apply()
        ixnetwork.Traffic.StartStatelessTrafficBlocking()   # start traffic BEFORE capture

    ixnetwork.StartCapture()
    time.sleep(CAPTURE_SECONDS)
    ixnetwork.StopCapture()
    if ixnetwork.Traffic.State == 'started':
        ixnetwork.Traffic.StopStatelessTrafficBlocking()
    ixnetwork.info('Captured data={} control={} packets'.format(
        rx_port.Capture.DataPacketCounter, rx_port.Capture.ControlPacketCounter))

    # 3. Save captures on the server, then download them --------------------------
    server_dir = ixnetwork.Globals.PersistencePath   # a writable folder on the API server
    sep = '\\' if session.TestPlatform.Platform == 'windows' else '/'
    capture_dir = server_dir + sep + 'start101_captures'
    for remote in ixnetwork.SaveCaptureFiles(Arg1=capture_dir) or []:
        local = os.path.join(RESULTS_DIR, os.path.basename(remote.replace('\\', '/')))
        session.Session.DownloadFile(remote, local)
        ixnetwork.info('Capture downloaded -> {}'.format(local))

    # 4. Save and download the configuration ---------------------------------------
    cfg_name = 'lesson06_saved.ixncfg'
    ixnetwork.SaveConfig(Files(cfg_name))
    session.Session.DownloadFile(cfg_name, os.path.join(RESULTS_DIR, cfg_name))
    ixnetwork.info('Config downloaded -> {}'.format(os.path.join(RESULTS_DIR, cfg_name)))

    # 5. Statistics -------------------------------------------------------------------
    stat_view_to_csv(session, 'Port Statistics', 'lesson06_ports.csv')
    if len(ixnetwork.Traffic.TrafficItem.find()):
        stat_view_to_csv(session, 'Traffic Item Statistics', 'lesson06_traffic_items.csv')
