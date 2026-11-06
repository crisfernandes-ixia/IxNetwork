"""
03_build_l2l3_from_scratch.py
=============================
Lesson 3 - Build a test from an empty config: 2 ports, Ethernet + IPv4, traffic.

This is the foundation for every protocol (BGP, MACsec, PTP ...) - they are all
stacked the same way:

    Topology (one per port)
      └── DeviceGroup (Multiplier = how many emulated devices)
            └── Ethernet  (MAC, VLAN)
                  └── IPv4 (address, gateway, prefix)
                        └── <protocols: BGP, OSPF ...>

What you learn
  * NGPF objects: Topology / DeviceGroup / Ethernet / Ipv4
  * "Multivalues": every per-device field can be Single(), Increment(),
    ValueList(), Random() ... -> one line configures 1 or 10 000 devices.
  * Create a traffic item between two IPv4 stacks, set rate/size/count.

Run
  python 03_build_l2l3_from_scratch.py
"""
import lab_config as cfg
from common import (check_traffic_loss, connect_ports, ixnetwork_session, run_traffic,
                    start_protocols_and_wait, stat_view_to_csv, verify_protocol_sessions)

DEVICES_PER_PORT = 1      # try 10 - nothing else needs to change

with ixnetwork_session('lesson03') as session:
    ixnetwork = session.Ixnetwork

    # 1. Ports ------------------------------------------------------------------
    vport1, vport2 = connect_ports(session, cfg.PORTS[:2])

    # 2. Topologies / device groups / ethernet / ipv4 -----------------------------
    stacks = []
    for idx, vport in enumerate((vport1, vport2), start=1):
        topology = ixnetwork.Topology.add(Name='Topo_{}'.format(idx), Ports=vport)
        dg = topology.DeviceGroup.add(Name='DG_{}'.format(idx), Multiplier=DEVICES_PER_PORT)

        eth = dg.Ethernet.add(Name='Eth_{}'.format(idx))
        eth.Mac.Increment(start_value='00:1{}:01:00:00:01'.format(idx), step_value='00:00:00:00:00:01')
        # Optional VLAN:
        # eth.EnableVlans.Single(True)
        # eth.Vlan.find().VlanId.Single(100)

        ipv4 = eth.Ipv4.add(Name='IPv4_{}'.format(idx))
        # Both ports on the same subnet through an L2 DUT (switch):
        # port 1 = 10.1.0.1, port 2 = 10.1.0.101, each uses the other as gateway.
        # For an L3 DUT (router) use the DUT interface IPs as gateways instead.
        me, peer = ('10.1.0.1', '10.1.0.101') if idx == 1 else ('10.1.0.101', '10.1.0.1')
        ipv4.Address.Increment(start_value=me, step_value='0.0.0.1')
        ipv4.GatewayIp.Increment(start_value=peer, step_value='0.0.0.1')
        ipv4.Prefix.Single(24)
        ipv4.ResolveGateway.Single(True)
        stacks.append(ipv4)

    # 3. Start protocols (here: ARP) and verify -------------------------------------
    start_protocols_and_wait(ixnetwork)
    verify_protocol_sessions(session)

    # 4. Traffic item ------------------------------------------------------------------
    ti = ixnetwork.Traffic.TrafficItem.add(Name='IPv4_P1_to_P2', TrafficType='ipv4',
                                           BiDirectional=True)
    ti.EndpointSet.add(Sources=stacks[0], Destinations=stacks[1])
    ce = ti.ConfigElement.find()[0]
    ce.FrameSize.update(Type='fixed', FixedSize=512)
    ce.FrameRate.update(Type='percentLineRate', Rate=50)
    ce.TransmissionControl.update(Type='fixedFrameCount', FrameCount=100000)
    ti.Tracking.find()[0].TrackBy = ['trackingenabled0', 'sourceDestEndpointPair0']

    # 5. Run & results ------------------------------------------------------------------
    run_traffic(ixnetwork)
    passed = check_traffic_loss(session)
    stat_view_to_csv(session, 'Traffic Item Statistics', 'lesson03_traffic_items.csv')
    stat_view_to_csv(session, 'Flow Statistics', 'lesson03_flows.csv')
    print('\nRESULT: {}'.format('PASS' if passed else 'FAIL'))
