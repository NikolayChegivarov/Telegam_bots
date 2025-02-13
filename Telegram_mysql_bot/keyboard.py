from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


class RegistrationKeyboard:
    def __init__(self):
        self.markup = InlineKeyboardMarkup(row_width=2)
        self.button_yes = InlineKeyboardButton('Регистрация', callback_data='register')
        self.button_no = InlineKeyboardButton('Нет, спасибо', callback_data='no')

    def get_markup(self):
        self.markup.add(self.button_yes, self.button_no)
        print('Предложили выбор кнопок.')
        return self.markup


