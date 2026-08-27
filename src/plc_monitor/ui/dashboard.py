import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from plc_monitor.config.settings import REFRESH_MS
from plc_monitor.services.export import export_readings


class DashboardWindow(tk.Toplevel):
    def __init__(self, parent, plc, connection, database):
        super().__init__(parent)
        self.title(f"Dashboard — {plc.name} ({plc.ip})")
        self.geometry("540x500")
        self.plc = plc
        self.conn = connection
        self.db = database
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        info = ttk.Frame(top)
        info.pack(side="left")
        self.status_label = ttk.Label(info, text="Status: —", font=("Segoe UI", 12, "bold"))
        self.status_label.pack(anchor="w")
        self.aluno_label = ttk.Label(info, text="Aluno: —", font=("Segoe UI", 10))
        self.aluno_label.pack(anchor="w")
        ttk.Button(top, text="Exportar CSV deste CLP", command=self._export).pack(side="right")
        ttk.Label(self, text="Valores monitorados:", padding=(8, 4)).pack(anchor="w")
        self.values_tree = ttk.Treeview(self, columns=("tag", "valor"), show="headings", height=8)
        self.values_tree.heading("tag", text="Tag")
        self.values_tree.heading("valor", text="Valor")
        self.values_tree.pack(fill="x", padx=8)
        ttk.Label(self, text="Últimos eventos de status:", padding=(8, 4)).pack(anchor="w")
        self.log_list = tk.Listbox(self)
        self.log_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._refresh()

    def _refresh(self):
        if not self.winfo_exists():
            return
        status = self.conn.last_status if self.conn else "Desconhecido"
        conexao = self.conn.connection_state if self.conn else "Offline"
        self.status_label.config(text=f"Status: {status}  ({conexao})")
        aluno = (self.conn.student_name if self.conn else None) or "—"
        self.aluno_label.config(text=f"Aluno: {aluno}")
        self.values_tree.delete(*self.values_tree.get_children())
        if self.conn:
            for label, value in self.conn.last_values.items():
                self.values_tree.insert("", "end", values=(label, value))
        self.log_list.delete(0, "end")
        for status_value, ts in self.db.fetch_status_history(self.plc.id, limit=20):
            self.log_list.insert(0, f"{ts} — {status_value}")
        self.after(REFRESH_MS, self._refresh)

    def _export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile=f"{self.plc.name}.csv", title="Exportar dados deste CLP")
        if not path:
            return
        export_readings(self.db, path, self.plc.id)
        messagebox.showinfo("Exportação concluída", f"Dados exportados para:\n{path}")
