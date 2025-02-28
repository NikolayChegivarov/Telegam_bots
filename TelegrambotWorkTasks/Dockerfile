FROM python:3.9-slim
LABEL authors="nikolai"
WORKDIR /telegram_work_tasks
COPY . /telegram_work_tasks
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*
CMD ["python", "main.py"]
EXPOSE 8000
