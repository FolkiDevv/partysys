from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timedelta

import discord

from config import CONF
from src import utils
from src.services import errors

from .base import BaseView
from .embeds import InterfaceEmbed, SuccessEmbed
from .modals import AdvModal
from .views import JoinInterface


class Adv:
    def __init__(self, msg: discord.Message | None = None):
        self._message = msg
        self.custom_text = ""
        self.delete_after: datetime | None = None

        self._update_delayed = False

    def __bool__(self):
        return self._message is not None

    # TODO: Добавить адекватную реакцию на ошибки (например, нет прав и т.п.)
    async def send(
        self,
        adv_channel: discord.TextChannel,
        temp_voice: utils.TempVoiceABC,
        text: str,
    ) -> int:
        self.custom_text = text

        if not temp_voice.channel.user_limit:
            # If channel has unlimited slots, adv will be deleted after 3
            # minutes without changes
            self.delete_after = datetime.now() + timedelta(
                minutes=CONF["adv"]["delete_after_unlimit"]
            )

        self._message = await adv_channel.send(
            embed=AdvEmbed(temp_voice=temp_voice, text=self.custom_text),
            view=JoinInterface(
                invite_url=await temp_voice.invite_url(),
                disabled=len(temp_voice.channel.members)
                >= temp_voice.channel.user_limit,
            ),
        )
        return self._message.id

    async def update(
        self, temp_voice: utils.TempVoiceABC, text: str = ""
    ) -> None:
        if text:
            self.custom_text = text
        elif self._message is None and not self._update_delayed:
            # if channel update state while adv sent
            self._update_delayed = True

            await asyncio.sleep(2.)

            temp_voice.updated()
            await self.update(temp_voice, text)

            return
        elif self._update_delayed:
            self._update_delayed = False

        if not temp_voice.channel.user_limit:
            self.delete_after = datetime.now() + timedelta(
                minutes=CONF["adv"]["delete_after_unlimit"]
            )
        elif len(temp_voice.channel.members) >= temp_voice.channel.user_limit:
            self.delete_after = datetime.now() + timedelta(
                minutes=CONF["adv"]["delete_after_fillment"]
            )
        else:
            self.delete_after = None

        view = None
        if temp_voice.privacy == utils.Privacy.PUBLIC:
            view = JoinInterface(
                invite_url=await temp_voice.invite_url(),
                disabled=len(temp_voice.channel.members)
                >= temp_voice.channel.user_limit
                if temp_voice.channel.user_limit > 0
                else False,
            )

        try:
            if self._message:
                await self._message.edit(
                    embed=AdvEmbed(
                        temp_voice=temp_voice,
                        text=self.custom_text,
                    ),
                    view=view,
                )
        except (discord.NotFound, discord.HTTPException) as e:
            if isinstance(e, discord.NotFound):
                await temp_voice.delete_adv()
            elif e.code == 30046:
                with suppress(discord.NotFound):
                    await self.delete()
                    await temp_voice.send_adv(custom_text=self.custom_text)
            else:
                raise e

    async def delete(self) -> bool:
        if not self:
            return False

        try:
            with suppress(discord.NotFound):
                await self._message.delete()
        except discord.DiscordServerError as e:
            if e.code == 0:
                with suppress(discord.NotFound):
                    msg = await self._message.fetch()
                    await msg.delete()
            else:
                raise e

        self._message, self.delete_after, self._update_delayed = (
            None,
            None,
            False,
        )
        return True


class AdvControlInterface(BaseView):
    def __init__(
            self,
            bot: utils.BotABC
    ):
        super().__init__(bot)

    @discord.ui.button(
        emoji="📝", custom_id="adv:public", style=discord.ButtonStyle.primary
    )
    async def adv_public(self, interaction: discord.Interaction, *_):
        if self.temp_voice.privacy == utils.Privacy.PUBLIC:
            if self.temp_voice.channel.user_limit > len(
                self.temp_voice.channel.members
            ):
                await interaction.response.send_modal(
                    AdvModal(self.temp_voice)
                )
            else:
                raise errors.AdvChannelIsFullError
        else:
            raise errors.AdvRequirePublicPrivacyError

    @discord.ui.button(
        emoji="🗑️", custom_id="adv:delete", style=discord.ButtonStyle.red
    )
    async def adv_delete(self, interaction: discord.Interaction, *_):
        self.temp_voice.reminder = False  # Disable reminder
        await self.temp_voice.delete_adv()
        await interaction.response.edit_message(
            view=None, embed=SuccessEmbed("Объявление было удалено.")
        )


