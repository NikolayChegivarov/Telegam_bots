import os
from utils.parsing_docx import parsing_all_docx
from utils.parsing_exсel import parsing_excel_file
from utils.parsing_pdf import parsing_all_pdf


def extract_structured_data(word_path, pdf_path, excel_path):
    """
    Извлекает и объединяет данные из трех файлов в единый словарь, готовый для шаблона.
    """
    print("Начинаем парсинг.")

    data_docx = parsing_all_docx(word_path) if word_path else {}
    print("Данные из .docx файла собраны")

    data_pdf = parsing_all_pdf(pdf_path) if pdf_path else {}
    print("Данные из PDF файла собраны")

    # Получим ИНН из Word-данных, если он там есть
    company_inn = data_docx.get("ИНН", None)
    data_excel = parsing_excel_file(excel_path, company_inn) if excel_path else {}
    print("Данные из .xlsx файла собраны")

    combined = {}

    # Объединяем все данные
    for data in (data_docx, data_pdf, data_excel):
        for key, val in data.items():
            if key in combined and isinstance(val, dict) and isinstance(combined[key], dict):
                combined[key].update(val)
            else:
                combined[key] = val

    # Печатаем финальные данные в читабельной форме
    from pprint import pprint
    print("\nПолучили данные с 3х файлов:")
    pprint(combined)

    return combined
