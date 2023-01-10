from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, List

import discord
from asyncpg import Connection

from imp.classes.option import PollOption
from imp.classes.vote import PollVote
from imp.database.database import Database
from imp.emoji import Emojis
from imp.views.poll import PollView

if TYPE_CHECKING:
    from imp.better.bot import BetterBot


# noinspection PyTypeChecker
class Poll:
    UPDATE_TIME = 10
    MAX_OPTION_COUNT = 8

    def __init__(self, client: BetterBot, poll_hid: str):
        self.client = client
        self.poll_hid = poll_hid

        self._guild: Optional[discord.Guild] = None
        self._channel: Optional[discord.TextChannel] = None
        self._message: Optional[discord.PartialMessage] = None
        self.view: Optional[PollView] = None
        self._last_vote: datetime.datetime = None

    def update_ready(self):
        return (datetime.datetime.now()-self._last_vote).total_seconds() > self.UPDATE_TIME

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

    async def options(self, cursor: Connection) -> Optional[List[PollOption]]:
        options = await self.client.database.get_poll_options(
            cursor,
            poll_hid=self.poll_hid
        )

        return [
            PollOption.from_data(self, code) for code in options
        ]

    async def guild(self, cursor: Connection) -> str:
        return await self.client.database.get_poll_guild(
            cursor,
            poll_hid=self.poll_hid
        )

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
            view=await PollView(self).run(cursor)
        )
        await self.update(cursor)

    async def stop(self, cursor: Connection):
        await self.view.press_stop()
        await self.client.database.poll_stop(
            cursor,
            poll_hid=self.poll_hid
        )

        options = await self.options(cursor)
        max_opt = await self.client.database.get_max_poll_option_name(
            cursor,
            poll_hid=self.poll_hid
        )
        total_votes = await self.total_votes(cursor)

        _option_string = []
        _color_string = ""
        chars_used = 0
        max_chars = 100

        for i, opt in enumerate(options):
            name = await opt.name(cursor)
            vote_count = await opt.vote_count(cursor)
            percentage = round(vote_count / total_votes, 4) if total_votes >= 1 else 0.0000

            line = f"{Emojis.emojis[i]} **{name}**:{(max_opt - len(name)) * ' '} {percentage * 100}%"
            _option_string.append(line)

            char_count = int(percentage*max_chars)
            chars_used += char_count
            _color_string += char_count * Emojis.emojis[i]

        option_string = "\n".join(_option_string)
        _color_string += (max_chars - chars_used) * Emojis.black
        color_string = "\n".join([_color_string[i:i + 25] for i in range(0, len(_color_string), 25)])

        poll_info = f"```\n{await self.description(cursor)}```"
        poll_votes = f"**Total Votes**: {await self.total_votes(cursor)}"

        guild = await self.guild(cursor)
        title_translation = await self.client.translator.translate(
            cursor,
            guild_hid=guild,
            key="poll.title",
            name=(await self.title(cursor)).upper()
        )
        stopped_translation = await self.client.translator.translate(
            cursor,
            guild_hid=guild,
            key="poll.finished"
        )
        embed = discord.Embed(
            title=title_translation,
            description=f"{poll_info}\n{color_string}\n{stopped_translation}\n{poll_votes}\n{option_string}",
            colour=discord.Colour.red()
        )
        embed.set_footer(
            text=await self.client.translator.translate(
                cursor,
                guild_hid=await self.guild(cursor),
                key="poll.footer",
                id=self.poll_hid
            )
        )
        message = await self.message(cursor)
        await message.edit(embed=embed, view=self.view)
        await self.delete(cursor)

    async def delete(self, cursor: Connection):
        await self.client.database.delete_poll(
            cursor,
            poll_hid=self.poll_hid
        )

    async def add_option(self, cursor: Connection, name: str) -> Optional[int]:
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

    async def get_option(self, cursor: Connection, option_hid: str):
        return [i for i in await self.options(cursor) if i.option_hid == option_hid][0]

    async def update(self, cursor: Connection):
        options = await self.options(cursor)
        max_opt = await self.client.database.get_max_poll_option_name(
            cursor,
            poll_hid=self.poll_hid
        )
        total_votes = await self.total_votes(cursor)

        _option_string = []
        _color_string = ""
        chars_used = 0
        max_chars = 100

        for i, opt in enumerate(options):
            name = await opt.name(cursor)
            vote_count = await opt.vote_count(cursor)
            percentage = round(vote_count/total_votes, 4) if total_votes >= 1 else 0.0000

            line = f"{Emojis.emojis[i]} **{name}**:{(max_opt - len(name)) * ' '} {percentage * 100}%"
            _option_string.append(line)

            char_count = int(percentage*max_chars)
            chars_used += char_count
            _color_string += char_count * Emojis.emojis[i]

        option_string = "\n".join(_option_string)
        _color_string += (max_chars-chars_used) * Emojis.black
        color_string = "\n".join([_color_string[i:i+25] for i in range(0, len(_color_string), 25)])

        poll_info = f"```\n{await self.description(cursor)}```"
        poll_votes = f"**Total Votes**: {await self.total_votes(cursor)}"

        title_translation = await self.client.translator.translate(
            cursor,
            guild_hid=await self.guild(cursor),
            key="poll.title",
            name=await self.title(cursor)
        )
        print(title_translation)
        embed = discord.Embed(
            title=title_translation,
            description=f"{poll_info}\n{color_string}\n{poll_votes}\n{option_string}",
            colour=discord.Colour.green() if await self.started(cursor) else discord.Colour.yellow()
        )
        embed.set_footer(
            text=await self.client.translator.translate(
                cursor,
                guild_hid=await self.guild(cursor),
                key="poll.footer",
                id=self.poll_hid
            )
        )
        message = await self.message(cursor)
        await message.edit(embed=embed)

    async def add_vote(self, cursor: Connection, vote: PollVote):
        self._last_vote = datetime.datetime.now()
        _option_hid, *_ = Database.save_unpack(self.client.option_hashids.decode(vote.option))

        _vote_hid, = await cursor.fetchrow(
            "INSERT INTO poll_votes(\"option\", \"user\") VALUES($1, $2) RETURNING \"id\"",
            _option_hid, vote.user
        )
        return self.client.vote_hashids.encode(_vote_hid)

    async def user_voted(self, cursor: Connection, user: int):
        return await self.client.database.poll_user_voted(
            cursor, poll_hid=self.poll_hid, user_id=user
        )

    async def option_count(self, cursor: Connection):
        return await self.client.database.poll_option_count(cursor, self.poll_hid)

