from typing import Optional, Iterable, TypeVar, Tuple, List

from asyncpg import Connection

T = TypeVar("T")


_BOOL = TypeVar("_BOOL")
_STR = TypeVar("_STR")
_INT = TypeVar("_INT")
_FLOAT = TypeVar("_FLOAT")

DB_BOOL = Optional[Tuple[_BOOL, ]]
DB_STR = Optional[Tuple[_STR, ]]
DB_INT = Optional[Tuple[_INT, ]]
DB_FLOAT = Optional[Tuple[_FLOAT, ]]


RT_BOOL = Optional[_BOOL]
RT_STR = Optional[_STR]
RT_INT = Optional[_INT]
RT_FLOAT = Optional[_FLOAT]

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
        values: DB_BOOL = await cursor.fetchrow("SELECT EXISTS(SELECT 1 FROM guilds WHERE guild = $1);", guild_id)
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

        values: DB_STR = await cursor.fetchrow("INSERT INTO guilds(guild) VALUES($1) RETURNING id;", guild_id)
        guild_uuid, *_ = Database.save_unpack(values)

        await cursor.execute("INSERT INTO settings(guild, language) VALUES($1, $2);", guild_uuid, "34ac8b6b-40d5-49cd-a045-c417c8d90037")
        return guild_uuid

    @staticmethod
    async def get_guild_uuid(
            *,
            cursor: Connection,
            guild_id: int
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT id FROM guilds WHERE guild = $1;", guild_id)
        guild_uuid, *_ = Database.save_unpack(values)

        return guild_uuid

    @staticmethod
    async def get_guild_id(
            *,
            cursor: Connection,
            guild_uuid: str
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow("SELECT guild FROM guilds WHERE id = $1;", guild_uuid)
        guild_id, *_ = Database.save_unpack(values)

        return guild_id

    @staticmethod
    async def get_guild_language(
            *,
            cursor: Connection,
            guild_uuid: str
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT language FROM settings WHERE guild = $1;", guild_uuid)
        language_id, *_ = Database.save_unpack(values)

        return language_id



    @staticmethod
    async def get_key_id(
            *,
            cursor: Connection,
            key_name: str
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT id FROM keys WHERE code = $1;", key_name)
        key_id, *_ = Database.save_unpack(values)

        return key_id

    @staticmethod
    async def get_translation(
            *,
            cursor: Connection,
            language_id: str,
            key_id: str
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow(
            "SELECT translation FROM translations WHERE language = $1 AND code = $2;",
            language_id, key_id
        )
        translation, *_ = Database.save_unpack(values)

        return translation



    @staticmethod
    async def poll_exists(
            *,
            cursor: Connection,
            poll_id: int
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM polls WHERE id = $1);",
            poll_id
        )

        exists, *_ = Database.save_unpack(values)
        return exists

    @staticmethod
    async def poll_name_exists(
            *,
            cursor: Connection,
            guild_uuid: str,
            poll_name: str
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM polls WHERE guild = $1 AND name = $2);",
            guild_uuid, poll_name
        )
        exists, *_ = Database.save_unpack(values)

        return exists

    @staticmethod
    async def poll_started(
            *,
            cursor: Connection,
            poll_id: int
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT started FROM polls WHERE id = $1",
            poll_id
        )
        started, *_ = Database.save_unpack(values)

        return started

    @staticmethod
    async def poll_user_voted(
            *,
            cursor: Connection,
            poll_id: int,
            user_id: int
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_votes WHERE poll = $1 AND member = $2)",
            poll_id, user_id
        )
        voted, *_ = Database.save_unpack(values)

        return voted

    @staticmethod
    async def poll_has_flag(
            *,
            cursor: Connection,
            poll_id: int,
            flag_id: int
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_flags WHERE poll = $1 AND flag = $2)",
            poll_id, flag_id
        )
        hf, *_ = Database.save_unpack(values)

        return hf

    @staticmethod
    async def poll_name(
            *,
            cursor: Connection,
            poll_id: int
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT name FROM polls WHERE id = $1", poll_id)
        name, *_ = Database.save_unpack(values)

        return name

    @staticmethod
    async def poll_vote_count(
            *,
            cursor: Connection,
            poll_id: int
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow("SELECT count(*) FROM poll_votes WHERE poll = $1", poll_id)
        count, *_ = Database.save_unpack(values)

        return count

    @staticmethod
    async def poll_info(
            *,
            cursor: Connection,
            poll_id: int
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT info FROM poll_config WHERE poll = $1", poll_id)
        info, *_ = Database.save_unpack(values)

        return info

    @staticmethod
    async def poll_start(
            *,
            cursor: Connection,
            poll_id: int
    ) -> None:
        await cursor.execute("UPDATE polls SET started = $1 WHERE id = $2", True, poll_id)

    @staticmethod
    async def poll_stop(
            *,
            cursor: Connection,
            poll_id: int
    ) -> None:
        await cursor.execute("UPDATE polls SET started = $1 WHERE id = $2", False, poll_id)

    @staticmethod
    async def create_poll(
            *,
            cursor: Connection,
            guild_uuid: str,
            channel_id: int,
            message_id: int,
            poll_name: str,
            poll_info: str
    ) -> RT_INT:
        poll_exists = await Database.poll_name_exists(
            cursor=cursor,
            guild_uuid=guild_uuid,
            poll_name=poll_name
        )
        if poll_exists:
            return None

        values: DB_INT = await cursor.fetchrow(
            "INSERT INTO polls(guild, channel, message, name) VALUES($1, $2, $3, $4) RETURNING id;",
            guild_uuid, channel_id, message_id, poll_name
        )
        poll_id, *_ = Database.save_unpack(values)

        await cursor.execute("INSERT INTO poll_config(poll, info) VALUES($1, $2);", poll_id, poll_info)
        return poll_id

    @staticmethod
    async def get_poll_guild_uuid(
            *,
            cursor: Connection,
            poll_id: int
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT guild FROM polls WHERE id = $1", poll_id)
        guild_uuid, *_ = Database.save_unpack(values)

        return guild_uuid

    @staticmethod
    async def get_poll_channel_id(
            *,
            cursor: Connection,
            poll_id: int
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow("SELECT channel FROM polls WHERE id = $1", poll_id)
        channel_id, *_ = Database.save_unpack(values)

        return channel_id

    @staticmethod
    async def get_poll_message_id(
            *,
            cursor: Connection,
            poll_id: int
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow("SELECT message FROM polls WHERE id = $1", poll_id)
        message_id, *_ = Database.save_unpack(values)

        return message_id

    @staticmethod
    async def delete_poll(
            *,
            cursor: Connection,
            poll_id: int
    ) -> None:
        await cursor.execute("DELETE FROM polls WHERE id = $1", poll_id)



    @staticmethod
    async def poll_option_name_exists(
            *,
            cursor: Connection,
            poll_id: int,
            option_name: str
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_options WHERE poll = $1 AND name = $2);",
            poll_id, option_name
        )
        option_name_exists, *_ = Database.save_unpack(values)

        return option_name_exists

    @staticmethod
    async def create_poll_option(
            *,
            cursor: Connection,
            poll_id: int,
            option_name: str,
            option_info: str
    ) -> RT_INT:
        poll_option_exists = await Database.poll_option_name_exists(
            cursor=cursor,
            poll_id=poll_id,
            option_name=option_name
        )
        if poll_option_exists:
            return None

        values: DB_INT = await cursor.fetchrow(
            "INSERT INTO poll_options(poll, name, info) VALUES($1, $2, $3) RETURNING id",
            poll_id, option_name, option_info
        )
        poll_option_id, *_ = Database.save_unpack(values)

        return poll_option_id

    @staticmethod
    async def remove_poll_option(
            *,
            cursor: Connection,
            option_id: int
    ) -> None:
        await cursor.execute("DELETE FROM poll_options WHERE id = $1;", option_id)

    @staticmethod
    async def get_poll_option_name(
            *,
            cursor: Connection,
            option_id: int
    ) -> RT_STR:
        values: DB_STR = await cursor.fetchrow("SELECT name FROM poll_options WHERE id = $1", option_id)
        option_name, *_ = Database.save_unpack(values)

        return option_name

    @staticmethod
    async def get_poll_option_info(
            *,
            cursor: Connection,
            option_id: int
    ):
        values: DB_STR = await cursor.fetchrow("SELECT info FROM poll_options WHERE id = $1", option_id)
        option_info, *_ = Database.save_unpack(values)

        return option_info

    @staticmethod
    async def get_max_poll_option_name(
            *,
            cursor: Connection,
            poll_id: int
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow(
            "SELECT length(name) FROM poll_options WHERE poll = $1 ORDER BY length(name) DESC LIMIT 1",
            poll_id
        )
        l, *_ = Database.save_unpack(values)

        return l

    @staticmethod
    async def get_poll_option_vote_percentage(
            *,
            cursor: Connection,
            poll_id: int,
            option_id: int
    ) -> RT_FLOAT:
        values: DB_FLOAT = await cursor.fetchrow(
            """
SELECT (
    CASE (SELECT count(*) FROM poll_votes WHERE poll = $1)
        WHEN 0 THEN 0
        ELSE round(
            (
                cast(
                    (
                        SELECT count(*)
                        FROM poll_votes
                        WHERE option = $2
                    ) AS numeric
                ) / cast(
                    (
                        SELECT count(*)
                        FROM poll_votes
                        WHERE poll = $1
                    ) AS numeric
                )
            )*100,
            2
        )
    END
);""",
            poll_id, option_id
        )
        vp, *_ = Database.save_unpack(values)

        return vp

    @staticmethod
    async def poll_option_exists(
            *,
            cursor: Connection,
            guild_uuid: str,
            option_id: int
    ) -> RT_BOOL:
        values: DB_BOOL = await cursor.fetchrow(
            "SELECT EXISTS(SELECT 1 FROM poll_options JOIN polls p on poll_options.poll = p.id WHERE p.guild = $1 AND poll_options.id = $2)",
            guild_uuid, option_id
        )
        option_exists, *_ = Database.save_unpack(values)

        return option_exists

    @staticmethod
    async def get_poll_option_poll(
            *,
            cursor: Connection,
            option_id: int
    ) -> RT_INT:
        values: DB_INT = await cursor.fetchrow(
            "SELECT p.id FROM poll_options JOIN polls p on poll_options.poll = p.id AND poll_options.id = $1",
            option_id
        )
        poll_id, *_ = Database.save_unpack(values)

        return poll_id
