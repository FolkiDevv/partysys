from discord import Embed


class ErrorEmbed(Embed):
    def __init__(self, text: str = 'Произошла неизвестная ошибка.'):
        super().__init__(
            title='<:error:1177315110923018300> Ошибка.',
            color=0xED4245,
            description=text
        )
        self.set_footer(text='Обо всех недоработках сообщайте разработчику. Спасибо.')


class SuccessEmbed(Embed):
    def __init__(self, text: str):
        super().__init__(
            title='<:ok:1177313861368545392> Успех.',
            color=0x57F287,
            description=text
        )
        # self.set_footer(text='Обо всех недоработках сообщайте разработчику. Спасибо.')


class InterfaceEmbed(Embed):
    def __init__(self, title: str, text: str):
        super().__init__(
            title=title,
            color=0x36393F,
            description=text
        )
        self.set_footer(
            text='Обратите внимание, весь интерфейс расположен под этим смс.',
            icon_url='https://media.discordapp.net/attachments/1063285484266213466/1153439703962492988/585767366743293952.png'
        )


class ChannelControlEmbed(Embed):
    def __init__(self):
        super().__init__(
            title='<:staff:1177318013985370162> Интерфейс управления голосовым каналом',
            color=0x36393F,
            description='**Описание функционала кнопок:**\n\n'
                        '🪧 - создание/изменение/удаление объявления;\n\n'
                        '<:rename:1174291347511980052> - изменение названия канала;\n\n'
                        '<:limit:1174292033062580276> - изменение максимального числа пользователей в канале;\n\n'
                        '<:privacy:1174291348388589652> - изменение режима приватности: '
                        'публичный *(по умолчанию)* - все видят канал и могут присоединиться, '
                        'закрытый - присоединиться могут только пользователи, которым <:get_access:1174291352339623956> разрешили, '
                        'скрытый - аналогичен режиму "закрытый", однако при этом режиме все остальные еще и не смогут видеть канал;\n\n'
                        '<:get_access:1174291352339623956> - добавить пользователя(ей),'
                        ' которым будет Разрешено просматривать/присоединяться '
                        'к каналу *(используйте, если режим приватности отличен от "публичный")*;\n\n'
                        '<:take_access:1174291359792898218> - добавить пользователя(ей),'
                        ' которым будет Запрещено просматривать/присоединяться '
                        'к каналу *(применимо только к существующему каналу, запрет не будет распространяться на каналы,'
                        ' которые вы создадите после)*;\n\n'
                        '<:kick:1174291365300011079> - отключить пользователя от канала;\n\n'
                        '<:ban:1174291351106506792> - добавить пользователя в бан-лист '
                        '(пользователям из вашего бан-листа всегда на моменте создания вами нового канала будет выдаваться '
                        'запрет на просмотр/подключение к нему);\n\n'
                        '<:unban:1174291357586706442> - убрать пользователя из бан-листа;\n\n'
                        '<:return_owner:1174291361390940241> - вернуть права на управление каналом '
                        '*(если вы их кому-то передавали ранее)*;\n\n'
                        '<:transfer_owner:1174291356210962462> - передать права на управление каналом;\n\n'
                        '<:trash:1174291363873951776> - безвозвратно удалить канал.'
        )
        self.set_footer(
            text='Используйте кнопки под этим сообщением для управления вашим временным каналом.',
            icon_url='https://media.discordapp.net/attachments/1063285484266213466/1153439703962492988/585767366743293952.png'
        )


class ReminderEmbed(Embed):
    def __init__(self):
        super().__init__(
            title='<:info:1177314633124696165> Создано объявление о поиске команды для этого канала',
            color=0x36393F,
            description='⬇️ Нажмите на кнопку "🪧" под этим сообщением, чтобы изменить/удалить объявление.'
        )
