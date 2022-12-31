from __future__ import annotations

from discord.ext.commands import Cog

from imp.data.colors import Colors
from datetime import datetime

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class BetterCog(Cog):
    def __init__(self, client: BetterBot):
        self.client = client
        self.name = self.qualified_name

    async def cog_load(self) -> None:
        self.log("cog_load", "Loaded", Colors.Y)

    async def cog_unload(self) -> None:
        self.log("cog_unload", "Unloaded", Colors.Y)

    def log(self, agent: str, message: str, color: str = Colors.GREEN):
        print(
            "%s%s[%s%s%s%s%s]%s %s[%s%s%s%s@%s%s%s%s]%s ~ %s%s%s" % (
                Colors.E, Colors.BOLD, Colors.E, Colors.B, datetime.now(), Colors.E, Colors.BOLD, Colors.E,
                Colors.BOLD, Colors.E, Colors.C, agent, Colors.E, Colors.C, self.name, Colors.E, Colors.BOLD, Colors.E,
                color, message, Colors.E
            )
        )
