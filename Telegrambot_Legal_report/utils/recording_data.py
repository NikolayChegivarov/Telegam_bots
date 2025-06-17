import os
from docx import Document
import time
from datetime import datetime
import re
import ast

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
    import ast

    document = Document(template_path)

    # --- Формируем текст для актуальных участников
    actual_founders = data.get('Учредители/участники', {}).get('Актуальные участники', [])
    founders_text = ""
    for i, founder in enumerate(actual_founders, 1):
        name = founder.get('Наимен. и реквизиты', '')
        share = founder.get('Доля в %', '')
        founders_text += f"{i}. {name} — {share}\n"
    founders_text = founders_text.strip()

    # --- Директор или КУ
    director_role = "Генеральный директор"
    director_data = data.get("Генеральный директор", {})
    ku_data = data.get("Конкурсный управляющий", {})

    if ku_data.get("ИНН") or ku_data.get("ФИО"):
        director_role = "Конкурсный управляющий"
        director_data = ku_data

    fio = director_data.get("ФИО", "")
    inn = director_data.get("ИНН", "")

    # --- Основная таблица
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

    # --- Сведения о сотрудниках ---
    table2 = document.tables[1]

    def extract_value(dictionary_str):
        try:
            parsed = ast.literal_eval(dictionary_str)
            if isinstance(parsed, dict):
                key = next(iter(parsed.keys()))
                val = parsed[key]
                return key, val
        except Exception:
            return "", ""
        return "", ""

    employee_info = data.get("Сведения о сотрудниках", {})
    headcount = employee_info.get("Среднесписочная численность", {})
    salary = employee_info.get("Средняя заработная плата", {})

    # Подготовим год и значения в правильном порядке
    columns = ['year_3', 'year_2', 'year_1']  # year_3 — старый год (2021), справа — новые (2023)
    years = []
    headcount_values = []
    salary_values = []

    for year_key in columns:
        y, v1 = extract_value(headcount.get(year_key, ''))
        _, v2 = extract_value(salary.get(year_key, ''))
        years.append(y)
        headcount_values.append(v1)
        salary_values.append(v2)

    # Заполняем таблицу
    for i, year in enumerate(years):
        table2.cell(0, i + 1).text = year  # заголовки: 2021 2022 2023
        table2.cell(1, i + 1).text = headcount_values[i]
        table2.cell(2, i + 1).text = salary_values[i]

    # Устанавливаем подписи строк явно
    table2.cell(1, 0).text = "Среднесписочная численность"
    table2.cell(2, 0).text = "Средняя заработная плата"

    # --- Сведения о залоге долей ---
    table4 = document.tables[3]  # Таблица #4 по индексу

    # Удаляем строку-шаблон (вторая строка таблицы)
    if len(table4.rows) > 1:
        tbl = table4._tbl
        tbl.remove(tbl.tr_lst[1])  # удаление второй строки на уровне XML

    pledges = data.get("Сведения о залогах", [])
    for pledge in pledges:
        row_cells = table4.add_row().cells
        row_cells[0].text = pledge.get("Залогодатель", "")
        row_cells[1].text = pledge.get("Дата залога", "")
        row_cells[2].text = pledge.get("Залогодержатель", "")

    document.save(output_path)

