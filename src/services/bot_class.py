from __future__ import annotations

from discord.ext import commands

from src import services


class PartySysBot(
    commands.Bot
):  # Use commands.AutoShardedBot if you have more than 1k guilds
    def __init__(self, command_prefix, *, intents, **options):
        super().__init__(command_prefix, intents=intents, **options)

        self.servers: dict[int, services.ServerTempVoices] = {}

    def server(self, guild_id: int) -> services.ServerTempVoices | None:
        if guild_id not in self.servers:
            if guild := self.get_guild(guild_id):
                self.servers[guild_id] = services.ServerTempVoices(self, guild)
                return self.servers[guild_id]
            else:
                return None
        if self.servers[guild_id].server_id:
            return self.servers[guild_id]
        else:
            return None
