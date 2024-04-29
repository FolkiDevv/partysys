from __future__ import annotations

import asyncio
import logging
import traceback
from contextlib import suppress
from datetime import datetime, timedelta

import discord
import sentry_sdk

import source.bot_class
from source.base_classes import BaseModal, BaseView
from source.embeds import (
    ChannelControlEmbed,
    ErrorEmbed,
    InterfaceEmbed,
    ReminderEmbed,
    SuccessEmbed,
)
from source.errors import (
    AdvChannelIsFull,
    AdvRequirePublicPrivacy,
    BotNotConfigured,
    NoUsersInChannel,
    UnknownDisError,
    UserAlreadyBanned,
    UserAlreadyOwner,
    UserBanLimit,
    UserNotBanned,
    UserNoTempChannels,
    UserUseAlienControlInterface,
)
from source.modals import LimitModal, RenameModal
from source.views import (
    BanInterface,
    GetAccessInterface,
    JoinInterface,
    KickInterface,
    PrivacyInterface,
    TakeAccessInterface,
    TransferOwnerInterface,
    UnbanInterface,
)


class AdvModal(BaseModal):
    def __init__(self, temp_voice: TempVoice):
        super().__init__(
            title="Изменить объявление"
            if temp_voice.adv
            else "Опубликовать объявление",
            custom_id="adv:public:modal",
        )
        self.temp_voice = temp_voice

        self.text_inp = discord.ui.TextInput(
            label="Текст объявления",
            placeholder="Опишите требования к искомым тиммейтам/ваши планы. "
            "Оставьте пустым, если нечего сказать.",
            style=discord.TextStyle.long,
            required=False,
            max_length=240,
            custom_id="adv:public:modal:text_input",
            default=temp_voice.adv.custom_text
            if temp_voice.adv and len(temp_voice.adv.custom_text)
            else None,
        )
        self.add_item(self.text_inp)

    async def on_submit(self, interaction: discord.Interaction):
        if self.temp_voice.adv:
            await self.temp_voice.update_adv(custom_text=self.text_inp.value)
            await interaction.response.edit_message(
                view=None,
                embed=SuccessEmbed("Объявление было отредактировано."),
            )
        elif self.temp_voice.channel.user_limit == 0:
            await self.temp_voice.send_adv(custom_text=self.text_inp.value)
            await interaction.response.send_message(
                ephemeral=True,
                embed=SuccessEmbed(
                    "Объявление было отправлено.\nУ вашего канала нет "
                    "ограничению по числу пользователей,"
                    "поэтому объявление будет удалено спустя 2 минуты простоя "
                    "без изменений."
                ),
            )
            sentry_sdk.metrics.incr(
                "adv_manual_send",
                1,
                tags={"server": self.temp_voice.server_id},
            )
        else:
            await self.temp_voice.send_adv(custom_text=self.text_inp.value)
            await interaction.response.send_message(
                ephemeral=True,
                embed=SuccessEmbed("Объявление было отправлено."),
            )
            sentry_sdk.metrics.incr(
                "adv_manual_send",
                1,
                tags={"server": self.temp_voice.server_id},
            )


