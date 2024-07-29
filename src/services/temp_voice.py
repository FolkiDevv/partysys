from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timedelta

import discord

from src import ui, utils
from src.models import TCBans, TempChannels
from src.services import errors


class TempVoice(utils.TempVoiceABC):
    async def invite_url(self):
        if not self._invite_url:
            for inv in await self.channel.invites():
                if inv.inviter.id == self.bot.user.id:
                    self._invite_url = inv.url
                    break

        if not self._invite_url:
            self._invite_url = (
                await self.channel.create_invite(
                    reason="Join link to this temp voice."
                )
            ).url
        return self._invite_url

    def updated(self):
        new_state = self.bot.get_channel(self.channel.id)
        if new_state and new_state.type == discord.ChannelType.voice:
            self.channel = new_state

        if (
                self.privacy == utils.Privacy.PUBLIC
                and not self.adv
                and self.reminder is not False
                and self.channel.user_limit > len(self.channel.members)
        ):
            self.reminder = datetime.now() + timedelta(minutes=2.0)
        elif self.reminder:
            self.reminder = None

    async def send_adv(self, custom_text):
        if not (server := self.bot.server(self.channel.guild.id)):
            raise errors.BotNotConfiguredError
        elif self.adv:
            return

        if adv_msg_id := await self.adv.send(
                adv_channel=server.adv_channel, temp_voice=self,
                text=custom_text
        ):
            await (TempChannels
                   .filter(dis_id=self.channel.id)
                   .update(dis_adv_msg_id=adv_msg_id))

    async def update_adv(self, custom_text=""):
        if self.adv:
            await self.adv.update(temp_voice=self, text=custom_text)

    async def delete_adv(self):
        if self.adv:
            await self.adv.delete()
            await (TempChannels
                   .filter(dis_id=self.channel.id)
                   .update(dis_adv_msg_id=None))
            return True
        return False

    async def send_reminder(self):
        if self.privacy == utils.Privacy.PUBLIC and not self.adv:
            await self.send_adv("")
            await self.channel.send(
                embed=ui.ReminderEmbed(),
                view=ui.AdvInterface(self.bot),
                delete_after=120,
            )  # Notify users in channel that adv sent
        self.reminder = None

    def _update(
            self,
            channel,
            creator,
            owner,
    ):
        self.channel, self.creator, self.owner = channel, creator, owner

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
        await (TempChannels
               .filter(dis_id=self.channel.id)
               .update(dis_owner_id=new_owner.id))

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
            server_id=self.server_id,
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
            view=ui.ControlInterface(self.bot),
        )

    async def delete(self):
        with suppress(discord.NotFound):
            await self.channel.delete(
                reason="Temp channel is empty or deleted by owner."
            )
            await self.delete_adv()
