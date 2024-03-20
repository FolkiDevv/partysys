class CustomExc(Exception):
    def __init__(self):
        self.err_msg: str = ''


class BotNotConfigured(CustomExc):
    def __init__(self):
        self.err_msg = 'На этом сервере еще не настроен бот! Обратитесь к администрации сервера.'


class UnknownDisError(CustomExc):
    def __init__(self):
        self.err_msg = ('Произошла неизвестная ошибка со стороны Discord. Попробуйте снова.'
                        '\n*Если ошибка повторяется - обратитесь в тех.поддержку бота.*')


class UnknownError(CustomExc):
    def __init__(self):
        self.err_msg = ('Произошла неизвестная ошибка. Попробуйте снова.'
                        '\n*Если ошибка повторяется - обратитесь в тех.поддержку бота.*')


class UserNoTempChannels(CustomExc):
    def __init__(self):
        self.err_msg = ('**У вас нет голосового канала, которым вы можете управлять.**\n'
                        'Сначала создайте свой канал используя каналы-создатели.')


class UserUseAlienControlInterface(CustomExc):
    def __init__(self):
        self.err_msg = ('**Вы пытаетесь использовать интерфейс управления из чата чужого временного голосового канала.**\n'
                        'Используйте интерфейс управления из вашего чата временного голосового канала, или из общего.')


class UserAlreadyOwner(CustomExc):
    def __init__(self):
        self.err_msg = ('Вы уже управляете временным каналом.'
                        '\n\n*P.s. Если хотите вернуть права на старый канал, то надо удалить текущий.*')


class UserAlreadyBanned(CustomExc):
    def __init__(self):
        self.err_msg = 'Пользователь уже в бане :)'


class UserNotBanned(CustomExc):
    def __init__(self):
        self.err_msg = 'Пользователь не в бане.'


class UserBanLimit(CustomExc):
    def __init__(self):
        self.err_msg = 'Вы исчерпали лимит в 25 банов!'


class NumbersOnly(CustomExc):
    def __init__(self):
        self.err_msg = 'Допускаются только числовые значения!'


class NoUsersInChannel(CustomExc):
    def __init__(self):
        self.err_msg = 'В канале нет никого, кроме вас.'


class AdvChannelIsFull(CustomExc):
    def __init__(self):
        self.err_msg = 'Вы не можете дать объявление, когда ваш канал заполнен.'


class AdvRequirePublicPrivacy(CustomExc):
    def __init__(self):
        self.err_msg = 'Чтобы опубликовать/изменить объявление ваш канал должен быть "Публичным".'
