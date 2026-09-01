import math
import uuid

from plc_monitor.config.settings import POLL_INTERVAL
from plc_monitor.core.discovery.scanner import list_local_subnets, scan_for_opcua
from plc_monitor.core.models import PLCConfig
from plc_monitor.core.plc.opcua_client import OPCUAConnection
from plc_monitor.services.config_store import load_config, save_config


def _sanitize(value):
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    return value


class Api:
    def __init__(self):
        self.plcs = load_config()
        self.connections = {}
        self._start_all_connections()

    def _start_all_connections(self):
        for plc in self.plcs:
            self._start_connection(plc)

    def _start_connection(self, plc):
        conn = OPCUAConnection(plc, poll_interval=POLL_INTERVAL)
        conn.start()
        self.connections[plc.id] = conn

    def _stop_connection(self, plc_id):
        conn = self.connections.pop(plc_id, None)
        if conn:
            conn.stop()

    # ---------- called from JS ----------
    def get_subnets(self):
        return list_local_subnets() or ["192.168.0.0/24"]

    def scan(self, subnet):
        try:
            results = scan_for_opcua(subnet)
        except Exception:
            results = []
        known_ips = {p.ip for p in self.plcs}
        new_devices = [d for d in results if d.ip not in known_ips]
        for device in new_devices:
            plc = PLCConfig(
                id=str(uuid.uuid4()),
                name=device.name,
                ip=device.ip,
                port=device.port,
                endpoint_url=device.endpoint_url,
                application_uri=device.application_uri,
            )
            self.plcs.append(plc)
            self._start_connection(plc)
        if new_devices:
            save_config(self.plcs)
        return {"found": len(results), "added": len(new_devices)}

    def remove_plc(self, plc_id):
        self._stop_connection(plc_id)
        self.plcs = [p for p in self.plcs if p.id != plc_id]
        save_config(self.plcs)
        return True

    def set_student(self, plc_id, name):
        for plc in self.plcs:
            if plc.id == plc_id:
                plc.student = name.strip()
                save_config(self.plcs)
                return True
        return False

    def get_state(self):
        cards = []
        online = 0
        for plc in self.plcs:
            conn = self.connections.get(plc.id)
            is_online = bool(conn and conn.is_connected)
            online += 1 if is_online else 0
            metrics = conn.last_metrics if conn else None
            cards.append(
                {
                    "id": plc.id,
                    "name": plc.name,
                    "ip": plc.ip,
                    "student": plc.student,
                    "online": is_online,
                    "t": conn.last_t if conn else [],
                    "y": conn.last_y if conn else [],
                    "setpoint": conn.last_setpoint_series if conn else [],
                    "u": conn.last_u if conn else [],
                    "last_data_at": conn.last_data_at if conn else None,
                    "overshoot_pct": metrics.overshoot_pct if metrics else None,
                    "peak_time_s": metrics.peak_time_s if metrics else None,
                    "settling_time_s": metrics.settling_time_s if metrics else None,
                    "settling_time_s_5pct": metrics.settling_time_s_5pct if metrics else None,
                    "steady_state_error_pct": metrics.steady_state_error_pct if metrics else None,
                    "iae": conn.last_iae if conn else None,
                }
            )
        return _sanitize({"online": online, "offline": len(self.plcs) - online, "cards": cards})

    def shutdown(self):
        for conn in self.connections.values():
            conn.stop()
