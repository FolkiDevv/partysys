from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timedelta
from typing import Self

import discord

from config import CFG
from src import ui, utils
from src.models import TCBans, TempChannels
from src.services import errors


class TempVoice(utils.TempVoiceABC):
    __slots__ = (
        "channel",
        "server",
        "creator",
        "owner",
        "adv",
        "reminder",
        "privacy",
        "_invite_url",
    )

    @classmethod
    async def create(
        cls,
        category,
        creator_channel,
        member,
        name_formatter,
        server,
    ) -> Self:
        channel = await category.create_voice_channel(
            name=name_formatter(creator_channel.def_name),
            user_limit=creator_channel.def_user_limit,
        )
        temp_voice = cls(
            channel,
            member,
            server,
            member,
        )

        await TempChannels.create(
            dis_id=channel.id,
            dis_creator_id=member.id,
            dis_owner_id=member.id,
            server_id=server.id,
        )

        try:
            await member.move_to(
                channel,
                reason="Move to created temp voice",
            )
        except discord.HTTPException as e:
            if e.code == 40032:
                # If owner leaved from creator channel delete temp voice
                await temp_voice.delete()
            raise e

        overwrites = {
            member: discord.PermissionOverwrite(
                move_members=True,
            )
        }

        # Next get owner ban list and restore them to the new channel
        for raw_ban in await TCBans.filter(
            server=server.id, dis_creator_id=member.id, banned=True
        ):
            if banned_member := channel.guild.get_member(raw_ban.dis_banned_id):
                overwrites[banned_member] = discord.PermissionOverwrite(
                    view_channel=False,
                    connect=False,
                    speak=False,
                    send_messages=False,
                    add_reactions=False,
                    send_messages_in_threads=False,
                )

        try:
            overwrites.update(channel.overwrites)
            await channel.edit(overwrites=overwrites, reason="Set permissions")

            await temp_voice.send_interface()
        except (discord.NotFound, discord.HTTPException) as err:
            await temp_voice.delete()
            raise err

        return temp_voice

    async def invite_url(self):
        if not self._invite_url:
            for inv in await self.channel.invites():
                if inv.inviter.id == self.server.bot.user.id:
                    self._invite_url = inv.url
                    return self._invite_url

            self._invite_url = (
                await self.channel.create_invite(
                    reason="Join link to this temp voice."
                )
            ).url
        return self._invite_url

    def updated(self):
        if new_state := self.server.bot.get_channel(self.channel.id):
            self.channel = new_state

        if (
            self.privacy == utils.Privacy.PUBLIC
            and not self.adv
            and self.reminder is not False
            and self.channel.user_limit > len(self.channel.members)
        ):
            self.reminder = datetime.now() + timedelta(
                minutes=CFG["before_auto_pub"]
            )
        elif self.reminder:
            self.reminder = None

    async def send_reminder(self, adv_channel):
        if self.privacy == utils.Privacy.PUBLIC and not self.adv:
            await self.adv.send("")
            await self.channel.send(
                embed=ui.ReminderEmbed(),
                view=ui.AdvInterface(self.server.bot),
                delete_after=120,
            )  # Notify users in channel that adv sent
        self.reminder = None

    async def change_owner(self, new_owner):
        self.owner = new_owner
        await self.channel.set_permissions(
            target=self.creator, overwrite=None
        )  # Reset temp voice old owner permissions
        await self.channel.set_permissions(
            target=self.owner,
            overwrite=discord.PermissionOverwrite(
                move_members=True,  # deafen_members=True,
            ),
        )  # Get temp voice new owner permissions
        await TempChannels.filter(dis_id=self.channel.id).update(
            dis_owner_id=new_owner.id
        )

    async def get_access(self, member):
        await self.channel.set_permissions(
            target=member,
            overwrite=discord.PermissionOverwrite(
                view_channel=True,
                read_messages=True,
                connect=True,
                send_messages=True,
            ),
        )

    async def kick(self, member):
        if (
            member.voice
            and member.voice.channel
            and member.voice.channel == self.channel
        ):
            await member.move_to(channel=None, reason="Kicked by channel owner")

    async def take_access(self, member):
        """
        Set block overwrites for user
        :param member:
        :return:
        """
        await self.channel.set_permissions(
            target=member,
            overwrite=discord.PermissionOverwrite(
                view_channel=False,
                read_messages=False,
                connect=False,
                send_messages=False,
            ),
        )
        await self.kick(member)

    async def ban(self, member):
        await TCBans.update_or_create(
            server_id=self.server.id,
            dis_creator_id=self.creator.id,
            dis_banned_id=member.id,
            banned=True,
        )
        await self.take_access(member)

    async def unban(self, ban_id):
        ban = await TCBans.get_or_none(id=ban_id)
        if ban and ban.banned:
            ban.banned = False
            await ban.save()
            if member := self.channel.guild.get_member(ban.dis_banned_id):
                await self.channel.set_permissions(
                    target=member, overwrite=None
                )  # Drop overwrite on this user
                return member.id
            else:
                return 1
        else:
            raise errors.UserNotBannedError

    async def change_privacy(self, mode):
        overwrite = discord.PermissionOverwrite()
        match mode:
            case utils.Privacy.PUBLIC:
                overwrite.update(
                    view_channel=True,
                    read_messages=True,
                    connect=True,
                    send_messages=True,
                )
            case utils.Privacy.PRIVATE:
                overwrite.update(
                    view_channel=True,
                    read_messages=True,
                    connect=False,
                    send_messages=False,
                )
            case utils.Privacy.HIDDEN:
                overwrite.update(
                    view_channel=False,
                    read_messages=False,
                    connect=False,
                    send_messages=False,
                )
            case _:
                raise ValueError("Invalid mode")

        self.privacy = mode
        await self.channel.set_permissions(
            target=self.channel.guild.default_role, overwrite=overwrite
        )

    async def send_interface(self):
        await self.channel.send(
            embed=ui.ChannelControlEmbed(),
            content=self.owner.mention,
            view=ui.ControlInterface(self.server.bot),
        )

    async def delete(self):
        with suppress(discord.NotFound):
            await self.channel.delete(
                reason="Temp channel is empty or deleted by owner."
            )
            await self.adv.delete()

            await TempChannels.filter(dis_id=self.channel.id).update(
                deleted=True
            )
