from __future__ import annotations

from re import fullmatch

import discord

import source.bot_class
import source.errors
from source.base_classes import BaseModal
from source.embeds import SuccessEmbed


# noinspection PyUnresolvedReferences
class LimitModal(BaseModal):
    def __init__(self, bot: source.bot_class.PartySysBot, current_limit: int):
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
        server = self.bot.server(interaction.guild_id)
        if server:
            temp_voice = server.get_user_channel(interaction.user)
            if temp_voice:
                if not self.text_inp.value or self.text_inp.value == "0":
                    await temp_voice.channel.edit(user_limit=0)
                    await interaction.response.send_message(
                        embed=SuccessEmbed(
                            "Лимит по количеству пользователей сменен на: "
                            "**без ограничений**."
                        ),
                        ephemeral=True,
                    )
                elif fullmatch(r"^[0-9]+$", self.text_inp.value):
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
                else:
                    raise source.errors.NumbersOnly
            else:
                raise source.errors.UserNoTempChannels
        else:
            raise source.errors.BotNotConfigured


# noinspection PyUnresolvedReferences
class RenameModal(BaseModal):
    def __init__(self, bot: source.bot_class.PartySysBot, current_name: str):
        super().__init__(
            title="Изменить название канала", custom_id="rename:modal"
        )
        self.bot: source.bot_class.PartySysBot = bot
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
        server = self.bot.server(interaction.guild_id)
        if server:
            temp_voice = server.get_user_channel(interaction.user)
            if temp_voice:
                await temp_voice.channel.edit(name=self.text_inp.value)
                await interaction.response.send_message(
                    embed=SuccessEmbed(
                        f"Название канала изменено на: "
                        f"**{self.text_inp.value}**."
                    ),
                    ephemeral=True,
                )
            else:
                raise source.errors.UserNoTempChannels
        else:
            raise source.errors.BotNotConfigured
