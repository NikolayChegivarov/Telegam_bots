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
    from docx import Document

    document = Document(template_path)

    # Формируем текст для актуальных участников
    actual_founders = data.get('Учредители/участники', {}).get('Актуальные участники', [])
    founders_text = ""
    for i, founder in enumerate(actual_founders, 1):
        name = founder.get('Наимен. и реквизиты', '')
        share = founder.get('Доля в %', '')
        founders_text += f"{i}. {name} — {share}\n"
    founders_text = founders_text.strip()

    # Выбор между директором и конкурсным управляющим
    director_role = "Генеральный директор"
    director_data = data.get("Генеральный директор", {})
    ku_data = data.get("Конкурсный управляющий", {})

    if ku_data.get("ИНН") or ku_data.get("ФИО"):
        director_role = "Конкурсный управляющий"
        director_data = ku_data

    fio = director_data.get("ФИО", "")
    inn = director_data.get("ИНН", "")

    # Общая информация. Строчка колонка
    table1 = document.tables[0]
    table1.cell(0, 1).text = data.get("Краткое наименование", "")
    table1.cell(1, 1).text = data.get("ОГРН", "")
    table1.cell(2, 1).text = f"{data.get('ИНН', '')} / {data.get('КПП', '')}"
    table1.cell(3, 1).text = data.get("Юридический адрес", "")
    table1.cell(4, 1).text = data.get("Дата образования", "")
    table1.cell(5, 1).text = founders_text
    table1.cell(6, 1).text = data.get("Уставный капитал", "")
    table1.cell(7, 0).text = director_role
    table1.cell(7, 1).text = f"{fio}, ИНН {inn}".strip(", ")
    table1.cell(8, 1).text = data.get("ОКВЭД(основной)", "")
    table1.cell(9, 1).text = data.get("Система налогообложения", "")

    # Сведения о сотрудниках.
    table2 = document.tables[1]
    table2.cell(0, 1).text = data.get("", "")
    table2.cell(1, 1).text = data.get("", "")

    document.save(output_path)

