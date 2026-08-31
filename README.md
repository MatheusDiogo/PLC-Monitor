# Monitor de CLPs — Prova Prática

Aplicação desktop (Python + pywebview, front-end HTML/CSS/JS) para o professor acompanhar, em tempo real, os CLPs Siemens S7-1500/S7-1200 de todas as bancadas via OPC UA.

Os CLPs **não são cadastrados manualmente**: o app varre a sub-rede local em busca de servidores OPC UA (porta 4840) e conecta automaticamente em todos os que encontrar. Pré-requisito: o servidor OPC UA de cada CPU precisa estar habilitado na TIA Portal, com um objeto "Dados" expondo as tags `n`, `i`, `y` (saída) e `u` (entrada).

## Estrutura do projeto

```
PLC-Monitor/
├── src/plc_monitor/            # pacote principal (pip install -e .)
│   ├── app.py                   # entry-point main() — cria a janela pywebview
│   ├── __main__.py              # python -m plc_monitor
│   ├── config/settings.py       # portas/timeouts de varredura, período de amostragem, WEB_DIR
│   ├── core/
│   │   ├── models.py            # PLCConfig
│   │   ├── metrics.py           # overshoot / tempo de subida / tempo de acomodação
│   │   ├── database.py          # SQLite :memory: (reservado para fase futura)
│   │   ├── discovery/scanner.py # varredura da rede por servidores OPC UA
│   │   └── plc/opcua_client.py  # OPCUAConnection: conecta, navega até "Dados" e lê n/i/y/u
│   ├── services/
│   │   ├── config_store.py      # load/save JSON (data/clps_config.json)
│   │   └── export.py            # export CSV (reservado para fase futura)
│   └── web/
│       ├── api.py               # ponte Python↔JS exposta ao front-end (js_api do pywebview)
│       └── static/              # index.html, style.css, app.js
├── data/                        # runtime: clps_config.json (não versionado)
├── build.spec                   # PyInstaller onefile
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

Ao abrir: escolha a sub-rede (detectada automaticamente) e clique em "VARRER REDE" — todos os CLPs OPC UA encontrados são conectados e aparecem como cards, com gráficos de saída/entrada e as métricas de resposta ao degrau.

## Gerando o executável (.exe)

```bash
pip install pyinstaller
pyinstaller build.spec
```

O `clps_config.json` é salvo em `data/` em dev e ao lado do `.exe` quando empacotado (via `CONFIG_FILE` em `settings.py` com `sys._MEIPASS`). Os assets web (`web/static/`) são empacotados junto via `datas` no `.spec`.

## Ajustando as métricas de resposta

`config/settings.py`:
- `DATA_OBJECT_NAME` / `TAG_COUNT` / `TAG_INDEX` / `TAG_OUTPUT` / `TAG_INPUT` — nomes das tags OPC UA procuradas (busca por nome, não por NodeId fixo, então funciona mesmo com namespace diferente por projeto).
- `SAMPLE_PERIOD_S` — período de amostragem usado pelo programa do CLP ao gravar os arrays `y`/`u`. Precisa bater com o valor real do projeto, senão os tempos de subida/acomodação saem fora de escala.
- `SETTLING_BAND_PCT` — banda de tolerância (padrão 2%) usada para calcular o tempo de acomodação.

## Roadmap

Fase 1 (descoberta/conexão) e leitura de tags/gráficos/métricas já implementadas. Próximas etapas: exportação de dados e histórico persistente.
