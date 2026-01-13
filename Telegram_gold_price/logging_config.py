# logging_config.py
import logging
import logging.handlers
import os
from datetime import datetime, timedelta


def setup_logging():
    """Настройка логирования с ротацией файлов"""
    # Создаем папку для логов если её нет
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Настраиваем формат
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Основной логгер приложения
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Убираем лишние логи httpx и apscheduler
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)

    # 1. FileHandler с ротацией по дням (храним 2 дня)
    log_file = os.path.join(log_dir, "bot.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',  # ротация в полночь
        interval=1,  # каждый день
        backupCount=2,  # храним 2 файла (сегодня + 2 предыдущих дня)
        encoding='utf-8'
    )
    file_handler.suffix = "%Y-%m-%d.log"
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # 2. StreamHandler для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
