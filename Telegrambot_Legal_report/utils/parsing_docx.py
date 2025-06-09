# Функции для парсинга документа Выгрузка Контур Фокус .docx
from docx import Document
import os
import re

def extract_founders(doc):
    founders = []
    for table in doc.tables:
        header = [cell.text.strip().lower() for cell in table.rows[0].cells]
        if (
            "доля в %" in header[0]
            and "доля в руб." in header[1]
            and "наименование" in header[2]
        ):
            i = 1
            while i < len(table.rows):
                row = table.rows[i]
                cells = row.cells
                if len(cells) >= 3 and cells[0].text.strip():
                    share = cells[0].text.strip()
                    summ = cells[1].text.strip()
                    name = cells[2].text.strip()
                    date = ''
                    if len(cells) >= 4:
                        date = cells[3].text.strip()
                    elif i + 1 < len(table.rows):
                        next_row = table.rows[i + 1]
                        if (
                            len(next_row.cells) >= 4 and
                            not next_row.cells[0].text.strip() and
                            not next_row.cells[1].text.strip() and
                            not next_row.cells[2].text.strip()
                        ):
                            date = next_row.cells[3].text.strip()
                        elif (
                            len(next_row.cells) >= 1 and
                            re.match(r'\d{2}\.\d{2}\.\d{4}', next_row.cells[0].text.strip())
                        ):
                            date = next_row.cells[0].text.strip()
                    founders.append({
                        "share": share,
                        "sum": summ,
                        "name": name,
                        "date": date,
                    })
                i += 1
    return founders

def extract_collaterals_text(doc):
    collaterals = []
    all_text = []
    for para in doc.paragraphs:
        all_text.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                all_text.append(cell.text)
    text = '\n'.join(all_text)

    collateral_pattern = re.compile(
        r'(?P<date>\d{2}\.\d{2}\.\d{4})\s+(?P<regnum>\S+)\s*'
        r'(?:\s*Залогодатель[^\n]*\n(?P<pledger>.*?)\n)?'
        r'(?:\s*Залогодержатель[^\n]*\n(?P<holder>.*?)\n)?'
        r'(?:\s*Договор[^\n]*\n(?P<contract>.*?)\n)?'
        r'(?:\s*Срок исполнения[^\n]*\n(?P<term>.*?)\n)?'
        r'(?:\s*Тип имущества[^\n]*\n(?P<asset_type>.*?)\n)?'
        r'(?:\s*Описание[^\n]*\n(?P<asset>.*?))'
        r'(?:\n{2,}|$)',  # конец блока — две пустые строки или конец
        re.DOTALL | re.MULTILINE
    )

    for m in collateral_pattern.finditer(text):
        entry = {
            'date': m.group('date').strip() if m.group('date') else '',
            'regnum': m.group('regnum').strip() if m.group('regnum') else '',
            'pledger': m.group('pledger').strip() if m.group('pledger') else '',
            'holder': m.group('holder').strip() if m.group('holder') else '',
            'contract': m.group('contract').strip() if m.group('contract') else '',
            'term': m.group('term').strip() if m.group('term') else '',
            'asset_type': m.group('asset_type').strip() if m.group('asset_type') else '',
            'asset': m.group('asset').strip() if m.group('asset') else '',
        }
        entry['asset'] = re.split(r'\n\d{2}\.\d{2}\.\d{4}\s+\S+', entry['asset'])[0].strip()
        if entry['date'] and (entry['holder'] or entry['asset']):
            collaterals.append(entry)
    return collaterals