class AdvControlInterface(BaseView):
    def __init__(self, temp_voice: TempVoice):
        super().__init__()
        self.temp_voice = temp_voice

    @discord.ui.button(
        emoji="📝", custom_id="adv:public", style=discord.ButtonStyle.primary
    )
    async def adv_public(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        if self.temp_voice.privacy == "0":
            if self.temp_voice.channel.user_limit > len(
                self.temp_voice.channel.members
            ):
                await interaction.response.send_modal(AdvModal(self.temp_voice))
            else:
                raise AdvChannelIsFull
        else:
            raise AdvRequirePublicPrivacy

    @discord.ui.button(
        emoji="🗑️", custom_id="adv:delete", style=discord.ButtonStyle.red
    )
    async def adv_delete(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        # Disable reminder
        self.temp_voice.reminder = False
        await self.temp_voice.delete_adv()
        await interaction.response.edit_message(
            view=None, embed=SuccessEmbed("Объявление было удалено.")
        )


class AdvEmbed(discord.Embed):
    def __init__(self, temp_voice: TempVoice, text: str):
        super().__init__()
        self._gen_text(custom_text=text, temp_voice=temp_voice)

    @staticmethod
    def _gen_user_list(temp_voice: TempVoice) -> list[str]:
        text: list[str] = []
        max_users_count, users_count = (
            temp_voice.channel.user_limit,
            len(temp_voice.channel.members),
        )

        for member in temp_voice.channel.members:
            # Print first 15 users
            if member.id == temp_voice.owner.id:
                text.insert(
                    0,
                    f"<:king_yellow:1176147111239233656> "
                    f"{temp_voice.owner.mention}",
                )
            else:
                text.append(
                    f"<:member_white:1176147115282534440> {member.mention}"
                )

        text = text[:15]

        if len(temp_voice.channel.members) > 10:
            text.append(
                f"...\nИ другие <:member_white:1176147115282534440> "
                f"{len(text) - 10} пользователей."
            )

        if max_users_count == 0:
            text.append(
                "...\nНеограниченное число <:member_blue:1176147113739026432> "
                "свободных мест."
            )
        elif max_users_count - users_count > 10:
            text.append(
                f"...\nОсталось <:member_blue:1176147113739026432> "
                f"{max_users_count - users_count} свободных мест."
            )
        else:
            for _ in range(max_users_count - users_count):
                text.append("<:member_blue:1176147113739026432> ▢")

        return text

    def _gen_text(self, custom_text: str, temp_voice: TempVoice) -> None:
        if temp_voice.owner.avatar:
            avatar = temp_voice.owner.avatar.url
        else:
            avatar = temp_voice.owner.default_avatar.url
        self.set_author(name=f"{temp_voice.channel.name}", icon_url=avatar)

        max_users_count, users_count = (
            temp_voice.channel.user_limit,
            len(temp_voice.channel.members),
        )
        text: list[str] = []
        if len(custom_text):
            text.append(f"📢 {custom_text}\n")

        text += self._gen_user_list(temp_voice)  # Append users list

        if max_users_count == 0:
            self.set_footer(
                text="🔎 В поиске команды. Без ограничений по количеству."
            )
            self.colour = 0x57F287
        elif users_count >= max_users_count:
            self.set_footer(text="Канал заполнен ⛔")
            self.colour = 0x303136
        else:
            self.set_footer(
                text=f"🔎 В поиске команды. +{max_users_count - users_count}"
            )
            self.colour = 0x57F287

        self.description = "\n".join(text)
        self.timestamp = datetime.now()


class Adv:
    def __init__(self, msg: discord.Message = None):
        self._message: discord.Message | None = msg
        self.custom_text: str = ""
        self.delete_after: datetime | None = None

        self._update_delayed: bool = False

    async def send(
        self, adv_channel: discord.TextChannel, temp_voice: TempVoice, text: str
    ) -> int:
        try:
            self.custom_text = text

            view = JoinInterface(
                invite_url=temp_voice.invite_url,
                disabled=len(temp_voice.channel.members)
                >= temp_voice.channel.user_limit,
            )

            if temp_voice.channel.user_limit == 0:
                # If channel has unlimited slots, adv will be deleted after 3
                # minutes without changes
                self.delete_after = datetime.now() + timedelta(minutes=3.0)

            self._message = await adv_channel.send(
                embed=AdvEmbed(temp_voice=temp_voice, text=self.custom_text),
                view=view,
            )
            return self._message.id
        except Exception as e:
            logging.error(traceback.format_exc())
            raise UnknownDisError from e

    async def update(self, temp_voice: TempVoice, text: str = "") -> None:
        if text:
            self.custom_text = text
        elif self._message is None and not self._update_delayed:
            # if channel update state while adv sent
            self._update_delayed = True

            await asyncio.sleep(2.0)

            temp_voice.updated()
            await self.update(temp_voice, text)

            return
        elif self._update_delayed:
            self._update_delayed = False

        if temp_voice.channel.user_limit == 0:
            self.delete_after = datetime.now() + timedelta(minutes=3.0)
        elif len(temp_voice.channel.members) >= temp_voice.channel.user_limit:
            self.delete_after = datetime.now() + timedelta(minutes=4.0)
        else:
            self.delete_after = None

        view = None
        if temp_voice.privacy not in ("1", "2"):
            if not temp_voice.invite_url:
                try:
                    await temp_voice.get_invite()
                except discord.NotFound:
                    return

            view = JoinInterface(
                invite_url=temp_voice.invite_url,
                disabled=len(temp_voice.channel.members)
                >= temp_voice.channel.user_limit
                if temp_voice.channel.user_limit > 0
                else False,
            )

        try:
            await self._message.edit(
                embed=AdvEmbed(temp_voice=temp_voice, text=self.custom_text),
                view=view,
            )
        except discord.NotFound:
            await temp_voice.delete_adv()
        except discord.HTTPException as e:
            if e.code == 30046:
                # If too many requests, remove and send new adv
                with suppress(discord.NotFound):
                    await self.delete()
                    await temp_voice.send_adv(custom_text=self.custom_text)
            else:
                raise e

    async def delete(self) -> bool:
        if not self._message:
            return False

        try:
            await self._message.delete()
        except discord.DiscordServerError as e:
            if e.code == 0:
                with suppress(discord.NotFound):
                    msg = await self._message.fetch()
                    await msg.delete()
            else:
                raise e
        except discord.NotFound:
            pass

        self._message, self.delete_after = None, None
        self._update_delayed = False
        return True


class ReminderInterface(BaseView):
    def __init__(self, bot: source.bot_class.PartySysBot):
        super().__init__(timeout=None)
        self.bot = bot

    def check(self, interaction: discord.Interaction) -> TempVoice:
        server = self.bot.server(interaction.guild_id)
        if server:
            temp_channel = server.get_user_channel(
                interaction.user, interaction.channel_id
            )
            if temp_channel:
                return temp_channel
        raise UserNoTempChannels

    @discord.ui.button(
        emoji="🪧", custom_id="reminder:adv", style=discord.ButtonStyle.primary
    )
    async def adv(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        temp_voice = self.check(interaction)
        if temp_voice.adv is None:
            # If no created adv, send creation modal
            if temp_voice.privacy == "0":
                if temp_voice.channel.user_limit > len(
                    temp_voice.channel.members
                ):
                    await interaction.response.send_modal(AdvModal(temp_voice))
                else:
                    raise AdvChannelIsFull
            else:
                raise AdvRequirePublicPrivacy
        else:
            await interaction.response.send_message(
                ephemeral=True,
                view=AdvControlInterface(temp_voice),
                embed=InterfaceEmbed(
                    "Управление объявлением",
                    "📝 - Изменить текст объявления.\n\n🗑️ - Удалить "
                    "объявление.",
                ),
            )


class ControlInterface(BaseView):
    def __init__(self, bot: source.bot_class.PartySysBot):
        super().__init__(timeout=None)
        self.bot = bot

    def check(self, interaction: discord.Interaction) -> TempVoice:
        server = self.bot.server(interaction.guild_id)
        if server:
            temp_channel = server.get_user_channel(
                interaction.user, interaction.channel_id
            )
            if temp_channel:
                return temp_channel
        raise UserNoTempChannels

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        temp_voice = self.check(interaction)
        if (
            interaction.channel_id != temp_voice.channel.id
            and self.bot.server(interaction.guild_id).channel(
                interaction.channel_id
            )
            is not None
        ):
            raise UserUseAlienControlInterface
        return True

    @discord.ui.button(
        emoji="🪧", custom_id="adv", row=0, style=discord.ButtonStyle.primary
    )
    async def adv(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        temp_voice = self.check(interaction)
        if temp_voice.adv is None:
            # If no created adv, send creation modal
            if temp_voice.privacy == "0":
                if temp_voice.channel.user_limit > len(
                    temp_voice.channel.members
                ):
                    await interaction.response.send_modal(AdvModal(temp_voice))
                else:
                    raise AdvChannelIsFull
            else:
                raise AdvRequirePublicPrivacy
        else:
            await interaction.response.send_message(
                ephemeral=True,
                view=AdvControlInterface(temp_voice),
                embed=InterfaceEmbed(
                    "Управление объявлением",
                    "📝 - Изменить текст объявления.\n\n🗑️ - Удалить "
                    "объявление.",
                ),
            )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="rename", id=1174291347511980052),
        custom_id="rename",
        row=0,
    )
    async def rename(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        temp_voice = self.check(interaction)
        await interaction.response.send_modal(
            RenameModal(self.bot, temp_voice.channel.name)
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="change_limit", id=1174292033062580276),
        custom_id="limit",
        row=0,
    )
    async def limit(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        temp_voice = self.check(interaction)
        await interaction.response.send_modal(
            LimitModal(self.bot, temp_voice.channel.user_limit)
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="privacy", id=1174291348388589652),
        custom_id="privacy",
        row=0,
    )
    async def privacy(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        temp_voice = self.check(interaction)
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
    async def get_access(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.check(interaction)
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
    async def take_access(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.check(interaction)
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
    async def kick(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        temp_voice = self.check(interaction)
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
            raise NoUsersInChannel

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="ban", id=1174291351106506792),
        custom_id="ban",
        row=1,
    )
    async def ban(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.check(interaction)
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
    async def unban(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        temp_voice = self.check(interaction)

        query = self.bot.cur.execute(
            "SELECT id, dis_banned_id FROM ban_list WHERE server_id=%s AND dis_creator_id=%s AND banned=1",
            (temp_voice.server_id, temp_voice.creator.id),
        )
        if query:
            ban_list_raw = self.bot.cur.fetchall()
            if len(ban_list_raw):
                await interaction.response.send_message(
                    ephemeral=True,
                    view=UnbanInterface(
                        self.bot, interaction.guild, ban_list_raw
                    ),
                    embed=InterfaceEmbed(
                        title="Разбанить пользователя",
                        text="Выбранный пользователь будет убран с вашего "
                        "бан-листа.",
                    ),
                )
                return
        await interaction.response.send_message(
            ephemeral=True,
            embed=ErrorEmbed(
                "Список заблокированных пользователей пуст.\nНе бойтесь его "
                "пополнить, если потребуется :)"
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="return_owner", id=1174291361390940241),
        custom_id="return_owner",
        row=2,
    )
    async def return_owner(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        server = self.bot.server(interaction.guild_id)
        if server:
            temp_voice = server.get_user_transferred_channel(
                interaction.user.id
            )
            if temp_voice and temp_voice.owner != temp_voice.creator:
                if server.get_user_channel(interaction.user):
                    raise UserAlreadyOwner
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
                raise UserAlreadyOwner
        else:
            raise BotNotConfigured

    @discord.ui.button(
        emoji=discord.PartialEmoji(
            name="transfer_owner", id=1174291356210962462
        ),
        custom_id="transfer_owner",
        row=2,
    )
    async def transfer_owner(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.check(interaction)
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
    async def del_channel(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        temp_voice = self.check(interaction)
        await self.bot.server(interaction.guild_id).del_channel(
            temp_voice.channel.id
        )


# class JoinRequest:
#     def __init__(self, member: discord.Member, temp_channel_id: int):
#         self.member: discord.Member = member
#         self.temp_channel_id: int = temp_channel_id


class TempVoice:
    def __init__(
        self,
        bot: source.bot_class.PartySysBot,
        channel: discord.VoiceChannel,
        owner: discord.Member,
        server_id: int,
        creator: discord.Member = None,
    ):
        self.bot: source.bot_class.PartySysBot = bot
        # self.cur: dbutils.steady_db.SteadyDBCursor = cursor
        self.channel: discord.VoiceChannel = channel
        self.creator: discord.Member = owner if creator is None else creator
        self.owner: discord.Member = owner
        self.adv: Adv | None = None

        self.reminder: datetime | None | False = None

        self.privacy: str = "0"  # 0 - public, 1 - closed, 2 - hidden
        self.invite_url: str | None = None  # Store invite link on this channel
        self.server_id: int = server_id  # Local server id in DB

    def updated(self) -> None:
        new_state: discord.VoiceChannel = self.bot.get_channel(self.channel.id)
        if new_state and new_state.type == discord.ChannelType.voice:
            self.channel = new_state

        if (
            self.privacy == "0"
            and self.adv is None
            and self.reminder is not False
            and self.channel.user_limit > len(self.channel.members)
        ):
            self.reminder = datetime.now() + timedelta(minutes=2.0)
        elif self.reminder:
            self.reminder = None

    async def get_invite(self) -> str:
        invites = await self.channel.invites()
        for inv in invites:
            if inv.inviter.id == self.bot.user.id:
                self.invite_url = inv.url

        if not self.invite_url:
            create_inv = await self.channel.create_invite(
                reason="Join link to this temp voice."
            )
            self.invite_url = create_inv.url
        return self.invite_url

    async def send_adv(self, custom_text: str):
        server = self.bot.server(self.channel.guild.id)
        if not server:
            raise BotNotConfigured
        elif self.adv:
            return

        if not self.invite_url:
            try:
                await self.get_invite()
            except discord.NotFound:
                return

        self.adv = Adv()
        adv_msg_id = await self.adv.send(
            adv_channel=server.adv_channel, temp_voice=self, text=custom_text
        )
        if adv_msg_id:
            self.bot.cur.execute(
                "UPDATE temp_channels SET dis_adv_msg_id=%s WHERE dis_id=%s",
                (adv_msg_id, self.channel.id),
            )

    async def update_adv(self, custom_text: str = "") -> None:
        """
        Update adv
        :param custom_text:
        :return:
        """
        if self.adv:
            await self.adv.update(temp_voice=self, text=custom_text)

    async def delete_adv(self) -> bool:
        """
        Delete adv
        :return:
        """
        if self.adv:
            await self.adv.delete()
            # self.adv = None
            # self.reminder = False
            self.bot.cur.execute(
                "UPDATE temp_channels SET dis_adv_msg_id=NULL WHERE dis_id=%s",
                (self.channel.id,),
            )
            return True
        return False

    async def send_reminder(self) -> None:
        """
        Send reminder for owner
        :return:
        """
        if self.privacy == "0" and self.adv is None:
            await self.send_adv("")
            await self.channel.send(
                embed=ReminderEmbed(),
                view=ReminderInterface(self.bot),
                delete_after=120,
            )
        self.reminder = None

    def _update(
        self,
        channel: discord.VoiceChannel,
        creator: discord.Member,
        owner: discord.Member,
    ) -> None:
        """
        :param channel: store discord.VoiceChannel obj of this temp voice
        :param creator: store discord.Member obj, who firstly create
        this channel
        :param owner: store discord.Member obj, who owned this channel
        at the moment
        :return:
        """
        self.channel = channel
        self.creator = creator
        self.owner = owner

    async def change_owner(self, new_owner: discord.Member) -> None:
        """
        Change this temp voice owner
        :param new_owner:
        :return:
        """
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
        """
        Disconnect member from this channel
        :param member:
        :return:
        """
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
        query = self.bot.cur.execute(
            "SELECT * FROM ban_list WHERE server_id=%s AND dis_creator_id=%s",
            (self.server_id, self.creator.id),
        )
        if query:
            bans_raw = self.bot.cur.fetchall()
            if bans_raw:
                member_ban = None
                for ban in bans_raw:
                    if ban["dis_banned_id"] == member.id:
                        member_ban = ban
                        break

                if member_ban and member_ban["banned"]:
                    raise UserAlreadyBanned
                elif len(bans_raw) >= 25:
                    raise UserBanLimit

                if member_ban:
                    self.bot.cur.execute(
                        "UPDATE ban_list SET banned=1 WHERE server_id=%s AND dis_creator_id=%s AND dis_banned_id=%s",
                        (self.server_id, self.creator.id, member.id),
                    )
                else:
                    self.bot.cur.execute(
                        "INSERT INTO ban_list (dis_creator_id, dis_banned_id, server_id) VALUES (%s, %s, %s)",
                        (self.creator.id, member.id, self.server_id),
                    )
            else:
                self.bot.cur.execute(
                    "INSERT INTO ban_list (dis_creator_id, dis_banned_id, server_id) VALUES (%s, %s, %s)",
                    (self.creator.id, member.id, self.server_id),
                )
        else:
            self.bot.cur.execute(
                "INSERT INTO ban_list (dis_creator_id, dis_banned_id, server_id) VALUES (%s, %s, %s)",
                (self.creator.id, member.id, self.server_id),
            )
        await self.take_access(member)

    async def unban(self, ban_id: int) -> int:
        query = self.bot.cur.execute(
            "SELECT * FROM ban_list WHERE id=%s LIMIT 1", (ban_id,)
        )
        if query:
            ban = self.bot.cur.fetchone()
            if ban and ban["banned"]:
                self.bot.cur.execute(
                    "UPDATE ban_list SET banned=0 WHERE id=%s", (ban_id,)
                )
                member = self.channel.guild.get_member(ban["dis_banned_id"])
                if member:
                    await self.channel.set_permissions(
                        target=member, overwrite=None
                    )  # Drop overwrite on this user
                    return member.id
                else:
                    return 1
            else:
                raise UserNotBanned
        return False

    async def change_privacy(self, mode: str) -> None:
        """
        Change temp channel privacy mode
        :param mode:
        :return:
        """
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

    async def send_interface(self) -> None:
        await self.channel.send(
            embed=ChannelControlEmbed(),
            content=self.owner.mention,
            view=ControlInterface(self.bot),
        )

    async def delete(self) -> None:
        try:
            await self.channel.delete(
                reason="Temp channel empty or deleted by owner."
            )
            await self.delete_adv()
        except discord.NotFound:
            return
