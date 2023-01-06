from typing import Optional, Iterable, TypeVar, Tuple, List

from asyncpg import Connection

T = TypeVar("T")

_BOOL = TypeVar("_BOOL")
_STR = TypeVar("_STR")
_INT = TypeVar("_INT")
_FLOAT = TypeVar("_FLOAT")

DB_BOOL = Optional[Tuple[_BOOL,]]
DB_STR = Optional[Tuple[_STR,]]
DB_INT = Optional[Tuple[_INT,]]
DB_FLOAT = Optional[Tuple[_FLOAT,]]

RT_BOOL = Optional[_BOOL]
RT_STR = Optional[_STR]
RT_INT = Optional[_INT]
RT_FLOAT = Optional[_FLOAT]

"""
CREATE EXTENSION pg_hashids;

CREATE TABLE guilds (
    id SERIAL PRIMARY KEY NOT NULL UNIQUE,
    guild_id BIGINT NOT NULL UNIQUE
);

CREATE TABLE guild_settings (
    guild BIGINT PRIMARY KEY NOT NULL UNIQUE,
    display_language VARCHAR(2) NOT NULL DEFAULT "en",
     
    CONSTRAINT fk_guild FOREIGN KEY(guild) REFERENCES guilds(id) ON DELETE CASCADE
);

CREATE TABLE polls (
    id SERIAL PRIMARY KEY NOT NULL UNIQUE,
    guild BIGINT NOT NULL,
    started BOOLEAN NOT NULL DEFAULT FALSE,
    
    CONSTRAINT fk_guild FOREIGN KEY(guild) REFERENCES guilds(id) ON DELETE CASCADE
);

CREATE TABLE poll_config (
    poll BIGINT PRIMARY KEY NOT NULL UNIQUE,
    
    title TEXT,
    description TEXT,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL
);

CREATE TABLE poll_options (
    id SERIAL PRIMARY KEY NOT NULL UNIQUE,
    poll BIGINT NOT NULL,
    name TEXT NOT NULL,
    
    CONSTRAINT fk_poll FOREIGN KEY(poll) REFERENCES polls(id) ON DELETE CASCADE
);

CREATE TABLE poll_votes (
    id SERIAL PRIMARY KEY NOT NULL UNIQUE,
    option BIGINT NOT NULL,
    user BIGINT NOT NULL,
    UNIQUE(option, user),
    
    CONSTRAINT fk_option FOREIGN KEY(option) REFERENCES poll_options(id) ON DELETE CASCADE
);

"""

