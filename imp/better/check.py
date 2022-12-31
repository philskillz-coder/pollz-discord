from __future__ import annotations

from typing import Callable, Coroutine, Any

from imp import errors

from imp.better.interaction import BetterInteraction

CALLBACK = Callable[[BetterInteraction], Coroutine[Any, Any, bool]]

class BetterCheck:
    def __init__(self, name: str, callback: CALLBACK):
        self.name = name
        self.callback = callback

    async def __call__(self, interaction: BetterInteraction):
        res = None
        try:
            res = await self.callback(interaction)

        except errors.BetterCheckException as e:
            await interaction.response.send_message(
                **e.content,
                ephemeral=True
            )

            raise errors.HandeledCheckException(e, message="%s check failed" % self.name)

def better_check(name: str):
    def _better_check(callback: CALLBACK):
        return BetterCheck(name, callback)
    return _better_check
