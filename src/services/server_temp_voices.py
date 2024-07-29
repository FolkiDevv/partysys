from __future__ import annotations

import datetime
from types import MappingProxyType

import discord
from sentry_sdk import metrics

from src import ui, utils
from src.models import CreatorChannels, Servers, TCBans, TempChannels

from .temp_voice import TempVoice

roman_numbers = {
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
    for letter, value in roman_numbers.items():
        while number >= value:
            roman += letter
            number -= value
    return roman


class Server(utils.ServerABC):
    def _get_random_squad_name(self) -> str:
        name = self._random_names[self._random_names_index]
        if self._random_names_index >= len(self._random_names) - 1:
            self._random_names_index = 0
        else:
            self._random_names_index += 1
        return name

    async def _get_settings_from_db(self, guild_id):
        if server := await Servers.get_or_none(dis_id=guild_id):
            self.server_id: int = server.id
            self.adv_channel = self.bot.get_channel(
                server.dis_adv_channel_id
            )
        else:
            return

        # Select and store all server creator channels, where key is discord
        # channel id
        self._creator_channels = MappingProxyType(
            {channel.dis_id: channel
             for channel in
             await CreatorChannels.filter(server=self.server_id)}
        )

    async def update_server_data(self):
        if (datetime.datetime.now() - self._last_data_update
                >= datetime.timedelta(seconds=10)):
            await self._get_settings_from_db(self.guild.id)

    async def del_channel(self, channel_id):
        if channel_id in self._temp_channels:
            try:
                await self._temp_channels[channel_id].delete()
            finally:
                if channel_id in self._temp_channels:
                    del self._temp_channels[channel_id]

                await (TempChannels
                       .filter(dis_id=channel_id)
                       .update(deleted=True))

    async def create_channel(self, member, creator_channel_id):
        if creator_channel_id not in self._creator_channels:
            return None

        creator_category = self.bot.get_channel(
            self._creator_channels[creator_channel_id].dis_category_id
        )
        if not isinstance(creator_category, discord.CategoryChannel):
            return None

        temp_voice = await creator_category.create_voice_channel(
            name=str(
                self._creator_channels[creator_channel_id].def_name
            ).format(
                user=member.display_name,
                num=len(self._temp_channels) + 1,
                squad_title=self._get_random_squad_name(),
                roman_num=to_roman(len(self._temp_channels) + 1),
            )[:32],
            user_limit=self._creator_channels[creator_channel_id].def_user_limit
        )

        await TempChannels.create(
            dis_id=temp_voice.id,
            dis_creator_id=member.id,
            dis_owner_id=member.id
        )

        self._temp_channels[temp_voice.id] = TempVoice(
            self.bot, temp_voice, member, self.server_id
        )

        try:
            await member.move_to(
                temp_voice, reason="Move to created temp voice"
            )
        except discord.HTTPException as e:
            if e.code == 40032:
                # If owner leaved from creator channel delete temp voice
                await self.del_channel(temp_voice.id)
                return None
            else:
                raise e

        overwrites = {
            member: discord.PermissionOverwrite(
                move_members=True,  # deafen_members=True
            )
        }

        # Next get owner ban list and restore them to the new channel
        for raw_ban in await TCBans.filter(
                server=self.server_id,
                dis_creator_id=member.id,
                banned=True
        ):
            if banned_member := self.guild.get_member(raw_ban.dis_banned_id):
                overwrites[banned_member] = discord.PermissionOverwrite(
                    view_channel=False,
                    connect=False,
                    speak=False,
                    send_messages=False,
                    add_reactions=False,
                    send_messages_in_threads=False,
                )

        try:
            overwrites.update(temp_voice.overwrites)
            await temp_voice.edit(
                overwrites=overwrites, reason="Set permissions"
            )

            await self._temp_channels[temp_voice.id].send_interface()
        except KeyError:
            return None
        except (discord.NotFound, discord.HTTPException):
            await self.del_channel(temp_voice.id)
            return None

        metrics.incr(
            "temp_channel_created",
            1,
            tags={"server": self.guild.id},
        )

        return temp_voice if temp_voice.id in self._temp_channels else None

    def is_creator_channel(self, channel_id):
        return channel_id in self._creator_channels

    def is_temp_channel(self, channel_id):
        return channel_id in self._temp_channels

    def get_user_channel(self, member, interaction_channel_id=None):
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

    def get_user_transferred_channel(self, member_id):
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
        return self._creator_channels.keys()  # noqa

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
        owner = self.guild.get_member(owner_id) or self.guild.get_member(
            self.bot.user.id
        )
        creator = (
            owner
            if owner_id == creator_id
            else self.guild.get_member(creator_id)
        )

        self._temp_channels[channel.id] = TempVoice(
            self.bot, channel, owner, self.server_id, creator=creator
        )
        if adv_msg_id:
            try:
                if adv_msg := await self.adv_channel.fetch_message(adv_msg_id):
                    self._temp_channels[channel.id].adv = ui.Adv(adv_msg)
                    await self._temp_channels[channel.id].update_adv()
            except discord.NotFound:
                pass
        return self._temp_channels[channel.id]