def extract_leasing_info(doc):
    """Информация по лизингу."""
    leasing_info_all = []
    for table in doc.tables:
        if len(table.columns) != 2 or len(table.rows) < 5:
            continue
        first_cell = table.cell(0, 0).text.strip()
        if not re.match(r'\d{2}\.\d{2}\.\d{4}', first_cell):
            continue
        data = {
            "Лизингодатель": "",
            "Период лизинга": "",
            "Категория": "",
            "Текущий статус": ""
        }
        for row in table.rows:
            key = row.cells[0].text.strip().lower()
            value = row.cells[1].text.strip()
            if key.startswith("лизингодатель"):
                if "Сведения скрыты" in value:
                    data["Лизингодатель"] = "Сведения скрыты"
                else:
                    data["Лизингодатель"] = value.split("— ИНН")[0].strip() or value.strip()
            elif key.startswith("период лизинга"):
                data["Период лизинга"] = value
            elif key.startswith("категория"):
                data["Категория"] = value
            elif key.startswith("статус"):
                data["Текущий статус"] = value.split('\n')[0].strip()
        if data["Лизингодатель"] or data["Категория"]:
            leasing_info_all.append(data)

    not_finished = [
        x for x in leasing_info_all
        if 'завершился' not in x.get('Текущий статус', '').lower()
    ]
    if not leasing_info_all:
        return ["Информации по лизингу нет"]
    if not not_finished:
        return ["Информации по лизингу со статусом 'Действует' нет"]
    return not_finished

def extract_credit_debt(doc):
    """
    Извлекает кредиторскую задолженность из балансовой таблицы за последние 3 года.
    """
    for table in doc.tables:
        headers = [cell.text.lower() for cell in table.rows[0].cells]
        # Ориентируемся на таблицу с 4+ годами, в первой строке должны быть коды (второй столбец) и года
        if (
            len(headers) >= 4
            and any('код' in h for h in headers)
            and sum(re.search(r'20\d{2}', h) is not None for h in headers) >= 2
        ):
            debt_row = None
            for row in table.rows:
                if row.cells[0].text.strip().lower().startswith("кредиторская задолженность"):
                    debt_row = row
                    break
            if debt_row:
                # Собираем года и значения
                year_val = {}
                for idx, cell in enumerate(headers):
                    year_match = re.search(r'(20\d{2})', cell)
                    if year_match and idx < len(debt_row.cells):
                        year = year_match.group(1)
                        value = debt_row.cells[idx].text.strip().replace(' ', '').replace('–','0')
                        year_val[year] = value
                # Берём 3 последних года
                years_sorted = sorted(year_val.keys(), reverse=True)
                slots = ['year_1', 'year_2', 'year_3']
                res = {}
                for i, year in enumerate(years_sorted[:3]):
                    val = year_val[year]
                    res[slots[i]] = f"{{'{year}': '{val}'}}"
                return res
    # Если не нашли — возвращаем пустые строки
    return {'year_1': '', 'year_2': '', 'year_3': ''}


def extract_financial_results(doc):
    """
    Извлекает отчет о финансовых результатах за последние 4 года из таблицы с отчетом.
    Формирует результат: { 'Выручка': {'2024': ..., '2023': ..., ...}, ... }
    """
    financial_results = {}
    year_indices = {}
    last_years = []

    # Перебираем все таблицы и ищем заголовки с годами
    for table in doc.tables:
        header_row = table.rows[0]
        header_cells = [cell.text.strip() for cell in header_row.cells]
        # Определяем индексы годов в первой строке (ищем четыре последних года)
        temp_year_indices = {}
        for idx, text in enumerate(header_cells):
            match = re.match(r'конец\s*(20\d{2})', text.lower()) or re.match(r'(20\d{2})', text)
            if match:
                year = match.group(1)
                temp_year_indices[year] = idx
        # Таблица отчета — если в ней есть 2+ года и есть строка 'выручка'
        if len(temp_year_indices) >= 2:
            # Смотрим есть ли строка "выручка"
            for row in table.rows:
                first_cell = row.cells[0].text.strip().lower()
                if 'выручка' in first_cell:
                    year_indices = temp_year_indices
                    break
        if year_indices:
            # Нашли таблицу, собираем года (4 последних, если есть)
            last_years = sorted(year_indices, reverse=True)[:4]
            # Собираем все строки с названиями и значениями по годам
            for row in table.rows[1:]:
                if len(row.cells) < max(year_indices.values()) + 1:
                    continue
                row_name = row.cells[0].text.strip()
                if not row_name:
                    continue
                values = {}
                for y in last_years:
                    idx = year_indices[y]
                    val = row.cells[idx].text.strip().replace(' ', '').replace('–', '0')
                    values[y] = val
                if any(values.values()):
                    financial_results[row_name] = values
            break
    return financial_results


