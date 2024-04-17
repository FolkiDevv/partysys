from __future__ import annotations

import datetime
from random import shuffle

import discord
import sentry_sdk

import source.bot_class
import source.channel_class

SQUAD_TITLES = [
    "Альфа",
    "Омега",
    "Феникс",
    "Грифон",
    "Дракон",
    "Волк",
    "Сокол",
    "Титан",
    "Легион",
    "Центурион",
    "Шторм",
    "Север",
    "Молния",
    "Сталь",
    "Кобра",
    "Пантера",
    "Лев",
    "Гладиатор",
    "Викинг",
    "Спартанец",
    "Комета",
    "Буря",
    "Арктика",
    "Торнадо",
    "Ястреб",
    "Медведь",
    "Тигр",
    "Ягуар",
    "Скорпион",
    "Марс",
    "Железо",
    "Рубин",
    "Оникс",
    "Сапфир",
    "Жемчуг",
    "Топаз",
    "Аметист",
    "Опал",
    "Агат",
    "Бриллиант",
    "Небеса",
    "Ореол",
    "Квазар",
    "Нимб",
    "Аврора",
    "Баррикада",
    "Каратель",
    "Навигатор",
    "Пионер",
    "Квант",
    "Эклипс",
    "Галактика",
    "Импульс",
    "Метеор",
    "Нейтрон",
    "Протон",
    "Радар",
    "Сигма",
    "Циклон",
    "СБЭУ",
    "Профессионалов",
    "BEAR",
    "USEC",
    "Скайнет",
    "Скуфов",
    "Решал",
    "LABS",
    "GIGACHADS",
]

roman_numbers = {
    "M": 1000,
    "CM": 900,
    "D": 500,
    "CD": 400,
    "C": 100,
    "XC": 90,
    "L": 50,
    "XL": 40,
    "X": 10,
    "IX": 9,
    "V": 5,
    "IV": 4,
    "I": 1,
}


def to_roman(number):
    roman = ""
    for letter, value in roman_numbers.items():
        while number >= value:
            roman += letter
            number -= value
    return roman


