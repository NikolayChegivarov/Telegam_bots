
from openai import OpenAI

# Загрузка переменных окружения
import os
from dotenv import load_dotenv
load_dotenv()

AI_TOKEN = os.getenv("AI_TOKEN")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=AI_TOKEN,
)

completion = client.chat.completions.create(
  model="deepseek/deepseek-chat",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)
print(completion.choices[0].message.content)
