import re

# Валидация телефона
def validate_phone(phone: str) -> bool:
    phone_pattern = re.compile(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$')
    return bool(phone_pattern.match(phone))

# Валидация ИНН
def validate_inn(inn: str) -> bool:
    if len(inn) not in (10, 12) or not inn.isdigit():
        return False
    return True