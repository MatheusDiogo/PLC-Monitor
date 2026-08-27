import threading

import snap7
from snap7.util import get_bool, get_dint, get_int, get_real

SIZE_MAP = {"bool": 1, "int": 2, "dint": 4, "real": 4}


class PLCConnection:
    def __init__(self, plc_config, database, poll_interval=1.0, on_status_change=None):
        self.config = plc_config
        self.db = database
        self.poll_interval = poll_interval
        self.on_status_change = on_status_change
        self._client = snap7.client.Client()
        self._connected = False
        self._last_status = None
        self._stop_flag = threading.Event()
        self._thread = None
        self.last_values = {}
        self.student_name = None

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
            self._client.connect(self.config.ip, self.config.rack, self.config.slot)
            self._connected = self._client.get_connected()
        except Exception:
            self._connected = False
        return self._connected

    def _disconnect(self):
        try:
            if self._client.get_connected():
                self._client.disconnect()
        except Exception:
            pass
        self._connected = False

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
        try:
            state = self._client.get_cpu_state()
            self._set_status(str(state))
        except Exception:
            self._connected = False
            self._set_status("Offline")
            return
        ordered_tags = sorted(self.config.tags, key=lambda t: not t.is_identity)
        for tag in ordered_tags:
            try:
                value = self._read_tag(tag)
                self.last_values[tag.label] = value
                if tag.is_identity:
                    self.student_name = value
                self.db.insert_reading(self.config.id, tag.label, value, student=self.student_name)
            except Exception:
                self.last_values[tag.label] = "Erro de leitura"

    def _read_tag(self, tag):
        if tag.data_type == "string":
            return self._read_string(tag)
        size = SIZE_MAP.get(tag.data_type, 1)
        start = int(tag.offset)
        data = self._client.db_read(tag.db_number, start, size)
        if tag.data_type == "bool":
            return get_bool(data, 0, tag.bit)
        if tag.data_type == "int":
            return get_int(data, 0)
        if tag.data_type == "dint":
            return get_dint(data, 0)
        if tag.data_type == "real":
            return round(get_real(data, 0), 3)
        return None

    def _read_string(self, tag):
        start = int(tag.offset)
        max_len = max(int(tag.length), 1)
        size = 2 + max_len
        data = self._client.db_read(tag.db_number, start, size)
        actual_len = data[1]
        actual_len = min(actual_len, max_len)
        raw = data[2 : 2 + actual_len]
        return raw.decode("ascii", errors="replace").strip("\x00").strip()

    def _set_status(self, status):
        if status != self._last_status:
            self._last_status = status
            self.db.insert_status(self.config.id, status, student=self.student_name)
            if self.on_status_change:
                self.on_status_change(self.config.id, status)

    @property
    def is_connected(self):
        return self._connected

    @property
    def last_status(self):
        return self._last_status or "Conectando..."

    @property
    def connection_state(self):
        return "Online" if self._connected else "Offline"
