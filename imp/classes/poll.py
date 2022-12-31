from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Tuple, Dict

import discord
from asyncpg import Connection

from imp.classes.option import PollOption
from imp.classes.vote import PollVote
from imp.errors import PollException
from imp.views.poll import PollView

if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class Poll:
    def __init__(self, client: BetterBot, poll_id: int):
        self.client = client
        self.poll_id = poll_id

        self._clean_poll_id: Optional[str] = None

        self._guild: Optional[discord.Guild] = None
        self._channel: Optional[discord.TextChannel] = None
        self._message: Optional[discord.PartialMessage] = None
        self.view: Optional[PollView] = None

    @classmethod
    async def create(cls, client: BetterBot, guild_uuid: str, channel_id: int, message_id: int, poll_name: str, poll_info: str):
        async with client.pool.acquire() as cursor:
            name_exists = await client.db_mgr.poll_name_exists(
                cursor=cursor,
                guild_uuid=guild_uuid,
                poll_name=poll_name
            )
            if name_exists:
                raise PollException(f"A poll named {poll_name!r} does already exist!")

            raw_code = await client.db_mgr.create_poll(
                cursor=cursor,
                guild_uuid=guild_uuid,
                channel_id=channel_id,
                message_id=message_id,
                poll_name=poll_name.upper(),
                poll_info=poll_info
            )

            return cls(client, raw_code)

    def set_view(self, view: PollView):
        self.view = view

    async def started(self, cursor: Connection) -> Optional[bool]:
        return await self.client.db_mgr.poll_started(
            cursor=cursor,
            poll_id=self.poll_id
        )


    @property
    def clean_poll_id(self) -> Optional[str]:
        if self._clean_poll_id is not None:
            return self._clean_poll_id

        self._clean_poll_id = self.client.hash_mgr.encode(self.poll_id)
        return self._clean_poll_id

    async def name(self, cursor: Connection) -> Optional[str]:
        return await self.client.db_mgr.poll_name(
            cursor=cursor,
            poll_id=self.poll_id
        )

    async def info(self, cursor: Connection) -> Optional[str]:
        return await self.client.db_mgr.poll_info(
            cursor=cursor,
            poll_id=self.poll_id
        )

    async def total_votes(self, cursor: Connection) -> Optional[int]:
        return await self.client.db_mgr.poll_vote_count(
            cursor=cursor,
            poll_id=self.poll_id
        )

    async def options(self, cursor: Connection) -> Optional[Dict[int, PollOption]]:
        async with self.client.pool.acquire() as cursor:
            options: List[Tuple[int,]] = await cursor.fetch(
                "SELECT id FROM poll_options WHERE poll = $1",
                self.poll_id
            )

            return {
                code: PollOption(self.client, self, code) for code, in options
            }

    async def guild(self, cursor: Connection):
        if self._guild is not None:
            return self._guild

        async with self.client.pool.acquire() as cursor:
            self._guild = self.client.get_guild(
                await self.client.db_mgr.get_guild_id(
                    cursor=cursor,
                    guild_uuid=await self.client.db_mgr.get_poll_guild_uuid(
                        cursor=cursor,
                        poll_id=self.poll_id
                    )
                )
            )
            return self._guild

    async def channel(self, cursor: Connection):
        if self._channel is not None:
            return self._channel

        async with self.client.pool.acquire() as cursor:
            self._channel = self.client.get_channel(
                await self.client.db_mgr.get_poll_channel_id(
                    cursor=cursor,
                    poll_id=self.poll_id
                )
            )
            return self._channel

    async def message(self, cursor: Connection):
        if self._message is not None:
            return self._message

        async with self.client.pool.acquire() as cursor:
            chn = await self.channel(cursor)
            self._message = chn.get_partial_message(
                await self.client.db_mgr.get_poll_message_id(
                    cursor=cursor,
                    poll_id=self.poll_id
                )
            )
            return self._message

    async def exists(self, cursor: Connection) -> Optional[bool]:
        async with self.client.pool.acquire() as cursor:
            return await self.client.db_mgr.poll_exists(
                cursor=cursor,
                poll_id=self.poll_id
            )

    async def start(self, cursor: Connection):
        await self.client.db_mgr.poll_start(
            cursor=cursor,
            poll_id=self.poll_id
        )
        self.view.
        await (await self.message(cursor)).edit(
            view=await PollView(self.client, self).run(cursor)
        )
        await self.update(cursor)

    async def stop(self):
        pass

    async def delete(self):
        async with self.client.pool.acquire() as cursor:
            await self.client.db_mgr.delete_poll(
                cursor=cursor,
                poll_id=self.poll_id
            )

    async def add_option(self, name: str, info: str = None) -> Optional[int]:
        async with self.client.pool.acquire() as cursor:
            return await self.client.db_mgr.create_poll_option(
                cursor=cursor,
                poll_id=self.poll_id,
                option_name=name,
                option_info=info
            )

    async def remove_option(self, option_id: int):
        async with self.client.pool.acquire() as cursor:
            await self.client.db_mgr.remove_poll_option(
                cursor=cursor,
                option_id=option_id
            )

    async def get_option(self, cursor: Connection, option_id: int):
        return (await self.options(cursor)).get(option_id)

    async def update(self, cursor: Connection):
        options = await self.options(cursor)
        max_opt = await self.client.db_mgr.get_max_poll_option_name(
            cursor=cursor,
            poll_id=self.poll_id
        )

        raw_options = []
        for opt in options.values():
            v = f"**{opt.clean_option_id}** {await opt.name(cursor)}:{(max_opt - len(await opt.name(cursor))) * ' '} {await opt.vote_percentage(cursor)}%"
            raw_options.append(v)

        option_string = "\n".join(
            raw_options
        )
        poll_info = f"```\n{await self.info(cursor)}```"
        poll_votes = f"**Total Votes**: {await self.total_votes(cursor)}"

        description = f""
        message = await self.message(cursor)

        embed = discord.Embed(
            title=await self.client.translator.translate(
                cursor=cursor,
                guild=await self.guild(cursor),
                key="poll.title",
                name=(await self.name(cursor)).upper()
            ),
            description=f"**Poll has {'' if await self.started(cursor) else 'not'} started!**\n{poll_info}{poll_votes}\n{option_string}"
        )
        embed.set_footer(
            text=await self.client.translator.translate(
                cursor=cursor,
                guild=await self.guild(cursor),
                key="poll.footer",
                id=self.clean_poll_id
            )
        )
        await message.edit(embed=embed)

    # noinspection PyMethodMayBeStatic
    async def add_vote(self, cursor: Connection, vote: PollVote):
        _id, = await cursor.fetchrow("INSERT INTO poll_votes(poll, option, member) VALUES($1, $2, $3) RETURNING id",
                                     vote.poll, vote.option, vote.user)
        return _id

    async def user_voted(self, cursor: Connection, user: int):
        voted = await self.client.db_mgr.poll_user_voted(
            cursor=cursor,
            poll_id=self.poll_id,
            user_id=user
        )
        return voted

    async def has_flag(self, cursor: Connection, flag: int):
        hf = await self.client.db_mgr.poll_has_flag(
            cursor=cursor,
            poll_id=self.poll_id,
            flag_id=flag
        )
        return hf
