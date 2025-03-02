from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


class Keyboards:
    """
    Класс для создания клавиатуры регистрации с различными опциями выбора задач.

    Атрибуты:
    ...

    Методы:
    - __init__(): Инициализация объекта клавиатуры с созданием кнопок.
    - get_markup(): Добавление кнопок на клавиатуру и возврат готовой разметки.
    """
    def __init__(self):
        """
        Инициализация объекта клавиатуры с созданием кнопок.
        Создает экземпляр InlineKeyboardMarkup и определяет различные кнопки выбора задач.
        """
        self.markup = InlineKeyboardMarkup(row_width=2)
        self.button_natural_person = InlineKeyboardButton('Физ лицо', callback_data='natural_person')  #
        self.button_organization = InlineKeyboardButton('Организация', callback_data='organization')  #
        self.button_tasks_all = InlineKeyboardButton('Просмотр задач', callback_data='tasks')  #
        self.button_task_filter = InlineKeyboardButton('Задать фильтр', callback_data='filter')
        self.button_basic_menu = InlineKeyboardButton('Основное меню', callback_data='basic_menu')
        # Кнопки менеджерам.
        self.button_set_a_task = InlineKeyboardButton('Поставить задачу', callback_data='set_a_task')  #
        self.button_del = InlineKeyboardButton('Удалить задачу', callback_data='del')
        # Кнопки водителям.
        self.button_status = InlineKeyboardButton('Изменить статус', callback_data='status')
        self.button_take_task = InlineKeyboardButton('Взять задачу', callback_data='take_task')
        self.button_to_mark = InlineKeyboardButton('Пометить "сделано"', callback_data='to_mark')
        self.button_my_tasks = InlineKeyboardButton('Мои задачи', callback_data='my_tasks')
        # Кнопки администратору.
        self.button_accept = InlineKeyboardButton('Принять', callback_data='accept')
        self.button_reject = InlineKeyboardButton('Отклонить', callback_data='reject')

    def access_check(self):
        """
        Предоставление доступа админом.
        """
        self.markup.add(self.button_accept, self.button_reject)
        return self.markup

    def registration_keyboard(self):
        """
        Деление на юр/физ лицо.
        """
        self.markup.add(self.button_natural_person, self.button_organization)
        return self.markup

    def client_keyboard(self):
        """
        Клавиатура для клиентов.
        """
        self.markup.add(self.button_set_a_task, self.button_tasks_all)
        return self.markup

    def admin_keyboard(self):
        """
        Клавиатура для админа.
        """
        self.markup.add(self.button_tasks_all)
        return self.markup

    def filter_tasks_keyboard(self):
        """
        Выбор фильтра просмотра задач.
        """
        self.markup.add(self.button_task_kostroma, self.button_task_msk,
                        self.button_task_filter, self.button_basic_menu)
        return self.markup

    def alter_status(self):
        """
        Выбор фильтра просмотра задач.
        """
        self.markup.add(self.button_take_task, self.button_to_mark)
        return self.markup
