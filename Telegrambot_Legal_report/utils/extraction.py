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


def extract_from_word(file_path: str) -> dict:
    """Извлекает наименование организации, ИНН, КПП и ОГРН из документа. Возвращает словарь."""
    doc_text = get_doc_text(file_path)

    result = {'Организация': None, 'ОГРН': None, 'ИНН': None, 'КПП': None}

    org_match = re.search(r'^((?:ООО|АО|ЗАО|ИП|ПАО|ОАО)\s*["«][^"»]+["»])', doc_text)
    if org_match:
        result['Организация'] = org_match.group(1).strip()

    inn_match = re.search(r'ИНН[\s:–-]*(\d{10,12})', doc_text, re.IGNORECASE)
    if inn_match:
        result['ИНН'] = inn_match.group(1)

    kpp_match = re.search(r'КПП[\s:–-]*(\d{9})', doc_text, re.IGNORECASE)
    if kpp_match:
        result['КПП'] = kpp_match.group(1)

    ogrn_match = re.search(r'ОГРН[\s:–-]*(\d{13})', doc_text, re.IGNORECASE)
    if ogrn_match:
        result['ОГРН'] = ogrn_match.group(1)

    return result


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
