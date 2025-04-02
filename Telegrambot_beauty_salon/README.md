
Telegrambot_beauty_salon

Как запустить бота

Установите зависимости:

```bash
pip install aiogram psycopg2-binary python-dotenv
```

Создайте файл .env

TELEGRAM_TOKEN_BOT=
HOST=localhost
#HOST=host.docker.internal
USER=postgres
PASSWORD_DB=ххх
PORT=5432
NAME_DB=Telegrambot_beauty_salon
ADMIN=ххх
PAYMENT_PROVIDER_TOKEN=ххх

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