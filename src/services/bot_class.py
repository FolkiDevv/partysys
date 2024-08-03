from __future__ import annotations

from src import utils

from .server_temp_voices import Server


class PartySysBot(utils.BotABC):
    def server(self, guild_id):
        if guild_id not in self.servers:
            if guild := self.get_guild(guild_id):
                self.servers[guild_id] = Server.new(self, guild)

                return self.servers[guild_id]
            else:
                return None
        elif self.servers[guild_id].server_id:
            return self.servers[guild_id]
        else:
            return None
