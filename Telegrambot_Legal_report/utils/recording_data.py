import os
from docx import Document
from history.history_manager import write_to_history


def process_template(template_path: str, output_dir: str, org_data: dict) -> str | None:
    if not os.path.exists(template_path):
        print(f"❌ ОШИБКА: Файл шаблона не найден: {template_path}")
        return False

    try:
        doc = Document(template_path)
    except Exception:
        return None

    # Первая таблица шаблона — "Общие сведения"
    try:
        table = doc.tables[0]
        table.cell(0, 1).text = org_data.get('Организация', '—')
        table.cell(1, 1).text = org_data.get('ОГРН', '—')
        table.cell(2, 1).text = f"{org_data.get('ИНН', '')}/{org_data.get('КПП', '')}"
        table.cell(3, 1).text = org_data.get('Юр. адрес', '—')
        table.cell(4, 1).text = org_data.get('Дата создания', '—')
        table.cell(5, 1).text = org_data.get('Учредители', '—')
        table.cell(6, 1).text = org_data.get('Уставный капитал', '—')
        table.cell(7, 1).text = org_data.get('Директор', '—')
        table.cell(8, 1).text = org_data.get('ОКВЭД', '—')
        table.cell(9, 1).text = org_data.get('Система налогообложения', '—')
    except Exception:
        return None

    os.makedirs(output_dir, exist_ok=True)

    clean_name = "".join(c for c in org_data.get("Организация", "Отчет") if c.isalnum() or c in (' ', '_', '-')).strip()
    filename = f"{clean_name[:50]}.docx"
    output_path = os.path.join(output_dir, filename)

    try:
        doc.save(output_path)
        write_to_history(org_data.get("Организация", "Неизвестная организация"))
        return output_path
    except Exception:
        return None
