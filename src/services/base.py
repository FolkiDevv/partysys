from __future__ import annotations

from discord.ext import commands

from src import utils


class BaseCog(commands.Cog):
    def __init__(self, bot: utils.BotABC):
        self.bot = bot
