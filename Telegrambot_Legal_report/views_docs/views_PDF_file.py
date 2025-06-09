# views_docs/views_PDF_file.py
import os
import fitz  # PyMuPDF

def print_pdf_structure(pdf_path):
    """Выводит постраничное содержимое PDF-документа"""
    try:
        doc = fitz.open(pdf_path)
        print(f"Файл содержит {len(doc)} страниц\n")

        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text")
            print(f"Страница {page_number}:\n{text}\n{'-'*40}")

        doc.close()
    except Exception as e:
        print(f"❌ Ошибка при работе с PDF: {e}")

if __name__ == "__main__":
    pdf_path = os.path.join(os.path.dirname(__file__), "pdf.pdf")

    if not os.path.exists(pdf_path):
        print(f"❌ Файл не найден: {pdf_path}")
    else:
        print_pdf_structure(pdf_path)