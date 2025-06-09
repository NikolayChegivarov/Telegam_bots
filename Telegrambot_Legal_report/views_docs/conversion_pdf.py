import os
import camelot
from tabulate import tabulate
import warnings
import sys
import contextlib

def extract_tables_from_pdf(pdf_path):
    """
    Извлекает все таблицы из PDF с помощью Camelot.
    """
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream', strip_text='\n')
    return tables

def print_tables(tables):
    """
    Выводит таблицы в консоль в красивом формате с помощью tabulate.
    """
    if not tables or tables.n == 0:
        print("❌ Таблицы не найдены.")
        return

    for i, table in enumerate(tables):
        print(f"\n--- TABLE {i+1} ---\n")
        df = table.df
        df = df.applymap(lambda x: x.replace('\n', ' ').replace('\r', ' ').strip() if isinstance(x, str) else x)
        print(tabulate(df, headers='keys', tablefmt='github', showindex=False))

def suppress_warnings():
    # Подавить все предупреждения Python
    warnings.filterwarnings("ignore")
    # Подавить предупреждения из camelot и PyPDF2
    os.environ["PYTHONWARNINGS"] = "ignore"

@contextlib.contextmanager
def suppress_stderr():
    """Контекстный менеджер для скрытия вывода в stderr."""
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr

def main():
    suppress_warnings()
    pdf_path = os.path.join(os.path.dirname(__file__), "pdf.pdf")
    if not os.path.exists(pdf_path):
        print(f"❌ Файл не найден: {pdf_path}")
        return

    with suppress_stderr():
        tables = extract_tables_from_pdf(pdf_path)
    print_tables(tables)

if __name__ == "__main__":
    main()
