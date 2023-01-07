from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from asyncpg import Connection

if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class Translator:
    DEFAULT_LANGUAGE = "34ac8b6b-40d5-49cd-a045-c417c8d90037"

    def __init__(self, client: BetterBot):
        self.client = client

    async def __call__(self, cursor: Connection, guild: discord.Guild, key: str, **format_args):
        return await self.translate(cursor, guild, key, **format_args)

    async def translate(self, *_, key: str, **kwargs):
        return f"<TRANSLATION:{key}#{kwargs}>"

    #
    # async def translate(
    #         self,
    #         cursor: Connection,
    #         guild: Union[discord.Guild, str],
    #         key: str,
    #         **format_args
    # ):
    #     if isinstance(guild, discord.Guild):
    #         guild_uuid = await self.client.db_mgr.get_guild_hid(
    #             cursor=cursor,
    #             guild_id=guild.id
    #         )
    #     else:
    #         guild_uuid = guild
    #
    #     guild_language = await self.client.db_mgr.get_guild_language(
    #         cursor=cursor,
    #         guild_hid=guild_uuid
    #     )
    #
    #
    #     # noinspection PyBroadException
    #     try:
    #         return translation.format_map(format_args)
    #     except Exception as e:
    #         return "TRANSLATION NOT FOUND"
