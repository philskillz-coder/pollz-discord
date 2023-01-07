from __future__ import annotations

from discord import Interaction, InteractionResponse, TextChannel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class BetterInteraction(Interaction):
    client: BetterBot
    response: InteractionResponse
    channel: TextChannel
