# utils/extraction.py
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pprint import pprint


def extract_from_word(path):
    """Извлекает базовые сведения из таблиц Word-документа Контур.Фокус по содержимому ячеек с отчётностью."""
    doc = Document(path)
    data = {}

    # Ключевые слова и соответствующие им поля отчета
    keywords = {
        "Краткое наименование": "Организация",
        "ОГРН": "ОГРН",
        "ИНН": "ИНН",
        "КПП": "КПП",
        "Юр. адрес": "Юр. адрес",
        "Дата образования": "Дата образования",  # было "Дата создания"
        "Уставный капитал": "Уставный капитал",  # было "Размер уставного капитала"
        "Генеральный директор": "Директор",
        "Основной вид деятельности": "ОКВЭД",
        "Система налогообложения": "Система налогообложения",
        "Учредители": "Учредители и участники"
    }

    # Регистр-независимый список найденных ключей
    found_keys = set()

    for table in doc.tables:
        for row in table.rows:
            if len(row.cells) < 2:
                continue
            key_raw = row.cells[0].text.strip().replace('\xa0', ' ')
            value = row.cells[1].text.strip()
            for keyword, label in keywords.items():
                if keyword.lower() in key_raw.lower():
                    data[label] = value
                    found_keys.add(label)

    # Отчёт по каждому ключу
    print("\n🔍 Результаты извлечения:")
    for label in keywords.values():
        if label in data:
            print(f"✅ {label}: {data[label]}")
        else:
            print(f"❌ {label} не найден")

    return data


def extract_from_pdf(path):
    """Извлекает финансовые показатели из PDF-документа (Контур.Фокус)."""
    data = {}
    doc = fitz.open(path)
    full_text = "\n".join(page.get_text() for page in doc)
    doc.close()

    if "EBIT" in full_text:
        lines = full_text.splitlines()
        for i, line in enumerate(lines):
            if "EBIT" in line:
                try:
                    ebit_line = lines[i + 1]
                    data["EBIT"] = ebit_line.strip()
                except:
                    pass

    if "Чистая прибыль" in full_text:
        for line in full_text.splitlines():
            if "Чистая прибыль" in line:
                parts = line.split()
                for part in parts[::-1]:
                    if part.replace(',', '').replace('.', '').isdigit():
                        data["Чистая прибыль"] = part
                        break

    # print(data)
    return data


def extract_from_excel(path):
    """Извлекает дела истцов и ответчиков из Excel-документа."""
    data = {}
    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()

    istets = df[df['Роль'] == 'Истец'] if 'Роль' in df else pd.DataFrame()
    otvetchik = df[df['Роль'] == 'Ответчик'] if 'Роль' in df else pd.DataFrame()

    data["Истец_дела"] = istets.to_dict(orient="records")
    data["Ответчик_дела"] = otvetchik.to_dict(orient="records")

    # print(data)
    return data