from keyboard import RegistrationKeyboard
from database_connection import bot


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Выясняем id чата/пользователя для дальнейшего взаимодействия с пользователем.
    Присылаем кнопки."""
    keyboard = RegistrationKeyboard().get_markup()  # Присылаем клавиатуру.
    bot.send_message(message.chat.id, 'Приветствую. Если хотите зарегистрироваться нажми "Регистрация".',
                     reply_markup=keyboard)
    print('Поздоровались.')
    pass
