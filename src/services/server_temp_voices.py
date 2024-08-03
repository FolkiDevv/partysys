from __future__ import annotations

import datetime
from contextlib import suppress
from types import MappingProxyType

import discord
from sentry_sdk import metrics

from src import ui, utils
from src.models import CreatorChannels, Servers

from .temp_voice import TempVoice

ROMAN_NUMBERS = {
    "M": 1000,
    "CM": 900,
    "D": 500,
    "CD": 400,
    "C": 100,
    "XC": 90,
    "L": 50,
    "XL": 40,
    "X": 10,
    "IX": 9,
    "V": 5,
    "IV": 4,
    "I": 1,
}


def to_roman(number):
    roman = ""
    for letter, value in ROMAN_NUMBERS.items():
        while number >= value:
            roman += letter
            number -= value
    return roman


class Server(utils.ServerABC):
    __slots__ = (
        "bot",
        "guild",

        "server_id",
        "adv_channel",
        "_creator_channels",
        "_temp_channels",

        "_random_names",
        "_random_names_index",

        "_last_data_update",
    )

    def _get_random_squad_name(self) -> str:
        name = self._random_names[self._random_names_index]
        if self._random_names_index >= len(self._random_names) - 1:
            self._random_names_index = 0
        else:
            self._random_names_index += 1
        return name

    async def _update_settings(self, guild_id):
        # TODO: адекватная обработка случая когда сервера нет в БД
        if server := await Servers.get_or_none(dis_id=guild_id):
            self.server_id = server.id
            self.adv_channel = self.bot.get_channel(
                server.dis_adv_channel_id
            )
            self._last_data_update = datetime.datetime.now()

            self._creator_channels = MappingProxyType(
                {channel.dis_id: channel
                 for channel in
                 await CreatorChannels.filter(server=self.server_id)}
            )

    async def update_settings(self):
        if (datetime.datetime.now() - self._last_data_update
                >= datetime.timedelta(seconds=10)):
            await self._update_settings(self.guild.id)

    async def del_channel(self, channel_id):
        if channel_id in self._temp_channels:
            try:
                await self._temp_channels[channel_id].delete()
            finally:
                if channel_id in self._temp_channels:
                    del self._temp_channels[channel_id]

    async def create_channel(self, member, creator_channel_id):
        if creator_channel_id not in self._creator_channels:
            return None

        creator_category = self.bot.get_channel(
            self._creator_channels[creator_channel_id].dis_category_id
        )
        if not isinstance(creator_category, discord.CategoryChannel):
            return None

        def _channel_name_formatter(name: str) -> str:
            return name.format(
                user=member.display_name,
                num=len(self._temp_channels) + 1,
                squad_title=self._get_random_squad_name(),
                roman_num=to_roman(len(self._temp_channels) + 1),
            )[:32]

        try:
            temp_voice = await TempVoice.create(
                self.bot,
                creator_category,
                self._creator_channels[creator_channel_id],
                member,
                _channel_name_formatter,
                self.server_id,
            )
        except (discord.NotFound, discord.HTTPException):
            return None

        self._temp_channels[temp_voice.channel.id] = temp_voice

        metrics.incr(
            "temp_channel_created",
            1,
            tags={"server": self.guild.id},
        )

        return temp_voice.channel \
            if temp_voice.channel.id in self._temp_channels \
            else None

    def is_creator_channel(self, channel_id):
        return channel_id in self._creator_channels

    def is_temp_channel(self, channel_id):
        return channel_id in self._temp_channels

    def get_member_tv(self, member, interaction_channel_id=None):
        if (
                interaction_channel_id
                and member.guild_permissions.administrator
                and interaction_channel_id in self._temp_channels
        ):
            return self._temp_channels[interaction_channel_id]

        for temp_channel in self._temp_channels.values():
            if temp_channel.owner.id == member.id:
                return temp_channel
        return False

    def get_member_transferred_tv(self, member_id):
        """
        Try to find user temp voice when user transfer his owner
        :param member_id:
        :return:
        """
        for temp_channel in self._temp_channels.values():
            if temp_channel.creator.id == member_id:
                return temp_channel
        return False

    def get_creator_channels_ids(self):
        return self._creator_channels.keys()

    def channel(self, channel_id):
        if channel_id not in self._temp_channels:
            return None

        return self._temp_channels[channel_id]

    def all_channels(self):
        return self._temp_channels

    async def restore_channel(
            self,
            channel,
            owner_id,
            creator_id,
            adv_msg_id,
    ):
        owner = self.guild.get_member(owner_id)
        creator = (
            owner
            if owner_id == creator_id
            else self.guild.get_member(creator_id)
        )

        temp_voice = TempVoice(
            self.bot,
            channel,
            owner,
            self.server_id,
            creator,
        )

        self._temp_channels[channel.id] = temp_voice
        if adv_msg_id:
            with suppress(discord.NotFound):
                if adv_msg := await self.adv_channel.fetch_message(adv_msg_id):
                    self._temp_channels[channel.id].adv = ui.Adv(
                        channel.id,
                        adv_msg
                    )
                    await self._temp_channels[channel.id].adv.update()
        return self._temp_channels[channel.id]
