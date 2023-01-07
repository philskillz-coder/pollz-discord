from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from asyncpg import Connection

if TYPE_CHECKING:
    from imp.classes.poll import Poll


class PollOption:
    def __init__(self, poll: Poll, option_hid: str):
        self.poll = poll
        self._option_hid = option_hid

    @property
    def option_hid(self) -> str:
        return self._option_hid

    async def name(self, cursor: Connection) -> Optional[str]:
        return await self.poll.client.database.get_poll_option_name(
            cursor,
            option_hid=self.option_hid
        )

    async def vote_percentage(self, cursor: Connection) -> Optional[float]:
        return await self.poll.client.database.get_poll_option_vote_percentage(
            cursor,
            poll_hid=self.poll.poll_hid,
            option_hid=self.option_hid
        )
