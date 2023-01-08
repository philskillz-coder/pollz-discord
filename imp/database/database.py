from typing import Optional, Iterable, TypeVar, Tuple, List

from asyncpg import Connection
from hashids import Hashids

T = TypeVar("T")

_BOOL = TypeVar("_BOOL")
_STR = TypeVar("_STR")
_INT = TypeVar("_INT")
_FLOAT = TypeVar("_FLOAT")

DB_BOOL = Optional[Tuple[_BOOL,]]
DB_STR = Optional[Tuple[_STR,]]
DB_INT = Optional[Tuple[_INT,]]
DB_FLOAT = Optional[Tuple[_FLOAT,]]
DB_LIST = Optional[List[T]]

RT_BOOL = Optional[bool]
RT_STR = Optional[str]
RT_INT = Optional[int]
RT_FLOAT = Optional[float]
RT_LIST = Optional[List[T]]

DB_GENERIC = Optional[Tuple[T]]
RT_GENERIC = Optional[T]

"""
CREATE TABLE guilds (
    "id" SERIAL PRIMARY KEY NOT NULL UNIQUE,
    "guild_id" BIGINT NOT NULL UNIQUE
);

CREATE TABLE guild_settings (
    "guild" BIGINT PRIMARY KEY NOT NULL UNIQUE,
    "display_language" VARCHAR(5) NOT NULL DEFAULT 'de-de',
     
    CONSTRAINT fk_guild FOREIGN KEY("guild") REFERENCES guilds("id") ON DELETE CASCADE
);

CREATE TABLE polls (
    "id" SERIAL PRIMARY KEY NOT NULL UNIQUE,
    "guild" BIGINT NOT NULL,
    "started" BOOLEAN NOT NULL DEFAULT FALSE,
    "option_count" SMALLINT NOT NULL DEFAULT 0,
    
    CONSTRAINT fk_guild FOREIGN KEY("guild") REFERENCES guilds("id") ON DELETE CASCADE
);

CREATE TABLE poll_config (
    "poll" BIGINT PRIMARY KEY NOT NULL UNIQUE,
    
    "title" TEXT,
    "description" TEXT,
    "channel" BIGINT NOT NULL,
    "message" BIGINT NOT NULL,
    
    CONSTRAINT fk_poll FOREIGN KEY("poll") REFERENCES polls("id") ON DELETE CASCADE
);

CREATE TABLE poll_options (
    "id" SERIAL PRIMARY KEY NOT NULL UNIQUE,
    "poll" BIGINT NOT NULL,
    "name" TEXT NOT NULL,
    
    CONSTRAINT fk_poll FOREIGN KEY("poll") REFERENCES polls("id") ON DELETE CASCADE
);

CREATE TABLE poll_votes (
    "id" SERIAL PRIMARY KEY NOT NULL UNIQUE,
    "option" BIGINT NOT NULL,
    "user" BIGINT NOT NULL,
    UNIQUE("option", "user"),
    
    CONSTRAINT fk_option FOREIGN KEY("option") REFERENCES poll_options("id") ON DELETE CASCADE
);

"""