class Database:
    @staticmethod
    def save_unpack(values: Optional[Iterable[T]]) -> Tuple[Optional[T], List[T]]:
        if not values:
            return None, []

        x, *y = values
        return x, y

    @staticmethod
    async def guild_id_exists(
            *,
            cursor: Connection,
            guild_id: int
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow("SELECT EXISTS(SELECT 1 FROM guilds WHERE guild_id = $1);", guild_id)
        exists, *_ = Database.save_unpack(values)

        return exists

    @staticmethod
    async def create_guild(
            *,
            cursor: Connection,
            guild_id: int
    ) -> RT_STR:
        guild_exists = await Database.guild_id_exists(
            cursor=cursor,
            guild_id=guild_id
        )
        if guild_exists:
            return None

        values: DB_STR = await cursor.fetchrow(
            "INSERT INTO guilds(guild_id) VALUES($1) RETURNING id_encode(id);",
            guild_id
        )
        guild_hid, *_ = Database.save_unpack(values)

        await cursor.execute("INSERT INTO settings(guild) VALUES(id_decode($1));", guild_hid)

        return guild_hid

    @staticmethod
    async def get_guild_hid(
            *,
            cursor: Connection,
            guild_id: int
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT id_encode(id) FROM guilds WHERE guild_id = $1;", guild_id)
        guild_hid, *_ = Database.save_unpack(values)

        return guild_hid

    @staticmethod
    async def get_guild_id(
            *,
            cursor: Connection,
            guild_hid: str
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow("SELECT guild FROM guilds WHERE id = id_decode($1);", guild_hid)
        guild_id, *_ = Database.save_unpack(values)

        return guild_id

    @staticmethod
    async def get_guild_language(
            *,
            cursor: Connection,
            guild_hid: str
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT display_language FROM settings WHERE guild = id_decode($1);", guild_hid)
        display_language, *_ = Database.save_unpack(values)

        return display_language

    @staticmethod
    async def poll_exists(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM polls WHERE id = id_decode($1));",
            poll_hid
        )

        exists, *_ = Database.save_unpack(values)
        return exists

    @staticmethod
    async def poll_started(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT started FROM polls WHERE id = $1",
            poll_hid
        )
        started, *_ = Database.save_unpack(values)

        return started

    @staticmethod
    async def poll_user_voted(
            *,
            cursor: Connection,
            poll_hid: str,
            user_id: int
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_votes WHERE poll = id_decode($1) AND user = $2)",
            poll_hid, user_id
        )
        voted, *_ = Database.save_unpack(values)

        return voted

    @staticmethod
    async def get_poll_name(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT name FROM poll_config WHERE poll = id_decode($1)", poll_hid)
        name, *_ = Database.save_unpack(values)

        return name

    @staticmethod
    async def poll_vote_count(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow("SELECT count(id) FROM poll_votes WHERE poll = id_decode($1)", poll_hid)
        count, *_ = Database.save_unpack(values)

        return count

    @staticmethod
    async def poll_info(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT description FROM poll_config WHERE poll = id_decode($1)", poll_hid)
        info, *_ = Database.save_unpack(values)

        return info

    @staticmethod
    async def poll_start(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> None:
        await cursor.execute("UPDATE polls SET started = TRUE WHERE id = id_decode($1)", poll_hid)

    @staticmethod
    async def poll_stop(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> None:
        await cursor.execute("UPDATE polls SET started = FALSE WHERE id = id_decode($1)", poll_hid)

    @staticmethod
    async def create_poll(
            *,
            cursor: Connection,
            guild_hid: str,
            channel_id: int,
            message_id: int,
            poll_title: str,
            poll_description: str
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow(
            "INSERT INTO polls(guild) VALUES(id_decode($1)) RETURNING id_encode(id);",
            guild_hid
        )
        poll_id, *_ = Database.save_unpack(values)

        await cursor.execute(
            "INSERT INTO poll_config(poll, channel_id, message_id, title, description) VALUES(id_decode($1), $4);",
            poll_id, channel_id, message_id, poll_title, poll_description
        )
        return poll_id

    @staticmethod
    async def get_poll_guild(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT guild FROM polls WHERE id = id_decode($1)", poll_hid)
        guild_uuid, *_ = Database.save_unpack(values)

        return guild_uuid

    @staticmethod
    async def get_poll_channel(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow("SELECT channel_id FROM polls WHERE id = id_decode($1)", poll_hid)
        channel_id, *_ = Database.save_unpack(values)

        return channel_id

    @staticmethod
    async def get_poll_message(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow("SELECT message_id FROM polls WHERE id = id_decode($1)", poll_hid)
        message_id, *_ = Database.save_unpack(values)

        return message_id

    @staticmethod
    async def delete_poll(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> None:
        await cursor.execute("DELETE FROM polls WHERE id = id_decode($1)", poll_hid)

    @staticmethod
    async def create_poll_option(
            *,
            cursor: Connection,
            poll_hid: int,
            option_name: str
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow(
            "INSERT INTO poll_options(poll, name) VALUES(id_decode($1), $2) RETURNING id_encode(id)",
            poll_hid, option_name
        )
        poll_option_id, *_ = Database.save_unpack(values)

        return poll_option_id

    @staticmethod
    async def remove_poll_option(
            *,
            cursor: Connection,
            option_hid: str
    ) -> None:
        await cursor.execute("DELETE FROM poll_options WHERE id = id_decode($1);", option_hid)

    @staticmethod
    async def get_poll_option_name(
            *,
            cursor: Connection,
            option_hid: str
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT name FROM poll_options WHERE id = id_decode($1)", option_hid)
        option_name, *_ = Database.save_unpack(values)

        return option_name

    @staticmethod
    async def get_max_poll_option_name(
            *,
            cursor: Connection,
            poll_hid: str
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow(
            "SELECT length(name) FROM poll_options WHERE poll = id_decode($1) ORDER BY length(name) DESC LIMIT 1",
            poll_hid
        )
        l, *_ = Database.save_unpack(values)

        return l

    @staticmethod
    async def get_poll_option_vote_percentage(
            *,
            cursor: Connection,
            poll_hid: str,
            option_hid: str
    ) -> RT_FLOAT:
        values: DB_FLOAT = await cursor.fetchrow(
            """
SELECT (
    CASE (SELECT count(id) FROM poll_votes WHERE poll = id_decode($1))
        WHEN 0 THEN 0
        ELSE round(
            (
                cast(
                    (
                        SELECT count(id)
                        FROM poll_votes
                        WHERE option = id_decode($2)
                    ) AS numeric
                ) / cast(
                    (
                        SELECT count(id)
                        FROM poll_votes AS vote
                        WHERE poll = id_decode($1)
                        JOIN poll_options AS option ON option.id = vote.option
                        JOIN polls AS poll ON poll.id = option.poll
                    ) AS numeric
                )
            )*100,
            2
        )
    END
);""",
            poll_hid, option_hid
        )
        vp, *_ = Database.save_unpack(values)

        return vp

    @staticmethod
    async def poll_option_exists(
            *,
            cursor: Connection,
            guild_hid: str,
            option_hid: str
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_options WHERE poll.guild = id_decode($1) AND poll_options.id = id_decode($2) JOIN polls AS poll on poll_options.poll = poll.id)",
            guild_hid, option_hid
        )
        option_exists, *_ = Database.save_unpack(values)

        return option_exists

    @staticmethod
    async def get_option_poll(
            *,
            cursor: Connection,
            option_hid: str
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow(
            "SELECT poll.id FROM poll_options WHERE poll_options.id = id_decode($1) JOIN polls AS poll on poll_options.poll = poll.id",
            option_hid
        )
        poll_id, *_ = Database.save_unpack(values)

        return poll_id
