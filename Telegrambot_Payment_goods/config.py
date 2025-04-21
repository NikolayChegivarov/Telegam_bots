from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN_BOT')
    PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN')
    ADMINS = list(map(int, os.getenv("ADMIN").split(',')))

    # Database settings
    DB_NAME = os.getenv("NAME_DB")
    DB_HOST = os.getenv("HOST")
    DB_USER = os.getenv("USER")
    DB_PASSWORD = os.getenv("PASSWORD_DB")
    DB_PORT = os.getenv("PORT")