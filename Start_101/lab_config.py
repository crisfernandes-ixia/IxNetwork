"""
lab_config.py - ONE place to describe your lab.

Every Start_101 script imports this file, so this is the only file you need to
edit when moving between labs. Every value can also be overridden with an
environment variable, which is handy for CI pipelines, e.g.:

    Linux/macOS:  export IXN_API_SERVER=10.80.81.2
    Windows:      set IXN_API_SERVER=10.80.81.2
"""
import os

# ---------------------------------------------------------------------------
# IxNetwork API server
#   - Windows IxNetwork GUI on your PC : 'localhost' (REST port 11009)
#   - IxNetwork Web Edition / Linux API server / chassis-hosted : its IP (REST port 443)
# Leave REST_PORT as None and RestPy will auto-detect it.
# ---------------------------------------------------------------------------
API_SERVER = os.environ.get('IXN_API_SERVER', 'localhost')
REST_PORT = os.environ.get('IXN_REST_PORT') or None
USERNAME = os.environ.get('IXN_USERNAME', 'admin')
# Never commit real passwords - set IXN_PASSWORD in your shell instead.
PASSWORD = os.environ.get('IXN_PASSWORD', 'admin')

# ---------------------------------------------------------------------------
# Chassis and test ports (card, port)
# Lab: ports 2/1..2/4 are cabled to the DUT (NXP TSN switch) with 1G copper.
# ---------------------------------------------------------------------------
CHASSIS_IP = os.environ.get('IXN_CHASSIS', '10.80.81.2')
PORTS = [(2, 1), (2, 2), (2, 3), (2, 4)]

# Layer-1 settings applied after the ports are connected.
# Set either value to None to keep the port's default.
PORT_MEDIA = 'copper'        # 'copper' | 'fiber' | 'sgmii' (depends on the card)
PORT_SPEED = 'speed1000'     # e.g. 'speed100fd', 'speed1000', 'speed10g'

# ---------------------------------------------------------------------------
# Session housekeeping
# ---------------------------------------------------------------------------
# Prefix used to build a unique, identifiable session name:
#   <prefix>-<os user>-<YYYYmmdd-HHMMSS>   e.g. start101-jdoe-20261106-141500
SESSION_PREFIX = os.environ.get('IXN_SESSION_PREFIX', 'start101')

# Set IXN_KEEP_SESSION=1 to leave the session (and ports) up for debugging in the
# Web UI. Remember to delete it yourself afterwards - sessions consume licenses!
KEEP_SESSION = os.environ.get('IXN_KEEP_SESSION', '0') == '1'

# RestPy log level: 'none' | 'info' | 'warning' | 'request' | 'request_response' | 'all'
# 'request' is a great way to learn the underlying REST calls.
LOG_LEVEL = os.environ.get('IXN_LOG_LEVEL', 'info')
