from __future__ import annotations

import discord

import src.services.errors
from src.services.base_classes import BaseModal
from src.ui.embeds import SuccessEmbed


# noinspection PyUnresolvedReferences
class LimitModal(BaseModal):
    def __init__(self, bot: src.services.bot_class.PartySysBot,
                 current_limit: int):
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
            if temp_voice := server.get_user_channel(interaction.user):
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
                        raise src.services.errors.NumbersOnlyError from e
            else:
                raise src.services.errors.UserNoTempChannelsError
        else:
            raise src.services.errors.BotNotConfiguredError


# noinspection PyUnresolvedReferences
class RenameModal(BaseModal):
    def __init__(self, bot: src.services.bot_class.PartySysBot,
                 current_name: str):
        super().__init__(
            title="Изменить название канала", custom_id="rename:modal"
        )
        self.bot: src.services.bot_class.PartySysBot = bot
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
            if temp_voice := server.get_user_channel(interaction.user):
                await temp_voice.channel.edit(name=self.text_inp.value)
                await interaction.response.send_message(
                    embed=SuccessEmbed(
                        f"Название канала изменено на: "
                        f"**{self.text_inp.value}**."
                    ),
                    ephemeral=True,
                )
            else:
                raise src.services.errors.UserNoTempChannelsError
        else:
            raise src.services.errors.BotNotConfiguredError
