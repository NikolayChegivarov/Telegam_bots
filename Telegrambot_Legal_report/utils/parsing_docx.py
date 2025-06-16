from docx import Document
from docx.shared import Parented
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import os
import re

def extract_inn_ogrn(text):
    """Извлекает ИНН и ОГРН из строки и возвращает очищенный текст без ИНН/ОГРН, а также отдельные значения."""
    inn_match = re.search(r'\bИНН[\s:\xa0]*([0-9]{10,12})\b', text)
    ogrn_match = re.search(r'\bОГРН[\s:\xa0]*([0-9]{13})\b', text)

    inn = inn_match.group(1) if inn_match else ''
    ogrn = ogrn_match.group(1) if ogrn_match else ''

    # Удалим из строки все фрагменты с ИНН и ОГРН
    cleaned_text = re.sub(r'ИНН[\s:\xa0]*[0-9]{10,12}', '', text)
    cleaned_text = re.sub(r'ОГРН[\s:\xa0]*[0-9]{13}', '', cleaned_text)
    cleaned_text = cleaned_text.strip(" ,–—\u2002")

    return cleaned_text, inn, ogrn


def extract_text_from_cell(cell):
    """Извлекает и объединяет текст из всех непустых параграфов ячейки."""
    return '\n'.join(
        paragraph.text.strip()
        for paragraph in cell.paragraphs
        if paragraph.text.strip()
    ).strip()


def extract_text_without_strikethrough(paragraph):
    """Извлекает текст из параграфа, исключая зачеркнутые части."""
    return ''.join(run.text for run in paragraph.runs if not is_strikethrough(run))


def is_strikethrough(run):
    """Проверяет, является ли текст зачеркнутым."""
    if run.font.strike:
        return True
    rPr = run._element.get_or_add_rPr()
    strike = rPr.find(qn('w:strike'))
    if strike is not None and strike.get(qn('w:val')) != '0':
        return True
    return False


def extract_competitive_manager(doc):
    """Извлекает информацию о конкурсном управляющем из таблиц документа."""
    target_keys = [
        "Исполняющий обязанности конкурсного управляющего",
        "Конкурсный управляющий"
    ]

    for table in doc.tables:
        for row in table.rows:
            if len(row.cells) < 2:
                continue

            key = extract_text_from_cell(row.cells[0])
            value = extract_text_from_cell(row.cells[1])

            if any(target.lower() in key.lower() for target in target_keys):
                return split_director_info(value)

    return {'ФИО': '', 'ИНН': ''}


def split_director_info(text):
    """Возвращает словарь с ФИО и ИНН, очищает пробелы и неразрывные пробелы."""
    cleaned = re.sub(r'[\u00A0\s]', '', text)  # удаляем пробелы и неразрывные пробелы
    match = re.search(r'(\d{10}|\d{12})', cleaned)

    if match:
        inn = match.group(1)
        # найти, где начинается ИНН, и отрезать всё до него для ФИО
        raw_fio = text[:text.find('ИНН')].strip(' ,')
        return {'ФИО': raw_fio, 'ИНН': inn}
    else:
        return {'ФИО': text.strip(), 'ИНН': ''}


