from __future__ import annotations

import discord
from discord import Interaction
from discord.ui import View
from sentry_sdk import metrics

from src import utils
from src.models import TCBans
from src.services import errors

from .base import BaseView
from .embeds import InfoEmbed, SuccessEmbed


class KickInterface(BaseView):
    def __init__(
        self,
        bot: utils.BotABC,
        users: list[discord.Member],
        owner: discord.Member,
    ):
        super().__init__(bot)

        self.select_user = discord.ui.Select(
            custom_id="kick:select", placeholder="Кого выгоняем?"
        )
        for user in users:
            if user.id != owner.id:
                self.select_user.add_option(
                    label=user.display_name, value=str(user.id)
                )
        if not len(self.select_user.options):
            self.select_user.disabled = True
            self.select_user.placeholder = "Кроме вас в канале никого нет :("

        self.add_item(self.select_user)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        await super().interaction_check(interaction)

        selected_user = interaction.guild.get_member(
            int(self.select_user.values[0])
        )
        await self.temp_voice.kick(member=selected_user)
        await interaction.response.edit_message(
            view=None,
            embed=SuccessEmbed(
                f"{selected_user.mention} был исключен из "
                f"вашего голосового канала."
            ),
        )

        metrics.incr(
            "temp_channel_user_kick",
            1,
            tags={"server": interaction.guild_id},
        )

        return True


class TransferOwnerInterface(BaseView):
    def __init__(self, bot: utils.BotABC):
        super().__init__(bot)

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        custom_id="transfer_owner:select",
        placeholder="Кому передаем права на управления?",
    )
    async def select_callback(
        self, interaction: discord.Interaction, select: discord.ui.UserSelect
    ):
        await super().interaction_check(interaction)

        await self.temp_voice.change_owner(select.values[0])

        await interaction.response.edit_message(
            embed=SuccessEmbed(
                f"Вы передали права на управления каналом пользователю "
                f"{select.values[0].mention}.\n"
                f"*В любой момент вы можете вернуть свои права на "
                f"управления используя соответствующую кнопку*"
            ),
            view=None,
        )
        await self.temp_voice.channel.send(
            content=select.values[0].mention,
            embed=InfoEmbed(
                "Переданы права на управление этим каналом",
                f"{select.values[0].mention} теперь"
                f" управляет этим каналом.",
            ),
        )

        metrics.incr(
            "temp_channel_change_owner",
            1,
            tags={"server": interaction.guild_id},
        )

        return True


class BanInterface(BaseView):
    def __init__(self, bot: utils.BotABC):
        super().__init__(bot)

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        custom_id="ban:select",
        placeholder="Кого баним?",
    )
    async def select_callback(
        self, interaction: discord.Interaction, select: discord.ui.UserSelect
    ):
        await super().interaction_check(interaction)

        await self.temp_voice.ban(select.values[0])

        await interaction.response.edit_message(
            embed=SuccessEmbed(
                f"{select.values[0].mention} теперь не сможет "
                f"подключиться к текущему и к "
                f"будущем голосовым каналам, созданными вами."
            ),
            view=None,
        )

        metrics.incr(
            "temp_channel_user_ban",
            1,
            tags={"server": interaction.guild_id},
        )

        return True


class UnbanInterface(BaseView):
    def __init__(
        self,
        bot: utils.BotABC,
        guild: discord.Guild,
        ban_list_raw: list[TCBans],
    ):
        super().__init__(bot)

        self.select_user = discord.ui.Select(
            custom_id="unban:select", placeholder="Кому даруем помилование?"
        )
        for ban in ban_list_raw:
            user = guild.get_member(ban.dis_banned_id)
            if user:
                self.select_user.add_option(
                    label=f"{user.display_name} (ID: {user.id})", value=ban.id
                )
            else:
                self.select_user.add_option(
                    label=f"ID: {ban.dis_banned_id}", value=ban.id
                )

        self.add_item(self.select_user)

    async def interaction_check(self, interaction: discord.Interaction):
        await super().interaction_check(interaction)

        unbanned = await self.temp_voice.unban(int(self.select_user.values[0]))
        if unbanned == 1:
            await interaction.response.edit_message(
                embed=SuccessEmbed(f"Бан #{self.select_user.values[0]} снят."),
                view=None,
            )
        elif unbanned:
            await interaction.response.edit_message(
                embed=SuccessEmbed(f"<@{unbanned}> был разбанен."),
                view=None,
            )
        else:
            raise errors.PartySysException(
                "Произошла неизвестная ошибка. Попробуйте снова.\n*Если ошибка "
                "повторяется - обратитесь в тех.поддержку бота."
            )

        metrics.incr(
            "temp_channel_user_unban",
            1,
            tags={"server": interaction.guild_id},
        )

        return True


