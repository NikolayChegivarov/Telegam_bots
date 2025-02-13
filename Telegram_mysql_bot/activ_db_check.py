def activ_check(cursor):
    cursor.execute("SELECT DATABASE();")
    active_db = cursor.fetchone()
    print(f"База данных: {active_db[0]} активная ")