def extract_assets_and_receivables(doc):
    """
    Извлекает данные по Основным средствам и Дебиторской задолженности за последние 3 года.
    """
    result = {
        "Основные средства": {},
        "Дебиторская задолженность": {}
    }
    for table in doc.tables:
        header_cells = [cell.text.strip().lower() for cell in table.rows[0].cells]
        # определяем индексы годов
        year_to_col = {}
        for idx, txt in enumerate(header_cells):
            m = re.search(r'конец\s*(20\d{2})', txt)
            if m:
                year_to_col[m.group(1)] = idx
        # нужно хотя бы 3 последних года
        if len(year_to_col) >= 3:
            years_sorted = sorted(year_to_col.keys(), reverse=True)[:3]  # последние 3 года
            # ищем нужные строки
            row_ос = None
            row_дебит = None
            for row in table.rows:
                first_cell = row.cells[0].text.strip().lower()
                if first_cell == "основные средства":
                    row_ос = row
                if first_cell == "дебиторская задолженность":
                    row_дебит = row
            if row_ос and row_дебит:
                for i, year in enumerate(years_sorted):
                    idx = year_to_col[year]
                    val_os = row_ос.cells[idx].text.strip().replace(' ', '').replace('–','0')
                    val_db = row_дебит.cells[idx].text.strip().replace(' ', '').replace('–','0')
                    result["Основные средства"][f'year_{i+1}'] = {year: val_os}
                    result["Дебиторская задолженность"][f'year_{i+1}'] = {year: val_db}
                break
    return result



