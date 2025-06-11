
# views_docs/views_word_file.py
from docx import Document
import os


def print_doc_structure(doc):
    """Выводит структуру документа в терминал"""
    print("\nСтруктура документа:")
    for table_idx, table in enumerate(doc.tables, 1):
        print(f"\nТаблица #{table_idx} - {len(table.rows)} строк, {len(table.columns)} столбцов")
        for row_idx, row in enumerate(table.rows, 1):
            for cell_idx, cell in enumerate(row.cells, 1):
                cell_text = cell.text.replace('\n', '\\n')
                print(f"Ячейка {row_idx}.{cell_idx}: '{cell_text}'")


if __name__ == "__main__":
    # Получаем путь к корневой директории проекта (на два уровня выше текущего файла)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(project_root, "шаблон.docx")

    if not os.path.exists(template_path):
        print(f"❌ Файл не найден: {template_path}")
        print("Убедитесь, что файл 'шаблон.docx' находится в корне проекта")
    else:
        try:
            document = Document(template_path)
            print_doc_structure(document)
        except Exception as e:
            print(f"❌ Ошибка при открытии документа: {e}")