## t.me/Communication_with_AI_bot  ##

*Telegram-бот, использующий модель DeepSeek для генерации  
ответов на пользовательские запросы. Бот поддерживает  
асинхронное взаимодействие и управление состоянием для  
обеспечения плавной работы с большим количеством пользователей.*

**Создайте виртуальное окружение.  
Установите зависимости помощью команды:**
```bash
pip install -r requirements.txt
```
Или вручную:
```bash
python.exe -m pip install --upgrade pip
pip install openai 
pip install aiogram
pip install python-dotenv 
```
**Создайте файл .env и укажите следующие переменные:**  
AI_TOKEN=  
TELEGRAM_TOKEN=

**Запустите бота:**
```bash
python run.py
```

**В Telegram:**  
Начните диалог с ботом. Отправьте любое сообщение.  
Получите ответ, сгенерированный моделью DeepSeek.