import camelot
import os
import warnings
import contextlib
import sys
import re

def suppress_warnings():
    warnings.filterwarnings("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr

def split_multi_numbers(cell):
    """
    Делит строку с несколькими подряд числами на отдельные значения:
    '244668421183' -> ['244668', '421183']
    '244 668 421 183' -> ['244668', '421183']
    '244 668' -> ['244668']
    """
    if not isinstance(cell, str):
        return []
    cleaned = cell.replace('\xa0', '').replace('\n', ' ').replace('\r', ' ').replace(' ', '')
    # Если слеплены, разбиваем на куски по 6 или 5 цифр
    matches = re.findall(r'\d{6}|\d{5}', cleaned)
    # Если ничего не нашли — возможно, уже с пробелом: ищем стандартный вариант
    if not matches:
        matches = re.findall(r'\d{1,3} \d{3}', cell)
        matches = [m.replace(' ', '') for m in matches]
    return matches

def darsing_all_pdf(pdf_path):
    suppress_warnings()
    result = {
        "Основные средства и задолженность": {
            "основные средства": {},
            "дебиторская задолженность": {}
        }
    }
    found_osnovnye = {}
    found_debitor = {}

    with suppress_stderr():
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream', strip_text='\n')
    for table in tables:
        df = table.df
        df = df.applymap(lambda x: x.replace('\n', ' ').replace('\r', ' ').strip() if isinstance(x, str) else x)
        rows = df.values.tolist()
        # Найти годы (порядок)
        years = []
        for row in rows:
            for cell in row:
                for match in re.findall(r'31\.12\.(20\d\d)', cell.replace(" ", "")):
                    years.append(match)
            if len(years) >= 2:
                break
        if not years or len(years) < 2:
            years = ['2023', '2024']

        # --- Парсим "основные средства" ---
        for i in range(1, len(rows)):
            prev_row = rows[i-1]
            row = rows[i]
            if prev_row[0].strip().lower() == "в том числе: основные":
                # Следующая строка: значения во 2 и 3 столбце
                if len(row) > 2 and row[0].strip() == "":
                    num1 = row[1].replace(' ', '').replace('\xa0', '')
                    num2 = row[2].replace(' ', '').replace('\xa0', '')
                    if num1.isdigit() and num2.isdigit():
                        found_osnovnye[years[0]] = num1
                        found_osnovnye[years[1]] = num2
                        break

        # --- Парсим "дебиторская задолженность" ---
        for row in rows:
            row_str = " ".join(row).lower()
            if "дебиторская задолженность" in row_str:
                nums = []
                for cell in row:
                    nums += split_multi_numbers(cell)
                if len(nums) >= 2:
                    found_debitor[years[0]] = nums[0]
                    found_debitor[years[1]] = nums[1]
                    break

    result["Основные средства и задолженность"]["основные средства"] = found_osnovnye
    result["Основные средства и задолженность"]["дебиторская задолженность"] = found_debitor
    return result

if __name__ == "__main__":
    pdf_path = "pdf.pdf"
    result = darsing_all_pdf(pdf_path)
    from pprint import pprint
    pprint(result)
