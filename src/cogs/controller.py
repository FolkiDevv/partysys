from __future__ import annotations

import logging
import os
import traceback

import discord
from discord import app_commands

from src import services, ui
from src.services import errors


# TODO: сделать единую обработку ошибок
# noinspection PyUnresolvedReferences
class Controller(services.BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @staticmethod
    async def on_application_command_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        error = getattr(error, "original", error)
        if isinstance(error, app_commands.CommandNotFound):
            return

        embed = ui.ErrorEmbed()
        try:
            if isinstance(error, app_commands.MissingPermissions):
                embed.description = (
                    "У вас не хватает прав для использования "
                    "этой команды: {perms}!"
                ).format(perms=", ".join(error.missing_permissions))
            elif isinstance(error, app_commands.CommandOnCooldown):
                embed.description = (
                    f"Этот функционал можно использовать только "
                    f"{int(error.cooldown.rate)} раз в "
                    f"{int(error.cooldown.per)} секунд."
                    f"Попробуйте через {round(error.retry_after)} секунд."
                )
            elif isinstance(error, app_commands.errors.CheckFailure):
                embed.description = "Вы не можете использовать эту команду."
            elif isinstance(error, errors.PartySysException):
                embed.description = str(error)
            elif not isinstance(
                error, app_commands.errors.CommandInvokeError
            ) or not isinstance(error, discord.errors.NotFound):
                raise error

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(e)

    @app_commands.command(
        name="ext_reload",
        description=".",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(int(os.getenv("DEV_SERVER_ID")))
    async def ext_reload(self, interaction: discord.Interaction, cog: str):
        cog = f"cogs.{cog}"
        try:
            await self.bot.reload_extension(cog)
            logging.info(
                f"Пользователь {interaction.user.id} перезагрузил {cog}!"
            )
            await interaction.response.send_message(
                f"{cog} Перезагружено успешно!", ephemeral=True
            )
        except Exception as e:
            if isinstance(e, discord.ext.commands.ExtensionNotLoaded):
                await interaction.response.send_message(
                    f"{cog} Не был загружен!", ephemeral=True
                )
            elif isinstance(e, discord.ext.commands.ExtensionNotFound):
                await interaction.response.send_message(
                    f"{cog} Не найден!", ephemeral=True
                )
            elif isinstance(e, discord.ext.commands.NoEntryPointError):
                await interaction.response.send_message(
                    f"{cog} Отсутствует setup фун-я!", ephemeral=True
                )
            elif isinstance(e, discord.ext.commands.ExtensionFailed):
                await interaction.response.send_message(
                    f"{cog} Ошибка при старте: {e!s}", ephemeral=True
                )
            else:
                logging.error(traceback.format_exc())

    @app_commands.command(
        name="ext_load",
        description=".",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(int(os.getenv("DEV_SERVER_ID")))
    async def ext_load(self, interaction: discord.Interaction, cog: str):
        cog = f"cogs.{cog}"
        try:
            await self.bot.load_extension(cog)
            logging.info(f"Пользователь {interaction.user.id} загрузил {cog}!")
            await interaction.response.send_message(
                f"{cog} Загружено успешно!", ephemeral=True
            )
        except Exception as e:
            if isinstance(e, discord.ext.commands.ExtensionAlreadyLoaded):
                await interaction.response.send_message(
                    f"{cog} Уже загружен!", ephemeral=True
                )
            elif isinstance(e, discord.ext.commands.ExtensionNotFound):
                await interaction.response.send_message(
                    f"{cog} Не найден!", ephemeral=True
                )
            elif isinstance(e, discord.ext.commands.NoEntryPointError):
                await interaction.response.send_message(
                    f"{cog} Отсутствует setup фун-я!", ephemeral=True
                )
            elif isinstance(e, discord.ext.commands.ExtensionFailed):
                await interaction.response.send_message(
                    f"{cog} Ошибка при старте: {e!s}", ephemeral=True
                )
            else:
                logging.error(traceback.format_exc())

    @app_commands.command(
        name="ext_unload",
        description=".",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(int(os.getenv("DEV_SERVER_ID")))
    async def ext_unload(self, interaction: discord.Interaction, cog: str):
        cog = f"cogs.{cog}"
        try:
            await self.bot.unload_extension(cog)
            logging.info(f"Пользователь {interaction.user.id} выгрузил {cog}!")
            await interaction.response.send_message(
                f"{cog} Выгружен успешно!", ephemeral=True
            )
        except Exception as e:
            if isinstance(e, discord.ext.commands.ExtensionNotFound):
                await interaction.response.send_message(
                    f"{cog} Не найден!", ephemeral=True
                )
            elif isinstance(e, discord.ext.commands.ExtensionNotLoaded):
                await interaction.response.send_message(
                    f"{cog} Не был загружен!", ephemeral=True
                )
            else:
                logging.error(traceback.format_exc())

    @app_commands.command(
        name="sync_cmds",
        description=".",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(int(os.getenv("DEV_SERVER_ID")))
    async def sync_cmds(self, interaction: discord.Interaction, guild: str):
        guild = int(guild)
        try:
            await self.bot.tree.sync(
                guild=discord.Object(guild) if guild > 0 else None
            )
            logging.info(
                f"Пользователь {interaction.user.id} синхронизировал команды "
                f"сервера: {guild}!"
            )
            await interaction.response.send_message(
                f"Синхронизировал команды сервера: {guild}!", ephemeral=True
            )
        except:
            await interaction.response.send_message(
                "Произошла ошибка (подробнее в логах)!", ephemeral=True
            )
            logging.error(traceback.format_exc())


async def setup(bot):
    controller_class = Controller(bot)
    bot.tree.error(controller_class.on_application_command_error)
    await bot.add_cog(controller_class)
