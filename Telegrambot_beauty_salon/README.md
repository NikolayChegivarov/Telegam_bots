
# Beauty Salon Telegram Bot
> *Бот для салона красоты, позволяющий клиентам записываться на услуги, а мастерам - управлять своими записями. Реализован на aiogram 3.x с использованием PostgreSQL.*

### 📌  Функционал 
##### Для клиентов:
* Просмотр услуг и цен  
* Запись на услуги  
* Просмотр своих записей  
* Управление профилем  
* Возможность оплаты  

##### Для мастеров:
* Просмотр своих записей  
* Управление профилем  
* Просмотр графика работы  

##### Для администраторов:
* Добавление новых мастеров  
* Добавление новых услуг  
* Просмотр статистики  

### 🛠 Технологии
* Python 3.10+  
* Aiogram 3.x  
* PostgreSQL  
* psycopg2-binary  
* python-dotenv  
* yookassa   
* flask  

### ⚙️ Установка

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
pip install aiogram psycopg2-binary python-dotenv yookassa flask
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
Что бы узнать свой telegram id обратитесь к "@my_id_bot"

### 🏃‍♂️ Запуск

1 Запустите бота:
```bash
python main.py
```

### 🗄 Структура проекта  
beauty-salon-bot/  
├── .env  
├── .gitignore  
├── main.py  
├── database.py  
├── requirements.txt  
├── middleware.py  
├── keyboards.py  
├── utils.py  
├── bot_instance.py  
├── payments.py  
├── Webhook.py  
├── handlers/  
│   ├── __init__.py  
│   ├── common_handlers.py  
│   ├── client_handlers.py  
│   ├── master_handlers.py  
│   └── admin_handlers.py  
└── README.md  

### 🔧 Настройка PostgreSQL

1 Установите PostgreSQL

2 Создайте пользователя и базу данных:
```sql
CREATE USER beauty_salon_user WITH PASSWORD 'ваш_пароль';
CREATE DATABASE beauty_salon OWNER beauty_salon_user;
```

3 Обновите настройки в .env:
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

### 📜 Лицензия

MIT License

### ✉️ Контакты

Гусаров Николай - nikolai_polos@mail.ru