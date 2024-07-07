import logging

import discord
from discord.ext import commands
from sentry_sdk import metrics

from services.bot_class import PartySysBot


class Voice(commands.Cog):
    def __init__(self, bot: PartySysBot):
        self.bot = bot
        self.channels_restored = False

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if after.channel == before.channel:
            return None

        if after.channel.type == discord.ChannelType.voice and (
            after_server := self.bot.server(after.channel.guild.id)
        ):
            if after_server.is_creator_channel(after.channel.id):
                # Check if user join in Creator channel
                if temp_voice := await after_server.create_channel(
                    member, after.channel.id
                ):
                    logging.info(
                        f"Temp voice {temp_voice.id} created and user "
                        f"{member.id} moved into."
                    )
            elif after_server.is_temp_channel(after.channel.id):
                # Check if user join Temp channel
                if after_temp_voice := after_server.channel(after.channel.id):
                    metrics.incr(
                        "temp_channel_user_join",
                        1,
                        tags={"server": after_server.guild.id},
                    )
                    after_temp_voice.updated()
                    await after_temp_voice.update_adv()

        if before.channel.type == discord.ChannelType.voice and (
            before_server := self.bot.server(before.channel.guild.id)
        ):
            if before_server.is_temp_channel(before.channel.id):
                # Check if user leave Temp channel
                if not len(before.channel.members):
                    await before_server.del_channel(before.channel.id)
                    logging.info(
                        f"Temp voice {before.channel.id} deleted, because "
                        f"its empty."
                    )
                else:
                    if before_temp_voice := before_server.channel(
                        before.channel.id
                    ):
                        before_temp_voice.updated()
                        await before_temp_voice.update_adv()

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ):
        """
        Check if updated channel is temp channel and update adv (if existed)
        :param before:
        :param after:
        :return:
        """
        if after.type == discord.ChannelType.voice and (
            server := self.bot.server(after.guild.id)
        ):
            if temp_voice := server.channel(before.id):
                temp_voice.updated()
                if temp_voice.adv:
                    await temp_voice.update_adv()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.channels_restored:
            self.bot.cur.execute("SELECT * FROM temp_channels WHERE deleted=0")
            raw_channels = self.bot.cur.fetchall()
            for raw_channel in raw_channels:
                if channel := self.bot.get_channel(raw_channel["dis_id"]):
                    temp_channel = await self.bot.server(
                        channel.guild.id
                    ).restore_channel(
                        channel,
                        raw_channel["dis_owner_id"],
                        raw_channel["dis_creator_id"],
                        raw_channel["dis_adv_msg_id"],
                    )
                    if not temp_channel.channel.members:
                        await self.bot.server(channel.guild.id).del_channel(
                            channel.id
                        )
            self.channels_restored = True
            logging.info("All channels restored!")


async def setup(bot: PartySysBot):
    await bot.add_cog(Voice(bot))
