from typing import TYPE_CHECKING, Optional

from asyncpg import Connection

if TYPE_CHECKING:
    from imp.classes.poll import Poll


class PollOption:

    # noinspection PyTypeChecker
    def __init__(self, poll: "Poll", option_rid: int):
        self.poll: "Poll" = poll

        self._rid: int = option_rid
        self._hid: Optional[str] = None
        self._name: Optional[str] = None

    @classmethod
    def from_data(cls, poll: "Poll", option_rid: int):
        return cls(poll, option_rid)

    @property
    def rid(self) -> int:
        return self._rid

    @property
    def hid(self) -> str:
        if self._hid is not None:
            return self._hid

        self._hid = self.poll.client.option_hashids.encode(self._hid)
        return self._hid

    async def name(self, cursor: Connection) -> str:
        if self._name is not None:
            return self._name

        self._name = await self.poll.client.database.poll_option_name(
            cursor,
            option_rid=self.rid
        )
        return self._name

    async def vote_count(self, cursor: Connection) -> int:
        return await self.poll.client.database.option_vote_count(
            cursor,
            option_rid=self.rid
        )

