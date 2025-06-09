import os
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Создает и возвращает соединение с БД."""
    return psycopg2.connect(
        host=os.getenv('HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME')
    )

def write_to_history(org_name: str, file_path: str):
    """
    Добавляет запись об отчете в базу данных (таблица reports_history).
    org_name — название организации.
    file_path — путь к файлу отчета.
    """
    query = """
        INSERT INTO reports_history (org_name, file_path, created_at)
        VALUES (%s, %s, %s)
    """
    now = datetime.now()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (org_name, file_path, now))
        conn.commit()

def read_history(period_index: int) -> list[tuple[str, str, str]]:
    """
    Возвращает список отчетов за указанный период.
    period_index — цифра от 1 до 12 (1 = 30 дней, 2 = 60 дней, и т.д.)
    Возвращает список кортежей: (org_name, file_path, created_at)
    """
    assert 1 <= period_index <= 12, "Период должен быть от 1 до 12"
    days = period_index * 30
    since = datetime.now() - timedelta(days=days)
    query = """
        SELECT org_name, file_path, created_at
        FROM reports_history
        WHERE created_at >= %s
        ORDER BY created_at DESC
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (since,))
            rows = cur.fetchall()
    # rows: list of tuples (org_name, file_path, created_at)
    return rows

def export_full_history(filename: str = "full_history_export.csv"):
    """
    Экспортирует всю историю отчетов из базы данных в CSV-файл.
    Возвращает путь к файлу.
    """
    query = """
        SELECT org_name, file_path, created_at
        FROM reports_history
        ORDER BY created_at DESC
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
    # Записываем в csv
    import csv
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["org_name", "file_path", "created_at"])
        for row in rows:
            writer.writerow(row)
    return os.path.abspath(filename)

# Примеры использования:
if __name__ == "__main__":
    # Добавить запись
    # write_to_history("ООО Вектор", "Reports/ООО_Вектор.docx")

    # Получить историю за 2 месяца (60 дней)
    history = read_history(2)
    for org_name, file_path, created_at in history:
        print(f"{created_at}: {org_name} — {file_path}")

    # Экспорт всей истории в файл
    path = export_full_history()
    print(f"Файл истории сохранён: {path}")
