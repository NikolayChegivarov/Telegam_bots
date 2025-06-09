import os
import pandas as pd

def parsing_excel_file(excel_path, company_inn=None):
    """
    Парсит excel-файл и возвращает две таблицы:
    - 'prosuzhivaemaya' (анализируемая компания — истец/кредитор)
    - 'prosuzhennaya' (анализируемая компания — ответчик/должник)
    company_inn — ИНН анализируемой компании (строкой).
    """
    if not os.path.isfile(excel_path):
        raise FileNotFoundError(f"Файл не найден: {excel_path}")

    df = pd.read_excel(excel_path, dtype=str)
    df.fillna('', inplace=True)

    # Названия столбцов из твоего примера
    case_col = 'Номер дела'
    istets_col = 'Истец/Кредитор'
    istets_inn_col = 'ИНН Истца/Кредитора'
    otv_col = 'Ответчик/Должник'
    otv_inn_col = 'ИНН Ответчика/Должника'
    isk_col = 'Исковые требования'
    status_col = 'Статус дела'

    prosuzhivaemaya = []
    prosuzhennaya = []

    for i, row in df.iterrows():
        inn_istets = str(row[istets_inn_col]).strip()
        inn_otv = str(row[otv_inn_col]).strip()

        # Если ИНН компании — истец
        if company_inn and company_inn == inn_istets:
            prosuzhivaemaya.append({
                "№ Дела": row[case_col],
                "Ответчик": row[otv_col],
                "Исковые требования": row[isk_col],
                "Статус": row[status_col]
            })
        # Если ИНН компании — ответчик
        if company_inn and company_inn == inn_otv:
            prosuzhennaya.append({
                "№ Дела": row[case_col],
                "Ответчик": row[otv_col],
                "Исковые требования": row[isk_col],
                "Статус": row[status_col]
            })

    result = {
        "prosuzhivaemaya": prosuzhivaemaya,
        "prosuzhennaya": prosuzhennaya
    }
    return result

if __name__ == "__main__":
    excel_path = "excel.xlsx"  # Имя твоего файла
    company_inn = "5049021498"  # ИНН анализируемой компании
    result = parsing_excel_file(excel_path, company_inn)
    from pprint import pprint
    pprint(result)
