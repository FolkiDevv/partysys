import logging

import discord
import sentry_sdk
from discord.ext import commands

from source.bot_class import PartySysBot

# import os
# # --- LOAD ENV VARS --- #
# dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
# if os.path.exists(dotenv_path):
#     load_dotenv(dotenv_path)


# def check_if_it_is_me(interaction: discord.Interaction) -> bool:
#     return interaction.user.id == os.getenv("DEV_ID")


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
    ) -> None:
        if after.channel == before.channel:
            return None

        if isinstance(after.channel, discord.VoiceChannel):
            after_server = self.bot.server(after.channel.guild.id)
            if after_server:
                if after_server.is_creator_channel(after.channel.id):
                    # Check if user join in CREATOR channel
                    if temp_voice := await after_server.create_channel(
                        member, after.channel.id
                    ):
                        logging.info(
                            f"Temp voice {temp_voice.id} created and user "
                            f"{member.id} moved into."
                        )
                elif after_server.is_temp_channel(after.channel.id):
                    # Check if user join in TEMP channel
                    after_temp_voice = after_server.channel(after.channel.id)
                    if after_temp_voice:
                        sentry_sdk.metrics.incr(
                            "temp_channel_user_join",
                            1,
                        )
                        after_temp_voice.updated()
                        await after_temp_voice.update_adv()

        if isinstance(before.channel, discord.VoiceChannel):
            before_server = self.bot.server(before.channel.guild.id)
            if before_server:
                if before_server.is_temp_channel(before.channel.id):
                    # Check if user leave in TEMP channel
                    if not len(before.channel.members):
                        await before_server.del_channel(before.channel.id)
                        logging.info(
                            f"Temp voice {before.channel.id} deleted, because "
                            f"its empty."
                        )
                    else:
                        before_temp_voice = before_server.channel(
                            before.channel.id
                        )
                        if before_temp_voice:
                            sentry_sdk.metrics.incr(
                                "temp_channel_user_leave",
                                1,
                            )
                            before_temp_voice.updated()
                            await before_temp_voice.update_adv()

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
        if after.type == discord.ChannelType.voice:
            server = self.bot.server(after.guild.id)
            if server:
                temp_voice = server.channel(before.id)
                if temp_voice:
                    temp_voice.updated()
                    if temp_voice.adv:
                        await temp_voice.update_adv()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.channels_restored:
            query = self.bot.cur.execute(
                "SELECT * FROM temp_channels WHERE deleted=0"
            )
            if query:
                raw_channels = self.bot.cur.fetchall()
                for raw_channel in raw_channels:
                    channel = self.bot.get_channel(raw_channel["dis_id"])
                    if channel is not None:
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
                logging.info("All channels restored!")
            else:
                logging.info("Nothing to restore.")
            self.channels_restored = True


async def setup(bot: PartySysBot):
    await bot.add_cog(Voice(bot))
