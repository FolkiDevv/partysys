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
            return

        logger.debug("on_voice_state_update event triggered")

        if (
            after.channel
            and after.channel.type == discord.ChannelType.voice
            and (after_server := await self.bot.server(after.channel.guild.id))
        ):
            await after_server.update_settings()
            if after_server.is_creator_channel(after.channel.id):
                logger.info(
                    f"{member.id} joined to C{after.channel.id} channel"
                )
                # Check if user join in Creator channel
                if temp_voice := await after_server.create_tv(
                    member, after.channel.id
                ):
                    logger.info(
                        f"TV{temp_voice.id} created and user "
                        f"{member.id} moved into."
                    )
            elif after_server.is_tv_channel(after.channel.id) and (
                after_temp_voice := after_server.tv(after.channel.id)
            ):
                logger.info(
                    f"{member.id} joined to TV{after.channel.id} channel"
                )

                after_temp_voice.updated()
                await after_temp_voice.adv.update()

                metrics.incr(
                    "temp_channel_user_join",
                    1,
                    tags={"server": after_server.guild.id},
                )

        if (
            before.channel
            and before.channel.type == discord.ChannelType.voice
            and (
                before_server := await self.bot.server(before.channel.guild.id)
            )
        ):
            await before_server.update_settings()
            if before_server.is_tv_channel(before.channel.id):
                # Check if user leave Temp channel
                if not len(before.channel.members):
                    logger.info(
                        f"TV{before.channel.id} deleted, because its empty."
                    )

                    await before_server.del_tv(before.channel.id)
                elif before_temp_voice := before_server.tv(before.channel.id):
                    logger.info(
                        f"{member.id} leaved from TV{before.channel.id} channel"
                    )

                    before_temp_voice.updated()
                    await before_temp_voice.adv.update()

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ) -> None:
        if after.type == discord.ChannelType.voice and (
            (server := await self.bot.server(after.guild.id))
            and (temp_voice := server.tv(before.id))
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
                    temp_channel = await server.restore_tv(
                        channel,
                        raw_channel.dis_owner_id,
                        raw_channel.dis_creator_id,
                        raw_channel.dis_adv_msg_id,
                    )
                    if not temp_channel.channel.members:
                        await server.del_tv(channel.id)
                    logger.success(f"TV{channel.id} channel restored")
                await asyncio.sleep(0.1)
            self.channels_restored = True
            logger.info("Restored all temp channels")


async def setup(bot):
    await bot.add_cog(Voice(bot))
