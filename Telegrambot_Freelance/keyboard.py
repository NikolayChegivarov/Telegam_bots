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
        # Общие кнопки
        self.button_tasks_all = InlineKeyboardButton('Просмотр задач', callback_data='tasks')
        self.button_del_task = InlineKeyboardButton('Удалить задачу', callback_data='del_task')
        # Кнопки клиенту
        self.button_natural_person = InlineKeyboardButton('Физ лицо', callback_data='natural_person')
        self.button_organization = InlineKeyboardButton('Организация', callback_data='organization')
        self.button_set_a_task = InlineKeyboardButton('Поставить задачу', callback_data='set_a_task')
        # Кнопки исполнителю.
        self.button_status = InlineKeyboardButton('Изменить статус', callback_data='status')
        self.button_work_task = InlineKeyboardButton('В работе', callback_data='work_task')
        self.button_to_mark = InlineKeyboardButton('Сделано', callback_data='to_mark')
        self.button_to_payment = InlineKeyboardButton('На оплату', callback_data='to_payment')

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
        self.markup.add(self.button_set_a_task, self.button_tasks_all, self.button_del_task)
        return self.markup

    def admin_keyboard(self):
        """
        Клавиатура для админа.
        """
        self.markup.add(self.button_tasks_all, self.button_status, self.button_del_task, self.button_to_payment)
        return self.markup

    def alter_status(self):
        """
        Изменить статус задачи /'В работе'/'Сделано'.
        """
        self.markup.add(self.button_work_task, self.button_to_mark)
        return self.markup

    def to_payment(self):
        """
        Отправить на оплату. Статус 'На оплате'.
        """
        self.markup.add(self.button_to_payment)
        return self.markup
