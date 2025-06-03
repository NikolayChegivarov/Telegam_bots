import os
from docx import Document
import pandas as pd
import pdfplumber
from dotenv import load_dotenv
import openai

# Загружаем переменные окружения из .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- 1. Извлечение текста из файлов ---

def extract_text_from_docx(file_path):
    """
    Извлекает весь текст из Word (.docx) файла.
    """
    try:
        doc = Document(file_path)
        fullText = []
        for para in doc.paragraphs:
            fullText.append(para.text)
        return '\n'.join(fullText)
    except Exception as e:
        return f"[Ошибка при извлечении Word: {e}]"

def extract_text_from_pdf(file_path):
    """
    Извлекает весь текст из PDF файла.
    """
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        return text
    except Exception as e:
        return f"[Ошибка при извлечении PDF: {e}]"

def extract_text_from_excel(file_path):
    """
    Извлекает данные из первой страницы Excel-файла и возвращает в виде текста (таблицы в виде строки).
    """
    try:
        df = pd.read_excel(file_path)
        return df.to_string(index=False)
    except Exception as e:
        return f"[Ошибка при извлечении Excel: {e}]"

# --- 2. Формируем промпт для GPT ---

def build_prompt(word_text, pdf_text, excel_text):
    """
    Формирует промпт для GPT с пояснениями, что извлекать
    """
    prompt = f"""
У тебя три типа данных для юридического отчета:

1. Word файл «Выгрузка Контур.Фокус»:
----------------
{word_text}
----------------

2. PDF файл «Финансовая выгрузка из Контур.Фокус»:
----------------
{pdf_text}
----------------

3. Excel файл «Выгрузка арбитражных производств»:
----------------
{excel_text}
----------------

Твоя задача — **извлечь и структурировать** следующую информацию:
- Наименование организации
- ИНН
- Руководитель/Генеральный директор
- Финансовые показатели (выручка, чистая прибыль, активы, обязательства и т.д. — всё, что есть в отчетах)
- Информация об арбитражных делах (номер дела, дата, суть, сумма, статус и т.д.)

Верни результат СТРОГО в виде JSON следующей структуры:
{{
    "org_name": "",
    "inn": "",
    "ceo": "",
    "financial": {{
        "revenue": "",
        "net_profit": "",
        "assets": "",
        "liabilities": "",
        "other": ""
    }},
    "arbitration_cases": [
        {{
            "case_number": "",
            "date": "",
            "summary": "",
            "amount": "",
            "status": ""
        }}
    ]
}}
Если какая-то информация отсутствует — оставь соответствующее поле пустым.
    """
    return prompt

# --- 3. Отправка запроса к GPT с openai 1.x.x ---

def gpt_extract_data(word_text, pdf_text, excel_text):
    """
    Отправляет текст всех файлов в GPT и возвращает структурированный JSON.
    """
    prompt = build_prompt(word_text, pdf_text, excel_text)
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY не найден в .env файле.")
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",  # Можно поменять на gpt-4, gpt-3.5-turbo, gpt-4-turbo и т.п.
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0
        )
        content = response.choices[0].message.content
        # Обрезаем всё, кроме JSON (иногда GPT пишет лишний текст)
        import re, json
        json_match = re.search(r'({.*})', content, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
            try:
                data = json.loads(json_text)
                return data
            except json.JSONDecodeError:
                return {"error": "Не удалось распарсить JSON из ответа GPT.", "raw": content}
        else:
            return {"error": "JSON не найден в ответе GPT.", "raw": content}
    except Exception as e:
        return {"error": f"Ошибка запроса к GPT: {e}"}

# --- 4. Главная функция для вызова из report.py ---

def extract_structured_data(word_path, pdf_path, excel_path):
    """
    Главная функция для извлечения данных из трёх файлов с помощью GPT.
    Возвращает словарь (структура для подстановки в шаблон).
    """
    word_text = extract_text_from_docx(word_path)
    pdf_text = extract_text_from_pdf(pdf_path)
    excel_text = extract_text_from_excel(excel_path)
    return gpt_extract_data(word_text, pdf_text, excel_text)
