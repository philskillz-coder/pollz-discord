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
        async with interaction.client.pool.acquire() as cursor:
            exists = await interaction.client.database.poll_option_exists(
                cursor,
                option_hid=value
            )

            if not exists:
                raise TransformerException(f"A poll option with the id `{value}` does not exist!")

            poll_hid = await interaction.client.database.get_option_poll(
                cursor,
                option_hid=value
            )

            return await (interaction.client.manager.get_poll(poll_hid)).get_option(cursor, value)

    @classmethod
    async def autocomplete(cls, interaction: BetterInteraction, value: str) -> List[app_commands.Choice[str]]:
        async with interaction.client.pool.acquire() as cursor:
            poll_hid = interaction.namespace.poll
            _poll_hid, *_ = Database.save_unpack(interaction.client.poll_hashids.decode(poll_hid))

            if _poll_hid is None:
                return []

            # noinspection SpellCheckingInspection
            _option_hids: List[Tuple[int, str]] = await cursor.fetch(
                "SELECT id, name FROM poll_options WHERE poll = $1",
                _poll_hid
            )

        value = value.lower()

        choices: List[app_commands.Choice] = []
        for _option_hid, name in _option_hids:
            option_hid = interaction.client.option_hashids.encode(_option_hid)
            if option_hid.lower().startswith(value) or name.lower().startswith(value):
                choices.append(app_commands.Choice(name=f"{option_hid} ({name})", value=option_hid))

        return choices
