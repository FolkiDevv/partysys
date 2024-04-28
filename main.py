import asyncio
import inspect
import logging
import logging.handlers
import os
import traceback
from sys import stderr

import discord
from loguru import logger

from source.bot_class import PartySysBot

LOG_PATH = "./logs"

logger.add(
    f"{LOG_PATH}/error.log",
    level="WARNING",
    rotation="12:00",
    compression="lzma",
    enqueue=True,
)
logger.add(
    f"{LOG_PATH}/info.log",
    level="INFO",
    filter=lambda record: record["level"].name == "INFO",
    rotation="12:00",
    compression="lzma",
    enqueue=True,
)

logger.info("Logger initialized.")


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (
            depth == 0 or frame.f_code.co_filename == logging.__file__
        ):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


discord.utils.setup_logging(handler=InterceptHandler())


# class OnlyThisLevelFilter(logging.Filter):
#     def __init__(self, level):
#         super().__init__()
#         self.__level = level
#
#     def filter(self, log_record: logging.LogRecord):
#         return log_record.levelno == self.__level
#
#
# inf_handler = logging.handlers.TimedRotatingFileHandler(
#     filename="./logs/info.log", encoding="utf-8", when="d", interval=1
# )
# inf_handler.setLevel(logging.INFO)
# inf_handler.addFilter(OnlyThisLevelFilter(logging.INFO))
# discord.utils.setup_logging(handler=inf_handler)
#
# err_handler = logging.handlers.TimedRotatingFileHandler(
#     filename="./logs/error.log", encoding="utf-8", when="d", interval=1
# )
# err_handler.setLevel(logging.WARNING)
# discord.utils.setup_logging(handler=err_handler)


bot_intents = discord.Intents.default()
bot_intents.members = True
bot_intents.guild_reactions = True
bot_intents.messages = True
bot_intents.message_content = True
bot_intents.guild_messages = True
bot = PartySysBot(
    command_prefix="n.",
    intents=bot_intents,
    activity=discord.CustomActivity(name="Работает в тестовом режиме."),
)
bot.remove_command("help")
COGS = [
    "cogs.controller",
    "cogs.voice",
    "cogs.slash_commands",
    "cogs.scheduler",
    # "cogs.healthcheck",
]


@bot.event
async def on_ready():
    logging.debug(f"Logged in as {bot.user.name} {bot.user.id}.")
    logging.info("Bot ready!")
    await bot.tree.sync(guild=discord.Object(838114056123842570))


async def main():
    async with bot:
        for extension in COGS:
            try:
                await bot.load_extension(extension)
            except:
                print(f"Failed to load extension {extension}.", file=stderr)
                logging.error(traceback.format_exc())
        await bot.start(os.getenv("DISCORD_TOKEN"))


if os.getenv("DEBUG", "0") == "1":
    debug_handler = logging.FileHandler(
        filename=f"{LOG_PATH}/debug.log", encoding="utf-8", mode="w"
    )
    discord.utils.setup_logging(handler=debug_handler)
    # logger.add(f'./logs/debug.log', format="{time} {level} {message}",
    # level="DEBUG", rotation="10:00", compression="zip")
else:
    import sentry_sdk

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        # Enable performance monitoring
        enable_tracing=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        _experiments={
            # Turns on the metrics module
            "enable_metrics": True,
            # Enables sending of code locations for metrics
            "metric_code_locations": True,
        },
    )
# logger.remove(handler_id=None) logger.add(f'./logs/info.log', format="{
# time} {level} {message}", level="INFO", rotation="10:00",
# compression="zip") logger.add(f'./logs/error.log', format="{time} {level} {
# message}", level="WARNING", rotation="10:00", compression="zip")

asyncio.run(main())
