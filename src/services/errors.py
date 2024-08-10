import discord.errors


class PartySysException(discord.errors.DiscordException):
    ...


class BotNotConfiguredError(PartySysException):
    def __init__(self):
        super().__init__(
            "На этом сервере еще не настроен бот! Обратитесь к "
            "администрации сервера."
        )


class UnknownDisError(PartySysException):
    def __init__(self):
        super().__init__(
            "Произошла неизвестная ошибка со стороны Discord. "
            "Попробуйте снова."
            "\n*Если ошибка повторяется - обратитесь в "
            "тех.поддержку бота.*"
        )


class UserNoTempChannelsError(PartySysException):
    def __init__(self):
        super().__init__(
            "**У вас нет голосового канала, которым вы можете "
            "управлять.**\n"
            "Сначала создайте свой канал используя "
            "каналы-создатели."
        )


class UserUseAlienControlInterfaceError(PartySysException):
    def __init__(self):
        super().__init__(
            "**Вы пытаетесь использовать интерфейс управления из "
            "чата чужого временного голосового канала.**\n"
            "Используйте интерфейс управления из вашего чата "
            "временного голосового канала, или из общего."
        )


class UserAlreadyOwnerError(PartySysException):
    def __init__(self):
        super().__init__(
            "Вы уже управляете временным каналом."
            "\n\n*P.s. Если хотите вернуть права на старый канал, "
            "то надо удалить текущий.*"
        )


class UserNotBannedError(PartySysException):
    def __init__(self):
        super().__init__("Пользователь не в бане.")


class NumbersOnlyError(PartySysException):
    def __init__(self):
        super().__init__("Допускаются только числовые значения!")


class NoUsersInChannelError(PartySysException):
    def __init__(self):
        super().__init__("В канале нет никого, кроме вас.")


class AdvChannelIsFullError(PartySysException):
    def __init__(self):
        super().__init__(
            "Вы не можете дать объявление, когда ваш канал заполнен."
        )


class AdvRequirePublicPrivacyError(PartySysException):
    def __init__(self):
        super().__init__(
            "Чтобы опубликовать/изменить объявление ваш канал "
            'должен быть "Публичным".'
        )
