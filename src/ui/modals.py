from __future__ import annotations

import discord
from sentry_sdk import metrics

from src import utils
from src.services import errors

from .base import BaseModal
from .embeds import SuccessEmbed


class AdvModal(BaseModal):
    def __init__(self, temp_voice: utils.TempVoiceABC):
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
            default=temp_voice.adv.text
            if temp_voice.adv and len(temp_voice.adv.text)
            else None,
        )
        self.add_item(self.text_inp)

    async def on_submit(self, interaction: discord.Interaction):
        if self.temp_voice.adv:
            await self.temp_voice.adv.update(custom_text=self.text_inp.value)
            await interaction.response.edit_message(
                view=None,
                embed=SuccessEmbed("Объявление было отредактировано."),
            )
        else:
            await self.temp_voice.adv.send(
                custom_text=self.text_inp.value
            )
            await interaction.response.send_message(
                ephemeral=True,
                embed=SuccessEmbed(
                    "Объявление было отправлено."
                    if self.temp_voice.channel.user_limit
                    else "Объявление было отправлено.\nУ вашего канала нет "
                    "ограничению по числу пользователей,"
                    "поэтому объявление будет удалено спустя 2 минуты простоя "
                    "без изменений."
                ),
            )

            metrics.incr(
                "adv_manual_send",
                1,
                tags={"server": self.temp_voice.server.id},
            )


# noinspection PyUnresolvedReferences
class LimitModal(BaseModal):
    def __init__(self, bot: utils.BotABC, current_limit: int):
        super().__init__(
            title="Изменить лимит пользователей", custom_id="limit:modal"
        )
        self.bot = bot

        self.text_inp = discord.ui.TextInput(
            label="Укажите макс. число пользователей",
            style=discord.TextStyle.short,
            default=str(current_limit),
            max_length=2,
            custom_id="limit:modal:text_input",
        )
        self.add_item(self.text_inp)

    async def on_submit(self, interaction: discord.Interaction):
        if server := self.bot.server(interaction.guild_id):
            if temp_voice := server.get_member_tv(interaction.user):
                if not self.text_inp.value or self.text_inp.value == "0":
                    await temp_voice.channel.edit(user_limit=0)
                    await interaction.response.send_message(
                        embed=SuccessEmbed(
                            "Лимит по количеству пользователей сменен на: "
                            "**без ограничений**."
                        ),
                        ephemeral=True,
                    )
                else:
                    try:
                        await temp_voice.channel.edit(
                            user_limit=int(self.text_inp.value)
                        )
                        await interaction.response.send_message(
                            embed=SuccessEmbed(
                                f"Лимит по количеству пользователей сменен на: "
                                f"**{self.text_inp.value}**."
                            ),
                            ephemeral=True,
                        )
                    except ValueError as e:
                        raise errors.NumbersOnlyError from e
            else:
                raise errors.UserNoTempChannelsError
        else:
            raise errors.BotNotConfiguredError


# noinspection PyUnresolvedReferences
class RenameModal(BaseModal):
    def __init__(self, bot: utils.BotABC, current_name: str):
        super().__init__(
            title="Изменить название канала", custom_id="rename:modal"
        )
        self.bot = bot
        self.text_inp = discord.ui.TextInput(
            label="Название канала",
            style=discord.TextStyle.short,
            max_length=32,
            min_length=1,
            default=current_name,
            custom_id="rename:modal:text_input",
        )
        self.add_item(self.text_inp)

    async def on_submit(self, interaction: discord.Interaction):
        if server := self.bot.server(interaction.guild_id):
            if temp_voice := server.get_member_tv(interaction.user):
                await temp_voice.channel.edit(name=self.text_inp.value)
                await interaction.response.send_message(
                    embed=SuccessEmbed(
                        f"Название канала изменено на: "
                        f"**{self.text_inp.value}**."
                    ),
                    ephemeral=True,
                )
            else:
                raise errors.UserNoTempChannelsError
        else:
            raise errors.BotNotConfiguredError
