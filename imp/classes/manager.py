from __future__ import annotations

from imp.classes.poll import Poll

from typing import TYPE_CHECKING, Dict
if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class PollManager:
    def __init__(self, client: BetterBot):
        self.client = client
        self.polls: Dict[str, Poll] = {}

    def init_poll(self, poll_hid: str) -> Poll:
        _poll = Poll(self.client, poll_hid)
        self.polls[poll_hid] = _poll
        return _poll

    def get_poll(self, poll_hid: str) -> Poll:
        _poll = self.polls.get(poll_hid)

        if _poll is None:
            _poll = self.init_poll(poll_hid)

        return _poll

    def set_poll(self, poll: Poll):
        self.polls[poll.poll_hid] = poll

