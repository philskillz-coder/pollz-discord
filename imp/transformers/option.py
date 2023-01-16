from __future__ import annotations

from abc import ABC

from discord import app_commands

from imp.classes.option import PollOption
from imp.database.database import Database
from imp.better.check import BetterCheckFailure

from typing import TYPE_CHECKING, List, Tuple
if TYPE_CHECKING:
    from imp.better.interaction import BetterInteraction


class Option_Transformer(app_commands.Transformer, ABC):
    @classmethod
    async def transform(cls, interaction: BetterInteraction, value: str) -> PollOption:
        option_rid, *_ = Database.save_unpack(interaction.client.option_hashids.decode(value))
        if option_rid is None:
            # raise TransformerException(f"A poll option with the id `{value}` does not exist!")
            raise BetterCheckFailure(
                interaction.guild.id,
                "checks.option.not_exist",
                value=value
            )
        async with interaction.client.pool.acquire() as cursor:
            poll_rid = await interaction.client.database.option_poll(
                cursor,
                option_rid=option_rid
            )
            poll = interaction.client.manager.get_poll(poll_rid)
            return await poll.get_option(cursor, option_rid)

    @classmethod
    async def autocomplete(cls, interaction: BetterInteraction, value: str) -> List[app_commands.Choice[str]]:
        async with interaction.client.pool.acquire() as cursor:
            poll_hid = interaction.namespace.poll
            poll_rid, *_ = Database.save_unpack(interaction.client.poll_hashids.decode(poll_hid))

            if poll_rid is None:
                return []

            option_rids: List[Tuple[int, str]] = await cursor.fetch(
                "SELECT id, name FROM poll_options WHERE poll = $1",
                poll_rid
            )

        value = value.lower()

        choices: List[app_commands.Choice] = []
        for option_rid, name in option_rids:
            option_hid = interaction.client.option_hashids.encode(option_rid)
            if option_hid.lower().startswith(value) or name.lower().startswith(value):
                choices.append(app_commands.Choice(name=f"{option_hid} ({name})", value=option_hid))

        return choices
