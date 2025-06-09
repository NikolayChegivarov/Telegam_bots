# Для дальнейшего парсинга таблицы:
# Например, фильтрация по столбцу, анализ значений и пр.
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
    word_path = os.path.join(os.path.dirname(__file__), "word.docx")

    if not os.path.exists(word_path):
        print(f"❌ Файл не найден: {word_path}")
    else:
        try:
            document = Document(word_path)
            print_doc_structure(document)
        except Exception as e:
            print(f"❌ Ошибка при открытии документа: {e}")
