import threading

from asyncua.sync import Client

SERVER_STATE_NODE_ID = "ns=0;i=2259"


class OPCUAConnection:
    def __init__(self, plc_config, poll_interval=1.0, on_status_change=None):
        self.config = plc_config
        self.poll_interval = poll_interval
        self.on_status_change = on_status_change
        self._client = None
        self._connected = False
        self._last_status = None
        self._stop_flag = threading.Event()
        self._thread = None

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
        except Exception:
            self._connected = False
        return self._connected

    def _disconnect(self):
        try:
            if self._client:
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
            state = self._client.get_node(SERVER_STATE_NODE_ID).read_value()
            self._set_status(str(state))
        except Exception:
            self._connected = False
            self._set_status("Offline")

    def _set_status(self, status):
        if status != self._last_status:
            self._last_status = status
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
