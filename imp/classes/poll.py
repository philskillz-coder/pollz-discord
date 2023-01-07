from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict

import discord
from asyncpg import Connection

from imp.classes.option import PollOption
from imp.classes.vote import PollVote
from imp.database.database import Database
from imp.views.poll import PollView

if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class Poll:
    def __init__(self, client: BetterBot, poll_hid: str):
        self.client = client
        self.poll_hid = poll_hid

        self._guild: Optional[discord.Guild] = None
        self._channel: Optional[discord.TextChannel] = None
        self._message: Optional[discord.PartialMessage] = None
        self.view: Optional[PollView] = None

    @classmethod
    async def create(cls, client: BetterBot, guild_hid: str, channel_id: int, message_id: int, poll_title: Optional[str] = None, poll_description: Optional[str] = None):
        async with client.pool.acquire() as cursor:
            poll_hid = await client.database.create_poll(
                cursor,
                guild_hid=guild_hid,
                channel_id=channel_id,
                message_id=message_id,
                poll_title=poll_title,
                poll_description=poll_description
            )

            return cls(client, poll_hid)

    def set_view(self, view: PollView):
        self.view = view

    async def started(self, cursor: Connection) -> Optional[bool]:
        return await self.client.database.poll_started(
            cursor,
            poll_hid=self.poll_hid
        )

    async def title(self, cursor: Connection) -> Optional[str]:
        return await self.client.database.get_poll_title(
            cursor,
            poll_hid=self.poll_hid
        )

    async def description(self, cursor: Connection) -> Optional[str]:
        return await self.client.database.poll_description(
            cursor,
            poll_hid=self.poll_hid
        )

    async def total_votes(self, cursor: Connection) -> Optional[int]:
        return await self.client.database.poll_vote_count(
            cursor,
            poll_hid=self.poll_hid
        )

    async def options(self, cursor: Connection) -> Optional[Dict[int, PollOption]]:
        options = await self.client.database.get_poll_options(
            cursor,
            poll_hid=self.poll_hid
        )

        return {
            code: PollOption(self.client, self, code) for code in options
        }

    async def guild(self, cursor: Connection):
        if self._guild is not None:
            return self._guild

        self._guild = self.client.get_guild(
            await self.client.database.get_guild_id(
                cursor,
                guild_hid=await self.client.database.get_poll_guild(
                    cursor,
                    poll_hid=self.poll_hid
                )
            )
        )
        return self._guild

    async def channel(self, cursor: Connection):
        if self._channel is not None:
            return self._channel

        self._channel = self.client.get_channel(
            await self.client.database.get_poll_channel(
                cursor,
                poll_hid=self.poll_hid
            )
        )
        return self._channel

    async def message(self, cursor: Connection):
        if self._message is not None:
            return self._message

        chn = await self.channel(cursor)
        self._message = chn.get_partial_message(
            await self.client.database.get_poll_message(
                cursor,
                poll_hid=self.poll_hid
            )
        )
        return self._message

    async def exists(self, cursor: Connection) -> Optional[bool]:
        return await self.client.database.poll_exists(
            cursor,
            poll_hid=self.poll_hid
        )

    async def start(self, cursor: Connection):
        await self.client.database.poll_start(
            cursor,
            poll_hid=self.poll_hid
        )
        await (await self.message(cursor)).edit(
            view=await PollView(self.client, self).run(cursor)
        )
        await self.update(cursor)

    async def stop(self):
        pass

    async def delete(self):
        async with self.client.pool.acquire() as cursor:
            await self.client.database.delete_poll(
                cursor,
                poll_hid=self.poll_hid
            )

    async def add_option(self, cursor: Connection, name: str, info: str = None) -> Optional[int]:
        return await self.client.database.create_poll_option(
            cursor,
            poll_hid=self.poll_hid,
            option_name=name
        )

    async def remove_option(self, cursor: Connection, option_hid: str):
        await self.client.database.remove_poll_option(
            cursor,
            option_hid=option_hid
        )

    async def get_option(self, cursor: Connection, option_hid: int):
        return (await self.options(cursor)).get(option_hid)

    async def update(self, cursor: Connection):
        options = await self.options(cursor)
        max_opt = await self.client.database.get_max_poll_option_name(
            cursor,
            poll_hid=self.poll_hid
        )

        raw_options = []
        for opt in options.values():
            v = f"**{opt.option_hid}** {await opt.name(cursor)}:{(max_opt - len(await opt.name(cursor))) * ' '} {await opt.vote_percentage(cursor)}%"
            raw_options.append(v)

        option_string = "\n".join(
            raw_options
        )
        poll_info = f"```\n{await self.description(cursor)}```"
        poll_votes = f"**Total Votes**: {await self.total_votes(cursor)}"

        description = f""
        message = await self.message(cursor)

        embed = discord.Embed(
            title=await self.client.translator.translate(
                cursor=cursor,
                guild=await self.guild(cursor),
                key="poll.title",
                name=(await self.title(cursor)).upper()
            ),
            description=f"**Poll has {'' if await self.started(cursor) else 'not'} started!**\n{poll_info}{poll_votes}\n{option_string}"
        )
        embed.set_footer(
            text=await self.client.translator.translate(
                cursor=cursor,
                guild=await self.guild(cursor),
                key="poll.footer",
                id=self.poll_hid
            )
        )
        await message.edit(embed=embed)

    # noinspection PyMethodMayBeStatic
    async def add_vote(self, cursor: Connection, vote: PollVote):
        _option_hid, *_ = Database.save_unpack(self.client.option_hashids.decode(vote.option))

        _vote_hid, = await cursor.fetchrow(
            "INSERT INTO poll_votes(\"option\", \"user\") VALUES($1, $2) RETURNING \"id\"",
            _option_hid, vote.user
        )
        vote_hid = self.client.vote_hashids.encode(_vote_hid)
        return vote_hid

    async def user_voted(self, cursor: Connection, user: int):
        voted = await self.client.database.poll_user_voted(
            cursor,
            poll_hid=self.poll_hid,
            user_id=user
        )
        return voted
