
Beauty Salon Telegram Bot
Бот для салона красоты, позволяющий клиентам записываться на услуги, а мастерам - управлять своими записями. Реализован на aiogram 3.x с использованием PostgreSQL.

📌 Функционал
Для клиентов:
Просмотр услуг и цен

Запись на услуги

Просмотр своих записей

Управление профилем

Для мастеров:
Просмотр своих записей

Управление профилем

Просмотр графика работы

Для администраторов:
Добавление новых мастеров

Добавление новых услуг

Просмотр статистики

🛠 Технологии
Python 3.10+

Aiogram 3.x

PostgreSQL

psycopg2-binary

python-dotenv

⚙️ Установка

1 Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-репозиторий/beauty-salon-bot.git
cd beauty-salon-bot
```

2 Создайте виртуальное окружение:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/MacOS
.venv\Scripts\activate     # Windows
```

3 Установите зависимости:
```bash
pip install -r requirements.txt
```
или
```bash
pip install aiogram psycopg2-binary python-dotenv
```

4 Создайте файл .env на основе .env.example:
```ini
TELEGRAM_TOKEN_BOT=ваш_токен_бота
HOST=localhost
NAME_DB=beauty_salon
USER=postgres
PASSWORD_DB=ваш_пароль
PORT=5432
NAME_DB=Telegrambot_beauty_salon
ADMIN=ххх
PAYMENT_PROVIDER_TOKEN=ххх
```

🏃‍♂️ Запуск

1 Инициализируйте базу данных:





Создайте базу данных, выполнив database.py

Запустите бота:
```bash
python main.py
```

Этот бот реализует основные функции для салона красоты:
Регистрация клиентов и мастеров
Просмотр услуг и запись на них
Управление профилем
Просмотр своих записей
Администрирование услуг (для администраторов)