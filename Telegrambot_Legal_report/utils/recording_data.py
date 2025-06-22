import os
from docx import Document
import time
from datetime import datetime
import re
import ast
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def generate_filename(data: dict):
    """Формирует имя файла в формате: 'название_организации_дата_время.docx'
    Удаляет опасные символы из имени организации для корректного сохранения файла."""
    org_name = data.get('org_name', 'report')
    org_name = org_name.replace('"', '').replace("'", '')
    org_name = re.sub(r'[<>:/\\|?*]', '', org_name)
    # Дата и время для уникальности
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f"{org_name}_{timestamp}.docx"
    return filename


def safe_str(val):
    """Преобразует значение в безопасную строку, удаляя непечатаемые символы типа u0000."""
    if val is None:
        return ""
    s = str(val)
    return ''.join(c for c in s if c.isprintable())


def fill_table1(table, data: dict):
    """Заполнение таблицы 1 - Основные сведения о компании"""
    # Формируем текст для актуальных участников
    actual_founders = data.get('Учредители/участники', {}).get('Актуальные участники', [])
    founders_text = ""
    for i, founder in enumerate(actual_founders, 1):
        name = founder.get('Наимен. и реквизиты', '')
        share = founder.get('Доля в %', '')
        founders_text += f"{i}. {name} — {share}\n"
    founders_text = founders_text.strip()

    # Директор или КУ
    director_role = "Генеральный директор"
    director_data = data.get("Генеральный директор", {})
    ku_data = data.get("Конкурсный управляющий", {})

    if ku_data.get("ИНН") or ku_data.get("ФИО"):
        director_role = "Конкурсный управляющий"
        director_data = ku_data

    fio = director_data.get("ФИО", "")
    inn = director_data.get("ИНН", "")

    # Заполнение ячеек таблицы
    table.cell(0, 1).text = data.get("Краткое наименование", "")
    table.cell(1, 1).text = data.get("ОГРН", "")
    table.cell(2, 1).text = f"{data.get('ИНН', '')} / {data.get('КПП', '')}"
    table.cell(3, 1).text = data.get("Юридический адрес", "")
    table.cell(4, 1).text = data.get("Дата образования", "")
    table.cell(5, 1).text = founders_text
    table.cell(6, 1).text = data.get("Уставный капитал", "")
    table.cell(7, 0).text = director_role
    table.cell(7, 1).text = f"{fio}, ИНН {inn}".strip(", ")
    table.cell(8, 1).text = data.get("ОКВЭД(основной)", "")
    table.cell(9, 1).text = data.get("Система налогообложения", "")


def fill_table2(table, data: dict):
    """Заполнение таблицы 2 - Сведения о сотрудниках"""
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
        table.cell(0, i + 1).text = year  # заголовки: 2021 2022 2023
        table.cell(1, i + 1).text = headcount_values[i]
        table.cell(2, i + 1).text = salary_values[i]

    # Устанавливаем подписи строк явно
    table.cell(1, 0).text = "Среднесписочная численность"
    table.cell(2, 0).text = "Средняя заработная плата"


def fill_table4(table, data: dict):
    """Заполнение таблицы 4 — Сведения о залоге долей, или удаление таблицы"""
    value = data.get("О залоге долей")

    if isinstance(value, str) and "нет" in value.lower():
        # Удаляем таблицу, если информация отсутствует
        tbl_element = table._tbl
        parent_element = tbl_element.getparent()
        parent_element.remove(tbl_element)

        # Добавляем параграф вместо таблицы
        paragraph = table._parent.add_paragraph("Долей в залоге нет")
        run = paragraph.runs[0]
        run.italic = True
        return

    if not isinstance(value, dict):
        print("⚠️ Ожидался словарь или строка в поле 'О залоге долей'")
        return

    table.cell(1, 0).text = value.get("Залогодатель", "")
    table.cell(1, 1).text = value.get("Дата залога", "")
    table.cell(1, 2).text = value.get("Залогодержатель", "")


def fill_table5(table, data: dict):
    """Заполнение таблицы 5 - Аффилированность и ближайшие связи"""
    # Удаляем все строки после заголовка (оставляем только строку с заголовками)
    while len(table.rows) > 1:
        table._tbl.remove(table.rows[1]._tr)

    # Получаем данные
    links_data = data.get("Ближайшие связи", {})
    if isinstance(links_data, dict) and "Ближайшие связи" in links_data:
        links_data = links_data["Ближайшие связи"]

    for company_name, company_info in links_data.items():
        row_cells = table.add_row().cells

        # 1. Наименование и ИНН
        inn = company_info.get("Реквизиты", {}).get("ИНН", "")
        row_cells[0].text = f"{company_name}\nИНН: {inn}"

        # 2. Генеральный директор
        gen_dir = company_info.get("Генеральный директор", "").strip(", ")
        row_cells[1].text = gen_dir

        # 3. Участники
        participants = company_info.get("Участники", [])
        formatted_participants = "\n".join(
            f"{i + 1}) {p.strip('► ').strip()}" for i, p in enumerate(participants)
        )
        row_cells[2].text = formatted_participants

        # 4. Адрес
        row_cells[3].text = company_info.get("Адрес", "")

        # 5. Взаимосвязь — пусто или логика
        row_cells[4].text = ""


