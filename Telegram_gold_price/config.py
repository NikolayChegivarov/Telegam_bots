# config.py
import os
from dotenv import load_dotenv
from typing import List

# Загружаем переменные из .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ID администраторов (можно несколько через запятую)
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

# Файл для хранения данных
DATA_FILE = os.getenv("DATA_FILE", "bot_data.json")

# Имя менеджера (username без @)
MANAGER_NAME = os.getenv("MANAGER_NAME", "GUSAROV_NIK")
MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID"))

# Дополнительные переменные (если нужны)
# LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
# DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле")

if not ADMIN_IDS:
    print("⚠️  ВНИМАНИЕ: ADMIN_IDS не установлены или пустые")
    ADMIN_IDS = []

print(f"✅ Загружено {len(ADMIN_IDS)} ID администраторов")
print(f"✅ Менеджер: @{MANAGER_NAME}")
