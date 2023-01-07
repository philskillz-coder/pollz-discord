from __future__ import annotations

from abc import ABC

from discord import app_commands

from imp.classes.option import PollOption
from imp.database.database import Database
from imp.errors import TransformerException

from typing import TYPE_CHECKING, List, Tuple
if TYPE_CHECKING:
    from imp.better.interaction import BetterInteraction


class Option_Transformer(app_commands.Transformer, ABC):
    @classmethod
    async def transform(cls, interaction: BetterInteraction, value: str) -> PollOption:
        raw_code = interaction.client.hash_mgr.decode(value)
        if not raw_code:
            raise TransformerException(f"`{value}` is not a option id!")

        code, *_ = raw_code

        async with interaction.client.pool.acquire() as cursor:
            guild_uuid = await interaction.client.database.get_guild_hid(
                cursor,
                guild_id=interaction.guild.id
            )
            exists = await interaction.client.database.poll_option_exists(
                cursor,
                guild_hid=guild_uuid,
                option_hid=code
            )

            if not exists:
                raise TransformerException(f"A poll option with the id `{code}` does not exist!")

            poll_hid = await interaction.client.database.get_option_poll(
                cursor,
                option_hid=code
            )
            return await (interaction.client.manager.get_poll(poll_hid)).get_option(cursor, code)

    @classmethod
    async def autocomplete(cls, interaction: BetterInteraction, value: str) -> List[app_commands.Choice[str]]:
        async with interaction.client.pool.acquire() as cursor:
            poll_hid = interaction.namespace.poll
            _poll_hid, *_ = Database.save_unpack(interaction.client.poll_hashids.decode(poll_hid))

            if _poll_hid is None:
                return []

            raw_ids: List[Tuple[int, str]] = await cursor.fetch(
                "SELECT id, name FROM poll_options WHERE poll = $1",
                _poll_hid
            )

        value = value.upper()

        choices: List[app_commands.Choice] = []
        for raw_id, name in raw_ids:
            clean_id = interaction.client.option_hashids.encode(raw_id)
            if clean_id.startswith(value) or name.startswith(value):
                choices.append(app_commands.Choice(name=f"{clean_id} | {name}", value=clean_id))

        return choices
