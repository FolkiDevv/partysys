from __future__ import annotations

import asyncio

import discord
from discord.ext import commands
from loguru import logger
from sentry_sdk import metrics

from src import services
from src.models import TempChannels


class Voice(services.BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.channels_restored = False

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if after.channel == before.channel:
            return None

        logger.debug("on_voice_state_update event triggered")

        if (
            after.channel
            and after.channel.type == discord.ChannelType.voice
            and (after_server := await self.bot.server(after.channel.guild.id))
        ):
            await after_server.update_settings()
            if after_server.is_creator_channel(after.channel.id):
                logger.debug("User joined to creator channel")
                # Check if user join in Creator channel
                if temp_voice := await after_server.create_channel(
                    member, after.channel.id
                ):
                    logger.info(
                        f"Temp voice {temp_voice.id} created and user "
                        f"{member.id} moved into."
                    )
            elif after_server.is_temp_channel(after.channel.id) and (
                after_temp_voice := after_server.channel(after.channel.id)
            ):
                logger.debug("User joined to temp channel")
                metrics.incr(
                    "temp_channel_user_join",
                    1,
                    tags={"server": after_server.guild.id},
                )
                after_temp_voice.updated()
                await after_temp_voice.adv.update()

        if (
            before.channel
            and before.channel.type == discord.ChannelType.voice
            and (
                before_server := await self.bot.server(before.channel.guild.id)
            )
        ):
            await before_server.update_settings()
            if before_server.is_temp_channel(before.channel.id):
                # Check if user leave Temp channel
                if not len(before.channel.members):
                    await before_server.del_channel(before.channel.id)
                    logger.info(
                        f"Temp voice {before.channel.id} deleted, because "
                        f"its empty."
                    )
                elif before_temp_voice := before_server.channel(
                    before.channel.id
                ):
                    before_temp_voice.updated()
                    await before_temp_voice.adv.update()

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ) -> None:
        """
        Check if updated channel is temp channel and update adv (if existed)
        :param before:
        :param after:
        :return:
        """
        if after.type == discord.ChannelType.voice and (
            (server := await self.bot.server(after.guild.id))
            and (temp_voice := server.channel(before.id))
        ):
            temp_voice.updated()
            if temp_voice.adv:
                await temp_voice.adv.update()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.channels_restored:
            for raw_channel in await TempChannels.filter(deleted=0):
                if (channel := self.bot.get_channel(raw_channel.dis_id)) and (
                    server := await self.bot.server(channel.guild.id)
                ):
                    temp_channel = await server.restore_channel(
                        channel,
                        raw_channel.dis_owner_id,
                        raw_channel.dis_creator_id,
                        raw_channel.dis_adv_msg_id,
                    )
                    if not temp_channel.channel.members:
                        await server.del_channel(channel.id)
                    logger.info(f"Channel {channel.id} restored")
                await asyncio.sleep(0.1)
            self.channels_restored = True
            logger.info("Channels restore done")


async def setup(bot):
    await bot.add_cog(Voice(bot))
