import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from plc_monitor.config.settings import POLL_INTERVAL, REFRESH_MS
from plc_monitor.core.database import Database
from plc_monitor.core.plc.client import PLCConnection
from plc_monitor.services.config_store import load_config, save_config
from plc_monitor.services.export import export_readings
from plc_monitor.ui.dashboard import DashboardWindow
from plc_monitor.ui.dialogs import AddPLCDialog
from plc_monitor.ui.utils import resolve_hostname


class PLCMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de CLPs — Prova Prática")
        self.root.geometry("860x500")
        self.db = Database()
        self.plcs = load_config()
        self.connections = {}
        self.dashboards = {}
        self._build_ui()
        self._start_all_connections()
        self._refresh_loop()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x", padx=8, pady=8)
        ttk.Button(toolbar, text="+ Adicionar CLP", command=self._open_add_dialog).pack(side="left")
        ttk.Button(toolbar, text="Exportar tudo (CSV)", command=self._export_all).pack(side="left", padx=8)
        ttk.Button(toolbar, text="Remover CLP selecionado", command=self._remove_selected).pack(side="left")
        columns = ("rede", "nome", "ip", "host", "conexao", "status", "aluno", "atualizado")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)
        headers = [("rede", "Rede", 90), ("nome", "Nome", 110), ("ip", "IP", 110), ("host", "PC/Host", 110), ("conexao", "Conexão", 80), ("status", "CLP", 90), ("aluno", "Aluno", 130), ("atualizado", "Última leitura", 110)]
        for col, label, width in headers:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=4)
        self.tree.bind("<Double-1>", self._open_dashboard_for_selected)
        self.tree.tag_configure("online", background="#e6f4ea")
        self.tree.tag_configure("offline", background="#fbe9e7")
        hint = ttk.Label(self.root, text="Duplo clique em um CLP para abrir o dashboard. Com um único adaptador Wi-Fi, apenas os CLPs da rede atual ficam \"Online\" (verde) — os demais aparecem \"Offline\" (vermelho) até você trocar de rede. Os dados capturados existem apenas enquanto o programa estiver aberto — exporte antes de fechar.", foreground="#555555", wraplength=820, justify="left")
        hint.pack(pady=(0, 6), padx=8, anchor="w")
        self._reload_tree()

    def _reload_tree(self):
        self.tree.delete(*self.tree.get_children())
        for plc in self.plcs:
            conn = self.connections.get(plc.id)
            conexao = conn.connection_state if conn else "Offline"
            status = conn.last_status if conn else "—"
            aluno = conn.student_name if conn and conn.student_name else "—"
            host = resolve_hostname(plc.ip)
            row_tag = "online" if conexao == "Online" else "offline"
            self.tree.insert("", "end", iid=plc.id, values=(plc.network, plc.name, plc.ip, host, conexao, status, aluno, ""), tags=(row_tag,))

    def _start_all_connections(self):
        for plc in self.plcs:
            self._start_connection(plc)

    def _start_connection(self, plc):
        conn = PLCConnection(plc, self.db, poll_interval=POLL_INTERVAL)
        conn.start()
        self.connections[plc.id] = conn

    def _stop_connection(self, plc_id):
        conn = self.connections.pop(plc_id, None)
        if conn:
            conn.stop()

    def _refresh_loop(self):
        for plc in self.plcs:
            conn = self.connections.get(plc.id)
            if conn and self.tree.exists(plc.id):
                conexao = conn.connection_state
                self.tree.set(plc.id, "conexao", conexao)
                self.tree.set(plc.id, "status", conn.last_status)
                self.tree.set(plc.id, "aluno", conn.student_name or "—")
                self.tree.item(plc.id, tags=("online" if conexao == "Online" else "offline",))
                if conn.last_values:
                    self.tree.set(plc.id, "atualizado", time.strftime("%H:%M:%S"))
        self.root.after(REFRESH_MS, self._refresh_loop)

    def _open_add_dialog(self):
        AddPLCDialog(self.root, on_save=self._add_plc)

    def _add_plc(self, plc):
        self.plcs.append(plc)
        save_config(self.plcs)
        self._start_connection(plc)
        self._reload_tree()

    def _remove_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        plc_id = sel[0]
        if not messagebox.askyesno("Remover", "Remover este CLP da lista e parar o monitoramento?"):
            return
        self._stop_connection(plc_id)
        self.plcs = [p for p in self.plcs if p.id != plc_id]
        save_config(self.plcs)
        self._reload_tree()

    def _open_dashboard_for_selected(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        plc_id = sel[0]
        plc = next((p for p in self.plcs if p.id == plc_id), None)
        if not plc:
            return
        if plc_id in self.dashboards and self.dashboards[plc_id].winfo_exists():
            self.dashboards[plc_id].lift()
            return
        conn = self.connections.get(plc_id)
        dash = DashboardWindow(self.root, plc, conn, self.db)
        self.dashboards[plc_id] = dash

    def _export_all(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Exportar todos os dados capturados")
        if not path:
            return
        export_readings(self.db, path)
        messagebox.showinfo("Exportação concluída", f"Dados exportados para:\n{path}")

    def _on_close(self):
        for conn in self.connections.values():
            conn.stop()
        self.db.close()
        self.root.destroy()
