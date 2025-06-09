import os
from docx import Document
import time
from datetime import datetime
import re

def generate_filename(data: dict):
    org_name = data.get('org_name', 'report')
    org_name = org_name.replace('"', '').replace("'", '')
    org_name = re.sub(r'[<>:/\\|?*]', '', org_name)
    # Дата и время для уникальности
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f"{org_name}_{timestamp}.docx"
    return filename


def safe_str(val):
    if val is None:
        return ""
    s = str(val)
    return ''.join(c for c in s if c.isprintable())

def save_filled_doc(template_path: str, output_path: str, data: dict):
    if not os.path.exists(template_path):
        raise FileNotFoundError("❌ Не обнаружен шаблон.docx")
    document = Document(template_path)

    table = document.tables[0]  # Первая таблица

    FIELDS = {
        "Наименование:": "Полное наименование",
        "ОГРН:": "ОГРН",
        "ИНН/КПП:": lambda d: f"{d.get('ИНН', '')} / {d.get('КПП', '')}",
        "Юридический адрес:": "Юр. адрес",
        "Дата создания:": "Дата образования",
        "Учредители/участники (текущие):": "Учредители/участники (текущие)",
        "Размер уставного капитала:": "Размер уставного капитала",
        "Генеральный директор:": "Генеральный директор",
        "ОКВЭД (основной)": "ОКВЭД (основной)",
        "Система налогообложения": "Система налогообложения"
    }

    for row in table.rows:
        label = row.cells[0].text.strip()
        if label in FIELDS:
            field = FIELDS[label]
            value = field(data) if callable(field) else data.get(field, "")
            try:
                row.cells[1].text = safe_str(value)
                print(f"Записано: {label} -> {safe_str(value)}")
            except Exception as e:
                print(f"Ошибка при вставке '{value}' для '{label}': {e}")

    document.save(output_path)
    time.sleep(1)
    print(
        f"Файл сохранён: {output_path}, существует: {os.path.exists(output_path)}, размер: {os.path.getsize(output_path)}"
    )
