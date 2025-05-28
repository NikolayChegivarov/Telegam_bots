import os
from docx import Document
from history.history_manager import write_to_history


def process_template(template_path: str, output_dir: str, org_data: dict) -> str | None:
    """Записывает переданные данные в шаблон и сохраняет файл в указанную директорию."""
    if not os.path.exists(template_path):
        print(f"❌ Шаблон не найден: {template_path}")
        return None

    try:
        doc = Document(template_path)
    except Exception as e:
        print(f"❌ Ошибка при загрузке шаблона: {e}")
        return None

    # Обработка первой таблицы (базовые данные)
    try:
        table = doc.tables[0]
        table.cell(0, 1).text = org_data.get('Организация', '—')
        table.cell(1, 1).text = org_data.get('ОГРН', '—')
        table.cell(2, 1).text = f"{org_data.get('ИНН', '')}/{org_data.get('КПП', '')}"
    except Exception as e:
        print(f"❌ Ошибка при заполнении таблицы: {e}")
        return None

    # Создание выходной папки, если нужно
    os.makedirs(output_dir, exist_ok=True)

    # Имя файла по наименованию организации
    clean_name = "".join(c for c in org_data.get("Организация", "Отчет") if c.isalnum() or c in (' ', '_', '-')).strip()
    filename = f"{clean_name[:50]}.docx"
    output_path = os.path.join(output_dir, filename)

    try:
        doc.save(output_path)
        write_to_history(org_data.get("Организация", "Неизвестная организация"))
        return output_path
    except Exception as e:
        print(f"❌ Ошибка при сохранении файла: {e}")
        return None