def clean_sum_text(sum_text):
    """Приводит сумму к формату '1000000,00' (без пробелов, символов валюты и прочего текста)."""
    if not sum_text:
        return ''
    cleaned = sum_text.replace('\xa0', '').replace(' ', '')
    cleaned = re.sub(r'руб(\.|ль)?|р\.|₽', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[^\d,]', '', cleaned)
    cleaned = cleaned.replace('.', ',')
    if cleaned.count(',') > 1:
        first = cleaned.find(',')
        cleaned = cleaned[:first + 1] + cleaned[first + 1:].replace(',', '')
    return cleaned


def extract_first_address_block(full_address: str) -> str:
    """
    Извлекает только первый логически завершённый адресный блок из полной строки.
    Предполагается, что новые блоки начинаются с нового индекса (например, 115280).
    """
    match = list(re.finditer(r'\b1\d{5}\b', full_address))  # ищем все индексы

    if len(match) >= 2:
        return full_address[:match[1].start()].rstrip(', ')
    return full_address.strip(', ')


def extract_basic_info(doc):
    """Извлекает основную информацию о компании из документа."""
    basic_info = {
        'Краткое наименование': '',
        'ИНН': '',
        'КПП': '',
        'ОГРН': '',
        'Дата образования': '',
        'Юридический адрес': [],
        'Уставный капитал': '',
        'Генеральный директор': '',
        'ОКВЭД(основной)': ''
    }

    for table in doc.tables:
        for row in table.rows:
            if len(row.cells) < 2:
                continue

            key = extract_text_from_cell(row.cells[0])
            value = extract_text_from_cell(row.cells[1])

            if not key and not value:
                continue

            if "Краткое наименование" in key:
                basic_info['Краткое наименование'] = value
            elif key == "ИНН":
                basic_info['ИНН'] = value
            elif key == "КПП":
                basic_info['КПП'] = value
            elif key == "ОГРН":
                basic_info['ОГРН'] = value
            elif key == "Дата образования":
                basic_info['Дата образования'] = value
            elif "Юр. адрес" in key or "Юридический адрес" in key:
                if value:
                    basic_info['Юридический адрес'].extend(value.split('\n'))
            elif "Уставный капитал" in key:
                basic_info['Уставный капитал'] = value
            elif "Генеральный директор" in key:
                basic_info['Генеральный директор'] = split_director_info(value)
            elif "Основной вид деятельности" in key:
                basic_info['ОКВЭД(основной)'] = value

    raw_address = ', '.join(
        addr.strip() for addr in basic_info['Юридический адрес'] if addr.strip())
    basic_info['Юридический адрес'] = extract_first_address_block(raw_address)

    return basic_info


def extract_staff_info(doc):
    """Извлекает информацию о сотрудниках: численность и среднюю зарплату."""
    staff_info = {
        'Среднесписочная численность': {'year_1': '', 'year_2': '', 'year_3': ''},
        'Средняя заработная плата': {'year_1': '', 'year_2': '', 'year_3': ''}
    }
    staff_years_count = {}
    staff_years_salary = {}

    for table in doc.tables:
        rows = table.rows
        i = 0
        while i < len(rows):
            cells = rows[i].cells
            key = extract_text_without_strikethrough(cells[0].paragraphs[0]).strip().lower() if cells[0].paragraphs else ''
            value = extract_text_without_strikethrough(cells[1].paragraphs[0]).strip() if len(cells) > 1 and cells[1].paragraphs else ''

            # Среднесписочная численность
            if 'среднесписоч' in key:
                text_block_count = value
                j = i + 1
                while j < len(rows):
                    next_key = extract_text_without_strikethrough(rows[j].cells[0].paragraphs[0]).strip().lower() if rows[j].cells[0].paragraphs else ''
                    next_value = extract_text_without_strikethrough(rows[j].cells[1].paragraphs[0]).strip() if len(rows[j].cells) > 1 and rows[j].cells[1].paragraphs else ''
                    if next_key:
                        break
                    text_block_count += "\n" + next_value
                    j += 1
                matches = re.findall(r'за\s+(\d{4}):\s*([0-9]+)', text_block_count)
                for year, val in matches:
                    staff_years_count[year] = val
                i = j
                continue

            # Средняя заработная плата
            elif 'средняя заработная плата' in key or 'среднемесячная заработная плата' in key:
                text_block_salary = value
                j = i + 1
                while j < len(rows):
                    next_key = extract_text_without_strikethrough(rows[j].cells[0].paragraphs[0]).strip().lower() if rows[j].cells[0].paragraphs else ''
                    next_value = extract_text_without_strikethrough(rows[j].cells[1].paragraphs[0]).strip() if len(rows[j].cells) > 1 and rows[j].cells[1].paragraphs else ''
                    if next_key:
                        break
                    text_block_salary += "\n" + next_value
                    j += 1
                matches = re.findall(r'за\s+(\d{4}):\s*([\d\s]+)', text_block_salary)
                for year, val in matches:
                    salary_clean = clean_sum_text(val)
                    staff_years_salary[year] = salary_clean
                i = j
                continue

            i += 1

    # Формируем словарь результата
    slots = ['year_1', 'year_2', 'year_3']
    for idx, year in enumerate(sorted(staff_years_count.keys(), reverse=True)[:3]):
        staff_info['Среднесписочная численность'][slots[idx]] = f"{{'{year}': '{staff_years_count[year]}'}}"

    for idx, year in enumerate(sorted(staff_years_salary.keys(), reverse=True)[:3]):
        staff_info['Средняя заработная плата'][slots[idx]] = f"{{'{year}': '{staff_years_salary[year]}'}}"

    return staff_info


def extract_founders(doc):
    """Извлекает информацию об учредителях, деля их на актуальных и неактуальных по зачеркнутости ФИО или отсутствию доли."""
    actual = []
    outdated = []

    for table in doc.tables:
        header = [extract_text_without_strikethrough(cell.paragraphs[0]).strip().lower()
                  for cell in table.rows[0].cells if cell.paragraphs]

        col_map = {'share': None, 'sum': None, 'name': None, 'date': None}
        for idx, text in enumerate(header):
            if 'доля' in text and '%' in text:
                col_map['share'] = idx
            elif 'руб' in text or 'вклад' in text or 'сумма' in text:
                col_map['sum'] = idx
            elif 'участник' in text or 'наименование' in text or 'фио' in text:
                col_map['name'] = idx
            elif 'дата' in text:
                col_map['date'] = idx

        if not all(col_map[k] is not None for k in ('share', 'sum', 'name')):
            continue

        i = 1
        while i < len(table.rows):
            row = table.rows[i]
            cells = row.cells

            def get_full_text(cell):
                return '\n'.join(p.text.strip() for p in cell.paragraphs if p.text.strip()).strip()

            def has_strikethrough(cell):
                for p in cell.paragraphs:
                    for run in p.runs:
                        if is_strikethrough(run) and run.text.strip():
                            return True
                return False

            share = get_full_text(cells[col_map['share']]) if col_map['share'] < len(cells) else ''
            summ = get_full_text(cells[col_map['sum']]) if col_map['sum'] < len(cells) else ''
            name_cell = cells[col_map['name']] if col_map['name'] < len(cells) else None
            name = get_full_text(name_cell) if name_cell else ''
            has_strike = has_strikethrough(name_cell) if name_cell else False
            date = get_full_text(cells[col_map['date']]) if col_map['date'] is not None and col_map['date'] < len(cells) else ''

            # Попытка взять дату из следующей строки
            if not date and i + 1 < len(table.rows):
                next_row = table.rows[i + 1]
                if next_row.cells and next_row.cells[0].paragraphs:
                    candidate = extract_text_without_strikethrough(next_row.cells[0].paragraphs[0]).strip()
                    if re.match(r'\d{2}\.\d{2}\.\d{4}', candidate):
                        date = candidate
                        i += 1

            name_clean, inn, _ = extract_inn_ogrn(name)
            full_name = f"{name_clean}, ИНН {inn}".strip(', ') if inn else name_clean

            # Формирование записи
            record = {
                "Доля в %": share,
                "Доля в руб": clean_sum_text(summ),
                "Наимен. и реквизиты": full_name,
                "Дата": date
            }

            if any(record.values()):
                # Критерий неактуальности: зачёркнут ИЛИ доля отсутствует/равна '–'
                if has_strike or share.strip() == '–' or not share.strip():
                    outdated.append(record)
                else:
                    actual.append(record)

            i += 1

    return {
        "Актуальные участники": actual,
        "Неактуальные участники": outdated
    }


def extract_collaterals(doc):
    """Извлекает информацию о залогах из таблиц с парами 'ключ-значение' и возвращает ключи на русском языке."""
    collaterals = []

    keys_map = {
        'Залогодатель': 'Залогодатель',
        'Залогодержатель': 'Залогодержатель',
        'Договор': 'Договор',
        'Срок исполнения': 'Срок исполнения',
        'Тип имущества': 'Тип имущества',
        'Описание': 'Описание',
    }

    date_regnum_pattern = re.compile(r'(\d{2}\.\d{2}\.\d{4})\s+([\d\-]+)')

    for table in doc.tables:
        collateral_entry = {
            'Дата': '',
            'Регистрационный номер': '',
            'Залогодатель': '',
            'Залогодержатель': '',
            'Договор': '',
            'Срок исполнения': '',
            'Тип имущества': '',
            'Описание': ''
        }

        for row in table.rows:
            cells = row.cells
            if len(cells) < 2:
                continue

            left = extract_text_without_strikethrough(cells[0].paragraphs[0]).strip() if cells[0].paragraphs else ''
            right = extract_text_without_strikethrough(cells[1].paragraphs[0]).strip() if cells[1].paragraphs else ''

            if not collateral_entry['Дата'] or not collateral_entry['Регистрационный номер']:
                date_match = date_regnum_pattern.search(left + ' ' + right)
                if date_match:
                    collateral_entry['Дата'] = date_match.group(1)
                    collateral_entry['Регистрационный номер'] = date_match.group(2)
                    continue

            for label in keys_map:
                if label.lower() in left.lower():
                    collateral_entry[label] = right
                    break

        if collateral_entry['Дата'] and (collateral_entry['Описание'] or collateral_entry['Залогодержатель']):
            collaterals.append(collateral_entry)

    return collaterals


def extract_leasing_info(doc):
    """Извлекает информацию о лизинге."""
    leasing_info_all = []
    for table in doc.tables:
        if len(table.columns) != 2 or len(table.rows) < 5:
            continue

        first_cell_text = extract_text_without_strikethrough(table.cell(0, 0).paragraphs[0]).strip()
        if not re.match(r'\d{2}\.\d{2}\.\d{4}', first_cell_text):
            continue

        data = {
            "Лизингодатель": "",
            "Период лизинга": "",
            "Категория": "",
            "Текущий статус": ""
        }

        for row in table.rows:
            key = extract_text_without_strikethrough(row.cells[0].paragraphs[0]).strip().lower()
            value = extract_text_without_strikethrough(row.cells[1].paragraphs[0]).strip()

            if key.startswith("лизингодатель"):
                if "Сведения скрыты" in value:
                    data["Лизингодатель"] = "Сведения скрыты"
                else:
                    name, inn, ogrn = extract_inn_ogrn(value)
                    data["Лизингодатель"] = f"{name}, ИНН {inn}, ОГРН {ogrn}".strip(', ')
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
    """Извлекает информацию о кредиторской задолженности."""
    for table in doc.tables:
        headers = [extract_text_without_strikethrough(cell.paragraphs[0]).lower()
                   for cell in table.rows[0].cells if cell.paragraphs]
        if (len(headers) >= 4
                and any('код' in h for h in headers)
                and sum(re.search(r'20\d{2}', h) is not None for h in headers) >= 2):

            debt_row = None
            for row in table.rows:
                if extract_text_without_strikethrough(row.cells[0].paragraphs[0]).strip().lower().startswith(
                        "кредиторская задолженность"):
                    debt_row = row
                    break

            if debt_row:
                year_val = {}
                for idx, cell in enumerate(headers):
                    year_match = re.search(r'(20\d{2})', cell)
                    if year_match and idx < len(debt_row.cells):
                        year = year_match.group(1)
                        value = extract_text_without_strikethrough(debt_row.cells[idx].paragraphs[0]).strip().replace(
                            ' ', '').replace('–', '0')
                        year_val[year] = value

                years_sorted = sorted(year_val.keys(), reverse=True)
                slots = ['year_1', 'year_2', 'year_3']
                res = {}
                for i, year in enumerate(years_sorted[:3]):
                    val = year_val[year]
                    res[slots[i]] = f"{{'{year}': '{val}'}}"
                return res
    return {'year_1': '', 'year_2': '', 'year_3': ''}


def extract_financial_results(doc):
    """Извлекает финансовые результаты."""
    financial_results = {}
    year_indices = {}
    last_years = []

    for table in doc.tables:
        header_row = table.rows[0]
        header_cells = [extract_text_without_strikethrough(cell.paragraphs[0]).strip()
                        for cell in header_row.cells if cell.paragraphs]
        temp_year_indices = {}

        for idx, text in enumerate(header_cells):
            match = re.match(r'конец\s*(20\d{2})', text.lower()) or re.match(r'(20\d{2})', text)
            if match:
                year = match.group(1)
                temp_year_indices[year] = idx

        if len(temp_year_indices) >= 2:
            for row in table.rows:
                first_cell = extract_text_without_strikethrough(row.cells[0].paragraphs[0]).strip().lower() if \
                row.cells[0].paragraphs else ''
                if 'выручка' in first_cell:
                    year_indices = temp_year_indices
                    break

        if year_indices:
            last_years = sorted(year_indices, reverse=True)[:4]
            for row in table.rows[1:]:
                if len(row.cells) < max(year_indices.values()) + 1:
                    continue

                row_name = extract_text_without_strikethrough(row.cells[0].paragraphs[0]).strip() if row.cells[
                    0].paragraphs else ''
                if not row_name:
                    continue

                values = {}
                for y in last_years:
                    idx = year_indices[y]
                    if idx < len(row.cells) and row.cells[idx].paragraphs:
                        val = extract_text_without_strikethrough(row.cells[idx].paragraphs[0]).strip().replace(' ',
                                                                                                               '').replace(
                            '–', '0')
                        values[y] = val

                if any(values.values()):
                    financial_results[row_name] = values
            break

    return financial_results


def extract_assets_and_receivables(doc):
    """Извлекает информацию об основных средствах и дебиторской задолженности."""
    result = {
        "Основные средства": {},
        "Дебиторская задолженность": {}
    }

    for table in doc.tables:
        header_cells = [extract_text_without_strikethrough(cell.paragraphs[0]).strip().lower()
                        for cell in table.rows[0].cells if cell.paragraphs]
        year_to_col = {}

        for idx, txt in enumerate(header_cells):
            m = re.search(r'конец\s*(20\d{2})', txt)
            if m:
                year_to_col[m.group(1)] = idx

        if len(year_to_col) >= 3:
            years_sorted = sorted(year_to_col.keys(), reverse=True)[:3]
            row_ос = None
            row_дебит = None

            for row in table.rows:
                first_cell = extract_text_without_strikethrough(row.cells[0].paragraphs[0]).strip().lower() if \
                row.cells[0].paragraphs else ''
                if first_cell == "основные средства":
                    row_ос = row
                if first_cell == "дебиторская задолженность":
                    row_дебит = row

            if row_ос and row_дебит:
                for i, year in enumerate(years_sorted):
                    idx = year_to_col[year]
                    val_os = extract_text_without_strikethrough(row_ос.cells[idx].paragraphs[0]).strip().replace(' ',
                                                                                                                 '').replace(
                        '–', '0') if idx < len(row_ос.cells) and row_ос.cells[idx].paragraphs else '0'
                    val_db = extract_text_without_strikethrough(row_дебит.cells[idx].paragraphs[0]).strip().replace(' ',
                                                                                                                    '').replace(
                        '–', '0') if idx < len(row_дебит.cells) and row_дебит.cells[idx].paragraphs else '0'
                    result["Основные средства"][f'year_{i + 1}'] = {year: val_os}
                    result["Дебиторская задолженность"][f'year_{i + 1}'] = {year: val_db}
                break

    return result


def parsing_all_docx(docx_path):
    """Основная функция для парсинга всего документа."""
    company_data = {
        'Краткое наименование': '',
        'ИНН': '',
        'КПП': '',
        'ОГРН': '',
        'Дата образования': '',
        'Юридический адрес': '',
        'Уставный капитал': '',
        'Генеральный директор': '',
        'Конкурсный управляющий': '',  # <== добавили ключ
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
        'Основные средства и дебиторка': {
            'Основные средства': {},
            'Дебиторская задолженность': {}
        }
    }

    if not os.path.isfile(docx_path):
        print(f"Файл '{docx_path}' не найден.")
        return company_data

    try:
        doc = Document(docx_path)

        # Извлечение данных
        basic_info = extract_basic_info(doc)
        staff_info = extract_staff_info(doc)
        founders = extract_founders(doc)
        collaterals = extract_collaterals(doc)
        leasing_info = extract_leasing_info(doc)
        credit_debt = extract_credit_debt(doc)
        financial_results = extract_financial_results(doc)
        assets_receivables = extract_assets_and_receivables(doc)
        competitive_manager = extract_competitive_manager(doc)

        # Объединение данных
        company_data.update(basic_info)
        company_data['Сведения о сотрудниках'] = staff_info
        company_data['Учредители/участники'] = extract_founders(doc)
        company_data['Сведения о залогах'] = collaterals
        company_data['Сведения о лизинге'] = leasing_info
        company_data['Кредиторская задолженность'] = credit_debt
        company_data['Отчет о финансовых результатах'] = financial_results
        company_data['Основные средства и дебиторка'] = assets_receivables
        company_data['Конкурсный управляющий'] = competitive_manager

    except Exception as e:
        print(f"Ошибка при обработке файла '{docx_path}': {e}")

    return company_data


if __name__ == "__main__":
    docx_path = os.path.join(os.path.dirname(__file__), "word.docx")
    result = parsing_all_docx(docx_path)
    from pprint import pprint

    pprint(result)