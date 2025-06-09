import os
from dotenv import load_dotenv
from openai import OpenAI
import PyPDF2
from typing import Dict, Any
from tqdm import tqdm
import time
import json
import re

# --- Загрузка .env ---
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in environment!")

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Извлечение текста из PDF ---
def extract_text_from_pdf(pdf_path: str, pbar=None) -> str:
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        if pbar:
            pbar.set_description("Извлечение текста из PDF")
            pbar.reset(total=total_pages)
        for i, page in enumerate(reader.pages):
            text += page.extract_text() or ""
            if pbar:
                pbar.update(1)
        if pbar:
            pbar.n = total_pages
            pbar.refresh()
    return text

# --- Очищаем переносы строк в длинных текстах (рекурсивно) ---
def clean_text_recursive(obj):
    if isinstance(obj, dict):
        return {k: clean_text_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_text_recursive(v) for v in obj]
    elif isinstance(obj, str):
        # Склеиваем строки, убираем избыточные пробелы между строками
        s = obj.replace('\n', ' ')
        s = re.sub(r' {2,}', ' ', s)
        s = s.strip()
        return s
    else:
        return obj

# --- GPT-парсер ---
def gpt_extract_structured_data(pdf_text: str, prompt: str, pbar=None, stage_msg="") -> dict:
    if pbar:
        pbar.set_description(stage_msg)
        pbar.update(1)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты помогаешь структурировать табличные и текстовые финансовые данные из отчётов. Не добавляй никаких комментариев и пояснений, только чистый JSON."},
            {"role": "user", "content": prompt + "\n\n" + pdf_text}
        ],
        max_tokens=4096,
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        # Очищаем все длинные строки
        data = clean_text_recursive(data)
        return data
    except Exception as e:
        print("Ошибка парсинга ответа GPT:", e)
        print(content)
        return {}

def parsing_all_pdf(pdf_path: str) -> Dict[str, Any]:
    stages = [
        "Извлечение текста из PDF",
        "Извлечение данных для 'Отчета о финансовых результатах'",
        "Извлечение данных для 'Финансового анализа'",
        "Извлечение 'Оценки ключевых показателей'",
        "Готово"
    ]
    with tqdm(total=len(stages), ncols=90, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
        # 1. Извлекаем текст
        pdf_text = extract_text_from_pdf(pdf_path, pbar)
        pbar.set_description(stages[1])

        # 2. Парсим "Отчет о финансовых результатах"
        prompt_results = (
            "Извлеки из текста таблицу 'Отчет о финансовых результатах', как на примере. "
            "Сохрани структуру в формате JSON. Для каждой строки (показателя) используй ключ с её названием, "
            "значения по каждому году указывай по ключам 'конец 2020', 'конец 2021', 'конец 2022', 'конец 2023'.\n"
            "Пример:\n"
            "{\n"
            "  \"Отчет о финансовых результатах\": {\n"
            "    \"Выручка\": {\"конец 2020\": 170203, \"конец 2021\": 303497, \"конец 2022\": 318589, \"конец 2023\": 83889},\n"
            "    ...\n"
            "  }\n"
            "}\n"
            "Только JSON, никаких пояснений. Если данных по году нет, подставляй null или \"\"."
        )
        results = gpt_extract_structured_data(pdf_text, prompt_results, pbar, stages[1])

        # 3. Парсим "Финансовый анализ"
        prompt_ratios = (
            "Извлеки из текста таблицу 'Финансовый анализ на последнюю отчетную дату'. "
            "Верни структуру в виде JSON, как в примере ниже. "
            "В каждом показателе должны быть три поля: "
            "\"Значение показателя на 31.12.2022\", \"Значение показателя на 31.12.2023\", \"Описание показателя\".\n"
            "Пример:\n"
            "{\n"
            "  \"Финансовый анализ\": {\n"
            "    \"Коэффициент автономии\": {\n"
            "      \"Значение показателя на 31.12.2022\": -0.36,\n"
            "      \"Значение показателя на 31.12.2023\": -0.48,\n"
            "      \"Описание показателя\": \"Отношение собственного капитала к общей сумме капитала...\"\n"
            "    },\n"
            "    ...\n"
            "  }\n"
            "}\n"
            "Только JSON, никаких пояснений. Если какого-то значения нет, подставляй null или \"\"."
        )
        ratios = gpt_extract_structured_data(pdf_text, prompt_ratios, pbar, stages[2])

        # 4. Парсим "Оценка ключевых показателей" (всё между 3.1 и 3.2)
        prompt_key_assessment = (
            "Извлеки текст блока 3.1 'Оценка ключевых показателей' из отчёта, включая все списки и замечания, "
            "до начала блока 3.2. Верни JSON вида:\n"
            "{ \"Оценка ключевых показателей\": \"<весь текст блока>\" }\n"
            "Только JSON, никаких пояснений."
        )
        key_assessment = gpt_extract_structured_data(pdf_text, prompt_key_assessment, pbar, stages[3])

        pbar.set_description(stages[4])
        pbar.update(1)
        time.sleep(0.2)  # чтобы стадия "Готово" мигнула

    # Объединить все результаты
    result = {}
    if "Отчет о финансовых результатах" in results:
        result["Отчет о финансовых результатах"] = results["Отчет о финансовых результатах"]
    else:
        result["Отчет о финансовых результатов"] = {}

    if "Финансовый анализ" in ratios:
        result["Финансовый анализ"] = ratios["Финансовый анализ"]
    else:
        result["Финансовый анализ"] = {}

    if "Оценка ключевых показателей" in key_assessment:
        result["Оценка ключевых показателей"] = key_assessment["Оценка ключевых показателей"]
    else:
        result["Оценка ключевых показателей"] = ""

    # print("Данные из PDF файла собраны")
    return result

# --- CLI-запуск для теста ---
if __name__ == "__main__":
    pdf_path = "pdf.pdf"
    result = parsing_all_pdf(pdf_path)
    from pprint import pprint
    pprint(result)
