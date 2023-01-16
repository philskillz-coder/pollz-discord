from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from asyncpg import Connection
from discord import ui

from imp.classes.vote import PollVote
from imp.emoji import Emojis

if TYPE_CHECKING:
    from imp.better.interaction import BetterInteraction
    from imp.classes.option import PollOption
    from imp.classes.poll import Poll


class PollOptionButton(ui.Button):
    def __init__(self, option: PollOption, label: str, emoji: str, custom_id: str, row: int):
        super().__init__(
            label=label,
            emoji=emoji,
            custom_id=custom_id,
            row=row
        )
        self.option = option

    async def callback(self, interaction: BetterInteraction):
        # todo: require a role for voting
        async with interaction.client.pool.acquire() as cursor:
            if await self.option.poll.user_voted(
                    cursor,
                    user=interaction.user.id
            ):
                return await interaction.response.send_message(
                    content=await self.option.poll.client.translator.translate(
                        cursor,
                        guild_rid=await self.option.poll.guild_rid(cursor),
                        key="poll.already_voted"
                    ),
                    ephemeral=True
                )

            await interaction.response.send_message(
                content=await self.option.poll.client.translator.translate(
                    cursor,
                    guild_rid=await self.option.poll.guild_rid(cursor),
                    key="poll.voted",
                    option=await self.option.name(cursor)
                ),
                ephemeral=True
            )

            await self.option.poll.add_vote(
                cursor,
                PollVote(interaction.user.id, self.option.poll.rid, self.option.rid)
            )
            await asyncio.sleep(self.option.poll.POLL_UPDATE_TIME)
            if self.option.poll.update_ready():
                await self.option.poll.update(cursor)


# class PollStartButton(ui.Button):
#     def __init__(self, poll: Poll, custom_id: str, row: int):
#         super().__init__(
#             label="Start",
#             custom_id=custom_id,
#             style=discord.ButtonStyle.green,
#             row=row
#         )
#         self.poll = poll
#
#     async def callback(self, interaction: BetterInteraction):
#         if not interaction.user.resolved_permissions.administrator:
#             return await interaction.response.send_message(
#                 "No permissions",
#                 ephemeral=True
#             )
#         async with interaction.client.pool.acquire() as cursor:
#             await interaction.client.database.poll_start(
#                 cursor,
#                 poll_rid=self.poll.rid
#             )
#             await interaction.response.send_message(
#                 content=await self.poll.client.translator.translate(
#                     cursor,
#                     guild_rid=await self.poll.guild_rid(cursor),
#                     key="poll.start.success",
#                     id=self.poll.hid
#                 ),
#                 ephemeral=True
#             )
#             await self.view.press_start(cursor)
#             await self.poll.update(cursor)


# class PollStopButton(ui.Button):
#     def __init__(self, poll: Poll, custom_id: str, row: int):
#         super().__init__(
#             label="Stop",
#             custom_id=custom_id,
#             style=discord.ButtonStyle.red,
#             row=row
#         )
#         self.poll = poll
#
#     async def callback(self, interaction: BetterInteraction):
#         if not interaction.user.resolved_permissions.administrator:
#             return await interaction.response.send_message(
#                 "No permissions",
#                 ephemeral=True
#             )
#         async with interaction.client.pool.acquire() as cursor:
#             await interaction.response.send_message(
#                 content=await self.poll.client.translator.translate(
#                     cursor,
#                     guild_rid=await self.poll.guild_rid(cursor),
#                     key="poll.stop.success",
#                     id=self.poll.hid
#                 ),
#                 ephemeral=True
#             )
#
#             await self.poll.stop(cursor)


class PollView(ui.View):
    def __init__(self, poll: Poll):
        super().__init__(timeout=None)
        self.poll = poll
        self._option_count = 0

    async def add_options(self, cursor: Connection):
        options = await self.poll.options(cursor)
        self._option_count = len(options)
        for i, option in enumerate(options):
            self.add_item(
                PollOptionButton(
                    option,
                    label=await option.name(cursor),
                    emoji=Emojis.emojis[i],
                    custom_id=f"poll:{self.poll.hid}:option:{option.hid}",
                    row=i//4
                )
            )

        return self

    # async def add_stop(self):
    #     self.add_item(PollStopButton(self.poll, f"poll:{self.poll.hid}:stop", row=self._option_count//4+1))

    # async def add_start(self):
    #     self.add_item(PollStartButton(self.poll, f"poll:{self.poll.hid}:start", row=self._option_count//4+1))

    async def press_start(self, cursor: Connection):
        self.clear_items()
        await self.add_options(cursor)
        # await self.add_stop()

    async def press_stop(self):
        self.clear_items()
        self.stop()

    async def run(self, cursor: Connection):
        started = await self.poll.started(
            cursor,
        )

        if started:
            await self.add_options(cursor)
            # await self.add_stop()

        # else:
        #     await self.add_start()

        return self
