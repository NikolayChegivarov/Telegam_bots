import json
import os
from datetime import datetime

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history_requests.json")


def init_history_file():
    """Создает файл истории, если он отсутствует."""
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)


def write_to_history(org_name: str):
    """Добавляет запись об отчете в историю."""
    init_history_file()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        history = {}

    history[org_name] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)


def read_history() -> list[str]:
    """Возвращает список названий организаций из истории."""
    init_history_file()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        return list(history.keys())
    except Exception:
        return []
