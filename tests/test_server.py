from types import MappingProxyType

import discord
import pytest
from pytest_mock import MockFixture

from src.services import PartySysBot, Server
from src.utils import TempVoiceABC


@pytest.fixture
def bot(mocker: MockFixture) -> PartySysBot:
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
    bot.loop = mocker.AsyncMock()

    return bot


@pytest.fixture
async def server(mocker: MockFixture, bot) -> Server:
    mocker.patch.dict("config.CFG", {"squad_names": []})

    return await Server.new(
        bot=bot,
        guild=mocker.AsyncMock(spec=discord.Guild),
    )


@pytest.mark.asyncio
async def test_update_settings(mocker: MockFixture, server):
    mock_get_or_none = mocker.patch(
        "src.models.Servers.get_or_none",
        new_callable=mocker.AsyncMock,
        return_value=mocker.Mock(
            id=1,
            dis_adv_channel_id=1,
        ),
    )

    mock_filter = mocker.patch(
        "src.models.CreatorChannels.filter",
        new_callable=mocker.AsyncMock,
        return_value=[mocker.Mock(dis_id=1)],
    )

    mock_get_channel = mocker.patch(
        "src.services.PartySysBot.get_channel", return_value=mocker.Mock(id=1)
    )

    await server._update_settings(guild_id=1)

    mock_get_or_none.assert_called_once_with(dis_id=1)
    mock_filter.assert_called_once_with(server_id=1)
    mock_get_channel.assert_called_once_with(1)
    assert server.adv_channel.id == 1
    assert server.id == 1
    assert len(server._creator_channels) == 1
    assert server._creator_channels[1].dis_id == 1


@pytest.mark.asyncio
async def test_create_channel(mocker: MockFixture, server):
    server._creator_channels = MappingProxyType(
        {1: mocker.Mock(dis_category_id=1)}
    )
    mock_get_channel = mocker.patch(
        "src.services.PartySysBot.get_channel",
        return_value=mocker.Mock(spec=discord.CategoryChannel),
    )
    mock_temp_voice_create = mocker.patch(
        "src.services.temp_voice.TempVoice.create",
        return_value=mocker.Mock(
            channel=mocker.Mock(id=1, spec=discord.VoiceChannel)
        ),
    )

    res = await server.create_tv(mocker.Mock(display_name="test"), 1)

    assert isinstance(res, discord.VoiceChannel)
    assert res.id == 1
    mock_get_channel.assert_called_once_with(1)
    mock_temp_voice_create.assert_called_once()
    assert len(server._temp_channels) == 1
    assert server._temp_channels[1].channel.id == 1


@pytest.mark.asyncio
async def test_delete_channel(mocker: MockFixture, server):
    temp_channel = mocker.AsyncMock(id=1)
    server._temp_channels = {1: temp_channel}

    mocker.patch("src.services.TempVoice.delete")

    await server.del_tv(1)

    assert len(server._temp_channels) == 0


@pytest.mark.asyncio
async def test_get_member_tv_owner(mocker: MockFixture, server):
    member = mocker.Mock(
        id=2,
        guild_permissions=mocker.Mock(administrator=False),
        spec=discord.Member,
    )
    temp_channel = mocker.AsyncMock(id=11, owner=member)
    server._temp_channels = {11: temp_channel}

    assert server.get_member_tv(member)
    assert server.get_member_tv(mocker.Mock(id=1)) is False


@pytest.mark.asyncio
async def test_get_member_tv_admin(mocker: MockFixture, server):
    member = mocker.Mock(
        id=3,
        guild_permissions=mocker.Mock(administrator=True),
        spec=discord.Member,
    )
    temp_channel = mocker.AsyncMock(id=11, owner=mocker.Mock(id=3))
    server._temp_channels = {11: temp_channel}

    assert server.get_member_tv(member, 11)
    assert server.get_member_tv(member) is False


@pytest.mark.asyncio
async def test_get_member_transferred_tv(mocker: MockFixture, server):
    member = mocker.Mock(
        id=3,
        guild_permissions=mocker.Mock(administrator=True),
        spec=discord.Member,
    )
    temp_channel = mocker.AsyncMock(
        id=11,
        creator=member,
    )
    server._temp_channels = {11: temp_channel}

    assert server.get_member_transferred_tv(member)
    assert server.get_member_transferred_tv(mocker.Mock(id=1)) is False


@pytest.mark.asyncio
async def test_channel(mocker: MockFixture, server):
    channel = mocker.Mock(id=1)
    server._temp_channels = {1: channel}

    assert server.tv(1) == channel
    assert server.tv(2) is None


@pytest.mark.asyncio
async def test_restore_channel_without_adv(mocker: MockFixture, server):
    server.guild.get_member.return_value = mocker.Mock(
        id=1, spec=discord.Member
    )
    mock_fetch_message = mocker.patch(
        "discord.abc.Messageable.fetch_message",
    )
    mock_adv_update = mocker.patch("src.ui.adv.Adv.update")
    channel = mocker.Mock(id=1)

    res = await server.restore_tv(channel, 1, 1, 0)

    mock_fetch_message.assert_not_called()
    mock_adv_update.assert_not_called()
    assert isinstance(res, TempVoiceABC)
    assert res.channel.id == channel.id
    assert server.tv(channel.id) == res


@pytest.mark.asyncio
async def test_restore_channel_with_adv(mocker: MockFixture, server):
    server.guild.get_member.return_value = mocker.Mock(
        id=1, spec=discord.Member
    )
    server.adv_channel = mocker.AsyncMock(id=11)
    mock_adv_update = mocker.patch("src.ui.adv.Adv.update")
    channel = mocker.Mock(id=1)

    res = await server.restore_tv(channel, 1, 1, 11)

    mock_adv_update.assert_called_once_with(res)
    assert isinstance(res, TempVoiceABC)
    assert res.channel.id == channel.id
    assert server.tv(channel.id) == res
