import abc
import datetime
from random import sample
from types import MappingProxyType
from typing import Callable, ClassVar, Literal, NoReturn, Self, final

import discord
from discord.ext import commands

from config import CFG
from src import ui
from src.models import CreatorChannels

from .enums import Privacy


class TempVoiceABC(abc.ABC):
    def __init__(
            self,
            channel: discord.VoiceChannel,
            owner: discord.Member,
            server: 'ServerABC',
            creator: discord.Member | None = None,
    ):
        self.server = server
        self.channel = channel
        self.creator = creator if creator else owner
        self.owner = owner
        self.adv = ui.Adv(self)

        self.reminder: datetime.datetime | None | False = None

        self.privacy: Privacy = Privacy.PUBLIC
        self._invite_url: str | None = None  # Invite link on this channel

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} '
            f'server={self.server} '
            f'channel={self.channel} '
            f'creator={self.creator} '
            f'owner={self.owner} '
            f'adv={self.adv} '
            f'>'
        )

    @classmethod
    @abc.abstractmethod
    async def create(
            cls,
            category: discord.CategoryChannel,
            creator_channel: CreatorChannels,
            member: discord.Member,
            name_formatter: Callable[[str], str],
            server_id: int,
    ) -> Self:
        ...

    @abc.abstractmethod
    async def invite_url(self) -> str:
        ...

    @abc.abstractmethod
    def updated(self):
        ...

    @abc.abstractmethod
    async def send_reminder(self, adv_channel: discord.TextChannel):
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
    @final
    def __new__(cls, *args, **kwargs) -> NoReturn:
        raise TypeError(f"Can't create {cls.__name__!r} objects directly")

    def __init__(self, bot: 'BotABC', guild: discord.Guild):
        self.bot = bot
        self.guild = guild

        self.id: int | None = None  # Server id in DB
        self.adv_channel: discord.TextChannel | None = None
        self._creator_channels: MappingProxyType[
            int, CreatorChannels
        ] = MappingProxyType({})
        self._temp_channels: dict[int, TempVoiceABC] = {}

        # Random iterator for temp voice random squad name
        self._random_names = tuple(
            sample(CFG['squad_names'], len(CFG['squad_names']))
        )
        self._random_names_index = 0

        self._last_data_update = datetime.datetime.fromtimestamp(0.)

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} '
            f'server_id={self.id} '
            f'guild={self.guild} '
            f'>'
        )

    @classmethod
    @final
    def new(cls, bot: 'BotABC', guild: discord.Guild) -> Self:
        instance = super().__new__(cls)
        instance.__init__(bot, guild)

        bot.loop.create_task(
            instance._update_settings(guild.id)
        )

        return instance

    @abc.abstractmethod
    async def _update_settings(self, guild_id: int) -> None:
        ...

    @abc.abstractmethod
    async def update_settings(self) -> None:
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
    def get_member_tv(
            self,
            member: discord.Member,
            interaction_channel_id: int | None = None
    ) -> TempVoiceABC | Literal[False]:
        ...

    @abc.abstractmethod
    def get_member_transferred_tv(
            self,
            member_id: discord.Member,
    ) -> TempVoiceABC | Literal[False]:
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
            adv_msg_id: int | None = None,
    ) -> TempVoiceABC:
        ...


# Use commands.AutoShardedBot if you have more than 1k guilds
class BotABC(abc.ABC, commands.Bot):
    servers: ClassVar[dict[int, ServerABC]] = {}

    @abc.abstractmethod
    def server(self, guild_id: int) -> ServerABC | None:
        ...