class TakeAccessInterface(BaseView):
    def __init__(self, bot: utils.BotABC):
        super().__init__(bot)

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        max_values=10,
        custom_id="take_access:select",
        placeholder="Кому запрещаем подключаться?",
    )
    async def select_callback(
        self, interaction: discord.Interaction, select: discord.ui.UserSelect
    ):
        await super().interaction_check(interaction)

        mentions = []
        for selected_member in select.values:
            await self.temp_voice.take_access(selected_member)
            mentions.append(selected_member.mention)

        await interaction.response.edit_message(
            embed=SuccessEmbed(
                "Для следующих пользователей был запрещен доступ и "
                "просмотр вашего канала:\n"
                + "\n".join(mentions)
                + "\n\n*P.s. Применяется только к текущему каналу, "
                'используйте "Забанить", '
                "чтобы запретить пользователям подключаться и к "
                "будущем вашим каналам.*"
            ),
            view=None,
        )

        metrics.incr(
            "temp_channel_user_restrict_access",
            1,
            tags={"server": interaction.guild_id},
        )

        return True


class GetAccessInterface(BaseView):
    def __init__(self, bot: utils.BotABC):
        super().__init__(bot)

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        max_values=10,
        custom_id="get_access:select",
        placeholder="Кому разрешаем подключаться?",
    )
    async def select_callback(
        self, interaction: discord.Interaction, select: discord.ui.UserSelect
    ):
        await super().interaction_check(interaction)

        mentions = []
        for selected_member in select.values:
            await self.temp_voice.get_access(selected_member)
            mentions.append(selected_member.mention)

        await interaction.response.edit_message(
            embed=SuccessEmbed(
                "Следующие пользователи смогут видеть/зайти в канал "
                "вне зависимости от настроек приватности:\n"
                + "\n".join(mentions)
            ),
            view=None,
        )

        metrics.incr(
            "temp_channel_user_get_access",
            1,
            tags={"server": interaction.guild_id},
        )

        return True


class PrivacyInterface(BaseView):
    def __init__(self, bot: utils.BotABC, privacy: utils.Privacy):
        super().__init__(bot)

        self.select = discord.ui.Select(
            options=[
                discord.SelectOption(
                    label="Публичный",
                    value="0",
                    emoji="🔓",
                    default=privacy == utils.Privacy.PUBLIC,
                    description="Любой желающий сможет присоединиться к вашему "
                    "каналу.",
                ),
                discord.SelectOption(
                    label="Закрытый",
                    value="1",
                    emoji="🔒",
                    default=privacy == utils.Privacy.PRIVATE,
                    description="Все будут видеть ваш канал, но присоединиться "
                    "могут только пользователи с разрешением.",
                ),
                discord.SelectOption(
                    label="Скрытый",
                    value="2",
                    emoji="🔐",
                    default=privacy == utils.Privacy.HIDDEN,
                    description='Аналогичен режиму "Закрытый", однако '
                    "посторонние не смогут видеть данный канал.",
                ),
            ],
            custom_id="privacy:select",
        )
        self.add_item(self.select)

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        await super().interaction_check(interaction)

        await self.temp_voice.change_privacy(
            utils.Privacy(self.select.values[0])
        )
        await interaction.response.edit_message(
            embed=SuccessEmbed(
                f'Режим приватности изменен на: '
                f'{("🔓 Публичный", "🔒 Закрытый", "🔐 Скрытый")[int(self.select.values[0])]}'  # noqa: E501]}'
            ),
            view=None,
        )

        metrics.incr(
            "temp_channel_privacy_changed",
            1,
            tags={"server": interaction.guild_id},
        )

        if self.select.values[0] != utils.Privacy.PUBLIC:
            # Try to delete active adv if privacy changed to closed
            await self.temp_voice.adv.delete()
        return True


class JoinInterface(View):
    def __init__(self, invite_url: str, disabled: bool):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.url,
                url=invite_url,
                disabled=disabled,
                label="Подключиться",
            )
        )
