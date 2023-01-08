from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext.commands import Cog

from imp.better.logger import BetterLogger
from imp.data.colors import Colors

if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class BetterCog(Cog, BetterLogger):
    def __init__(self, client: BetterBot):
        self.client = client
        self.name = "COG-"+self.qualified_name

    async def cog_load(self) -> None:
        self.log("cog_load", "Loaded", Colors.Y)

    async def cog_unload(self) -> None:
        self.log("cog_unload", "Unloaded", Colors.Y)
