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


def normalize_company_name(full_name: str) -> str:
    if "Общество с ограниченной ответственностью" in full_name:
        return full_name.replace("Общество с ограниченной ответственностью", "ООО").strip()
    return full_name.strip()

def extract_from_word(path):
    """Извлекает базовые сведения из таблиц Word-документа Контур.Фокус."""
    doc = Document(path)
    data = {}

    try:
        table1 = doc.tables[0]
        table2 = doc.tables[1]

        raw_name = table1.cell(0, 1).text.strip()
        data["Организация"] = normalize_company_name(raw_name)

        data["Дата создания"] = table1.cell(0, 2).text.strip()
        data["ИНН"] = table1.cell(14, 1).text.strip()
        data["КПП"] = table1.cell(15, 1).text.strip()
        data["ОГРН"] = table1.cell(16, 1).text.strip()
        data["Юр. адрес"] = table1.cell(20, 1).text.strip()
        data["Уставный капитал"] = table1.cell(40, 1).text.strip()
        data["Директор"] = table1.cell(36, 1).text.strip()
        data["ОКВЭД"] = table2.cell(2, 1).text.strip()
        data["Учредители"] = table1.cell(2, 2).text.strip()

    except Exception as e:
        print(f"❌ Ошибка при извлечении из Word: {e}")

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
