"""
05_macsec_mka.py
================
Lesson 5 - MACsec with MKA (IEEE 802.1X-2010/2020 MACsec Key Agreement).

In production MACsec the SAK is NOT configured by hand: peers share a
pre-shared Connectivity Association Key (CAK) + name (CKN), run MKA, elect a
Key Server, and the Key Server distributes the SAK. This script emulates an
MKA participant on each test port and sends encrypted traffic once the
secure channel is up.

Stack built on each port (same Ethernet carries both layers):

    Topology -> DeviceGroup -> Ethernet ─┬─ Mka           (control plane: CAK/CKN, key server)
                                         │    └─ CakCache (CAK value + name)
                                         └─ StaticMacsec  (data plane: encrypts traffic with the
                                                           SAK learned from MKA)

What you learn
  * Mka object: key server priority, KDF, CAK/CKN, rekey options
  * Verifying MKA came up (Protocols Summary + MKA views)
  * Encrypted traffic over the MKA-derived SAK

Run
  python 05_macsec_mka.py
"""
import lab_config as cfg
from common import (check_traffic_loss, connect_ports, describe, ixnetwork_session, list_views,
                    run_traffic, start_protocols_and_wait, stat_view_to_csv,
                    verify_protocol_sessions)

# ----------------------------- test parameters --------------------------------
PORT_MACS = ['00:11:01:00:00:01', '00:12:01:00:00:01']
DUT_MACS = None              # DUT interface MACs if the DUT terminates MACsec (see lesson 4)
SOURCE_IPS = ['101.1.1.1', '101.1.2.1']

# CAK: 32 hex chars (128-bit, KDF AES-CMAC-128) or 64 hex chars (256-bit, AES-CMAC-256)
CAK = 'f123456789abcdef0123456789abcdeff123456789abcdef0123456789abcdef'
CKN = 'f123456789abcdef'         # CAK name, hex, must match the DUT
KEY_SERVER_PRIORITY = [10, 20]   # lower value = higher priority -> port 1 becomes key server
                                 # use 255 on both ports to let the DUT be the key server

# Optional periodic rekey (uncomment in the code below)
REKEY_INTERVAL_SEC = 30

FRAME_SIZE = 512
LINE_RATE_PERCENT = 90
FRAMES = 1000000
# --------------------------------------------------------------------------------

with ixnetwork_session('lesson05-macsec-mka') as session:
    ixnetwork = session.Ixnetwork
    vports = connect_ports(session, cfg.PORTS[:2])

    macsec_endpoints = []
    for idx, vport in enumerate(vports):
        topology = ixnetwork.Topology.add(Name='MKA_Topo_{}'.format(idx + 1), Ports=vport)
        dg = topology.DeviceGroup.add(Name='MKA_DG_{}'.format(idx + 1), Multiplier=1)
        eth = dg.Ethernet.add(Name='Eth_{}'.format(idx + 1))
        eth.Mac.Single(PORT_MACS[idx])

        # --- MKA (control plane) ------------------------------------------------------
        mka = eth.Mka.add(Name='MKA_{}'.format(idx + 1))
        mka.CakCount = 1
        mka.KeyServerPriority.Single(KEY_SERVER_PRIORITY[idx])
        cak = mka.CakCache
        if len(CAK) == 32:
            mka.KeyDerivationFunction.Single('aescmac128')
            cak.CakValue128.Single(CAK)
        else:
            mka.KeyDerivationFunction.Single('aescmac256')
            cak.CakValue256.Single(CAK)
        cak.CakName.Single(CKN)

        # Periodic rekey every N seconds (the key server distributes a new SAK):
        # mka.update(RekeyMode='timerBased', RekeyBehaviour='rekeyContinuous',
        #            PeriodicRekeyInterval=REKEY_INTERVAL_SEC)
        # Packet-number based rekey instead:
        # mka.update(RekeyMode='pNBased'); mka.RekeyThresholdPN.Single('0xC0000000')

        # --- MACsec (data plane) --------------------------------------------------------
        smac = eth.StaticMacsec.add(Name='MACsec_{}'.format(idx + 1))
        smac.EncryptedTrafficType = 'statelessL23'
        smac.DutMac.Single(DUT_MACS[idx] if DUT_MACS else PORT_MACS[1 - idx])
        smac.SourceIp.Single(SOURCE_IPS[idx])
        smac.EndStation.Single(True)
        macsec_endpoints.append(smac)

    describe(ixnetwork.Topology.find()[0].DeviceGroup.find().Ethernet.find().Mka.find())

    # --- bring up MKA and verify -----------------------------------------------------------
    start_protocols_and_wait(ixnetwork, settle_seconds=20)
    verify_protocol_sessions(session)           # all MKA sessions Up, none Down
    for view in list_views(session, 'mka'):     # e.g. MKA per port: key server, SAK, AN ...
        stat_view_to_csv(session, view, 'lesson05_{}.csv'.format(view.replace(' ', '_')))

    # --- encrypted traffic ------------------------------------------------------------------
    ti = ixnetwork.Traffic.TrafficItem.add(Name='MKA_Encrypted', TrafficType='ethernetVlan',
                                           BiDirectional=True)
    ti.EndpointSet.add(Sources=macsec_endpoints[0], Destinations=macsec_endpoints[1])
    ce = ti.ConfigElement.find()[0]
    ce.FrameSize.update(Type='fixed', FixedSize=FRAME_SIZE)
    ce.FrameRate.update(Type='percentLineRate', Rate=LINE_RATE_PERCENT)
    ce.TransmissionControl.update(Type='fixedFrameCount', FrameCount=FRAMES)

    run_traffic(ixnetwork)
    passed = check_traffic_loss(session)
    stat_view_to_csv(session, 'Traffic Item Statistics', 'lesson05_traffic_items.csv')
    for view in list_views(session, 'macsec'):
        stat_view_to_csv(session, view, 'lesson05_{}.csv'.format(view.replace(' ', '_')))

    print('\nRESULT: {}'.format('PASS' if passed else 'FAIL'))
