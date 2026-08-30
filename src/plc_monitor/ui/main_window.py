import threading
import uuid

import customtkinter as ctk
from tkinter import messagebox

from plc_monitor.config.settings import REFRESH_MS, POLL_INTERVAL
from plc_monitor.core.discovery.scanner import list_local_subnets, scan_for_opcua
from plc_monitor.core.models import PLCConfig
from plc_monitor.core.plc.opcua_client import OPCUAConnection
from plc_monitor.services.config_store import load_config, save_config

STATUS_COLORS = {"Online": "#2fa84f", "Offline": "#d1453b"}


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de CLPs")
        self.geometry("1040x680")
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.plcs = load_config()
        self.connections = {}
        self.discovered = []
        self.discovered_vars = {}
        self.connected_rows = {}

        self._build_ui()
        self._start_all_connections()
        self._refresh_loop()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text="Monitor de CLPs", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        scan_bar = ctk.CTkFrame(self, fg_color="transparent")
        scan_bar.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(scan_bar, text="Sub-rede:").pack(side="left", padx=(0, 8))
        subnets = list_local_subnets() or ["192.168.0.0/24"]
        self.subnet_combo = ctk.CTkComboBox(scan_bar, values=subnets, width=180)
        self.subnet_combo.set(subnets[0])
        self.subnet_combo.pack(side="left")
        self.scan_button = ctk.CTkButton(scan_bar, text="Buscar CLPs na rede", command=self._start_scan)
        self.scan_button.pack(side="left", padx=8)
        self.scan_status = ctk.CTkLabel(scan_bar, text="", text_color="gray60")
        self.scan_status.pack(side="left", padx=8)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        found_panel = ctk.CTkFrame(body)
        found_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(found_panel, text="Encontrados", font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        self.found_frame = ctk.CTkScrollableFrame(found_panel, fg_color="transparent")
        self.found_frame.pack(fill="both", expand=True, padx=8, pady=4)
        ctk.CTkButton(found_panel, text="Conectar selecionados", command=self._connect_selected).pack(
            fill="x", padx=12, pady=12
        )

        connected_panel = ctk.CTkFrame(body)
        connected_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(connected_panel, text="Conectados", font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        self.connected_frame = ctk.CTkScrollableFrame(connected_panel, fg_color="transparent")
        self.connected_frame.pack(fill="both", expand=True, padx=8, pady=(4, 12))

        self._reload_connected_list()

    def _start_scan(self):
        subnet = self.subnet_combo.get().strip()
        if not subnet:
            return
        self.scan_button.configure(state="disabled")
        self.scan_status.configure(text="Buscando...")
        for child in self.found_frame.winfo_children():
            child.destroy()
        self.discovered_vars = {}
        threading.Thread(target=self._scan_worker, args=(subnet,), daemon=True).start()

    def _scan_worker(self, subnet):
        try:
            results = scan_for_opcua(subnet)
        except Exception:
            results = []
        self.after(0, lambda: self._on_scan_done(results))

    def _on_scan_done(self, results):
        self.discovered = results
        known_ips = {p.ip for p in self.plcs}
        if not results:
            ctk.CTkLabel(self.found_frame, text="Nenhum CLP encontrado nesta sub-rede.").pack(
                anchor="w", padx=8, pady=8
            )
        for device in results:
            var = ctk.BooleanVar(value=False)
            self.discovered_vars[device.ip] = var
            label = f"{device.name}  ({device.ip})"
            if device.ip in known_ips:
                label += "  — já conectado"
            ctk.CTkCheckBox(self.found_frame, text=label, variable=var).pack(anchor="w", padx=8, pady=4)
        self.scan_status.configure(text=f"{len(results)} encontrado(s)")
        self.scan_button.configure(state="normal")

    def _connect_selected(self):
        known_ips = {p.ip for p in self.plcs}
        selected = [d for d in self.discovered if self.discovered_vars.get(d.ip) and self.discovered_vars[d.ip].get()]
        new_devices = [d for d in selected if d.ip not in known_ips]
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
            self._reload_connected_list()

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

    def _reload_connected_list(self):
        for child in self.connected_frame.winfo_children():
            child.destroy()
        self.connected_rows = {}
        if not self.plcs:
            ctk.CTkLabel(self.connected_frame, text="Nenhum CLP conectado ainda.").pack(anchor="w", padx=8, pady=8)
            return
        for plc in self.plcs:
            row = ctk.CTkFrame(self.connected_frame)
            row.pack(fill="x", padx=4, pady=4)
            dot = ctk.CTkLabel(row, text="●", text_color=STATUS_COLORS["Offline"], width=20)
            dot.pack(side="left", padx=(8, 4))
            info = ctk.CTkLabel(row, text=f"{plc.name}  ({plc.ip})", anchor="w")
            info.pack(side="left", fill="x", expand=True, padx=4)
            status_label = ctk.CTkLabel(row, text="Offline", text_color="gray60", width=90)
            status_label.pack(side="left", padx=4)
            ctk.CTkButton(
                row, text="Remover", width=80, fg_color="transparent", border_width=1,
                command=lambda pid=plc.id: self._remove_plc(pid),
            ).pack(side="right", padx=8)
            self.connected_rows[plc.id] = (dot, status_label)

    def _remove_plc(self, plc_id):
        if not messagebox.askyesno("Remover", "Remover este CLP da lista e parar o monitoramento?"):
            return
        self._stop_connection(plc_id)
        self.plcs = [p for p in self.plcs if p.id != plc_id]
        save_config(self.plcs)
        self._reload_connected_list()

    def _refresh_loop(self):
        for plc in self.plcs:
            conn = self.connections.get(plc.id)
            row = self.connected_rows.get(plc.id)
            if conn and row:
                dot, status_label = row
                state = conn.connection_state
                dot.configure(text_color=STATUS_COLORS.get(state, "gray60"))
                status_label.configure(text=state)
        self.after(REFRESH_MS, self._refresh_loop)

    def _on_close(self):
        for conn in self.connections.values():
            conn.stop()
        self.destroy()
