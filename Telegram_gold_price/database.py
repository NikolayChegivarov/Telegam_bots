# database.py
import json
import os
from config import DATA_FILE


class Database:
    def __init__(self):
        self.data = self._load_data()

    def _load_data(self):
        """Загружаем данные из файла"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        # Начальные значения
        return {
            "gold_price_nds": 5000,
            "gold_price_no_nds": 5000,
            "silver_price_nds": 60,
            "silver_price_no_nds": 60,
            "users": []
        }

    def _save_data(self):
        """Сохраняем данные в файл"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    # ПОЛУЧАЕМ ЦЕНЫ
    def get_gold_price_NDS(self):
        """Получаем текущую цену золота с НДС"""
        return self.data.get("gold_price_nds", 5000)

    def get_gold_price_no_NDS(self):
        """Получаем текущую цену золота без НДС"""
        return self.data.get("gold_price_no_nds", 5000)

    def get_silver_price_NDS(self):
        """Получаем текущую цену серебра с НДС"""
        return self.data.get("silver_price_nds", 60)

    def get_silver_price_no_NDS(self):
        """Получаем текущую цену серебра без НДС"""
        return self.data.get("silver_price_no_nds", 60)

    # УСТАНАВЛИВАЕМ ЦЕНЫ
    def set_gold_price_NDS(self, price):
        """Устанавливаем новую цену золота с НДС"""
        try:
            self.data["gold_price_nds"] = float(price)
            self._save_data()
            return True
        except:
            return False

    def set_gold_price_no_NDS(self, price):
        """Устанавливаем новую цену золота без НДС"""
        try:
            self.data["gold_price_no_nds"] = float(price)
            self._save_data()
            return True
        except:
            return False

    def set_silver_price_NDS(self, price):
        """Устанавливаем новую цену серебра с НДС"""
        try:
            self.data["silver_price_nds"] = float(price)
            self._save_data()
            return True
        except:
            return False

    def set_silver_price_no_NDS(self, price):
        """Устанавливаем новую цену серебра без НДС"""
        try:
            self.data["silver_price_no_nds"] = float(price)
            self._save_data()
            return True
        except:
            return False

    def add_user(self, user_id):
        """Добавляем пользователя в базу"""
        if user_id not in self.data["users"]:
            self.data["users"].append(user_id)
            self._save_data()

    def get_all_users(self):
        """Получаем список всех пользователей"""
        return self.data["users"]

    def remove_user(self, user_id):
        """Удаляем пользователя из базы"""
        if user_id in self.data["users"]:
            self.data["users"].remove(user_id)
            self._save_data()