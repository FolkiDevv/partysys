from aiohttp import web
from discord.ext import commands
from loguru import logger

from source.bot_class import PartySysBot

# import os
# # --- LOAD ENV VARS --- #
# dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
# if os.path.exists(dotenv_path):
#     load_dotenv(dotenv_path)


# def check_if_it_is_me(interaction: discord.Interaction) -> bool:
#     return interaction.user.id == os.getenv("DEV_ID")


class HealthCheck(commands.Cog):
    def __init__(self, bot: PartySysBot):
        self.site = None
        self.bot = bot
        self.site_started = False

    async def webserver(self):
        async def handler(request):
            return web.json_response(data={"status": "ok"})

        app = web.Application()
        app.router.add_get("/", handler)
        runner = web.AppRunner(app)
        await runner.setup()

        self.site = web.TCPSite(runner, "127.0.0.1", 8081)

        await self.bot.wait_until_ready()

        try:
            await self.site.start()
            self.site_started = True
        except Exception as e:
            logger.error(f"Error while starting webserver: \n{e}")
        else:
            logger.info("Health-Check Webserver started.")

    def __unload(self):
        if self.site_started:
            self.site.stop()


async def setup(bot: PartySysBot):
    health_check = HealthCheck(bot)
    await bot.add_cog(health_check)
    await bot.loop.create_task(health_check.webserver())
