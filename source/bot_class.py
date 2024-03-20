from __future__ import annotations

import logging
from os import getenv

import dbutils.steady_db
import pymysql
from discord.ext import commands

import source.server_class


class PartySysBot(
    commands.Bot
):  # Use commands.AutoShardedBot if you have more than 1k guilds
    def __init__(self, command_prefix, *, intents, **options):
        super().__init__(command_prefix, intents=intents, **options)
        con = dbutils.steady_db.connect(
            creator=pymysql,  # the rest keyword arguments belong to pymysql
            host=getenv("DB_HOST"),
            user=getenv("DB_USER"),
            password=getenv("DB_PASSWORD"),
            database=getenv("DB_NAME"),
            autocommit=True,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        with con:
            logging.info(f'Connected to {getenv("DB_NAME")}')
            self.cur: pymysql.Connection.cursorclass = con.cursor()

        self.servers: dict[int, source.server_class.ServerTempVoices] = {}

    def server(
        self, guild_id: int
    ) -> source.server_class.ServerTempVoices | None:
        """
        Return funcs.server_class.ServerTempVoices by guild id or None
        if not exists
        :param guild_id:
        :return:
        """
        if guild_id not in self.servers:
            guild = self.get_guild(guild_id)
            if guild:
                self.servers[guild_id] = source.server_class.ServerTempVoices(
                    self, guild
                )
                return self.servers[guild_id]
            else:
                return None
        if self.servers[guild_id].server_id:
            return self.servers[guild_id]
        else:
            return None
