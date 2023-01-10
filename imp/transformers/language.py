from abc import ABC

from discord import app_commands

from imp.errors import TransformerException

from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from imp.better.interaction import BetterInteraction


class Language_Transformer(app_commands.Transformer, ABC):
    @classmethod
    async def transform(cls, interaction: "BetterInteraction", value: str) -> str:
        if value not in interaction.client.translator.available_locales:
            raise TransformerException(f"The language `{value}` does not exist.")

        return value

    @classmethod
    async def autocomplete(cls, interaction: "BetterInteraction", value: str) -> List[app_commands.Choice[str]]:
        value = value.lower()

        choices: List[app_commands.Choice] = [
            app_commands.Choice(name=locale, value=locale)
            for locale in interaction.client.translator.available_locales
            if locale.lower().startswith(value)
        ]
        return choices
