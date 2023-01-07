from __future__ import annotations

from abc import ABC

from discord import app_commands

from imp.classes.poll import Poll
from imp.database.database import Database
from imp.errors import TransformerException

from typing import TYPE_CHECKING, List, Tuple
if TYPE_CHECKING:
    from imp.better.interaction import BetterInteraction


class Poll_Transformer(app_commands.Transformer, ABC):
    @classmethod
    async def transform(cls, interaction: BetterInteraction, value: str) -> Poll:
        async with interaction.client.pool.acquire() as cursor:
            guild_hid = await interaction.client.database.get_guild_hid(
                cursor,
                guild_id=interaction.guild.id
            )
            exists = await interaction.client.database.poll_exists(
                cursor,
                guild_hid=guild_hid,
                poll_hid=value,
            )

            if not exists:
                raise TransformerException(f"A poll with the id `{value}` does not exist!")

        return interaction.client.manager.get_poll(value)

    @classmethod
    async def autocomplete(cls, interaction: BetterInteraction, value: str) -> List[app_commands.Choice[str]]:
        async with interaction.client.pool.acquire() as cursor:
            guild_hid = await interaction.client.database.get_guild_hid(cursor, guild_id=interaction.guild.id)
            _guild_hid, *_ = Database.save_unpack(interaction.client.guild_hashids.decode(guild_hid))

            all_poll_ids: List[Tuple[int, str]] = await cursor.fetch("SELECT \"poll\".\"id\", \"config\".\"title\" FROM polls AS \"poll\" JOIN poll_config AS \"config\" ON \"config\".\"poll\" = \"poll\".\"id\" WHERE \"poll\".\"guild\" = $1", _guild_hid)
            print(all_poll_ids, guild_hid, _guild_hid)
        print(value)

        value = value.lower()
        choices: List[app_commands.Choice] = []
        for _poll_hid, title in all_poll_ids:
            print(_poll_hid, title)
            poll_hid = interaction.client.poll_hashids.encode(_poll_hid)
            if poll_hid.lower().startswith(value) or title.lower().startswith(value.lower()):
                choices.append(app_commands.Choice(name=f"{poll_hid} ({title})", value=poll_hid))

        return choices
