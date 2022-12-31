from __future__ import annotations

from abc import ABC

from discord import app_commands

from imp.classes.poll import Poll
from imp.errors import TransformerException

from typing import TYPE_CHECKING, List, Tuple
if TYPE_CHECKING:
    from imp.better.interaction import BetterInteraction


class Poll_Transformer(app_commands.Transformer, ABC):
    @classmethod
    async def transform(cls, interaction: BetterInteraction, value: str) -> Poll:
        raw_code = interaction.client.hash_mgr.decode(value)
        if not raw_code:
            raise TransformerException(f"`{value}` is not a poll id!")

        code, *_ = raw_code

        async with interaction.client.pool.acquire() as cursor:
            guild_uuid = await interaction.client.db_mgr.get_guild_uuid(
                cursor=cursor,
                guild_id=interaction.guild.id
            )
            exists = await interaction.client.db_mgr.poll_exists(
                cursor=cursor,
                poll_id=code
            )

            if not exists:
                raise TransformerException(f"A poll with the id `{code}` does not exist!")

        return interaction.client.manager.get_poll(code)

    @classmethod
    async def autocomplete(cls, interaction: BetterInteraction, value: str) -> List[app_commands.Choice[str]]:
        async with interaction.client.pool.acquire() as cursor:
            raw_ids: List[Tuple[int, str]] = await cursor.fetch(
                "SELECT id, name FROM polls WHERE guild = $1",
                await interaction.client.db_mgr.get_guild_uuid(
                    cursor=cursor,
                    guild_id=interaction.guild.id
                )
            )

        value = value.upper()

        choices: List[app_commands.Choice] = []
        for raw_id, name in raw_ids:
            clean_id = interaction.client.hash_mgr.encode(raw_id)
            if clean_id.startswith(value) or name.startswith(value):
                choices.append(app_commands.Choice(name=f"{clean_id} | {name}", value=clean_id))

        return choices
