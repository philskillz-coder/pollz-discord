from __future__ import annotations

import discord

from imp.errors import PollException

from asyncpg import Connection

from typing import TYPE_CHECKING, Optional, List, Tuple

if TYPE_CHECKING:
    from imp.better.bot import BetterBot
    from imp.classes.poll import Poll


class PollOption:
    def __init__(self, client: BetterBot, poll: Poll, option_id: int):
        self.client = client
        self.poll = poll
        self._option_id = option_id

        self._clean_option_id: Optional[str] = None

    @property
    def option_id(self) -> int:
        return self._option_id

    @property
    def clean_option_id(self):
        if self._clean_option_id is not None:
            return self._clean_option_id

        self._clean_option_id = self.client.hash_mgr.encode(self.option_id)
        return self._clean_option_id

    async def name(self, cursor: Connection) -> Optional[str]:
        return await self.client.db_mgr.get_poll_option_name(
            cursor=cursor,
            option_id=self.option_id
        )

    async def info(self, cursor: Connection) -> Optional[str]:
        return await self.client.db_mgr.get_poll_option_info(
            cursor=cursor,
            option_id=self.option_id
        )

    async def vote_percentage(self, cursor: Connection) -> Optional[float]:
        return await self.client.db_mgr.get_poll_option_vote_percentage(
            cursor=cursor,
            poll_id=self.poll.poll_id,
            option_id=self.option_id
        )
