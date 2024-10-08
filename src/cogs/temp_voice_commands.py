from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src import services, ui
from src.services import errors


class TempVoiceSlashCommands(services.BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.persistent_views_added = False

    @app_commands.command(
        name="adv_guide",
        description="Отправляет сообщение с инструкцией по использованию "
        "функционала объявлений.",
    )
    @app_commands.default_permissions(administrator=True)
    async def adv_guide(self, interaction: discord.Interaction):
        server = await self.bot.server(interaction.guild_id)
        if not server:
            raise errors.BotNotConfiguredError

        embed = discord.Embed(
            title="🔎 В поисках команды?", color=0x36393F, description=""
        )
        embed.add_field(
            inline=False,
            name="<:member_blue:1176147113739026432> Просмотрите текущие "
            "объявления о поиске команды.",
            value="Ниже в этом канале будут размещены актуальные объявления о "
            "поиске команды.\n\n"
            "Если вы нашли подходящее для себя объявления, то нажмите на "
            '**кнопку "Подключиться"** под ним, '
            "чтобы немедленно присоединиться к голосовому каналу.\n\n"
            "Объявление содержит в себе следующие элементы: название канала, "
            "аватар создателя канала, сообщение от создателя (если указано), "
            "список пользователей голосового канала и свободные места, кнопка "
            "для подключения к каналу.\n",
        )
        embed.add_field(
            inline=False,
            name="<:king_yellow:1176147111239233656> Или создайте "
            "собственный канал и разместите объявление о поиске.",
            value="**1. Создайте канал.** Подключитесь к одному из "
            "каналов-создателей (в зависимости от нужного размера "
            "группы):\n"
            + "\n".join(
                [f"<#{cid}>" for cid in server.get_creator_channels_ids()]
            )
            + "\n*Нажмите на требуемый канал, чтобы незамедлительно "
            "подключиться к нему.*\n\n"
            "**2. Разместите объявление.** Перейдите в чат созданного канала "
            "и в интерфейсе управления нажмите на кнопку"
            '"🪧", укажите текст объявления в всплывшем окне, а после нажмите '
            'на синюю кнопку в окне "Отправить".\n\n'
            "**3. Готово.** Объявление было размещено в канале поиска "
            "тиммейтов, ожидайте пока на него откликнутся.",
        )
        embed.set_footer(
            text="Описание всего доступного функционала можете найти в "
            "сообщении с интерфейсом управления в чате вашего голосового "
            "канала."
        )

        await interaction.response.defer(thinking=False)
        await interaction.channel.send(embed=embed)

    @app_commands.command(
        name="control_interface",
        description="Отправляет сообщение с интерфейсом управления голосовым "
        "каналом.",
    )
    @app_commands.default_permissions(administrator=True)
    async def control_interface(self, interaction: discord.Interaction):
        server = await self.bot.server(interaction.guild_id)
        if not server:
            raise errors.BotNotConfiguredError

        await interaction.response.defer(thinking=False)
        await interaction.channel.send(
            embed=ui.ChannelControlEmbed(), view=ui.ControlInterface(self.bot)
        )

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.persistent_views_added:
            self.bot.add_view(ui.ControlInterface(self.bot))
            self.persistent_views_added = True


async def setup(bot):
    await bot.add_cog(TempVoiceSlashCommands(bot))
