import os
import sys

REFRESH_MS = 1000
POLL_INTERVAL = 1.0
DEFAULT_OPCUA_PORT = 4840
SCAN_TIMEOUT = 0.3
OPCUA_PROBE_TIMEOUT = 2.5
SCAN_MAX_WORKERS = 100

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)

def _config_dir():
    if hasattr(sys, "_MEIPASS"):
        exe_dir = os.path.dirname(sys.executable)
        return exe_dir
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))

CONFIG_DIR = _config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "clps_config.json")
STATIC_DIR = resource_path(os.path.join("plc_monitor", "static"))
