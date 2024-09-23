from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timedelta

import discord

from config import CFG
from src import utils
from src.models import TempChannels
from src.services import errors

from .base import BaseView
from .embeds import InterfaceEmbed, SuccessEmbed
from .modals import AdvModal
from .views import JoinInterface


class Adv:
    __slots__ = (
        "_message",
        "delete_after",
        "temp_voice",
        "text",
    )

    def __init__(
        self, temp_voice: utils.TempVoiceABC, msg: discord.Message | None = None
    ):
        self.temp_voice = temp_voice
        self._message = msg

        self.text = ""
        self.delete_after: datetime | None = None

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"msg={self._message} "
            f"temp_voice={self.temp_voice}"
            f">"
        )

    def __bool__(self):
        return self._message is not None

    async def send(self, text: str) -> int:
        self.text = text
        self._set_delete_after()
        self._message = await self._send_or_edit_message()
        await TempChannels.filter(dis_id=self.temp_voice.channel.id).update(
            dis_adv_msg_id=self._message.id
        )
        return self._message.id

    async def update(self, text: str = "") -> None:
        if text:
            self.text = text
        self._set_delete_after()
        await self._send_or_edit_message()

    def _set_delete_after(self) -> None:
        if not self.temp_voice.channel.user_limit:
            self.delete_after = datetime.now() + timedelta(
                minutes=CFG["adv"]["delete_after_unlimit"]
            )
        elif (
            len(self.temp_voice.channel.members)
            >= self.temp_voice.channel.user_limit
        ):
            self.delete_after = datetime.now() + timedelta(
                minutes=CFG["adv"]["delete_after_fillment"]
            )
        else:
            self.delete_after = None

    async def _send_or_edit_message(self) -> discord.Message:
        embed = AdvEmbed(temp_voice=self.temp_voice, text=self.text)
        view = JoinInterface(
            invite_url=await self.temp_voice.invite_url(),
            disabled=len(self.temp_voice.channel.members)
            >= self.temp_voice.channel.user_limit,
        )
        if self._message:
            try:
                await self._message.edit(embed=embed, view=view)
            except discord.NotFound:
                await self.temp_voice.adv.delete()
            except discord.HTTPException as e:
                if e.code == 30046:
                    with suppress(discord.NotFound):
                        await self.delete()
                        await self.temp_voice.adv.send(self.text)
                else:
                    raise e
        else:
            self._message = await self.temp_voice.server.adv_channel.send(
                embed=embed, view=view
            )
        return self._message

    async def delete(self) -> bool:
        try:
            await self._message.delete()
        except (discord.NotFound, AttributeError):
            pass
        except discord.DiscordServerError as e:
            if e.code == 0:
                with suppress(discord.NotFound):
                    msg = await self._message.fetch()
                    await msg.delete()
            else:
                raise e
        finally:
            await TempChannels.filter(dis_id=self.temp_voice.channel.id).update(
                dis_adv_msg_id=None
            )

            self._message, self.delete_after = None, None
        return True


class AdvControlInterface(BaseView):
    def __init__(self, bot: utils.BotABC):
        super().__init__(bot)

    @discord.ui.button(
        emoji="📝", custom_id="adv:public", style=discord.ButtonStyle.primary
    )
    async def adv_public(self, interaction: discord.Interaction, *_):
        if self.temp_voice.privacy == utils.Privacy.PUBLIC:
            if self.temp_voice.channel.user_limit > len(
                self.temp_voice.channel.members
            ):
                await interaction.response.send_modal(AdvModal(self.temp_voice))
            else:
                raise errors.AdvChannelIsFullError
        else:
            raise errors.AdvRequirePublicPrivacyError

    @discord.ui.button(
        emoji="🗑️", custom_id="adv:delete", style=discord.ButtonStyle.red
    )
    async def adv_delete(self, interaction: discord.Interaction, *_):
        self.temp_voice.reminder = False  # Disable reminder
        await self.temp_voice.adv.delete()
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

        if users_count > CFG["adv"]["display_users_limit"]:
            text = text[: CFG["adv"]["display_users_limit"]]
            text.append(
                f"...\nИ другие <:member_white:1176147115282534440> "
                f"{len(text) - CFG["adv"]["display_users_limit"]}"
                f" пользователей."
            )

        if not max_users_count:
            text.append(
                "...\nНеограниченное число <:member_blue:1176147113739026432> "
                "свободных мест."
            )
        elif max_users_count - users_count > CFG["adv"]["display_users_limit"]:
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

        if not max_users_count:
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


class AdvInterface(BaseView):
    def __init__(self, bot: utils.BotABC):
        super().__init__(bot, timeout=None)

    async def check(
        self, interaction: discord.Interaction
    ) -> utils.TempVoiceABC:
        if (server := await self.bot.server(interaction.guild_id)) and (
            temp_channel := server.get_member_tv(
                interaction.user, interaction.channel_id
            )
        ):
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
            if temp_voice := await self.check(interaction):
                return await func(
                    self, interaction, temp_voice, *args, **kwargs
                )
            else:
                raise errors.UserNoTempChannelsError

        return _wrapper

    @staticmethod
    async def handle_no_adv(temp_voice, interaction):
        if temp_voice.privacy == utils.Privacy.PUBLIC:
            if not temp_voice.tv.user_limit or temp_voice.tv.user_limit > len(
                temp_voice.tv.members
            ):
                await interaction.response.send_modal(AdvModal(temp_voice))
            else:
                raise errors.AdvChannelIsFullError
        else:
            raise errors.AdvRequirePublicPrivacyError

    async def handle_existing_adv(self, interaction):
        await interaction.response.send_message(
            ephemeral=True,
            view=AdvControlInterface(self.bot),
            embed=InterfaceEmbed(
                "Управление объявлением",
                "📝 - Изменить текст объявления." "\n\n🗑️ - Удалить объявление.",
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
            await self.handle_existing_adv(interaction)
        else:
            await self.handle_no_adv(temp_voice, interaction)
