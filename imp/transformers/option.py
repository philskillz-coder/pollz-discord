from __future__ import annotations

from abc import ABC

from discord import app_commands

from imp.classes.option import PollOption
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
            guild_uuid = await interaction.client.db_mgr.get_guild_uuid(
                cursor=cursor,
                guild_id=interaction.guild.id
            )
            exists = await interaction.client.db_mgr.poll_option_exists(
                cursor=cursor,
                guild_hid=guild_uuid,
                option_hid=code
            )

            if not exists:
                raise TransformerException(f"A poll option with the id `{code}` does not exist!")

            poll_code = await interaction.client.db_mgr.get_option_poll(
                cursor=cursor,
                option_hid=code
            )
            return await (await interaction.client.manager.get_poll(poll_code)).get_option(cursor, code)

    @classmethod
    async def autocomplete(cls, interaction: BetterInteraction, value: str) -> List[app_commands.Choice[str]]:
        async with interaction.client.pool.acquire() as cursor:
            poll_clean_id = interaction.namespace.poll
            _poll_raw_id = interaction.client.hash_mgr.decode(poll_clean_id)
            if not _poll_raw_id:
                return []

            _id, *_ = _poll_raw_id

            raw_ids: List[Tuple[int, str]] = await cursor.fetch(
                "SELECT id, name FROM poll_options WHERE poll = $1",
                _id
            )

        value = value.upper()

        choices: List[app_commands.Choice] = []
        for raw_id, name in raw_ids:
            clean_id = interaction.client.hash_mgr.encode(raw_id)
            if clean_id.startswith(value) or name.startswith(value):
                choices.append(app_commands.Choice(name=f"{clean_id} | {name}", value=clean_id))

        return choices
