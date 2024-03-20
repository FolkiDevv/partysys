import logging
import os
import traceback

import discord
from discord import app_commands
from discord.ext import commands

from source.bot_class import PartySysBot
from source.embeds import ErrorEmbed
from source.errors import CustomExc

# from dotenv import load_dotenv
#
# # --- LOAD ENV VARS ---#
# dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
# if os.path.exists(dotenv_path):
#     load_dotenv(dotenv_path)
#
#
# # --- END LOAD ENV VARS --- #


# def check_if_it_is_me(interaction: discord.Interaction) -> bool:
#     return interaction.user.id == os.getenv("DEV_ID")


# noinspection PyUnresolvedReferences
class Controller(commands.Cog):
    def __init__(self, bot: PartySysBot):
        self.bot = bot

    @staticmethod
    async def on_application_command_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        error = getattr(error, "original", error)
        if isinstance(error, app_commands.CommandNotFound):
            return  # отключаем вывод ошибки о ненайденной команде

        embed = ErrorEmbed()
        try:
            if isinstance(error, app_commands.MissingPermissions):
                embed.description = (
                    "У вас не хватает прав для использования "
                    "этой команды: {perms}!"
                ).format(perms=", ".join(error.missing_permissions))
                await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )
            elif isinstance(error, app_commands.CommandOnCooldown):
                embed.description = (
                    f"Этот функционал можно использовать только "
                    f"{int(error.cooldown.rate)} раз в "
                    f"{int(error.cooldown.per)} секунд."
                    f"Попробуйте через {round(error.retry_after)} секунд."
                )
                await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )
            elif isinstance(error, app_commands.errors.CheckFailure):
                embed.description = "Вы не можете использовать эту команду."
                await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )
            elif isinstance(error, CustomExc):
                embed.description = error.err_msg
                await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )
            elif not isinstance(
                error, app_commands.errors.CommandInvokeError
            ) or not isinstance(error, discord.errors.NotFound):
                logging.error(traceback.format_exc())
        except Exception:
            logging.error(traceback.format_exc())

    # @commands.Cog.listener()
    # async def on_command_error(self, ctx, error):
    #     if hasattr(ctx.command, "on_error"):
    #         return
    #
    #     error = getattr(error, 'original', error)
    #     if isinstance(error, commands.CommandNotFound):
    #         return  # отключаем вывод ошибки о ненайденной команде
    #
    # try: if isinstance(error, commands.CommandOnCooldown): await ctx.reply(
    # "<a:alert:945680944524845136> Команду \"{cmd}\" можно использовать
    # только {rate} раз в {per} секунд. Попробуйте через" "{retry}"
    # "секунд.".format( cmd=ctx.command.qualified_name,
    # rate=error.cooldown.rate, per=error.cooldown.per,
    # retry=error.retry_after), delete_after=15) elif isinstance(error,
    # commands.MissingPermissions): await ctx.reply(
    # "<a:alert:945680944524845136> У вас не хватает прав для использования
    # этой команды: {perms}!".format( perms=", ".join(
    # error.missing_permissions)), delete_after=15) elif isinstance(error,
    # commands.BotMissingPermissions): await ctx.reply(
    # "<a:alert:945680944524845136> У бота не хватает разрешений для
    # полноценной работы: {perms}!".format( perms=", ".join(
    # error.missing_permissions)), delete_after=15) else: if ctx.command is
    # not None: await ctx.reply( "<a:alert:945680944524845136> Произошла
    # неизвестная ошибка при выполнении команды `{cmd}`: {error}".format(
    # cmd=ctx.command.name, error=str(error)), delete_after=15) else: await
    # ctx.reply("<a:alert:945680944524845136> Произошла неизвестная ошибка
    # при выполнении команды: {error}".format( error=str(error)),
    # delete_after=15) except Exception: return

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
                    f"{cog} Ошибка при старте: {str(e)}", ephemeral=True
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
                    f"{cog} Ошибка при старте: {str(e)}", ephemeral=True
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
