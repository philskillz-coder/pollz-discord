from __future__ import annotations

from abc import ABC

from discord import app_commands

from imp.classes.poll import Poll
from imp.database.database import Database
from imp.better.check import BetterCheckFailure
from typing import TYPE_CHECKING, List, Tuple
if TYPE_CHECKING:
    from imp.better.interaction import BetterInteraction


class Poll_Transformer(app_commands.Transformer, ABC):
    @classmethod
    async def transform(cls, interaction: BetterInteraction, value: str) -> Poll:
        poll_rid, *_ = Database.save_unpack(interaction.client.poll_hashids.decode(value))
        if poll_rid is None:
            # raise TransformerException(f"A poll with the id `{value}` does not exist!")
            raise BetterCheckFailure(
                interaction.guild.id,
                "checks.poll.not_exist",
                value=value
            )
        return interaction.client.manager.get_poll(poll_rid)

    @classmethod
    async def autocomplete(cls, interaction: BetterInteraction, value: str) -> List[app_commands.Choice[str]]:
        async with interaction.client.pool.acquire() as cursor:
            guild_rid = await interaction.client.database.get_guild_rid(cursor, guild_id=interaction.guild.id)
            poll_rids: List[Tuple[int, str]] = await cursor.fetch(
                "SELECT \"poll\".\"id\", \"config\".\"title\" FROM polls AS \"poll\" JOIN poll_config AS \"config\" "
                "ON \"config\".\"poll\" = \"poll\".\"id\" WHERE \"poll\".\"guild\" = $1",
                guild_rid
            )

        value = value.lower()
        choices: List[app_commands.Choice] = []
        for poll_rid, title in poll_rids:
            poll_hid = interaction.client.poll_hashids.encode(poll_rid)
            if poll_hid.lower().startswith(value) or title.lower().startswith(value.lower()):
                choices.append(app_commands.Choice(name=f"{poll_hid} ({title})", value=poll_hid))

        return choices
