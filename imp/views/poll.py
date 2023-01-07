from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import discord
from asyncpg import Connection
from discord import ui

from imp.classes.vote import PollVote

if TYPE_CHECKING:
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

    async def callback(self, interaction: BetterInteraction):
        async with interaction.client.pool.acquire() as cursor:
            if await self.option.poll.user_voted(
                    cursor,
                    user=interaction.user.id
            ):
                return await interaction.response.send_message(
                    content=await self.option.poll.client.translator.translate(
                        cursor,
                        guild=interaction.guild,
                        key="poll.already_voted"
                    )
                )

            await interaction.response.send_message(
                content=await self.option.poll.client.translator.translate(
                    cursor,
                    guild=interaction.guild,
                    key="poll.voted",
                    option=await self.option.name(cursor)
                ),
                ephemeral=True
            )

            await self.option.poll.add_vote(
                cursor,
                PollVote(interaction.user.id, self.option.poll.poll_hid, self.option.option_hid)
            )
            await asyncio.sleep(self.option.poll.UPDATE_TIME)
            if self.option.poll.update_ready():
                await self.option.poll.update(cursor)


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
            await interaction.client.database.poll_start(
                cursor,
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
            await self.poll.stop(cursor)
            await interaction.response.send_message(
                content="Stopped poll %s" % self.poll.poll_hid,
                ephemeral=True
            )


class PollView(ui.View):
    def __init__(self, poll: Poll):
        super().__init__(timeout=None)
        self.poll = poll

    async def add_options(self, cursor: Connection):
        for option in (await self.poll.options(cursor)).values():
            self.add_item(
                PollOptionButton(option, label=await option.name(cursor), custom_id=f"poll:{self.poll.poll_hid}:option:{option.option_hid}")
            )

        return self

    async def add_stop(self):
        self.add_item(PollStopButton(self.poll, f"poll:{self.poll.poll_hid}:stop"))

    async def add_start(self):
        self.add_item(PollStartButton(self.poll, f"poll:{self.poll.poll_hid}:start"))

    async def press_start(self, cursor: Connection):
        self.clear_items()
        await self.add_options(cursor)
        await self.add_stop()

        message = await self.poll.message(cursor)
        await message.edit(
            view=self
        )

    async def press_stop(self):
        self.clear_items()
        self.stop()

    async def run(self, cursor: Connection):
        started = await self.poll.client.database.poll_started(
            cursor,
            poll_hid=self.poll.poll_hid
        )

        if started:
            await self.add_options(cursor)
            await self.add_stop()

        else:
            await self.add_start()

        return self
