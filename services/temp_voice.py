from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timedelta

import discord

import services
from services.embeds import (
    ChannelControlEmbed,
    ErrorEmbed,
    InterfaceEmbed,
    ReminderEmbed,
    SuccessEmbed,
)
from services.errors import (
    BotNotConfiguredError,
    NoUsersInChannelError,
    UserAlreadyBannedError,
    UserAlreadyOwnerError,
    UserNotBannedError,
    UserUseAlienControlInterfaceError,
)
from services.modals import LimitModal, RenameModal
from services.views import (
    BanInterface,
    GetAccessInterface,
    KickInterface,
    PrivacyInterface,
    TakeAccessInterface,
    TransferOwnerInterface,
    UnbanInterface,
)


class ControlInterface(services.AdvInterface):
    def __init__(self, bot: services.PartySysBot):
        super().__init__(bot)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.channel_id != self.check(
            interaction
        ).channel.id and self.bot.server(interaction.guild_id).channel(
            interaction.channel_id
        ):
            raise UserUseAlienControlInterfaceError
        return True

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="rename", id=1174291347511980052),
        custom_id="rename",
        row=0,
    )
    @services.AdvInterface.check_decorator
    async def rename(
        self,
        interaction: discord.Interaction,
        temp_voice: TempVoice,
        *_,
    ):
        await interaction.response.send_modal(
            RenameModal(self.bot, temp_voice.channel.name)
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="change_limit", id=1174292033062580276),
        custom_id="limit",
        row=0,
    )
    @services.AdvInterface.check_decorator
    async def limit(
        self, interaction: discord.Interaction, temp_voice: TempVoice, *_
    ):
        await interaction.response.send_modal(
            LimitModal(self.bot, temp_voice.channel.user_limit)
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="privacy", id=1174291348388589652),
        custom_id="privacy",
        row=0,
    )
    @services.AdvInterface.check_decorator
    async def privacy(
        self, interaction: discord.Interaction, temp_voice: TempVoice, *_
    ):
        await interaction.response.send_message(
            ephemeral=True,
            view=PrivacyInterface(self.bot, temp_voice.privacy),
            embed=InterfaceEmbed(
                title="Изменение приватности",
                text="🔓 Публичный - все пользователи могут "
                "присоединяться/видеть ваш канал."
                "\n🔒 Закрытый - присоединиться смогут только те "
                "пользователи, которым вы "
                "<:get_access:1174291352339623956>"
                "Разрешите.\n"
                "🔐 Скрытый - аналогичен Закрытому, однако в этом случае "
                "пользователи,"
                "которым вы не <:get_access:1174291352339623956> Разрешали не "
                "смогут видеть ваш канал.",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="get_access", id=1174291352339623956),
        custom_id="get_access",
        row=1,
    )
    @services.AdvInterface.check_decorator
    async def get_access(self, interaction: discord.Interaction, *_):
        await interaction.response.send_message(
            ephemeral=True,
            view=GetAccessInterface(self.bot),
            embed=InterfaceEmbed(
                title="Разрешить просматривать/подключаться к каналу",
                text="Выбранные пользователи смогут "
                "присоединяться/просматривать ваш канал"
                "(используйте, если режим приватности вашего канала не "
                "Публичный).",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="take_access", id=1174291359792898218),
        custom_id="take_access",
        row=1,
    )
    @services.AdvInterface.check_decorator
    async def take_access(self, interaction: discord.Interaction, *_):
        await interaction.response.send_message(
            ephemeral=True,
            view=TakeAccessInterface(self.bot),
            embed=InterfaceEmbed(
                title="Запретить просматривать/подключаться к каналу",
                text="Выбранные пользователи НЕ смогут "
                "присоединяться/просматривать ваш канал"
                "(вне зависимости от выбранных настроек приватности).",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="kick", id=1174291365300011079),
        custom_id="kick",
        row=1,
    )
    @services.AdvInterface.check_decorator
    async def kick(
        self, interaction: discord.Interaction, temp_voice: TempVoice, *_
    ):
        if len(temp_voice.channel.members) > 1:
            await interaction.response.send_message(
                ephemeral=True,
                view=KickInterface(
                    self.bot, temp_voice.channel.members, temp_voice.owner
                ),
                embed=InterfaceEmbed(
                    title="Выгнать пользователя",
                    text="Выбранный пользователь будет отключен от голосового "
                    "канала.",
                ),
            )
        else:
            raise NoUsersInChannelError

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="ban", id=1174291351106506792),
        custom_id="ban",
        row=1,
    )
    @services.AdvInterface.check_decorator
    async def ban(self, interaction: discord.Interaction, *_):
        await interaction.response.send_message(
            ephemeral=True,
            view=BanInterface(self.bot),
            embed=InterfaceEmbed(
                title="Забанить пользователя",
                text="Выбранный пользователь будет отключен от текущего "
                "голосового канала"
                "и не сможет просматривать/подключаться к вашим "
                "ново-созданным каналам.",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="unban", id=1174291357586706442),
        custom_id="unban",
        row=2,
    )
    @services.AdvInterface.check_decorator
    async def unban(
        self, interaction: discord.Interaction, temp_voice: TempVoice, *_
    ):
        self.bot.cur.execute(
            "SELECT id, dis_banned_id FROM ban_list WHERE server_id=%s AND "
            "dis_creator_id=%s AND banned=1",
            (temp_voice.server_id, temp_voice.creator.id),
        )
        ban_list_raw = self.bot.cur.fetchall()
        if len(ban_list_raw):
            await interaction.response.send_message(
                ephemeral=True,
                view=UnbanInterface(self.bot, interaction.guild, ban_list_raw),
                embed=InterfaceEmbed(
                    title="Разбанить пользователя",
                    text="Выбранный пользователь будет убран с вашего "
                    "бан-листа.",
                ),
            )
        else:
            await interaction.response.send_message(
                ephemeral=True,
                embed=ErrorEmbed(
                    "Список заблокированных пользователей пуст."
                    "\nНе бойтесь его пополнить, если потребуется :)"
                ),
            )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="return_owner", id=1174291361390940241),
        custom_id="return_owner",
        row=2,
    )
    async def return_owner(self, interaction: discord.Interaction, *_):
        server = self.bot.server(interaction.guild_id)
        if server:
            temp_voice = server.get_user_transferred_channel(
                interaction.user.id
            )
            if temp_voice and temp_voice.owner != temp_voice.creator:
                if server.get_user_channel(interaction.user):
                    raise UserAlreadyOwnerError
                await temp_voice.channel.send(
                    f"<:info:1177314633124696165> {temp_voice.owner.mention} "
                    f"Права на управления каналом были возвращены "
                    f"создателю канала."
                )
                await temp_voice.change_owner(interaction.user)
                await interaction.response.send_message(
                    ephemeral=True,
                    embed=SuccessEmbed(
                        "Вам возвращены права на управления каналом."
                    ),
                )
            else:
                raise UserAlreadyOwnerError
        else:
            raise BotNotConfiguredError

    @discord.ui.button(
        emoji=discord.PartialEmoji(
            name="transfer_owner", id=1174291356210962462
        ),
        custom_id="transfer_owner",
        row=2,
    )
    @services.AdvInterface.check_decorator
    async def transfer_owner(self, interaction: discord.Interaction, *_):
        await interaction.response.send_message(
            ephemeral=True,
            view=TransferOwnerInterface(self.bot),
            embed=InterfaceEmbed(
                title="Передать права на управление каналом",
                text="Выбранный пользователь получит ваши права на "
                "управление каналом "
                "и вы больше не сможете им управлять, пока не вернете их себе.",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="trash", id=1174291363873951776),
        custom_id="del_channel",
        row=2,
    )
    @services.AdvInterface.check_decorator
    async def del_channel(
        self, interaction: discord.Interaction, temp_voice: TempVoice, *_
    ):
        await self.bot.server(interaction.guild_id).del_channel(
            temp_voice.channel.id
        )


