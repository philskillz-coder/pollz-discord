from typing import Optional, Iterable, TypeVar, Tuple, List

from asyncpg import Connection
from hashids import Hashids

T = TypeVar("T")

DB_BOOL = Optional[Tuple[bool, ]]
DB_STR = Optional[Tuple[str, ]]
DB_INT = Optional[Tuple[int, ]]
DB_FLOAT = Optional[Tuple[float, ]]
DB_LIST = Optional[List[T]]

DB_GENERIC = Optional[Tuple[T, ]]
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
    "finished" BOOLEAN NOT NULL DEFAULT FALSE CHECK(NOT ("started" AND "finished")),
    
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

    async def guild_id_exists(self, cursor: Connection, /, guild_id: int) -> RT_GENERIC[bool]:
        values: DB_GENERIC[bool] = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM guilds WHERE \"guild_id\" = $1);",
            guild_id
        )
        exists, *_ = Database.save_unpack(values)

        return exists

    async def create_guild(self, cursor: Connection, /, guild_id: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[str] = await cursor.fetchrow(
            "INSERT INTO guilds(\"guild_id\") VALUES($1) RETURNING \"id\";",
            guild_id
        )
        _guild_hid, *_ = Database.save_unpack(values)

        await cursor.execute("INSERT INTO guild_settings(\"guild\") VALUES($1);", _guild_hid)

        return _guild_hid

    async def get_guild_rid(self, cursor: Connection, /, guild_id: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "SELECT \"id\" FROM guilds WHERE \"guild_id\" = $1;",
            guild_id
        )
        guild_rid, *_ = Database.save_unpack(values)
        return guild_rid

    async def guild_language(self, cursor: Connection, /, guild_rid: int) -> RT_GENERIC[str]:
        values: DB_GENERIC[str] = await cursor.fetchrow(
            "SELECT \"display_language\" FROM guild_settings WHERE \"guild\" = $1;",
            guild_rid
        )
        display_language, *_ = Database.save_unpack(values)

        return display_language

    async def set_guild_language(self, cursor: Connection, /, guild_rid: int, language: str) -> None:
        await cursor.execute(
            "UPDATE guild_settings SET \"display_language\" = $1 WHERE guild = $2;",
            language, guild_rid
        )

    async def guild_poll_count(self, cursor: Connection, /, guild_rid: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "SELECT count(\"id\") FROM polls WHERE \"guild\" = $1",
            guild_rid
        )
        count, *_ = Database.save_unpack(values)
        return count

    async def guild_poll_ids(self, cursor: Connection, /, guild_rid: int) -> RT_GENERIC[List[int]]:
        return [
            i for i, in await cursor.fetch("SELECT \"id\" FROM polls WHERE \"guild\" = $1", guild_rid)
        ]

    async def poll_exists(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[bool]:
        values: DB_GENERIC[bool] = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM polls WHERE \"id\" = $1);",
            poll_rid
        )

        exists, *_ = Database.save_unpack(values)
        return exists

    async def poll_started(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[bool]:
        values: DB_GENERIC[bool] = await cursor.fetchrow(
            "SELECT \"started\" FROM polls WHERE \"id\" = $1",
            poll_rid
        )
        started, *_ = Database.save_unpack(values)

        return started

    async def poll_finished(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[bool]:
        values: DB_GENERIC[bool] = await cursor.fetchrow(
            "SELECT \"finished\" FROM polls WHERE \"id\" = $1",
            poll_rid
        )
        finished, *_ = Database.save_unpack(values)

        return finished

    async def poll_user_voted(self, cursor: Connection, /, poll_rid: int, user_id: int) -> RT_GENERIC[bool]:
        values: DB_GENERIC[bool] = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_votes AS \"vote\" JOIN poll_options AS \"option\" ON "
            "\"vote\".\"option\" = \"option\".\"id\" WHERE \"option\".\"poll\" = $1 AND \"user\" = $2)",
            poll_rid, user_id
        )
        voted, *_ = Database.save_unpack(values)

        return voted

    async def poll_title(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[str]:
        values: DB_GENERIC[str] = await cursor.fetchrow(
            "SELECT \"title\" FROM poll_config WHERE \"poll\" = $1",
            poll_rid
        )
        title, *_ = Database.save_unpack(values)

        return title

    async def poll_option_count(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "SELECT COUNT(\"option\".\"id\") FROM poll_options AS \"option\" JOIN polls AS \"poll\" ON "
            "\"option\".\"poll\" = \"poll\".\"id\" WHERE \"poll\".\"id\" = $1",
            poll_rid
        )
        count, *_ = Database.save_unpack(values)

        return count

    async def poll_vote_count(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "SELECT count(\"poll\".\"id\") FROM poll_votes AS \"vote\" JOIN poll_options AS \"option\" ON "
            "\"vote\".\"option\" = \"option\".\"id\" JOIN polls AS \"poll\" ON \"option\".\"poll\" = \"poll\".\"id\" "
            "WHERE \"poll\".\"id\" = $1",
            poll_rid
        )
        count, *_ = Database.save_unpack(values)

        return count

    async def poll_description(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[str]:
        values: DB_GENERIC[str] = await cursor.fetchrow(
            "SELECT \"description\" FROM poll_config WHERE \"poll\" = $1",
            poll_rid
        )
        description, *_ = Database.save_unpack(values)

        return description

    async def poll_start(self, cursor: Connection, /, poll_rid: int) -> None:
        await cursor.execute("UPDATE polls SET \"started\" = TRUE WHERE \"id\" = $1", poll_rid)

    async def poll_stop(self, cursor: Connection, /, poll_rid: int) -> None:
        await cursor.execute("UPDATE polls SET \"started\" = FALSE WHERE \"id\" = $1", poll_rid)

    async def poll_finish(self, cursor: Connection, /, poll_rid: int) -> None:
        await cursor.execute("UPDATE polls SET \"finished\" = TRUE, \"started\" = FALSE WHERE \"id\" = $1", poll_rid)

    async def poll_delete(self, cursor: Connection, /, poll_rid: int) -> None:
        await cursor.execute("DELETE FROM polls WHERE \"id\" = $1", poll_rid)

    async def create_poll(
            self,
            cursor: Connection,
            /,
            guild_rid: int,
            channel_id: int,
            message_id: int,
            poll_title: str,
            poll_description: str
    ) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "INSERT INTO polls(\"guild\") VALUES($1) RETURNING \"id\";",
            guild_rid
        )
        poll_rid, *_ = Database.save_unpack(values)

        await cursor.execute(
            "INSERT INTO poll_config(\"poll\", \"channel\", \"message\", \"title\", \"description\") VALUES($1, $2, "
            "$3, $4, $5);",
            poll_rid, channel_id, message_id, poll_title, poll_description
        )
        return poll_rid

    async def poll_guild(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "SELECT \"guild\".\"id\" FROM polls AS \"poll\" JOIN guilds AS \"guild\" ON \"poll\".\"guild\" = "
            "\"guild\".\"id\" WHERE \"poll\".\"id\" = $1",
            poll_rid
        )
        guild_rid, *_ = Database.save_unpack(values)
        return guild_rid

    async def poll_channel_id(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "SELECT \"channel\" FROM poll_config WHERE \"poll\" = $1",
            poll_rid
        )
        channel_id, *_ = Database.save_unpack(values)
        return channel_id

    async def poll_options(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[List[int]]:
        options: Optional[List[Tuple[int, ]]] = await cursor.fetch(
            "SELECT \"id\" FROM poll_options WHERE \"poll\" = $1",
            poll_rid
        )
        return [
            option for option, in options
        ]

    async def poll_message_id(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "SELECT \"message\" FROM poll_config WHERE \"poll\" = $1",
            poll_rid
        )
        message_id, *_ = Database.save_unpack(values)

        return message_id

    async def create_poll_option(self, cursor: Connection, /, poll_rid: int, name: str) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "INSERT INTO poll_options(\"poll\", \"name\") VALUES($1, $2) RETURNING \"id\"",
            poll_rid, name
        )
        option_rid, *_ = Database.save_unpack(values)
        return option_rid

    async def poll_option_name(self, cursor: Connection, /, option_rid: int) -> RT_GENERIC[str]:
        values: DB_GENERIC[str] = await cursor.fetchrow(
            "SELECT \"name\" FROM poll_options WHERE \"id\" = $1",
            option_rid
        )
        name, *_ = Database.save_unpack(values)

        return name

    async def longest_poll_option_name(self, cursor: Connection, /, poll_rid: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "SELECT length(\"name\") FROM poll_options WHERE \"poll\" = $1 ORDER BY length(\"name\") DESC LIMIT 1",
            poll_rid
        )
        max_length, *_ = Database.save_unpack(values)

        return max_length

    async def option_vote_count(self, cursor: Connection, /, option_rid: int) -> RT_GENERIC[int]:
        values: DB_INT = await cursor.fetchrow(
            "SELECT count(\"id\") FROM poll_votes WHERE \"option\" = $1",
            option_rid
        )
        count, *_ = Database.save_unpack(values)

        return count

    async def poll_option_exists(self, cursor: Connection, /, option_rid: int) -> RT_GENERIC[bool]:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_options AS \"option\" JOIN polls AS \"poll\" on \"option\".\"poll\" = "
            "\"poll\".\"id\" WHERE \"option\".\"id\" = $1)",
            option_rid
        )
        option_exists, *_ = Database.save_unpack(values)

        return option_exists

    async def option_poll(self, cursor: Connection, /, option_rid: int) -> RT_GENERIC[int]:
        values: DB_GENERIC[int] = await cursor.fetchrow(
            "SELECT \"poll\".\"id\" FROM poll_options AS \"option\" JOIN polls AS \"poll\" on \"option\".\"poll\" = "
            "\"poll\".\"id\" WHERE \"option\".\"id\" = $1",
            option_rid
        )
        poll_rid, *_ = Database.save_unpack(values)

        return poll_rid