def fill_table6(table, data: dict):
    """Заполнение таблицы 6 — Сведения о размере основных средств и дебиторской задолженности"""
    values = data.get("Основные средства и дебиторка", {})
    fixed_assets = values.get("Основные средства", {})
    receivables = values.get("Дебиторская задолженность", {})

    # Получаем список годов и значений
    year_map = {}  # year: column_index

    years = []
    for key in ['year_3', 'year_2', 'year_1']:
        y_fixed = fixed_assets.get(key, {})
        y_receiv = receivables.get(key, {})

        year = next(iter(y_fixed or y_receiv), None)
        if year:
            years.append(year)

    # Заполняем заголовки
    for col_idx, year in enumerate(years):
        if col_idx + 1 < len(table.columns):
            table.cell(0, col_idx + 1).text = year
            year_map[year] = col_idx + 1  # столбец, начиная с 1 (т.к. 0 — метка строки)

    # Заполнение строки "Размер основных средств"
    for key, year_data in fixed_assets.items():
        for year, val in year_data.items():
            col = year_map.get(year)
            if col:
                table.cell(1, col).text = f"{int(val):,}".replace(",", " ") + " руб."

    # Заполнение строки "Дебиторская задолженность"
    for key, year_data in receivables.items():
        for year, val in year_data.items():
            col = year_map.get(year)
            if col:
                table.cell(2, col).text = f"{int(val):,}".replace(",", " ") + " руб."

def fill_table8(table, data: dict):
    """Заполнение таблицы 8 — Сведения о залогах (Залогодержатель, дата, срок, имущество)"""
    items = data.get("Сведения о залогах", [])

    # Удаляем все строки, кроме заголовка
    while len(table.rows) > 1:
        table._tbl.remove(table.rows[1]._tr)

    for idx, item in enumerate(items, 1):
        row = table.add_row().cells
        row[0].text = str(idx)
        row[1].text = item.get("Залогодержатель", "")
        row[2].text = item.get("Дата залога", "")
        row[3].text = item.get("Срок залога", "") or ""
        row[4].text = item.get("Заложенное имущество", "") or ""


def fill_table9(table, data: dict):
    """Заполнение таблицы 9 — Сведения о лизинге с подстановкой если лизингодатель отсутствует"""
    leasers = data.get("Сведения о лизинге", [])

    if not isinstance(leasers, list):
        print("ОШИБКА: Сведения о лизинге не являются списком.")
        return

    # Удаляем все строки кроме заголовка
    while len(table.rows) > 1:
        table._tbl.remove(table.rows[1]._tr)

    for idx, lease in enumerate(leasers, start=1):
        if not isinstance(lease, dict):
            continue

        row_cells = table.add_row().cells

        row_cells[0].text = str(idx)

        # Если нет значения — подставляем формулировку
        leaser = lease.get("Лизингодатель", "").strip()
        row_cells[1].text = leaser if leaser else "Сведения о лизингодателе отсутствуют"

        row_cells[2].text = lease.get("Период лизинга", "")
        row_cells[3].text = lease.get("Категория", "")
        row_cells[4].text = lease.get("Текущий статус", "")


def fill_table10(table, data):
    """
    Заполняет таблицу 'Сведения о размере кредиторской задолженности по бух. балансу'.
    """
    if not isinstance(data, dict):
        raise ValueError("Ожидается словарь для 'Кредиторская задолженность'")

    year_data = {}
    for key in ['year_1', 'year_2', 'year_3']:
        year_data.update(data.get(key, {}))

    if not year_data:
        raise ValueError("Нет данных для заполнения кредиторской задолженности")

    # Сортируем года по возрастанию
    sorted_years = sorted(year_data.keys())

    # Обработка максимум 3 лет (если больше — игнорируем)
    for col_idx, year in enumerate(sorted_years[:3], start=1):
        if col_idx >= len(table.columns):
            break  # на случай неожиданной структуры
        table.cell(0, col_idx).text = str(year)
        value = year_data[year]
        table.cell(1, col_idx).text = f"{int(value):,} т.р.".replace(",", " ")


