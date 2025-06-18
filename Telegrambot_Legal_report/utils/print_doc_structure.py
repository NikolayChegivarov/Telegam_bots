from docx import Document
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from pprint import pprint
import os


def iter_block_items(parent):
    """
    Итерирует абзацы и таблицы внутри документа или ячейки.
    """
    for child in parent.element.body.iterchildren():
        if child.tag.endswith('}p'):
            yield Paragraph(child, parent)
        elif child.tag.endswith('}tbl'):
            if isinstance(parent, _Cell):
                yield parent._tbl(child)  # для ячеек
            else:
                yield Table(child, parent)  # для документа


def describe_paragraph(paragraph, context='вне таблицы'):
    style_name = paragraph.style.name if paragraph.style else 'Без стиля'
    return {
        "type": "paragraph",
        "context": context,
        "style": style_name,
        "text": paragraph.text.strip()
    }


def describe_table(table, table_index):
    table_info = {
        "type": "table",
        "table_index": table_index,
        "rows": []
    }

    for row_idx, row in enumerate(table.rows):
        row_info = []
        for cell_idx, cell in enumerate(row.cells):
            cell_info = {
                "cell_index": cell_idx,
                "paragraphs": []
            }
            for para_idx, para in enumerate(cell.paragraphs):
                style_name = para.style.name if para.style else 'Без стиля'
                cell_info["paragraphs"].append({
                    "paragraph_index": para_idx,
                    "style": style_name,
                    "text": para.text.strip()
                })
            row_info.append(cell_info)
        table_info["rows"].append(row_info)

    return table_info


def extract_structure(doc_path):
    doc = Document(doc_path)
    structure = []

    table_counter = 0
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            structure.append(describe_paragraph(block))
        elif isinstance(block, Table):
            structure.append(describe_table(block, table_counter))
            table_counter += 1

    return structure


def print_structure(structure):
    pprint(structure, width=160)


if __name__ == "__main__":
    filename = "word.docx"
    if not os.path.exists(filename):
        print(f"❌ Файл '{filename}' не найден в текущей директории.")
    else:
        doc_structure = extract_structure(filename)
        print_structure(doc_structure)
