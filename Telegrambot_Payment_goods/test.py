#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import locale
import psycopg2
import sys
print(f"Default encoding: {sys.getdefaultencoding()}")
print(f"Filesystem encoding: {sys.getfilesystemencoding()}")

# Принудительная настройка UTF-8
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# ASCII-only подключение
try:
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="your_password",  # Замените на ASCII пароль
        dbname="postgres",
        options="-c client_encoding=utf8"
    )

    with conn.cursor() as cur:
        cur.execute("SELECT 'тест кодировки' AS test")
        print(cur.fetchone()[0])

except Exception as e:
    print(f"Ошибка: {type(e).__name__}: {str(e)}", file=sys.stderr)
finally:
    if 'conn' in locals():
        conn.close()