class TempVoice:
    def __init__(
        self,
        bot: services.PartySysBot,
        channel: discord.VoiceChannel,
        owner: discord.Member,
        server_id: int,
        creator: discord.Member | None = None,
    ):
        self.bot = bot
        self.channel = channel
        self.creator = creator if creator else owner
        self.owner = owner
        self.adv = services.Adv()

        self.reminder: datetime | None | False = None

        self.privacy = "0"  # 0 - public, 1 - closed, 2 - hidden
        self._invite_url: str | None = None  # Invite link on this channel
        self.server_id = server_id  # Local server id in DB

    @property
    async def invite_url(self) -> str:
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
            self.privacy == "0"
            and not self.adv
            and self.reminder is not False
            and self.channel.user_limit > len(self.channel.members)
        ):
            self.reminder = datetime.now() + timedelta(minutes=2.0)
        elif self.reminder:
            self.reminder = None

    async def send_adv(self, custom_text: str) -> None:
        if not (server := self.bot.server(self.channel.guild.id)):
            raise BotNotConfiguredError
        elif self.adv:
            return

        if adv_msg_id := await self.adv.send(
            adv_channel=server.adv_channel, temp_voice=self, text=custom_text
        ):
            self.bot.cur.execute(
                "UPDATE temp_channels SET dis_adv_msg_id=%s WHERE dis_id=%s",
                (adv_msg_id, self.channel.id),
            )

    async def update_adv(self, custom_text: str = "") -> None:
        if self.adv:
            await self.adv.update(temp_voice=self, text=custom_text)

    async def delete_adv(self) -> bool:
        if self.adv:
            await self.adv.delete()
            self.bot.cur.execute(
                "UPDATE temp_channels SET dis_adv_msg_id=NULL WHERE dis_id=%s",
                (self.channel.id,),
            )
            return True
        return False

    async def send_reminder(self):
        """
        Send reminder for channel owner
        :return:
        """
        if self.privacy == "0" and not self.adv:
            await self.send_adv("")
            await self.channel.send(
                embed=ReminderEmbed(),
                view=services.AdvInterface(self.bot),
                delete_after=120,
            )  # Notify users in channel that adv sent
        self.reminder = None

    def _update(
        self,
        channel: discord.VoiceChannel,
        creator: discord.Member,
        owner: discord.Member,
    ) -> None:
        self.channel, self.creator, self.owner = channel, creator, owner

    async def change_owner(self, new_owner: discord.Member) -> None:
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
        self.bot.cur.execute(
            "UPDATE temp_channels SET dis_owner_id=%s WHERE dis_id=%s",
            (new_owner.id, self.channel.id),
        )

    async def get_access(self, member: discord.Member) -> None:
        """
        Set access overwrites for user
        :param member:
        :return:
        """
        await self.channel.set_permissions(
            target=member,
            overwrite=discord.PermissionOverwrite(
                view_channel=True, connect=True
            ),
        )

    async def kick(self, member: discord.Member) -> None:
        if (
            member.voice
            and member.voice.channel
            and member.voice.channel == self.channel
        ):
            await member.move_to(channel=None, reason="Kicked by channel owner")

    async def take_access(self, member: discord.Member) -> None:
        """
        Set block overwrites for user
        :param member:
        :return:
        """
        await self.channel.set_permissions(
            target=member,
            overwrite=discord.PermissionOverwrite(
                view_channel=False, connect=False
            ),
        )
        await self.kick(member)

    async def ban(self, member: discord.Member) -> None:
        # Check if the user is already banned
        self.bot.cur.execute(
            "SELECT banned FROM ban_list WHERE server_id=%s AND "
            "dis_creator_id=%s AND dis_banned_id=%s",
            (self.server_id, self.creator.id, member.id),
        )

        if result := self.bot.cur.fetchone():
            if result["banned"]:
                raise UserAlreadyBannedError
            else:
                # Update the ban status if the user is not banned
                self.bot.cur.execute(
                    "UPDATE ban_list SET banned=1 WHERE server_id=%s AND "
                    "dis_creator_id=%s AND dis_banned_id=%s",
                    (self.server_id, self.creator.id, member.id),
                )
        else:
            # Insert a new ban record if the user is not in the ban list
            self.bot.cur.execute(
                "INSERT INTO ban_list (dis_creator_id, dis_banned_id, "
                "server_id, banned) VALUES (%s, %s, %s, 1)",
                (self.creator.id, member.id, self.server_id),
            )
        await self.take_access(member)

    async def unban(self, ban_id: int) -> int:
        self.bot.cur.execute(
            "SELECT * FROM ban_list WHERE id=%s LIMIT 1", (ban_id,)
        )
        ban = self.bot.cur.fetchone()
        if ban and ban["banned"]:
            self.bot.cur.execute(
                "UPDATE ban_list SET banned=0 WHERE id=%s", (ban_id,)
            )
            if member := self.channel.guild.get_member(ban["dis_banned_id"]):
                await self.channel.set_permissions(
                    target=member, overwrite=None
                )  # Drop overwrite on this user
                return member.id
            else:
                return 1
        else:
            raise UserNotBannedError

    async def change_privacy(self, mode: str) -> None:
        overwrite = discord.PermissionOverwrite()
        if mode == "1":
            overwrite.update(view_channel=True, connect=False)
        elif mode == "2":
            overwrite.update(view_channel=False, connect=False)
        else:
            overwrite.update(view_channel=True, connect=True)
        self.privacy = mode
        await self.channel.set_permissions(
            target=self.channel.guild.default_role, overwrite=overwrite
        )

    async def send_interface(self):
        await self.channel.send(
            embed=ChannelControlEmbed(),
            content=self.owner.mention,
            view=ControlInterface(self.bot),
        )

    async def delete(self):
        with suppress(discord.NotFound):
            await self.channel.delete(
                reason="Temp channel empty or deleted by owner."
            )
            await self.delete_adv()
