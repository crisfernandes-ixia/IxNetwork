"""
04_macsec_static_sak.py
=======================
Lesson 4 - MACsec (IEEE 802.1AE) from scratch with STATIC keys (no MKA).

Static SAK is the simplest way to bring up MACsec: both ends are configured
with the same Secure Association Key, so no key negotiation is needed. Use it
to validate the DUT's data-plane encryption/decryption, line-rate throughput,
latency, PN handling, etc.

Stack built on each port:

    Topology -> DeviceGroup -> Ethernet -> StaticMacsec   (encrypted endpoint)
                                              ├── TxSakPool (key used to encrypt)
                                              └── RxSakPool (key used to decrypt)

What you learn
  * The StaticMacsec object and its most used attributes
  * Configuring Tx/Rx SAK pools
  * Encrypted traffic: the traffic endpoints are the StaticMacsec objects
  * Finding the MACsec statistic views

DUT scenarios (set DUT_MACS accordingly)
  a) DUT terminates MACsec on each link (hop-by-hop, typical switch/TSN case):
     DUT_MACS = MAC addresses of the DUT interfaces facing port 1 and port 2.
     The DUT must be configured with the SAME SAK / cipher on those interfaces.
  b) DUT is transparent (MACsec end-to-end between the two test ports):
     DUT_MACS = None -> each side uses the other test port's MAC.

Run
  python 04_macsec_static_sak.py
"""
import lab_config as cfg
from common import (check_traffic_loss, connect_ports, describe, ixnetwork_session, list_views,
                    run_traffic, stat_view_to_csv)

# ----------------------------- test parameters --------------------------------
PORT_MACS = ['00:11:01:00:00:01', '00:12:01:00:00:01']
DUT_MACS = None        # e.g. ['6c:6c:d3:ac:6a:8b', '6c:6c:d3:ac:6a:8c'] for scenario (a)
SOURCE_IPS = ['101.1.1.1', '101.1.2.1']

# 128-bit SAK = 32 hex chars, 256-bit SAK = 64 hex chars (needs a 256-bit cipher suite)
SAK = 'f123456789caffee0123456789abcdef'

FRAME_SIZES = [64, 512, 1500]  # one run per size; MACsec adds 24-32 bytes on the wire
LINE_RATE_PERCENT = 90         # leave headroom for the SecTAG + ICV overhead
FRAMES_PER_RUN = 100000
# --------------------------------------------------------------------------------

with ixnetwork_session('lesson04-macsec-static') as session:
    ixnetwork = session.Ixnetwork
    vports = connect_ports(session, cfg.PORTS[:2])

    macsec_endpoints = []
    for idx, vport in enumerate(vports):
        topology = ixnetwork.Topology.add(Name='MACsec_Topo_{}'.format(idx + 1), Ports=vport)
        dg = topology.DeviceGroup.add(Name='MACsec_DG_{}'.format(idx + 1), Multiplier=1)
        eth = dg.Ethernet.add(Name='Eth_{}'.format(idx + 1))
        eth.Mac.Single(PORT_MACS[idx])

        # --- the MACsec layer -------------------------------------------------------
        smac = eth.StaticMacsec.add(Name='StaticMACsec_{}'.format(idx + 1))
        smac.EncryptedTrafficType = 'statelessL23'   # L2/L3 traffic (vs 'statefulL47')

        peer_mac = DUT_MACS[idx] if DUT_MACS else PORT_MACS[1 - idx]
        smac.DutMac.Single(peer_mac)               # destination MAC of encrypted frames
        smac.SourceIp.Single(SOURCE_IPS[idx])      # IP header inside the encrypted payload
        smac.EndStation.Single(True)               # TCI ES bit: SCI derived from source MAC
        # Other commonly used knobs (see describe() output below for the full list):
        # smac.IncludeSci.Single(True)             # send explicit SCI in the SecTAG
        # smac.EnableConfidentiality.Single(False) # integrity only (no encryption)
        # smac.ConfidentialityOffset.Single(30)
        # smac.EnableEncryptedVlans.Single(True); smac.EncryptedVlanCount = 1
        # smac.InnerVlanList.find().VlanId.Single(100)

        # --- keys ---------------------------------------------------------------------
        smac.TxSakPoolSize = 1
        smac.RxSakPoolSize = 1
        if len(SAK) == 32:
            smac.TxSakPool.TxSak128.Single(SAK)
            smac.RxSakPool.RxSak128.Single(SAK)
        else:
            smac.TxSakPool.TxSak256.Single(SAK)
            smac.RxSakPool.RxSak256.Single(SAK)

        macsec_endpoints.append(smac)

    describe(macsec_endpoints[0])   # learning aid: every StaticMacsec property

    # Start protocols (brings up the MACsec device endpoints)
    ixnetwork.StartAllProtocols(Arg1='sync')

    # --- encrypted traffic ------------------------------------------------------------
    # Endpoints are the StaticMacsec objects -> the frames are encrypted by the port.
    ti = ixnetwork.Traffic.TrafficItem.add(Name='MACsec_Encrypted', TrafficType='ethernetVlan',
                                           BiDirectional=True)
    ti.EndpointSet.add(Sources=macsec_endpoints[0], Destinations=macsec_endpoints[1])
    ce = ti.ConfigElement.find()[0]
    ce.FrameRate.update(Type='percentLineRate', Rate=LINE_RATE_PERCENT)
    ce.TransmissionControl.update(Type='fixedFrameCount', FrameCount=FRAMES_PER_RUN)
    ce.FramePayload.update(Type='custom', CustomPattern='CAFEC0FFEE', CustomRepeat=True)

    results = {}
    for size in FRAME_SIZES:
        ixnetwork.info('=== Frame size {} ==='.format(size))
        ce.FrameSize.update(Type='fixed', FixedSize=size)
        ixnetwork.ClearStats()
        run_traffic(ixnetwork)
        results[size] = check_traffic_loss(session)
        stat_view_to_csv(session, 'Traffic Item Statistics', 'lesson04_traffic_{}B.csv'.format(size))

    # --- MACsec statistic views (Tx/Rx protected/encrypted, ICV errors ...) ------------
    for view in list_views(session, 'macsec'):
        stat_view_to_csv(session, view, 'lesson04_{}.csv'.format(view.replace(' ', '_')))

    print('\nSummary: ' + ', '.join('{}B={}'.format(s, 'PASS' if ok else 'FAIL')
                                   for s, ok in results.items()))
