from __future__ import annotations

import logging

import discord
from discord import Interaction

from src import utils
from src.services import errors

from .embeds import ErrorEmbed


class BaseView(discord.ui.View):
    def __init__(self, bot: utils.BotABC, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.server: utils.ServerABC | None = None
        self.temp_voice: utils.TempVoiceABC | None = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        self.server = self.bot.server(interaction.guild_id)
        if not self.server:
            raise errors.BotNotConfiguredError

        self.temp_voice = self.server.get_member_tv(
            interaction.user,
            interaction.channel_id,
        )
        if not self.temp_voice:
            raise errors.UserNoTempChannelsError

        return True

    async def on_error(
            self,
            interaction: discord.Interaction,
            error: Exception,
            item: discord.ui.Item,
    ):
        error = getattr(error, "original", error)

        embed = ErrorEmbed()
        try:
            if isinstance(error, discord.NotFound):
                embed.description = (
                    "Не можем найти исходное сообщение с интерфейсом."
                )
                await interaction.channel.send(
                    content=interaction.user.mention,
                    embed=embed,
                    delete_after=10.0,
                )
            elif isinstance(error, errors.UserActionError):
                embed.description = str(error)
                await interaction.response.send_message(
                    ephemeral=True, embed=embed
                )
            else:
                import traceback

                logging.error(traceback.format_exc())
        finally:
            pass


class BaseModal(discord.ui.Modal):
    async def on_error(self, interaction: Interaction, error: Exception, /):
        error = getattr(error, "original", error)

        embed = ErrorEmbed()
        try:
            if isinstance(error, discord.NotFound):
                embed.description = (
                    "Не можем найти исходное сообщение с интерфейсом."
                )
                await interaction.channel.send(embed=embed, delete_after=10.0)
            elif isinstance(error, errors.UserActionError):
                embed.description = str(error)
                await interaction.response.send_message(
                    ephemeral=True, embed=embed
                )
            else:
                logging.error(error)
        finally:
            pass