def parsing_all_docx(docx_path):
    company_docx = {
        'Краткое наименование': '',
        'ИНН': '',
        'КПП': '',
        'ОГРН': '',
        'Дата образования': '',
        'Юридический адрес': '',
        'Уставный капитал': '',
        'Генеральный директор': '',
        'Учредители/участники': [],
        'ОКВЭД(основной)': '',
        'Сведения о сотрудниках': {
            'Среднесписочная численность': {'year_1': '', 'year_2': '', 'year_3': ''},
            'Расходы на оплату труда': {'year_1': '', 'year_2': '', 'year_3': ''},
        },
        'Сведения о залогах': [],
        'Сведения о лизинге': [],
        'Кредиторская задолженность': {'year_1': '', 'year_2': '', 'year_3': ''},
        'Отчет о финансовых результатах': {},
    }

    if not os.path.isfile(docx_path):
        print(f"Файл '{docx_path}' не найден.")
        return company_docx
    print(f"Файл '{docx_path}' найден.")

    try:
        doc = Document(docx_path)
        staff_years = {}

        # --- Среднесписочная численность ---
        for table in doc.tables:
            rows = table.rows
            i = 0
            while i < len(rows):
                cells = rows[i].cells
                key = cells[0].text.strip()
                value = cells[1].text.strip() if len(cells) > 1 else ''
                if 'Среднесписоч' in key:
                    text_block = value
                    j = i + 1
                    while j < len(rows):
                        next_key = rows[j].cells[0].text.strip()
                        next_value = rows[j].cells[1].text.strip() if len(rows[j].cells) > 1 else ''
                        if next_key != '':
                            break
                        text_block += "\n" + next_value
                        j += 1
                    matches = re.findall(r'за (\d{4}):\s*([0-9]+)', text_block)
                    for year, val in matches:
                        staff_years[year] = val
                    i = j
                    continue
                if key == "Краткое наименование":
                    company_docx["Краткое наименование"] = value
                elif key == "ИНН":
                    company_docx["ИНН"] = value
                elif key == "КПП":
                    company_docx["КПП"] = value
                elif key == "ОГРН":
                    company_docx["ОГРН"] = value
                elif key == "Дата образования":
                    company_docx["Дата образования"] = value
                elif key in ["Юр. адрес", "Юридический адрес"]:
                    company_docx["Юридический адрес"] = value
                elif key == "Уставный капитал":
                    company_docx["Уставный капитал"] = value
                elif key == "Генеральный директор":
                    company_docx["Генеральный директор"] = value
                elif key == "Основной вид деятельности":
                    company_docx["ОКВЭД(основной)"] = value
                i += 1

        # --- Итог: года численности ---
        staff_years_sorted = sorted(staff_years, reverse=True)
        slots = ['year_1', 'year_2', 'year_3']
        staff_years_used = []
        for idx, year in enumerate(staff_years_sorted[:3]):
            val = staff_years[year]
            company_docx['Сведения о сотрудниках']['Среднесписочная численность'][slots[idx]] = f"{{'{year}': '{val}'}}"
            staff_years_used.append(year)

        # --- Расходы на оплату труда ---
        for table in doc.tables:
            header_row = None
            for row in table.rows:
                row_values = [cell.text.strip().lower() for cell in row.cells]
                if (
                    any('код' in cell for cell in row_values) and
                    sum(re.search(r'20\d{2}', cell) is not None for cell in row_values) >= 2
                ):
                    header_row = row
                    break

            if header_row:
                year_indices = {}
                for idx, cell in enumerate(header_row.cells):
                    match = re.search(r'(20\d{2})', cell.text)
                    if match:
                        year_indices[match.group(1)] = idx
                for row in table.rows:
                    first_cell = row.cells[0].text.strip().lower()
                    code_cell = row.cells[1].text.strip() if len(row.cells) > 1 else ''
                    if (
                        ('оплата труда работников' in first_cell or code_cell == '4122') and
                        len(row.cells) > 2
                    ):
                        year_to_val = {}
                        for year, idx in year_indices.items():
                            if idx < len(row.cells):
                                val = row.cells[idx].text.strip().replace(' ', '')
                                year_to_val[year] = val
                        used_years_sorted = [y for y in staff_years_used if y in year_to_val]
                        for slot, year in zip(slots, used_years_sorted):
                            val = year_to_val[year]
                            company_docx['Сведения о сотрудниках']['Расходы на оплату труда'][slot] = f"{{'{year}': '{val}'}}"
                        left_years = [y for y in sorted(year_to_val, reverse=True) if y not in used_years_sorted]
                        for slot in slots:
                            if not company_docx['Сведения о сотрудниках']['Расходы на оплату труда'][slot] and left_years:
                                year = left_years.pop(0)
                                val = year_to_val[year]
                                company_docx['Сведения о сотрудниках']['Расходы на оплату труда'][slot] = f"{{'{year}': '{val}'}}"
                        break

        company_docx['Учредители/участники'] = extract_founders(doc)

        company_docx['Сведения о залогах'] = extract_collaterals_text(doc)

        company_docx['Сведения о лизинге'] = extract_leasing_info(doc)

        company_docx['Кредиторская задолженность'] = extract_credit_debt(doc)

        company_docx['Отчет о финансовых результатах'] = extract_financial_results(doc)

        company_docx["Основные средства и дебиторка"] = extract_assets_and_receivables(doc)

        # print("Данные из .docx файла собраны")

    except Exception as e:
        print(f"Ошибка при обработке файла '{docx_path}': {e}")

    return company_docx


if __name__ == "__main__":
    docx_path = os.path.join(os.path.dirname(__file__), "word.docx")
    result = parsing_all_docx(docx_path)
    from pprint import pprint
    pprint(result)
