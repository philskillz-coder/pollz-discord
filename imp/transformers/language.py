from abc import ABC

from discord import app_commands
from imp.better.check import BetterCheckFailure
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from imp.better.interaction import BetterInteraction


class Language_Transformer(app_commands.Transformer, ABC):
    @classmethod
    async def transform(cls, interaction: "BetterInteraction", value: str) -> str:
        if value not in interaction.client.translator.available_locales:
            # raise BetterCheckFailure("The language `%s` does not exist." % value)
            raise BetterCheckFailure(
                interaction.guild.id,
                "checks.language.not_exist",
                value=value
            )
        return value

    @classmethod
    async def autocomplete(cls, interaction: "BetterInteraction", value: str) -> List[app_commands.Choice[str]]:
        value = value.lower()

        choices: List[app_commands.Choice] = []
        for locale in interaction.client.translator.available_locales:
            if locale.lower().startswith(value):
                choices.append(app_commands.Choice(name=locale, value=locale))

        return choices
