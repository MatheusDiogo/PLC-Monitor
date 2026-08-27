# Monitor de CLPs — Prova Prática

Aplicação em Python (Tkinter + python-snap7) para o professor acompanhar, em tempo real, os CLPs Siemens de todas as bancadas.

## Estrutura do projeto

```
PLC-Monitor/
├── src/plc_monitor/         # pacote principal (pip install -e .)
│   ├── app.py               # entry-point main()
│   ├── __main__.py          # python -m plc_monitor
│   ├── config/settings.py   # REFRESH_MS, CONFIG_FILE, resource_path (PyInstaller)
│   ├── core/
│   │   ├── models.py        # Tag, PLCConfig
│   │   ├── database.py      # SQLite :memory:
│   │   └── plc/client.py    # PLCConnection (thread polling)
│   ├── services/
│   │   ├── config_store.py  # load/save JSON (data/clps_config.json)
│   │   └── export.py        # export CSV
│   ├── ui/                  # equivale a routes/templates
│   │   ├── main_window.py   # PLCMonitorApp
│   │   ├── dialogs.py       # AddPLCDialog, TagDialog
│   │   ├── dashboard.py     # DashboardWindow
│   │   └── utils.py         # resolve_hostname
│   └── static/icons/        # assets (equiv. a static/)
├── data/                    # runtime: clps_config.json (não versionado)
├── build.spec               # PyInstaller onefile
├── pyproject.toml
└── requirements.txt
```

`ui/` = camada de rotas/views, `static/` = assets, `data/` = persistência, `core/` = domínio.

## Como rodar (modo desenvolvimento)

```bash
pip install -r requirements.txt
pip install -e .
python -m plc_monitor
# ou
plc-monitor
```

## Gerando o executável (.exe)

```bash
pip install pyinstaller
pyinstaller build.spec
# onefile alternativo:
pyinstaller --onefile --noconsole --name MonitorCLPs --add-data "src/plc_monitor/static;plc_monitor/static" src/plc_monitor/__main__.py
```

O `clps_config.json` é salvo em `data/` em dev e ao lado do `.exe` quando empacotado (via `CONFIG_FILE` em `settings.py` com `sys._MEIPASS`).

Se o `snap7.dll` não for encontrado no exe:
```bash
pyinstaller --onefile --noconsole --name MonitorCLPs --add-binary "caminho/para/snap7.dll;." --add-data "src/plc_monitor/static;plc_monitor/static" src/plc_monitor/__main__.py
```

## Migração

A pasta antiga `app/` foi removida — use `src/plc_monitor/`.
