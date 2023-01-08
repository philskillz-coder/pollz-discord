from typing import TYPE_CHECKING, Optional

from asyncpg import Connection

if TYPE_CHECKING:
    from imp.classes.poll import Poll


class PollOption:

    # noinspection PyTypeChecker
    def __init__(self):
        self.poll: "Poll" = None
        self._option_hid: str = None

    @classmethod
    def from_data(cls, poll: "Poll", option_hid: str):
        instance = cls()
        instance.poll = poll
        instance._option_hid = option_hid
        return instance

    @property
    def option_hid(self) -> str:
        return self._option_hid

    async def name(self, cursor: Connection) -> Optional[str]:
        return await self.poll.client.database.get_poll_option_name(
            cursor,
            option_hid=self.option_hid
        )

    async def vote_count(self, cursor: Connection) -> Optional[int]:
        return await self.poll.client.database.get_option_vote_count(
            cursor,
            option_hid=self.option_hid
        )