class AdvEmbed(discord.Embed):
    def __init__(self, temp_voice: utils.TempVoiceABC, text: str):
        super().__init__()
        self._gen_text(custom_text=text, temp_voice=temp_voice)

    @staticmethod
    def _gen_user_list(temp_voice: utils.TempVoiceABC) -> list[str]:
        text = []
        max_users_count, users_count = (
            temp_voice.channel.user_limit,
            len(temp_voice.channel.members),
        )

        for member in temp_voice.channel.members:
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

        if users_count > CONF["adv"]["display_users_limit"]:
            text = text[:CONF["adv"]["display_users_limit"]]
            text.append(
                f"...\nИ другие <:member_white:1176147115282534440> "
                f"{len(text) - CONF["adv"]["display_users_limit"]}"
                f" пользователей."
            )

        if not max_users_count:
            text.append(
                "...\nНеограниченное число <:member_blue:1176147113739026432> "
                "свободных мест."
            )
        elif max_users_count - users_count > CONF["adv"]["display_users_limit"]:
            text.append(
                f"...\nОсталось <:member_blue:1176147113739026432> "
                f"{max_users_count - users_count} свободных мест."
            )
        else:
            text.extend(
                "<:member_blue:1176147113739026432> ▢"
                for _ in range(max_users_count - users_count)
            )

        return text

    def _gen_text(
        self, custom_text: str, temp_voice: utils.TempVoiceABC
    ) -> None:
        avatar = (
            temp_voice.owner.avatar.url
            if temp_voice.owner.avatar
            else temp_voice.owner.default_avatar.url
        )
        self.set_author(name=temp_voice.channel.name, icon_url=avatar)

        max_users_count, users_count = (
            temp_voice.channel.user_limit,
            len(temp_voice.channel.members),
        )
        text = []
        if len(custom_text):
            text.append(f"📢 {custom_text}\n")

        text += self._gen_user_list(temp_voice)  # Append users list

        if users_count >= max_users_count:
            self.set_footer(text="Канал заполнен ⛔")
            self.colour = 0x303136
        elif not max_users_count:
            self.set_footer(
                text="🔎 В поиске команды. Без ограничений по количеству."
            )
            self.colour = 0x57F287
        else:
            self.set_footer(
                text=f"🔎 В поиске команды. +{max_users_count - users_count}"
            )
            self.colour = 0x57F287

        self.description = "\n".join(text)
        self.timestamp = datetime.now()


class AdvInterface(BaseView):
    def __init__(self, bot: utils.BotABC):
        super().__init__(bot, timeout=None)

    def check(self, interaction: discord.Interaction) -> utils.TempVoiceABC:
        if server := self.bot.server(interaction.guild_id):
            temp_channel = server.get_user_channel(
                interaction.user, interaction.channel_id
            )
            if temp_channel:
                return temp_channel
        raise errors.UserNoTempChannelsError

    @staticmethod
    def check_decorator(func):
        async def _wrapper(
            self: AdvInterface,
            interaction: discord.Interaction,
            *args,
            **kwargs,
        ):
            if temp_voice := self.check(interaction):
                return await func(self, interaction, temp_voice, *args, **kwargs)
            else:
                raise errors.UserNoTempChannelsError

        return _wrapper

    @staticmethod
    async def handle_no_adv(temp_voice, interaction):
        if temp_voice.privacy == utils.Privacy.PUBLIC:
            if temp_voice.channel.user_limit > len(temp_voice.channel.members):
                await interaction.response.send_modal(AdvModal(temp_voice))
            else:
                raise errors.AdvChannelIsFullError
        else:
            raise errors.AdvRequirePublicPrivacyError

    @staticmethod
    async def handle_existing_adv(temp_voice, interaction):
        await interaction.response.send_message(
            ephemeral=True,
            view=AdvControlInterface(temp_voice.bot),
            embed=InterfaceEmbed(
                "Управление объявлением",
                "📝 - Изменить текст объявления."
                "\n\n🗑️ - Удалить объявление.",
            ),
        )

    @discord.ui.button(
        emoji="🪧", custom_id="reminder:adv", style=discord.ButtonStyle.primary
    )
    @check_decorator
    async def adv(
        self,
        interaction: discord.Interaction,
        temp_voice: utils.TempVoiceABC,
        *_,
    ):
        if temp_voice.adv:
            await self.handle_existing_adv(temp_voice, interaction)
        else:
            await self.handle_no_adv(temp_voice, interaction)
