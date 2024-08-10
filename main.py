import inspect
import logging
import os
import sys

import discord
from loguru import logger
from tortoise import Tortoise, run_async

from config import TORTOISE_ORM
from src import services

logger.remove(0)
if os.getenv("DEBUG", "0") == "0":
    logger.add(
        sys.stderr,
        level="WARNING",
        enqueue=True,
    )
    logger.add(
        sys.stdout,
        level="INFO",
        filter=lambda record: record["level"].name == "INFO",
        enqueue=True,
    )
else:
    logger.add(
        sys.stdout,
        level="DEBUG",
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

bot_intents = discord.Intents.default()
bot_intents.members = True
bot_intents.guild_reactions = True
bot_intents.messages = True
bot_intents.message_content = True
bot_intents.guild_messages = True

bot = services.PartySysBot(
    command_prefix="n.",
    intents=bot_intents,
    activity=discord.CustomActivity(name="Работает в тестовом режиме."),
)
bot.remove_command("help")


@bot.event
async def on_ready():
    logger.success(f"Logged in as {bot.user.name} {bot.user.id}.")
    await bot.tree.sync(guild=discord.Object(os.getenv("DEV_SERVER_ID")))


async def main():
    # Initialize Tortoise
    await Tortoise.init(config=TORTOISE_ORM)

    async with bot:
        for extension in os.getenv("COGS", "").split(","):
            try:
                await bot.load_extension(f'src.cogs.{extension}')
                logger.info(f"Loaded extension {extension}.")
            except Exception as e:
                logger.error(e)
        await bot.start(os.getenv("DISCORD_TOKEN"))


if os.getenv("DEBUG", "0") == "0":
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

run_async(main())
