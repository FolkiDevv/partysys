from __future__ import annotations

import logging

import discord
from discord import Interaction

from services.embeds import ErrorEmbed
from services.errors import UserActionError


class BaseView(discord.ui.View):
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
            elif isinstance(error, UserActionError):
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
            elif isinstance(error, UserActionError):
                embed.description = str(error)
                await interaction.response.send_message(
                    ephemeral=True, embed=embed
                )
            else:
                import traceback

                logging.error(traceback.format_exc())
        finally:
            pass
