import re


def limit_text(text):
    # Разделяем текст на предложения
    sentences = re.split(r'[.!?]', text)

    # Удаляем пустые строки, которые могут возникнуть после разделения
    sentences = [sent for sent in sentences if sent]

    print('Конвертируем текст.')

    # Возвращаем первые три предложения
    return '. '.join(sentences[:3])


def convert_phone(phone):
    """Функция конвертирует номер телефона"""
    # Удаление всех нецифровых символов и пробелов
    cleaned_phone = ''.join(filter(str.isdigit, phone))

    # Проверка длины номера
    if len(cleaned_phone) != 10:
        return "Неверный номер телефона"

    # Добавление префикса и форматирование номера
    formatted_phone = f"998-{cleaned_phone[:2]}-{cleaned_phone[2:]}"

    print('Конвертируем номер телефона.')

    return formatted_phone
