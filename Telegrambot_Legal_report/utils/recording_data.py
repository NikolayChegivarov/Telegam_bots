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
    document = Document(template_path)
    table = document.tables[0]  # Первая таблица

    # Явное заполнение ячеек по номеру строки
    table.cell(0, 1).text = data.get("Краткое наименование", "")
    table.cell(1, 1).text = data.get("ОГРН", "")
    table.cell(2, 1).text = f"{data.get('ИНН', '')} / {data.get('КПП', '')}"
    table.cell(3, 1).text = data.get("Юр. адрес", "")
    table.cell(4, 1).text = data.get("Дата образования", "")
    table.cell(5, 1).text = data.get("Учредители/участники (текущие)", "")
    table.cell(6, 1).text = data.get("Размер уставного капитала", "")
    table.cell(7, 1).text = data.get("Генеральный директор", "")
    table.cell(8, 1).text = data.get("ОКВЭД (основной)", "")
    table.cell(9, 1).text = data.get("Система налогообложения", "")

    document.save(output_path)
