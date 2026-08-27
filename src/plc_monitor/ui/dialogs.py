import tkinter as tk
import uuid
from tkinter import messagebox, ttk

from plc_monitor.core.models import PLCConfig, Tag


class AddPLCDialog(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Adicionar CLP")
        self.geometry("440x520")
        self.on_save = on_save
        self.tags = []
        form = ttk.Frame(self, padding=10)
        form.pack(fill="both", expand=True)
        self.var_name = tk.StringVar()
        self.var_network = tk.StringVar(value="Wireless 1")
        self.var_ip = tk.StringVar()
        self.var_rack = tk.StringVar(value="0")
        self.var_slot = tk.StringVar(value="1")
        self._field(form, "Nome (ex.: Bancada 4)", self.var_name)
        self._field(form, "Rede (ex.: Wireless 1 / Wireless 2) — apenas organizacional", self.var_network)
        self._field(form, "IP do CLP", self.var_ip)
        self._field(form, "Rack", self.var_rack)
        self._field(form, "Slot", self.var_slot)
        ttk.Separator(form).pack(fill="x", pady=8)
        ttk.Label(form, text="Tags monitoradas (DBs):").pack(anchor="w")
        self.tags_list = tk.Listbox(form, height=6)
        self.tags_list.pack(fill="x", pady=4)
        ttk.Button(form, text="+ Adicionar tag", command=self._add_tag).pack(anchor="w")
        ttk.Separator(form).pack(fill="x", pady=8)
        btns = ttk.Frame(form)
        btns.pack(fill="x")
        ttk.Button(btns, text="Salvar", command=self._save).pack(side="right")
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="right", padx=6)

    def _field(self, parent, label, var):
        ttk.Label(parent, text=label).pack(anchor="w")
        ttk.Entry(parent, textvariable=var).pack(fill="x", pady=(0, 6))

    def _add_tag(self):
        TagDialog(self, on_save=self._append_tag)

    def _append_tag(self, tag):
        self.tags.append(tag)
        marker = "  [ALUNO]" if tag.is_identity else ""
        self.tags_list.insert("end", f"{tag.label}  (DB{tag.db_number}.{tag.offset} — {tag.data_type}){marker}")

    def _save(self):
        if not self.var_name.get() or not self.var_ip.get():
            messagebox.showwarning("Campos obrigatórios", "Preencha ao menos Nome e IP.")
            return
        try:
            rack = int(self.var_rack.get() or 0)
            slot = int(self.var_slot.get() or 1)
        except ValueError:
            messagebox.showwarning("Valor inválido", "Rack e Slot devem ser números inteiros.")
            return
        plc = PLCConfig(
            id=str(uuid.uuid4()),
            name=self.var_name.get(),
            ip=self.var_ip.get(),
            network=self.var_network.get(),
            rack=rack,
            slot=slot,
            tags=self.tags,
        )
        self.on_save(plc)
        self.destroy()


class TagDialog(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Nova tag")
        self.geometry("360x440")
        self.on_save = on_save
        form = ttk.Frame(self, padding=10)
        form.pack(fill="both", expand=True)
        self.var_label = tk.StringVar()
        self.var_db = tk.StringVar(value="1")
        self.var_offset = tk.StringVar(value="0")
        self.var_type = tk.StringVar(value="real")
        self.var_bit = tk.StringVar(value="0")
        self.var_length = tk.StringVar(value="20")
        self.var_identity = tk.BooleanVar(value=False)
        ttk.Label(form, text="Nome exibido (ex.: Nível tanque)").pack(anchor="w")
        ttk.Entry(form, textvariable=self.var_label).pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Número do DB").pack(anchor="w")
        ttk.Entry(form, textvariable=self.var_db).pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Offset (byte inicial)").pack(anchor="w")
        ttk.Entry(form, textvariable=self.var_offset).pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Tipo").pack(anchor="w")
        ttk.Combobox(form, textvariable=self.var_type, values=["bool", "int", "dint", "real", "string"], state="readonly").pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Bit (apenas para tipo bool, 0–7)").pack(anchor="w")
        ttk.Entry(form, textvariable=self.var_bit).pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Tamanho máx. em chars (apenas para tipo string)").pack(anchor="w")
        ttk.Entry(form, textvariable=self.var_length).pack(fill="x", pady=(0, 6))
        ttk.Separator(form).pack(fill="x", pady=6)
        ttk.Checkbutton(form, text="Usar como identificação do aluno/PC (PK do registro)", variable=self.var_identity).pack(anchor="w", pady=(0, 4))
        ttk.Label(form, text="Marque isso na tag onde o nome do aluno é escrito no DB\n(generally tipo string). O valor lido passa a identificar\nos dados desse CLP mesmo se o IP mudar de rede.", foreground="#555555", justify="left").pack(anchor="w")
        ttk.Button(form, text="Adicionar", command=self._save).pack(pady=10)

    def _save(self):
        if not self.var_label.get():
            messagebox.showwarning("Campo obrigatório", "Informe o nome da tag.")
            return
        try:
            tag = Tag(
                label=self.var_label.get(),
                db_number=int(self.var_db.get()),
                offset=float(self.var_offset.get()),
                data_type=self.var_type.get(),
                bit=int(self.var_bit.get() or 0),
                length=int(self.var_length.get() or 20),
                is_identity=bool(self.var_identity.get()),
            )
        except ValueError:
            messagebox.showwarning("Valor inválido", "DB, offset, bit e tamanho devem ser numéricos.")
            return
        self.on_save(tag)
        self.destroy()
