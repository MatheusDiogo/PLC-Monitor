import json
import os

from plc_monitor.config.settings import CONFIG_FILE
from plc_monitor.core.models import PLCConfig


def load_config(path=CONFIG_FILE):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PLCConfig.from_dict(d) for d in data]


def save_config(plcs, path=CONFIG_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in plcs], f, ensure_ascii=False, indent=2)
