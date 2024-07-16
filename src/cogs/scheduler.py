from datetime import datetime

from discord.ext import commands, tasks

from src import services


class Scheduler(commands.Cog):
    def __init__(self, bot: services.Bot):
        self.bot = bot

    @tasks.loop(minutes=1.0)
    async def adv_deleter(self):
        for server in self.bot.servers.copy().values():
            for temp_voice in server.all_channels().values():
                if (
                        temp_voice.adv
                        and temp_voice.adv.delete_after
                        and datetime.now() >= temp_voice.adv.delete_after
                ):
                    await temp_voice.delete_adv()

    @tasks.loop(minutes=1.0)
    async def reminder_sender(self):
        for server in self.bot.servers.copy().values():
            for temp_voice in list(server.all_channels().values()):
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

    def cog_load(self):
        if not self.adv_deleter.is_running():
            self.adv_deleter.start()
        if not self.reminder_sender.is_running():
            self.reminder_sender.start()

    def cog_unload(self):
        if self.adv_deleter.is_running():
            self.adv_deleter.cancel()
        if self.reminder_sender.is_running():
            self.reminder_sender.cancel()


async def setup(bot: services.Bot) -> None:
    await bot.add_cog(Scheduler(bot))
