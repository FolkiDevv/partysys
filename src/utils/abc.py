import abc
import datetime
from random import sample
from types import MappingProxyType

import discord
from discord.ext import commands

from src import ui
from src.models import CreatorChannels

from .enums import Privacy

SQUAD_TITLES = (
    "Альфа",
    "Омега",
    "Феникс",
    "Грифон",
    "Дракон",
    "Волк",
    "Сокол",
    "Титан",
    "Легион",
    "Центурион",
    "Шторм",
    "Север",
    "Молния",
    "Сталь",
    "Кобра",
    "Пантера",
    "Лев",
    "Гладиатор",
    "Викинг",
    "Спартанец",
    "Комета",
    "Буря",
    "Арктика",
    "Торнадо",
    "Ястреб",
    "Медведь",
    "Тигр",
    "Ягуар",
    "Скорпион",
    "Марс",
    "Железо",
    "Рубин",
    "Оникс",
    "Сапфир",
    "Жемчуг",
    "Топаз",
    "Аметист",
    "Опал",
    "Агат",
    "Бриллиант",
    "Небеса",
    "Ореол",
    "Квазар",
    "Нимб",
    "Аврора",
    "Баррикада",
    "Каратель",
    "Навигатор",
    "Пионер",
    "Квант",
    "Эклипс",
    "Галактика",
    "Импульс",
    "Метеор",
    "Нейтрон",
    "Протон",
    "Радар",
    "Сигма",
    "Циклон",
    "СБЭУ",
    "Профессионалов",
    "BEAR",
    "USEC",
    "Скайнет",
    "Скуфов",
    "Решал",
    "LABS",
    "GIGACHADS",
)


class TempVoiceABC(abc.ABC):
    def __init__(
            self,
            bot: 'BotABC',
            channel: discord.VoiceChannel,
            owner: discord.Member,
            server_id: int,
            creator: discord.Member | None = None,
    ):
        self.bot = bot
        self.channel = channel
        self.creator = creator if creator else owner
        self.owner = owner
        self.adv = ui.Adv()

        self.reminder: datetime.datetime | None | False = None

        self.privacy: Privacy = Privacy.PUBLIC
        self._invite_url: str | None = None  # Invite link on this channel
        self.server_id = server_id  # Local server id in DB

    @abc.abstractmethod
    async def invite_url(self) -> str:
        ...

    @abc.abstractmethod
    def updated(self):
        ...

    @abc.abstractmethod
    async def send_adv(self, custom_text: str) -> None:
        ...

    @abc.abstractmethod
    async def update_adv(self, custom_text: str = "") -> None:
        ...

    @abc.abstractmethod
    async def delete_adv(self) -> bool:
        ...

    @abc.abstractmethod
    async def send_reminder(self):
        ...

    @abc.abstractmethod
    def _update(
            self,
            channel: discord.VoiceChannel,
            creator: discord.Member,
            owner: discord.Member,
    ) -> None:
        ...

    @abc.abstractmethod
    async def change_owner(self, new_owner: discord.Member) -> None:
        ...

    @abc.abstractmethod
    async def get_access(self, member: discord.Member) -> None:
        """
        Set access overwrites for user
        :param member:
        :return:
        """
        ...

    @abc.abstractmethod
    async def kick(self, member: discord.Member) -> None:
        ...

    @abc.abstractmethod
    async def take_access(self, member: discord.Member) -> None:
        ...

    @abc.abstractmethod
    async def ban(self, member: discord.Member) -> None:
        ...

    @abc.abstractmethod
    async def unban(self, ban_id: int) -> int:
        ...

    @abc.abstractmethod
    async def change_privacy(self, mode: Privacy) -> None:
        ...

    @abc.abstractmethod
    async def send_interface(self):
        ...

    @abc.abstractmethod
    async def delete(self):
        ...


class ServerABC(abc.ABC):
    def __init__(self, bot: 'BotABC', guild: discord.Guild):
        self.bot = bot

        self.server_id: int | None = None  # Local ID
        self.adv_channel: discord.TextChannel | None = None
        self.guild = guild
        self._creator_channels: MappingProxyType[
            int, CreatorChannels] = MappingProxyType({})  # noqa: E501
        self._temp_channels: dict[int, TempVoiceABC] = {}

        # Random iterator for temp voice random squad name
        self._random_names = sample(SQUAD_TITLES, len(SQUAD_TITLES))
        self._random_names_index = 0

        self._last_data_update = datetime.datetime.fromtimestamp(0.)

    @abc.abstractmethod
    async def _get_settings_from_db(self, guild_id: int) -> None:
        ...

    @abc.abstractmethod
    async def update_server_data(self) -> None:
        ...

    @abc.abstractmethod
    def _get_random_squad_name(self) -> str:
        ...

    @abc.abstractmethod
    async def create_channel(
            self,
            member: discord.Member,
            creator_channel_id: int
    ) -> discord.VoiceChannel | None:
        ...

    @abc.abstractmethod
    async def del_channel(self, channel_id: int) -> None:
        ...

    @abc.abstractmethod
    def is_creator_channel(self, channel_id: int) -> bool:
        ...

    @abc.abstractmethod
    def is_temp_channel(self, channel_id: int) -> bool:
        ...

    @abc.abstractmethod
    def get_user_channel(
            self,
            member: discord.Member,
            interaction_channel_id: int = None
    ) -> TempVoiceABC | bool:
        ...

    @abc.abstractmethod
    def get_user_transferred_channel(
            self,
            member_id: int
    ) -> TempVoiceABC | bool:
        ...

    @abc.abstractmethod
    def get_creator_channels_ids(self) -> list[int]:
        ...

    @abc.abstractmethod
    def channel(self, channel_id: int) -> TempVoiceABC | None:
        ...

    @abc.abstractmethod
    def all_channels(self) -> dict[int, TempVoiceABC]:
        ...

    @abc.abstractmethod
    async def restore_channel(
            self,
            channel: discord.VoiceChannel,
            owner_id: int,
            creator_id: int,
            adv_msg_id: int,
    ) -> TempVoiceABC:
        ...


# Use commands.AutoShardedBot if you have more than 1k guilds
class BotABC(abc.ABC, commands.Bot):
    servers: dict[int, ServerABC] = {}

    @abc.abstractmethod
    def server(self, guild_id: int) -> ServerABC | None:
        ...
