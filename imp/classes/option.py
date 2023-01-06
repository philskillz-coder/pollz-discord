from __future__ import annotations

import discord

from imp.errors import PollException

from asyncpg import Connection

from typing import TYPE_CHECKING, Optional, List, Tuple

if TYPE_CHECKING:
    from imp.better.bot import BetterBot
    from imp.classes.poll import Poll


class PollOption:
    def __init__(self, client: BetterBot, poll: Poll, option_hid: str):
        self.client = client
        self.poll = poll
        self._option_hid = option_hid

    @property
    def option_hid(self) -> str:
        return self._option_hid

    async def name(self, cursor: Connection) -> Optional[str]:
        return await self.client.db_mgr.get_poll_option_name(
            cursor=cursor,
            option_hid=self.option_hid
        )

    async def vote_percentage(self, cursor: Connection) -> Optional[float]:
        return await self.client.db_mgr.get_poll_option_vote_percentage(
            cursor=cursor,
            poll_hid=self.poll.poll_hid,
            option_hid=self.option_hid
        )
