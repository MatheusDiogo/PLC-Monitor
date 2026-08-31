import os
import sys

POLL_INTERVAL = 0.2
DEFAULT_OPCUA_PORT = 4840
SCAN_TIMEOUT = 0.3
OPCUA_PROBE_TIMEOUT = 2.5
SCAN_MAX_WORKERS = 100

DATA_OBJECT_NAME = "Malha"
TAG_OUTPUT = "Y"
TAG_SETPOINT = "setpoint"
TAG_INPUT = "Ulim"
TAG_IAE = "iae"
TAG_FECHADA = "Fechada"
SETTLING_BAND_PCT = 0.02
SETTLING_MIN_VIOLATION_SAMPLES = 3
STEP_DETECT_EPSILON = 0.01
HISTORY_MAX_SECONDS = 60
BROWSE_MAX_DEPTH = 3

def _config_dir():
    if hasattr(sys, "_MEIPASS"):
        exe_dir = os.path.dirname(sys.executable)
        return exe_dir
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))

def _web_dir():
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "plc_monitor", "web", "static")
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "static"))

CONFIG_DIR = _config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "clps_config.json")
WEB_DIR = _web_dir()
