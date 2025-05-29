# utils/extraction.py
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
import re


def get_doc_text(file_path: str) -> str:
    """Извлекает весь текст из документа (параграфы + таблицы)."""
    doc = Document(file_path)
    full_text = []

    # Текст из параграфов
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            full_text.append(paragraph.text.strip())

    # Текст из таблиц
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    full_text.append(cell.text.strip())

    return '\n'.join(full_text)


# utils/extraction.py
from docx import Document


def extract_from_word(path):
    """Извлекает полную базовую информацию из Word-документа Контур.Фокус."""
    doc = Document(path)
    text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

    data = {}

    # Основные шаблонные ключи и значения
    mapping = {
        "Наименование": "Организация",
        "ОГРН": "ОГРН",
        "ИНН": "ИНН",
        "КПП": "КПП",
        "Юридический адрес": "Юр. адрес",
        "Дата создания": "Дата создания",
        "Размер уставного капитала": "Уставный капитал",
        "Генеральный директор": "Директор",
        "ОКВЭД": "ОКВЭД",
        "Система налогообложения": "Система налогообложения"
    }

    for paragraph in doc.paragraphs:
        for key, label in mapping.items():
            if paragraph.text.startswith(key):
                value = paragraph.text.split(":", 1)[-1].strip()
                if key == "ИНН" and "/" in value:
                    inn, kpp = value.split("/")
                    data["ИНН"] = inn.strip()
                    data["КПП"] = kpp.strip()
                else:
                    data[label] = value

    # Учредители (собираются списком)
    founders = []
    grab = False
    for p in doc.paragraphs:
        if "Учредители" in p.text or "Участники" in p.text:
            grab = True
        elif grab:
            if p.text.strip() == "":
                break
            founders.append(p.text.strip())

    data["Учредители"] = "\n".join(founders)

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
    return data
