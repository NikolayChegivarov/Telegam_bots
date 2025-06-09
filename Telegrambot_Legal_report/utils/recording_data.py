import os
from docx import Document

def generate_filename(data: dict) -> str:
    """
    Генерирует имя файла отчета на основе названия организации.
    Пример: "ООО Новые Технологии.docx"
    """
    org_name = data.get('org_name', 'report')
    safe_name = "".join(c for c in org_name if c.isalnum() or c in (' ', '_')).rstrip()
    return f"{safe_name}.docx"


def save_filled_doc(template_path: str, output_path: str, data: dict):
    if not os.path.exists(template_path):
        raise FileNotFoundError("❌ Не обнаружен шаблон.docx")
    document = Document(template_path)

    table = document.tables[0]  # Первая таблица

    # Сопоставление ключей из data и текста в ячейке таблицы
    FIELD_MAPPING = {
        'Полное наименование': 'Полное наименование',
        'Краткое наименование': 'Краткое наименование',
        'ИНН': 'ИНН',
        'КПП': 'КПП',
        'ОГРН': 'ОГРН',
        'Дата образования': 'Дата образования',
        'Юр. адрес': 'Юр. адрес',
        'Генеральный директор': 'Генеральный директор',
        # ... добавить другие поля по мере необходимости
    }

    for row in table.rows:
        field = row.cells[0].text.strip()
        if field in FIELD_MAPPING:
            key = FIELD_MAPPING[field]
            value = data.get(key, "")
            # Заполняем значение во второй ячейке (index 1)
            row.cells[1].text = str(value)

    document.save(output_path)

