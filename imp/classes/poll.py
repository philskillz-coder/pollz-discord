import discord
from asyncpg import Connection
from datetime import datetime

from imp.classes.option import PollOption
from imp.classes.vote import PollVote
from imp.database.database import Database
from imp.emoji import Emojis
from imp.views.poll import PollView

from typing import TYPE_CHECKING, Optional, List
if TYPE_CHECKING:
    from imp.better.bot import BetterBot


# noinspection PyTypeChecker
class Poll:
    GUILD_MAX_POLLS = 5
    POLL_UPDATE_TIME = 10
    POLL_MAX_OPTIONS = 8

    def __init__(self, client: "BetterBot", poll_rid: int):
        self.client = client
        self._rid = poll_rid
        self._hid: Optional[str] = None

        self._guild_rid: Optional[int] = None
        self._guild_hid: Optional[str] = None
        self._channel_id: Optional[int] = None
        self._message_id: Optional[int] = None
        self.view: Optional[PollView] = None
        self._last_vote: Optional[datetime] = None
        self._started: Optional[bool] = None
        self._title: Optional[str] = None
        self._description: Optional[str] = None

    def update_ready(self):
        return (datetime.now()-self._last_vote).total_seconds() > self.POLL_UPDATE_TIME

    @classmethod
    async def create(
            cls,
            client: "BetterBot",
            _guild_hid: str,
            channel_id: int,
            message_id: int,
            poll_title: Optional[str] = None,
            poll_description: Optional[str] = None
    ):
        async with client.pool.acquire() as cursor:
            poll_rid = await client.database.create_poll(
                cursor,
                guild_rid=_guild_hid,
                channel_id=channel_id,
                message_id=message_id,
                poll_title=poll_title,
                poll_description=poll_description
            )

            return cls(client, poll_rid)

    def set_view(self, view: PollView):
        self.view = view

    @property
    def rid(self) -> int:
        return self._rid

    @property
    def hid(self) -> str:
        if self._hid is not None:
            return self._hid

        self._hid = self.client.poll_hashids.encode(self.rid)
        return self._hid

    async def started(self, cursor: Connection) -> bool:
        if self._started is not None:
            return self._started

        self._started = await self.client.database.poll_started(
            cursor,
            poll_rid=self.rid
        )
        return self._started

    async def title(self, cursor: Connection) -> str:
        if self._title is not None:
            return self._title
        self._title = await self.client.database.poll_title(
            cursor,
            poll_rid=self.rid
        )
        return self._title

    async def description(self, cursor: Connection) -> str:
        if self._description is not None:
            return self._description

        self._description = await self.client.database.poll_description(
            cursor,
            poll_rid=self.rid
        )
        return self._description

    async def total_votes(self, cursor: Connection) -> int:
        return await self.client.database.poll_vote_count(
            cursor,
            poll_rid=self.rid
        )

    async def options(self, cursor: Connection) -> List[PollOption]:
        options = await self.client.database.poll_options(
            cursor,
            poll_rid=self.rid
        )

        return [
            PollOption.from_data(self, option_rid=option_rid) for option_rid in options
        ]

    async def guild_rid(self, cursor: Connection) -> int:
        if self._guild_rid is not None:
            return self._guild_rid

        self._guild_rid = await self.client.database.poll_guild(
            cursor,
            poll_rid=self.rid
        )
        return self._guild_rid

    async def guild_hid(self, cursor: Connection) -> int:
        if self._guild_hid is not None:
            return self._guild_hid

        self._guild_hid = self.client.poll_hashids.encode(await self.guild_rid(cursor))
        return self._guild_hid

    async def channel_id(self, cursor: Connection):
        if self._channel_id is not None:
            return self._channel_id
        self._channel_id = await self.client.database.poll_channel_id(
            cursor,
            poll_rid=self.rid
        )
        return self._channel_id

    async def message_id(self, cursor: Connection):
        if self._message_id is not None:
            return self._message_id

        self._message_id = await self.client.database.poll_message_id(
            cursor,
            poll_rid=self.rid
        )
        return self._message_id

    async def exists(self, cursor: Connection) -> Optional[bool]:
        return await self.client.database.poll_exists(
            cursor,
            poll_rid=self.rid
        )

    async def start(self, cursor: Connection):
        await self.client.database.poll_start(
            cursor,
            poll_rid=self.rid
        )
        channel = self.client.get_partial_messageable(
            await self.channel_id(cursor)
        )
        message = channel.get_partial_message(
            await self.message_id(cursor)
        )
        await message.edit(
            view=await PollView(self).run(cursor)
        )
        await self.update(cursor)

    async def stop(self, cursor: Connection):
        await self.view.press_stop()
        await self.client.database.poll_stop(
            cursor,
            poll_rid=self.rid
        )

        options = await self.options(cursor)
        max_opt = await self.client.database.longest_poll_option_name(
            cursor,
            poll_rid=self.rid
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

        guild_rid = await self.guild_rid(cursor)
        title_translation = await self.client.translator.translate(
            cursor,
            guild_rid=guild_rid,
            key="poll.title",
            name=await self.title(cursor)
        )
        stopped_translation = await self.client.translator.translate(
            cursor,
            guild_rid=guild_rid,
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
                guild_rid=guild_rid,
                key="poll.footer",
                id=self.hid
            )
        )
        channel = self.client.get_partial_messageable(
            await self.channel_id(cursor)
        )
        message = channel.get_partial_message(
            await self.message_id(cursor)
        )
        await message.edit(embed=embed, view=self.view)
        await self.delete(cursor)

    async def delete(self, cursor: Connection):
        await self.client.database.poll_delete(
            cursor,
            poll_rid=self.rid
        )

    async def add_option(self, cursor: Connection, name: str) -> Optional[int]:
        return await self.client.database.create_poll_option(
            cursor,
            poll_rid=self.rid,
            name=name
        )

    async def get_option(self, cursor: Connection, option_rid: int):
        return [i for i in await self.options(cursor) if i.rid == option_rid][0]

    async def update(self, cursor: Connection):
        options = await self.options(cursor)
        max_opt = await self.client.database.longest_poll_option_name(
            cursor,
            poll_rid=self.rid
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

        guild_rid = await self.guild_rid(cursor)
        title_translation = await self.client.translator.translate(
            cursor,
            guild_rid=guild_rid,
            key="poll.title",
            name=await self.title(cursor)
        )
        embed = discord.Embed(
            title=title_translation,
            description=f"{poll_info}\n{color_string}\n{poll_votes}\n{option_string}",
            colour=discord.Colour.green() if await self.started(cursor) else discord.Colour.yellow()
        )
        embed.set_footer(
            text=await self.client.translator.translate(
                cursor,
                guild_rid=guild_rid,
                key="poll.footer",
                id=self.hid
            )
        )
        channel = self.client.get_partial_messageable(
            await self.channel_id(cursor)
        )
        message = channel.get_partial_message(
            await self.message_id(cursor)
        )
        await message.edit(embed=embed)

    async def add_vote(self, cursor: Connection, vote: PollVote):
        # todo: rewrite this as add_vote(cursor, option, user)

        self._last_vote = datetime.now()
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
            poll_rid=self.rid,
            user_id=user
        )

        return voted

    async def option_count(self, cursor: Connection):
        return await self.client.database.poll_option_count(cursor, self.rid)
