from __future__ import annotations

from imp.classes.poll import Poll

from typing import TYPE_CHECKING, Dict
if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class PollManager:
    def __init__(self, client: BetterBot):
        self.client = client
        self.polls: Dict[int, Poll] = {}

    def init_poll(self, poll_id: int) -> Poll:
        _poll = Poll(self.client, poll_id)
        self.polls[poll_id] = _poll
        return _poll

    def get_poll(self, poll_id: int) -> Poll:
        _poll = self.polls.get(poll_id)

        if _poll is None:
            _poll = self.init_poll(poll_id)

        return _poll

    def set_poll(self, poll: Poll):
        self.polls[poll.poll_id] = poll

