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
    from tqdm import tqdm
    import re
    import time

    stages = [
        "Извлечение текста из PDF",
        "Извлечение данных для 'Финансового анализа'",
        "Готово"
    ]

    with tqdm(total=len(stages), ncols=90, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
        # Этап 1. Извлечение текста
        pdf_text = extract_text_from_pdf(pdf_path, pbar)
        pbar.set_description(stages[1])

        # Поиск годов вида 31.12.20XX
        found_years = sorted(set(re.findall(r"31\.12\.20\d{2}", pdf_text)))
        if len(found_years) < 2:
            # fallback, если не нашли двух лет
            found_years = ["31.12.2023", "31.12.2024"]
        year1, year2 = found_years[-2], found_years[-1]

        # Этап 2. Извлечение только "Финансового анализа"
        prompt_ratios = f"""Извлеки строго следующие показатели из текста финансового анализа и рентабельности.
Верни JSON строго по этой структуре:

{{
  "Финансовый анализ": {{
    "Коэффициент автономии": {{
      "Значение показателя на {year1}": null,
      "Значение показателя на {year2}": null,
      "Описание показателя": ""
    }},
    "Коэффициент обеспеченности собственными оборотными средствами": {{
      "Значение показателя на {year1}": null,
      "Значение показателя на {year2}": null,
      "Описание показателя": ""
    }},
    "Коэффициент текущей (общей) ликвидности": {{
      "Значение показателя на {year1}": null,
      "Значение показателя на {year2}": null,
      "Описание показателя": ""
    }},
    "Коэффициент быстрой (промежуточной) ликвидности": {{
      "Значение показателя на {year1}": null,
      "Значение показателя на {year2}": null,
      "Описание показателя": ""
    }},
    "Коэффициент абсолютной ликвидности": {{
      "Значение показателя на {year1}": null,
      "Значение показателя на {year2}": null,
      "Описание показателя": ""
    }},
    "EBIT": {{
      "Значение показателя на {year1}": null,
      "Значение показателя на {year2}": null,
      "Описание показателя": "Прибыль до уплаты процентов и налогов."
    }},
    "Рентабельность продаж по EBIT": {{
      "Значение показателя на {year1}": null,
      "Значение показателя на {year2}": null,
      "Описание показателя": "Величина прибыли от продаж до уплаты процентов и налогов в каждом рубле выручки."
    }},
    "Рентабельность продаж по чистой прибыли": {{
      "Значение показателя на {year1}": null,
      "Значение показателя на {year2}": null,
      "Описание показателя": "Величина чистой прибыли в каждом рубле выручки."
    }},
    "Коэффициент восстановления платежеспособности": {{
      "Значение показателя на {year1}": null,
      "Значение показателя на {year2}": null,
      "Описание показателя": "Оценивает возможность восстановления нормальной структуры баланса."
    }}
  }}
}}

Если данных по какому-либо показателю нет — ставь null. Только JSON. Без пояснений.
"""

        ratios = gpt_extract_structured_data(pdf_text, prompt_ratios, pbar, stages[1])

        # Этап 3. Финализируем
        pbar.set_description(stages[2])
        pbar.update(1)
        time.sleep(0.2)

    # Гарантируем наличие всех 9 ключей
    required_keys = [
        "Коэффициент автономии",
        "Коэффициент обеспеченности собственными оборотными средствами",
        "Коэффициент текущей (общей) ликвидности",
        "Коэффициент быстрой (промежуточной) ликвидности",
        "Коэффициент абсолютной ликвидности",
        "EBIT",
        "Рентабельность продаж по EBIT",
        "Рентабельность продаж по чистой прибыли",
        "Коэффициент восстановления платежеспособности"
    ]

    result_ratios = ratios.get("Финансовый анализ", {})
    for key in required_keys:
        if key not in result_ratios:
            result_ratios[key] = {
                f"Значение показателя на {year1}": None,
                f"Значение показателя на {year2}": None,
                "Описание показателя": ""
            }

    return {
        "Финансовый анализ": result_ratios
    }



# --- CLI-запуск для теста ---
if __name__ == "__main__":
    pdf_path = "pdf.pdf"
    result = parsing_all_pdf(pdf_path)
    from pprint import pprint
    pprint(result)
