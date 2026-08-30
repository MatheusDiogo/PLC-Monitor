# Monitor de CLPs — Prova Prática

Aplicação em Python (CustomTkinter + asyncua/OPC UA) para o professor acompanhar, em tempo real, os CLPs Siemens S7-1200 (CPU 1214C) de todas as bancadas.

Os CLPs **não são cadastrados manualmente**: o app varre a sub-rede local em busca de servidores OPC UA (porta 4840) e o usuário escolhe quais conectar. Pré-requisito: o servidor OPC UA de cada CPU 1214C precisa estar habilitado na TIA Portal.

## Estrutura do projeto

```
PLC-Monitor/
├── src/plc_monitor/           # pacote principal (pip install -e .)
│   ├── app.py                  # entry-point main()
│   ├── __main__.py             # python -m plc_monitor
│   ├── config/settings.py      # REFRESH_MS, CONFIG_FILE, portas/timeouts de varredura
│   ├── core/
│   │   ├── models.py           # PLCConfig
│   │   ├── database.py         # SQLite :memory: (reservado para leitura de tags — fase futura)
│   │   ├── discovery/scanner.py# varredura da rede por servidores OPC UA
│   │   └── plc/opcua_client.py # OPCUAConnection (thread de conexão/keepalive)
│   ├── services/
│   │   ├── config_store.py     # load/save JSON (data/clps_config.json)
│   │   └── export.py           # export CSV (reservado para fase futura)
│   ├── ui/
│   │   ├── main_window.py      # MainWindow: descoberta + lista de conectados
│   │   └── utils.py            # resolve_hostname
│   └── static/icons/           # assets
├── data/                       # runtime: clps_config.json (não versionado)
├── build.spec                  # PyInstaller onefile
├── pyproject.toml
└── requirements.txt
```

## Como rodar (modo desenvolvimento)

```bash
pip install -r requirements.txt
pip install -e .
python -m plc_monitor
# ou
plc-monitor
```

Na janela: escolha a sub-rede (detectada automaticamente), clique em "Buscar CLPs na rede", marque os CLPs encontrados e clique em "Conectar selecionados".

## Gerando o executável (.exe)

```bash
pip install pyinstaller
pyinstaller build.spec
```

O `clps_config.json` é salvo em `data/` em dev e ao lado do `.exe` quando empacotado (via `CONFIG_FILE` em `settings.py` com `sys._MEIPASS`).

## Roadmap

Esta fase cobre apenas descoberta e conexão dos CLPs. Leitura de tags (valores do CLP via OPC UA), dashboard por CLP e exportação de dados ficam para as próximas fases.