def fill_table13(table, data: dict):
    """Заполнение таблицы 13 — Отчет о финансовых результатах (без 'конец')"""
    fin_data = data.get("Отчет о финансовых результатах", {})

    all_years = set()
    normalized_data = {}

    # Преобразуем все ключи годов к числовому виду (строки типа '2021')
    for indicator, year_values in fin_data.items():
        normalized_data[indicator] = {}
        for raw_year, value in year_values.items():
            match = re.search(r"\d{4}", str(raw_year))
            if match:
                year = match.group(0)
                all_years.add(year)
                if value is not None:
                    normalized_data[indicator][year] = value

    sorted_years = sorted(all_years, key=int)

    # Вставляем заголовки: просто годы — 2020, 2021 и т.д.
    for col_idx, year in enumerate(sorted_years):
        if col_idx + 1 < len(table.columns):
            table.cell(0, col_idx + 1).text = year

    # Сопоставляем строки по названиям
    row_mapping = {}
    for row_idx in range(1, len(table.rows)):
        key = table.cell(row_idx, 0).text.strip()
        if key:
            row_mapping[key] = row_idx

    # Заполняем значения по годам и строкам
    for indicator, year_values in normalized_data.items():
        row_idx = row_mapping.get(indicator)
        if row_idx is None:
            continue
        for col_idx, year in enumerate(sorted_years):
            if col_idx + 1 < len(table.columns):
                value = year_values.get(year)
                if value is not None:
                    table.cell(row_idx, col_idx + 1).text = str(value)


def save_filled_doc(template_path: str, output_path: str, data: dict):
    """Основная функция для заполнения шаблона документа с отчетом об успешности вставки"""
    document = Document(template_path)
    status = {}

    try:
        fill_table1(document.tables[0], data)
        status["Краткое наименование"] = True
    except Exception as e:
        print("Ошибка при заполнении таблицы 1:", e)
        status["Краткое наименование"] = False

    try:
        fill_table2(document.tables[1], data)
        status["Сведения о сотрудниках"] = True
    except Exception as e:
        print("Ошибка при заполнении таблицы 2:", e)
        status["Сведения о сотрудниках"] = False

    try:
        fill_table4(document.tables[3], data)
        status["О залоге долей"] = True
    except Exception as e:
        print("Ошибка при заполнении таблицы 4:", e)
        status["О залоге долей"] = False

    try:
        fill_table5(document.tables[4], data)
        status["Ближайшие связи"] = True
    except Exception as e:
        print("Ошибка при заполнении таблицы 5:", e)
        status["Ближайшие связи"] = False

    try:
        fill_table6(document.tables[5], data)
        status["Основные средства и дебиторка"] = True
    except Exception as e:
        print("Ошибка при заполнении таблицы 6:", e)
        status["Основные средства и дебиторка"] = False

    try:
        fill_table8(document.tables[7], data)
        status["Сведения о залогах"] = True
    except Exception as e:
        print("Ошибка при заполнении таблицы 8:", e)
        status["Сведения о залогах"] = False

    try:
        fill_table9(document.tables[8], data)
        status["Сведения о лизинге"] = True
    except Exception as e:
        print("Ошибка при заполнении таблицы 9:", e)
        status["Сведения о лизинге"] = False

    try:
        fill_table10(document.tables[10], data.get("Кредиторская задолженность", {}))
        status["Кредиторская задолженность"] = True
    except Exception as e:
        print("Ошибка при заполнении таблицы 10:", e)
        status["Кредиторская задолженность"] = False

    try:
        fill_table13(document.tables[12], data)
        status["Отчет о финансовых результатах"] = True
    except Exception as e:
        print("Ошибка при заполнении таблицы 13:", e)
        status["Отчет о финансовых результатах"] = False

    # Конкурсный управляющий (если есть)
    if data.get("Конкурсный управляющий", {}).get("ФИО") or data.get("Конкурсный управляющий", {}).get("ИНН"):
        status["Конкурсный управляющий"] = True
    else:
        status["Конкурсный управляющий"] = False

    document.save(output_path)

    # Вывод отчета
    print("\nДОБАВЛЕНИЕ В ШАБЛОН:")
    for section in [
        "Краткое наименование",
        "Сведения о сотрудниках",
        "Учредители/участники",
        "Сведения о залогах",
        "Сведения о лизинге",
        "Кредиторская задолженность",
        "Отчет о финансовых результатах",
        "Основные средства и дебиторка",
        "Конкурсный управляющий",
        "Ближайшие связи",
        "О залоге долей",
    ]:
        mark = "✅" if status.get(section, False) else "❌"
        print(f"{section}: {mark}")
