from __future__ import annotations

from src import utils

from .server import Server


class PartySysBot(utils.BotABC):
    async def server(self, guild_id):
        if guild_id not in self.servers:
            if guild := self.get_guild(guild_id):
                self.servers[guild_id] = await Server.new(self, guild)

                return self.servers[guild_id]
            else:
                return None
        elif self.servers[guild_id].id:
            return self.servers[guild_id]
        else:
            return None
