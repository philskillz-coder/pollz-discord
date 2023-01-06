from __future__ import annotations

import discord
from discord import ui

from asyncpg import Connection
from imp.classes.vote import PollVote

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from imp.better.bot import BetterBot
    from imp.better.interaction import BetterInteraction
    from imp.classes.option import PollOption
    from imp.classes.poll import Poll


class PollOptionButton(ui.Button):
    def __init__(self, option: PollOption, label: str, custom_id: str):
        super().__init__(
            label=label,
            custom_id=custom_id
        )
        self.option = option

    # TODO: implelemt interaction check

    async def callback(self, interaction: BetterInteraction):
        async with interaction.client.pool.acquire() as cursor:
            await self.option.poll.add_vote(cursor, PollVote(interaction.user.id, self.option.poll.poll_hid,
                                                             self.option.option_hid))
            await self.option.poll.update(cursor)
            await interaction.response.send_message(
                content="Voted for %s" % self.option.option_hid,  # TODO: Add translation
                ephemeral=True
            )


class PollStartButton(ui.Button):
    def __init__(self, poll: Poll, custom_id: str):
        super().__init__(
            label="Start",
            custom_id=custom_id,
            style=discord.ButtonStyle.green
        )
        self.poll = poll

    async def callback(self, interaction: BetterInteraction):
        async with interaction.client.pool.acquire() as cursor:
            await interaction.client.db_mgr.poll_start(
                cursor=cursor,
                poll_hid=self.poll.poll_hid
            )
            await self.poll.update(cursor)
            await interaction.response.send_message(
                content="Started poll %s" % self.poll.poll_hid,
                ephemeral=True
            )
            await self.view.press_start(cursor)


class PollStopButton(ui.Button):
    def __init__(self, poll: Poll, custom_id: str):
        super().__init__(
            label="Stop",
            custom_id=custom_id,
            style=discord.ButtonStyle.red
        )
        self.poll = poll

    async def callback(self, interaction: BetterInteraction):
        async with interaction.client.pool.acquire() as cursor:
            await interaction.client.db_mgr.poll_stop(
                cursor=cursor,
                poll_hid=self.poll.poll_hid
            )
            await self.poll.update(cursor)
            await interaction.response.send_message(
                content="Stopped poll %s" % self.poll.poll_hid,
                ephemeral=True
            )
            await self.view.press_stop()


class PollView(ui.View):
    def __init__(self, client: BetterBot, poll: Poll):
        super().__init__(timeout=None)
        self.client = client
        self.poll = poll

    async def add_options(self, cursor: Connection):
        self.clear_items()

        for option in (await self.poll.options(cursor)).values():
            self.add_item(
                PollOptionButton(option, label=await option.name(cursor), custom_id=option.option_hid)
            )

        return self

    async def add_stop(self):
        self.add_item(PollStopButton(self.poll, f"{self.poll.poll_hid}.stop"))

    async def add_start(self):
        self.add_item(PollStartButton(self.poll, f"{self.poll.poll_hid}.start"))

    async def press_start(self, cursor: Connection):
        message = await self.poll.message(cursor)
        await self.add_options(cursor)
        await self.add_stop()

        await message.edit(
            view=self
        )

    async def press_stop(self):
        self.clear_items()
        self.stop()

        return self

    async def run(self, cursor: Connection):
        started = await self.client.db_mgr.poll_started(
            cursor=cursor,
            poll_hid=self.poll.poll_hid
        )

        if started:
            await self.add_options(cursor)
            await self.add_stop()

        else:
            await self.add_start()

        return self
