# database.py (зашифрованная версия - ЗАМЕНЯЕТ старый файл)
import json
import os
from cryptography.fernet import Fernet
from config import DATA_FILE


class Database:
    def __init__(self):
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        self.data = self._load_data()

    def _ensure_data_file_exists(self):
        """Проверяем существование файла и создаем если нужно"""
        from config import DATA_FILE

        if not os.path.exists(DATA_FILE):
            print(f"📁 Создаю файл данных: {DATA_FILE}")
            self._save_data()  # Сохраняем данные по умолчанию

    def _load_or_generate_key(self):
        """Загружаем или генерируем ключ шифрования"""
        key_file = "secret.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Генерируем новый ключ
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Защищаем файл с ключом
            if os.name != 'nt':  # не Windows
                os.chmod(key_file, 0o600)
            print("✅ Сгенерирован новый ключ шифрования")
            return key

    def _load_data(self):
        """Загружаем и расшифровываем данные"""
        if not os.path.exists(DATA_FILE):
            return self._get_default_data()

        try:
            with open(DATA_FILE, 'rb') as f:
                encrypted = f.read()

            # Дешифруем
            decrypted = self.cipher.decrypt(encrypted)
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            print(f"⚠️  Ошибка расшифровки данных: {e}")
            print("⚠️  Используются данные по умолчанию")
            return self._get_default_data()

    def _get_default_data(self):
        """Возвращаем данные по умолчанию"""
        return {
            "gold_price_nds": 5000.0,
            "gold_price_no_nds": 5000.0,
            "silver_price_nds": 60.0,
            "silver_price_no_nds": 60.0,
            "users": []
        }

    def _save_data(self):
        """Шифруем и сохраняем данные"""
        # Преобразуем данные в JSON
        json_str = json.dumps(self.data, ensure_ascii=False, indent=4)

        # Шифруем
        encrypted = self.cipher.encrypt(json_str.encode('utf-8'))

        # Сохраняем
        with open(DATA_FILE, 'wb') as f:
            f.write(encrypted)

        # Защищаем файл (на Linux/Mac)
        if os.name != 'nt':
            os.chmod(DATA_FILE, 0o600)

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С ЦЕНАМИ ==========

    def get_gold_price_NDS(self):
        return self.data.get("gold_price_nds", 5000.0)

    def get_gold_price_no_NDS(self):
        return self.data.get("gold_price_no_nds", 5000.0)

    def get_silver_price_NDS(self):
        return self.data.get("silver_price_nds", 60.0)

    def get_silver_price_no_NDS(self):
        return self.data.get("silver_price_no_nds", 60.0)

    def set_gold_price_NDS(self, price):
        try:
            self.data["gold_price_nds"] = float(price)
            self._save_data()
            return True
        except:
            return False

    def set_gold_price_no_NDS(self, price):
        try:
            self.data["gold_price_no_nds"] = float(price)
            self._save_data()
            return True
        except:
            return False

    def set_silver_price_NDS(self, price):
        try:
            self.data["silver_price_nds"] = float(price)
            self._save_data()
            return True
        except:
            return False

    def set_silver_price_no_NDS(self, price):
        try:
            self.data["silver_price_no_nds"] = float(price)
            self._save_data()
            return True
        except:
            return False

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========

    def add_user(self, user_id):
        if "users" not in self.data:
            self.data["users"] = []

        if user_id not in self.data["users"]:
            self.data["users"].append(user_id)
            self._save_data()
            return True
        return False

    def get_all_users(self):
        return self.data.get("users", [])

    def remove_user(self, user_id):
        if user_id in self.data.get("users", []):
            self.data["users"].remove(user_id)
            self._save_data()
            return True
        return False