from datetime import datetime

from discord.ext import commands, tasks

from source.bot_class import PartySysBot

# import os
# # --- LOAD ENV VARS ---#
# dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
# if os.path.exists(dotenv_path):
#     load_dotenv(dotenv_path)
#
#
# # --- END LOAD ENV VARS --- #


# def check_if_it_is_me(interaction: discord.Interaction) -> bool:
#     return interaction.user.id == os.getenv("DEV_ID")


class Scheduler(commands.Cog):
    def __init__(self, bot: PartySysBot):
        self.bot = bot

    @tasks.loop(minutes=1.0)
    async def adv_deleter(self):
        for server in self.bot.servers.values():
            for temp_voice in server.all_channels().values():
                if (
                    temp_voice.adv
                    and temp_voice.adv.delete_after
                    and datetime.now() >= temp_voice.adv.delete_after
                ):
                    await temp_voice.delete_adv()

    @tasks.loop(minutes=1.0)
    async def reminder_sender(self):
        for server in self.bot.servers.values():
            for temp_voice in list(server.all_channels().copy().values()):
                if (
                    temp_voice.reminder
                    and datetime.now() >= temp_voice.reminder
                ):
                    await temp_voice.send_reminder()

    @reminder_sender.before_loop
    async def before_remind_sender(self):
        await self.bot.wait_until_ready()

    @adv_deleter.before_loop
    async def before_adv_deleter(self):
        await self.bot.wait_until_ready()

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     if not self.adv_deleter.is_running():
    #         self.adv_deleter.start()
    #     if not self.reminder_sender.is_running():
    #         self.reminder_sender.start()

    def cog_load(self) -> None:
        if not self.adv_deleter.is_running():
            self.adv_deleter.start()
        if not self.reminder_sender.is_running():
            self.reminder_sender.start()

    def cog_unload(self):
        if self.adv_deleter.is_running():
            self.adv_deleter.cancel()
        if self.reminder_sender.is_running():
            self.reminder_sender.cancel()


async def setup(bot: PartySysBot):
    await bot.add_cog(Scheduler(bot))
