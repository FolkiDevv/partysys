from __future__ import annotations

from loguru import logger

from src import utils

from .server_temp_voices import Server


class PartySysBot(utils.BotABC):
    def server(self, guild_id):
        if guild_id not in self.servers:
            logger.debug(f"Guild {guild_id} 1")
            if guild := self.get_guild(guild_id):
                logger.debug(f"Guild {guild_id} 2")
                self.servers[guild_id] = Server(self, guild)
                self.loop.create_task(
                    self.servers[guild_id].update_server_data()
                )
                return self.servers[guild_id]
            else:
                return None
        if self.servers[guild_id].server_id:
            return self.servers[guild_id]
        else:
            return None