class ServerTempVoices:
    def __init__(self, bot: source.bot_class.PartySysBot, guild: discord.Guild):
        self.bot: source.bot_class.PartySysBot = bot

        self.server_id: int | None = None  # Local ID
        self.adv_channel: discord.TextChannel | None = None
        # self.wait_channel: Union[discord.TextChannel, None] = None
        self.guild: discord.Guild = guild
        self._creator_channels: dict[
            int, dict
        ] = {}  # Discord guild creator channels dict; key - discord channel id
        self._temp_channels: dict[
            int, source.channel_class.TempVoice
        ] = {}  # list of server temp voices; key - discord channel id
        # self._requests: dict[int, funcs.channel_class.JoinRequest] = dict()
        # list of JoinRequest; key - discord user id

        # Random iterator for temp voice random squad name
        self._random_names = SQUAD_TITLES.copy()
        shuffle(self._random_names)
        self._random_iter: int = 0

        self._last_data_update: datetime.datetime = datetime.datetime.now()

        self._update(guild.id)

    def _get_random_squad_name(self) -> str:
        name = self._random_names[self._random_iter]
        if self._random_iter >= len(self._random_names) - 1:
            self._random_iter = 0
        else:
            self._random_iter += 1
        return name

    def _update(self, guild_id: int) -> None:
        """
        :param guild_id: Discord guild ID
        :return:
        """
        query = self.bot.cur.execute(
            "SELECT * FROM servers WHERE dis_id=%s LIMIT 1", (guild_id,)
        )
        if query:
            server = self.bot.cur.fetchone()
            self.server_id: int = server["id"]
            self.adv_channel = self.bot.get_channel(
                server["dis_adv_channel_id"]
            )
            # self.wait_channel = self.bot.get_channel(server[
            # 'dis_wait_channel_id'])
        else:
            return

        # Select and store all server creator channels, where key is discord
        # channel id
        query = self.bot.cur.execute(
            "SELECT * FROM creator_channels WHERE server_id=%s",
            (self.server_id,),
        )
        if query:
            creator_channels = self.bot.cur.fetchall()
            for channel in creator_channels:
                self._creator_channels[channel["dis_id"]] = channel

    async def del_channel(self, channel_id: int) -> None:
        """
        Delete temp voice by id if exists
        :param channel_id:
        :return:
        """
        if channel_id in self._temp_channels:
            guild_id = self._temp_channels[channel_id].channel.guild.id
            try:
                await self._temp_channels[channel_id].delete()
            finally:
                if channel_id in self._temp_channels:
                    del self._temp_channels[channel_id]

                self.bot.cur.execute(
                    "UPDATE temp_channels SET deleted=1 WHERE dis_id=%s",
                    (channel_id,),
                )  # Mark channel as deleted in DB
                # self._update(guild_id)  # Update server settings from DB

    async def create_channel(
        self, member: discord.Member, creator_channel_id: int
    ) -> discord.VoiceChannel | None:
        """
        Create temp voice
        :param member:
        :param creator_channel_id:
        :return: obj of created voice channel
        """
        if creator_channel_id not in self._creator_channels:
            return None

        creator_category: discord.CategoryChannel = self.bot.get_channel(
            self._creator_channels[creator_channel_id]["dis_category_id"]
        )
        if not isinstance(creator_category, discord.CategoryChannel):
            return None

        temp_voice = await creator_category.create_voice_channel(
            name=str(
                self._creator_channels[creator_channel_id]["def_name"]
            ).format(
                user=member.display_name,
                num=len(self._temp_channels) + 1,
                squad_title=self._get_random_squad_name(),
                roman_num=to_roman(len(self._temp_channels) + 1),
            )[:32],
            user_limit=self._creator_channels[creator_channel_id][
                "def_user_limit"
            ],
        )

        # Save temp channel info into database
        self.bot.cur.execute(
            "INSERT INTO temp_channels (dis_id, dis_creator_id, dis_owner_id) VALUES (%s, %s, %s)",
            (temp_voice.id, member.id, member.id),
        )

        # Save temp channel info into memory
        self._temp_channels[temp_voice.id] = source.channel_class.TempVoice(
            self.bot, temp_voice, member, self.server_id
        )

        try:
            # Move owner to created channel
            await member.move_to(
                temp_voice, reason="Move to created temp voice"
            )
        except discord.HTTPException as e:
            if e.code == 40032:
                # If owner leaved from creator channel delete temp voice
                await self.del_channel(temp_voice.id)
            else:
                raise e

        overwrites: dict[
            discord.Member | discord.Role,
            discord.PermissionOverwrite,
        ] = {
            member: discord.PermissionOverwrite(
                move_members=True,  # deafen_members=True
            )
        }

        # Next get owner ban list and restore them to the new channel
        query = self.bot.cur.execute(
            "SELECT dis_banned_id FROM ban_list WHERE server_id=%s AND dis_creator_id=%s AND banned=1",
            (self.server_id, member.id),
        )
        if query:
            ban_list_raw = self.bot.cur.fetchall()
            for raw_ban in ban_list_raw:
                banned_member = self.guild.get_member(raw_ban["dis_banned_id"])
                if banned_member:
                    overwrites[banned_member] = discord.PermissionOverwrite(
                        view_channel=False,
                        connect=False,
                        speak=False,
                        send_messages=False,
                        add_reactions=False,
                        send_messages_in_threads=False,
                    )

        try:
            # Set permissions
            overwrites.update(temp_voice.overwrites)
            await temp_voice.edit(
                overwrites=overwrites, reason="Set permissions"
            )

            # Send control interface
            await self._temp_channels[temp_voice.id].send_interface()
        except discord.NotFound:
            await self.del_channel(temp_voice.id)
        except discord.HTTPException:
            await self.del_channel(temp_voice.id)

        # for key, overwrite in overwrites.items():
        #     try:
        #         await temp_voice.set_permissions(
        #             target=key, overwrite=overwrite
        #         )
        #     except discord.NotFound:
        #         continue

        # Increment temp channel created metric
        sentry_sdk.metrics.incr(
            "temp_channel_created",
            1,
            tags={"server": self.guild.id},
        )

        return temp_voice if temp_voice.id in self._temp_channels else None

    def is_creator_channel(self, channel_id: int) -> bool:
        """
        :param channel_id:
        :return:
        """
        return channel_id in self._creator_channels

    def is_temp_channel(self, channel_id: int) -> bool:
        """
        :param channel_id:
        :return:
        """
        return channel_id in self._temp_channels

    def get_user_channel(
        self, member: discord.Member, interaction_channel_id: int = None
    ) -> source.channel_class.TempVoice | False:
        """
        Return temp voice by discord member id if exists else return False
        :param interaction_channel_id: Use if user has administrative privileges
        :param member:
        :return:
        """
        if (
            interaction_channel_id
            and member.guild_permissions.administrator
            and interaction_channel_id in self._temp_channels
        ):
            return self._temp_channels[interaction_channel_id]

        for temp_channel in self._temp_channels.values():
            if temp_channel.owner.id == member.id:
                return temp_channel
        return False

    def get_user_transferred_channel(
        self, member_id: int
    ) -> source.channel_class.TempVoice | False:
        """
        Try to find user temp voice when user transfer his owner
        :param member_id:
        :return:
        """
        for temp_channel in self._temp_channels.values():
            if temp_channel.creator.id == member_id:
                return temp_channel
        return False

    def get_creator_channels_ids(self) -> list[int]:
        return self._creator_channels.keys()  # noqa

    def channel(self, channel_id: int) -> source.channel_class.TempVoice | None:
        """
        Return TempVoice by channel id or None if not exists
        :param channel_id:
        :return:
        """
        if channel_id not in self._temp_channels:
            return None

        if (
            datetime.datetime.now() - self._last_data_update
            >= datetime.timedelta(minutes=5)
        ):
            self._update(self.guild.id)

        return self._temp_channels[channel_id]

    def all_channels(self) -> dict[int, source.channel_class.TempVoice]:
        return self._temp_channels

    async def restore_channel(
        self,
        channel: discord.VoiceChannel,
        owner_id: int,
        creator_id: int,
        adv_msg_id: int,
    ) -> source.channel_class.TempVoice:
        owner = self.guild.get_member(owner_id)
        creator = self.guild.get_member(creator_id)
        if not owner:
            owner = self.guild.get_member(self.bot.user.id)
        self._temp_channels[channel.id] = source.channel_class.TempVoice(
            self.bot, channel, owner, self.server_id, creator=creator
        )
        if adv_msg_id:
            try:
                adv_msg = await self.adv_channel.fetch_message(adv_msg_id)
                if adv_msg:
                    self._temp_channels[
                        channel.id
                    ].adv = source.channel_class.Adv(adv_msg)
                    await self._temp_channels[channel.id].update_adv()
            except discord.NotFound:
                self._temp_channels[channel.id].adv = None
        return self._temp_channels[channel.id]