# noinspection PyMethodMayBeStatic
class Database:
    def __init__(self, guild_hashids: Hashids, poll_hashids: Hashids, option_hashids: Hashids, vote_hashids: Hashids):
        self._guild_hashids = guild_hashids
        self._poll_hashids = poll_hashids
        self._option_hashids = option_hashids
        self._vote_hashids = vote_hashids

    @staticmethod
    def save_unpack(values: Optional[Iterable[T]]) -> Tuple[Optional[T], List[T]]:
        if not values:
            return None, []

        x, *y = values
        return x, y

    async def guild_id_exists(self, cursor: Connection, /, guild_id: int) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow("SELECT EXISTS(SELECT 1 FROM guilds WHERE \"guild_id\" = $1);",
                                                guild_id)
        exists, *_ = Database.save_unpack(values)

        return exists

    async def create_guild(self, cursor: Connection, /, guild_id: int) -> RT_STR:
        guild_exists = await Database.guild_id_exists(
            self,
            cursor,
            guild_id=guild_id
        )

        if guild_exists:
            return None

        values: DB_STR = await cursor.fetchrow(
            "INSERT INTO guilds(\"guild_id\") VALUES($1) RETURNING \"id\";",
            guild_id
        )
        _guild_hid, *_ = Database.save_unpack(values)
        guild_hid = self._guild_hashids.encode(_guild_hid)

        await cursor.execute("INSERT INTO guild_settings(\"guild\") VALUES($1);", _guild_hid)

        return guild_hid

    async def get_guild_hid(self, cursor: Connection, /, guild_id: int) -> RT_STR:
        values: DB_INT = await cursor.fetchrow("SELECT \"id\" FROM guilds WHERE \"guild_id\" = $1;", guild_id)
        _guild_hid, *_ = Database.save_unpack(values)
        guild_hid = self._guild_hashids.encode(_guild_hid)

        return guild_hid

    async def get_guild_id(self, cursor: Connection, /, guild_hid: str) -> RT_INT:
        _guild_hid, *_ = Database.save_unpack(self._guild_hashids.decode(guild_hid))
        values: DB_INT = await cursor.fetchrow("SELECT \"guild_id\" FROM guilds WHERE \"id\" = $1;", _guild_hid)
        guild_id, *_ = Database.save_unpack(values)

        return guild_id

    async def get_guild_language(self, cursor: Connection, /, guild_hid: str) -> RT_STR:
        _guild_hid, *_ = Database.save_unpack(self._guild_hashids.decode(guild_hid))
        values: DB_STR = await cursor.fetchrow(
            "SELECT \"display_language\" FROM guild_settings WHERE \"guild\" = $1;",
            _guild_hid
        )
        display_language, *_ = Database.save_unpack(values)

        return display_language

    async def poll_exists(self, cursor: Connection, /, poll_hid: str) -> RT_BOOL:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM polls WHERE \"id\" = $1);",
            _poll_hid
        )

        exists, *_ = Database.save_unpack(values)
        return exists

    async def poll_started(self, cursor: Connection, /, poll_hid: str) -> RT_BOOL:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT \"started\" FROM polls WHERE \"id\" = $1",
            _poll_hid
        )
        started, *_ = Database.save_unpack(values)

        return started

    async def poll_user_voted(self, cursor: Connection, /, poll_hid: str, user_id: int) -> RT_BOOL:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_votes AS \"vote\" JOIN poll_options AS \"option\" ON \"vote\".\"option\" = \"option\".\"id\" WHERE \"option\".\"poll\" = $1 AND \"user\" = $2)",
            _poll_hid, user_id
        )
        voted, *_ = Database.save_unpack(values)

        return voted

    async def get_poll_title(self, cursor: Connection, /, poll_hid: str) -> RT_STR:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_STR = await cursor.fetchrow("SELECT \"title\" FROM poll_config WHERE \"poll\" = $1", _poll_hid)
        name, *_ = Database.save_unpack(values)

        return name

    async def poll_option_count(self, cursor: Connection, /, poll_hid: str) -> RT_INT:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_INT = await cursor.fetchrow(
            "SELECT \"option_count\" FROM polls WHERE \"id\" = $1",
            _poll_hid
        )
        count, *_ = Database.save_unpack(values)

        return count

    async def poll_vote_count(self, cursor: Connection, /, poll_hid: str) -> RT_INT:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_INT = await cursor.fetchrow(
            "SELECT count(\"poll\".\"id\") FROM poll_votes AS \"vote\" JOIN poll_options AS \"option\" ON \"vote\".\"option\" = \"option\".\"id\" JOIN polls AS \"poll\" ON \"option\".\"poll\" = \"poll\".\"id\" WHERE \"poll\".\"id\" = $1",
            _poll_hid)
        count, *_ = Database.save_unpack(values)

        return count

    async def poll_description(self, cursor: Connection, /, poll_hid: str) -> RT_STR:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_STR = await cursor.fetchrow("SELECT \"description\" FROM poll_config WHERE \"poll\" = $1", _poll_hid)
        info, *_ = Database.save_unpack(values)

        return info

    async def poll_start(self, cursor: Connection, /, poll_hid: str) -> None:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        await cursor.execute("UPDATE polls SET \"started\" = TRUE WHERE \"id\" = $1", _poll_hid)

    async def poll_stop(self, cursor: Connection, /, poll_hid: str) -> None:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        await cursor.execute("UPDATE polls SET \"started\" = FALSE WHERE \"id\" = $1", _poll_hid)

    async def create_poll(self, cursor: Connection, /, guild_hid: str, channel_id: int, message_id: int,
                          poll_title: str, poll_description: str) -> RT_STR:
        _guild_hid, *_ = Database.save_unpack(self._guild_hashids.decode(guild_hid))
        values: DB_INT = await cursor.fetchrow(
            "INSERT INTO polls(\"guild\") VALUES($1) RETURNING \"id\";",
            _guild_hid
        )
        _poll_hid, *_ = Database.save_unpack(values)
        poll_hid = self._poll_hashids.encode(_poll_hid)

        await cursor.execute(
            "INSERT INTO poll_config(\"poll\", \"channel\", \"message\", \"title\", \"description\") VALUES($1, $2, $3, $4, $5);",
            _poll_hid, channel_id, message_id, poll_title, poll_description
        )
        return poll_hid

    async def get_poll_guild(self, cursor: Connection, /, poll_hid: str) -> RT_STR:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_STR = await cursor.fetchrow(
            "SELECT \"guild_id\" FROM polls AS \"poll\" JOIN guilds AS \"guild\" ON \"poll\".\"guild\" = \"guild\".\"id\" WHERE \"poll\".\"id\" = $1",
            _poll_hid
        )
        _guild_hid, *_ = Database.save_unpack(values)

        return _guild_hid

    async def get_poll_channel(self, cursor: Connection, /, poll_hid: str) -> RT_INT:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_INT = await cursor.fetchrow("SELECT \"channel\" FROM poll_config WHERE \"poll\" = $1", _poll_hid)
        channel_id, *_ = Database.save_unpack(values)

        return channel_id

    async def get_poll_options(self, cursor: Connection, /, poll_hid: str) -> RT_LIST[str]:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        options: DB_LIST[Tuple[int,]] = await cursor.fetch(
            "SELECT \"id\" FROM poll_options WHERE \"poll\" = $1",
            _poll_hid
        )

        return [self._option_hashids.encode(option) for option, in options]

    async def get_poll_message(self, cursor: Connection, /, poll_hid: str) -> RT_INT:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_INT = await cursor.fetchrow("SELECT \"message\" FROM poll_config WHERE \"poll\" = $1", _poll_hid)
        message_id, *_ = Database.save_unpack(values)

        return message_id

    async def delete_poll(self, cursor: Connection, /, poll_hid: str) -> None:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        await cursor.execute("DELETE FROM polls WHERE \"id\" = $1", _poll_hid)

    async def create_poll_option(self, cursor: Connection, /, poll_hid: str, option_name: str) -> RT_INT:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        await cursor.execute("UPDATE polls SET \"option_count\" = \"option_count\" + 1 WHERE \"id\" = $1", _poll_hid)
        values: DB_INT = await cursor.fetchrow(
            "INSERT INTO poll_options(\"poll\", \"name\") VALUES($1, $2) RETURNING \"id\"",
            _poll_hid, option_name
        )
        _poll_option_hid, *_ = Database.save_unpack(values)
        poll_option_hid = self._option_hashids.encode(_poll_option_hid)

        return poll_option_hid

    async def remove_poll_option(self, cursor: Connection, /, option_hid: str) -> None:
        _option_hid, *_ = Database.save_unpack(self._option_hashids.decode(option_hid))
        await cursor.execute("DELETE FROM poll_options WHERE id = $1;", _option_hid)

    async def get_poll_option_name(self, cursor: Connection, /, option_hid: str) -> RT_STR:
        _option_hid, *_ = Database.save_unpack(self._option_hashids.decode(option_hid))
        values: DB_STR = await cursor.fetchrow("SELECT \"name\" FROM poll_options WHERE \"id\" = $1", _option_hid)
        option_name, *_ = Database.save_unpack(values)

        return option_name

    async def get_max_poll_option_name(self, cursor: Connection, /, poll_hid: str) -> RT_INT:
        _poll_hid, *_ = Database.save_unpack(self._poll_hashids.decode(poll_hid))
        values: DB_INT = await cursor.fetchrow(
            "SELECT length(\"name\") FROM poll_options WHERE \"poll\" = $1 ORDER BY length(\"name\") DESC LIMIT 1",
            _poll_hid
        )
        max_length, *_ = Database.save_unpack(values)

        return max_length

    async def get_option_vote_count(self, cursor: Connection, /, option_hid: str) -> RT_INT:
        _option_hid, *_ = Database.save_unpack(self._option_hashids.decode(option_hid))
        values: DB_INT = await cursor.fetchrow(
            "SELECT count(\"id\") FROM poll_votes WHERE \"option\" = $1",
            _option_hid
        )
        count, *_ = Database.save_unpack(values)

        return count

    async def poll_option_exists(self, cursor: Connection, /, option_hid: str) -> RT_BOOL:
        _option_hid, *_ = Database.save_unpack(self._option_hashids.decode(option_hid))

        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_options AS \"option\" JOIN polls AS \"poll\" on \"option\".\"poll\" = \"poll\".\"id\" WHERE \"option\".\"id\" = $1)",
            _option_hid
        )
        option_exists, *_ = Database.save_unpack(values)

        return option_exists

    async def get_option_poll(self, cursor: Connection, /, option_hid: str) -> RT_STR:
        _option_hid, *_ = Database.save_unpack(self._option_hashids.decode(option_hid))
        values: DB_INT = await cursor.fetchrow(
            "SELECT \"poll\".\"id\" FROM poll_options AS \"option\" JOIN polls AS \"poll\" on \"option\".\"poll\" = \"poll\".\"id\" WHERE \"option\".\"id\" = $1",
            _option_hid
        )
        poll_hid, *_ = Database.save_unpack(values)

        return poll_hid
