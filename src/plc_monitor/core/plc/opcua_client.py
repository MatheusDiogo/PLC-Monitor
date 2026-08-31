import threading
import time

from asyncua.sync import Client

from plc_monitor.config.settings import (
    BROWSE_MAX_DEPTH,
    DATA_OBJECT_NAME,
    HISTORY_MAX_SECONDS,
    SETTLING_BAND_PCT,
    SETTLING_MIN_VIOLATION_SAMPLES,
    STEP_DETECT_EPSILON,
    TAG_FECHADA,
    TAG_IAE,
    TAG_INPUT,
    TAG_OUTPUT,
    TAG_SETPOINT,
)
from plc_monitor.core.metrics import compute_step_response_metrics


def _find_child_by_name(node, name, max_depth=BROWSE_MAX_DEPTH):
    target = name.strip().lower()
    frontier = [(node, 0)]
    while frontier:
        current, depth = frontier.pop(0)
        try:
            children = current.get_children()
        except Exception:
            continue
        for child in children:
            try:
                browse_name = child.read_browse_name().Name
            except Exception:
                continue
            if browse_name.strip().lower() == target:
                return child
            if depth + 1 < max_depth:
                frontier.append((child, depth + 1))
    return None


class OPCUAConnection:
    def __init__(self, plc_config, poll_interval=0.2, on_status_change=None):
        self.config = plc_config
        self.poll_interval = poll_interval
        self.on_status_change = on_status_change
        self._client = None
        self._connected = False
        self._last_status = None
        self._stop_flag = threading.Event()
        self._thread = None
        self._tag_nodes = {}
        self._last_setpoint = None
        self._last_fechada = None

        self._t_buffer = []
        self._y_buffer = []
        self._setpoint_buffer = []
        self._u_buffer = []

        self.last_metrics = None
        self.last_data_at = None
        self.last_iae = None

    def start(self):
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=2)
        self._disconnect()

    def _connect(self):
        try:
            self._client = Client(self.config.endpoint_url, timeout=3)
            self._client.connect()
            self._connected = True
            self._discover_tags()
            self._set_status("Online")
        except Exception:
            self._connected = False
        return self._connected

    def _discover_tags(self):
        self._tag_nodes = {}
        try:
            data_node = _find_child_by_name(self._client.get_objects_node(), DATA_OBJECT_NAME)
            if not data_node:
                return
            for tag_name in (TAG_OUTPUT, TAG_SETPOINT, TAG_INPUT, TAG_IAE, TAG_FECHADA):
                child = _find_child_by_name(data_node, tag_name, max_depth=1)
                if child:
                    self._tag_nodes[tag_name] = child
        except Exception:
            self._tag_nodes = {}

    def _disconnect(self):
        try:
            if self._client:
                self._client.disconnect()
        except Exception:
            pass
        self._connected = False
        self._tag_nodes = {}

    def _run_loop(self):
        while not self._stop_flag.is_set():
            if not self._connected:
                self._connect()
            if self._connected:
                self._poll_once()
            else:
                self._set_status("Offline")
            self._stop_flag.wait(self.poll_interval)

    def _poll_once(self):
        if not self._tag_nodes:
            self._connected = False
            self._set_status("Offline")
            return
        try:
            y = self._tag_nodes[TAG_OUTPUT].read_value()
            setpoint = self._tag_nodes[TAG_SETPOINT].read_value()
            u = self._tag_nodes[TAG_INPUT].read_value()
        except Exception:
            self._connected = False
            self._set_status("Offline")
            return

        iae_node = self._tag_nodes.get(TAG_IAE)
        if iae_node:
            try:
                self.last_iae = iae_node.read_value()
            except Exception:
                pass

        fechada = None
        fechada_node = self._tag_nodes.get(TAG_FECHADA)
        if fechada_node:
            try:
                fechada = bool(fechada_node.read_value())
            except Exception:
                pass

        self._set_status("Online")
        now = time.time()

        setpoint_stepped = (
            self._last_setpoint is not None and abs(setpoint - self._last_setpoint) > STEP_DETECT_EPSILON
        )
        fechada_rising = fechada and self._last_fechada is False
        if setpoint_stepped or fechada_rising:
            self._t_buffer = []
            self._y_buffer = []
            self._setpoint_buffer = []
            self._u_buffer = []
        self._last_setpoint = setpoint
        if fechada is not None:
            self._last_fechada = fechada

        self._t_buffer.append(now)
        self._y_buffer.append(y)
        self._setpoint_buffer.append(setpoint)
        self._u_buffer.append(u)

        cutoff = now - HISTORY_MAX_SECONDS
        while len(self._t_buffer) > 1 and self._t_buffer[0] < cutoff:
            self._t_buffer.pop(0)
            self._y_buffer.pop(0)
            self._setpoint_buffer.pop(0)
            self._u_buffer.pop(0)

        self.last_data_at = now
        self.last_metrics = compute_step_response_metrics(
            self._t_buffer, self._y_buffer, setpoint, SETTLING_BAND_PCT, SETTLING_MIN_VIOLATION_SAMPLES
        )

    def _set_status(self, status):
        if status != self._last_status:
            self._last_status = status
            if self.on_status_change:
                self.on_status_change(self.config.id, status)

    @property
    def last_y(self):
        return list(self._y_buffer)

    @property
    def last_setpoint_series(self):
        return list(self._setpoint_buffer)

    @property
    def last_u(self):
        return list(self._u_buffer)

    @property
    def is_connected(self):
        return self._connected

    @property
    def last_status(self):
        return self._last_status or "Conectando..."

    @property
    def connection_state(self):
        return "Online" if self._connected else "Offline"
