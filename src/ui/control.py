from __future__ import annotations

import discord

from src import utils
from src.models import TCBans
from src.services import errors

from .adv import AdvInterface
from .embeds import ErrorEmbed, InterfaceEmbed, SuccessEmbed, WarningEmbed
from .modals import LimitModal, RenameModal
from .views import (
    BanInterface,
    GetAccessInterface,
    PrivacyInterface,
    TakeAccessInterface,
    UnbanInterface,
)


class ControlInterface(AdvInterface):
    def __init__(self, bot: utils.BotABC):
        super().__init__(bot)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.channel_id != self.check(
                interaction
        ).channel.id and self.bot.server(interaction.guild_id).channel(
            interaction.channel_id
        ):
            raise errors.UserUseAlienControlInterfaceError
        return True

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="rename", id=1174291347511980052),
        custom_id="rename",
        row=0,
    )
    @AdvInterface.check_decorator
    async def rename(
            self,
            interaction: discord.Interaction,
            temp_voice: utils.TempVoiceABC,
            *_,
    ):
        await interaction.response.send_modal(
            RenameModal(self.bot, temp_voice.channel.name)
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="change_limit", id=1174292033062580276),
        custom_id="limit",
        row=0,
    )
    @AdvInterface.check_decorator
    async def limit(
            self, interaction: discord.Interaction,
            temp_voice: utils.TempVoiceABC, *_
    ):
        await interaction.response.send_modal(
            LimitModal(self.bot, temp_voice.channel.user_limit)
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="privacy", id=1174291348388589652),
        custom_id="privacy",
        row=0,
    )
    @AdvInterface.check_decorator
    async def privacy(
            self, interaction: discord.Interaction,
            temp_voice: utils.TempVoiceABC, *_
    ):
        await interaction.response.send_message(
            ephemeral=True,
            view=PrivacyInterface(self.bot, temp_voice.privacy),
            embed=InterfaceEmbed(
                title="Изменение приватности",
                text="🔓 Публичный - все пользователи могут "
                     "присоединяться/видеть ваш канал."
                     "\n🔒 Закрытый - присоединиться смогут только те "
                     "пользователи, которым вы "
                     "<:get_access:1174291352339623956>"
                     "Разрешите.\n"
                     "🔐 Скрытый - аналогичен Закрытому, однако в этом случае "
                     "пользователи,"
                     "которым вы не <:get_access:1174291352339623956> "
                     "Разрешали не"
                     "смогут видеть ваш канал.",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="get_access", id=1174291352339623956),
        custom_id="get_access",
        row=1,
    )
    @AdvInterface.check_decorator
    async def get_access(self, interaction: discord.Interaction, *_):
        await interaction.response.send_message(
            ephemeral=True,
            view=GetAccessInterface(self.bot),
            embed=InterfaceEmbed(
                title="Разрешить просматривать/подключаться к каналу",
                text="Выбранные пользователи смогут "
                     "присоединяться/просматривать ваш канал"
                     "(используйте, если режим приватности вашего канала не "
                     "Публичный).",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="take_access", id=1174291359792898218),
        custom_id="take_access",
        row=1,
    )
    @AdvInterface.check_decorator
    async def take_access(self, interaction: discord.Interaction, *_):
        await interaction.response.send_message(
            ephemeral=True,
            view=TakeAccessInterface(self.bot),
            embed=InterfaceEmbed(
                title="Запретить просматривать/подключаться к каналу",
                text="Выбранные пользователи НЕ смогут "
                     "присоединяться/просматривать ваш канал"
                     "(вне зависимости от выбранных настроек приватности).",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="kick", id=1174291365300011079),
        custom_id="kick",
        row=1,
        disabled=True,
    )
    @AdvInterface.check_decorator
    async def kick(self, interaction: discord.Interaction, *_):
        await interaction.response.send_message(
            ephemeral=True,
            embed=WarningEmbed(
                "Воспользуйтесь встроенным функционалом Discord:"
                "\n**Нажмите ПКМ по пользователю в Вашем канале -> Отключить**"
            )
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="ban", id=1174291351106506792),
        custom_id="ban",
        row=1,
    )
    async def ban(self, interaction: discord.Interaction, *_):
        await interaction.response.send_message(
            ephemeral=True,
            view=BanInterface(self.bot),
            embed=InterfaceEmbed(
                title="Забанить пользователя",
                text="Выбранный пользователь будет отключен от текущего "
                     "голосового канала"
                     "и не сможет просматривать/подключаться к вашим "
                     "ново-созданным каналам.",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="unban", id=1174291357586706442),
        custom_id="unban",
        row=2,
    )
    async def unban(
            self, interaction: discord.Interaction,
            temp_voice: utils.TempVoiceABC, *_
    ):
        if ban_list_raw := await TCBans.filter(
                server=temp_voice.server_id,
                dis_creator_id=temp_voice.creator.id,
                banned=True,
        ):
            await interaction.response.send_message(
                ephemeral=True,
                view=UnbanInterface(
                    self.bot,
                    interaction.guild,
                    ban_list_raw
                ),
                embed=InterfaceEmbed(
                    title="Разбанить пользователя",
                    text="Выбранный пользователь будет убран с вашего "
                         "бан-листа.",
                ),
            )
        else:
            await interaction.response.send_message(
                ephemeral=True,
                embed=ErrorEmbed(
                    "Список заблокированных пользователей пуст."
                    "\nНе бойтесь его пополнить, если потребуется :)"
                ),
            )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="return_owner", id=1174291361390940241),
        custom_id="return_owner",
        row=2,
    )
    async def return_owner(self, interaction: discord.Interaction, *_):
        if server := self.bot.server(interaction.guild_id):
            temp_voice = server.get_user_transferred_channel(
                interaction.user.id
            )
            if temp_voice and temp_voice.owner != temp_voice.creator:
                if server.get_user_channel(interaction.user):
                    raise errors.UserAlreadyOwnerError
                await temp_voice.channel.send(
                    f"<:info:1177314633124696165> {temp_voice.owner.mention} "
                    f"Права на управления каналом были возвращены "
                    f"создателю канала."
                )
                await temp_voice.change_owner(interaction.user)
                await interaction.response.send_message(
                    ephemeral=True,
                    embed=SuccessEmbed(
                        "Вам возвращены права на управления каналом."
                    ),
                )
            else:
                raise errors.UserAlreadyOwnerError
        else:
            raise errors.BotNotConfiguredError

    @discord.ui.button(
        emoji=discord.PartialEmoji(
            name="transfer_owner", id=1174291356210962462
        ),
        custom_id="transfer_owner",
        row=2,
    )
    @AdvInterface.check_decorator
    async def transfer_owner(self, interaction: discord.Interaction, *_):
        await interaction.response.send_message(
            ephemeral=True,
            embed=InterfaceEmbed(
                title="Передать права на управление каналом",
                text="Выбранный пользователь получит ваши права на "
                     "управление каналом "
                     "и вы больше не сможете им управлять, пока не вернете их "
                     "себе.",
            ),
        )

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="trash", id=1174291363873951776),
        custom_id="del_channel",
        row=2,
    )
    @AdvInterface.check_decorator
    async def del_channel(
            self, interaction: discord.Interaction,
            temp_voice: utils.TempVoiceABC, *_
    ):
        await self.bot.server(interaction.guild_id).del_channel(
            temp_voice.channel.id
        )
