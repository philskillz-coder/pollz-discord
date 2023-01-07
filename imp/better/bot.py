from datetime import datetime

from discord.ext.commands import Bot
from asyncpg import Pool, create_pool
from hashids import Hashids
from imp.data import config
from imp.data.colors import Colors
from imp.database import database
from imp.translation.translator import Translator
from imp.classes import PollManager


class BetterBot(Bot):
    pool: Pool
    config = config
    database: database.Database
    translator: Translator
    manager: PollManager
    guild_hashids: Hashids
    poll_hashids: Hashids
    option_hashids: Hashids
    vote_hashids: Hashids

    async def init_pool(self):
        self.pool = await create_pool(
            **self.config.POOL
        )

    async def init_hash_ids(self):
        self.guild_hashids = Hashids(**config.GUILD_HASHIDS)
        self.poll_hashids = Hashids(**config.POLL_HASHIDS)
        self.option_hashids = Hashids(**config.OPTION_HASHIDS)
        self.vote_hashids = Hashids(**config.VOTES_HASHIDS)

    async def init_database(self):
        self.database = database.Database(
            self.guild_hashids,
            self.poll_hashids,
            self.option_hashids,
            self.vote_hashids
        )

    async def init_translator(self):
        self.translator = Translator(self)

    async def init_manager(self):
        self.manager = PollManager(self)

    def log(self, agent: str, message: str, color: str = Colors.GREEN):
        print(
            "%s%s[%s%s%s%s%s]%s %s[%s%s%s%s@%s%s%s%s]%s ~ %s%s%s" % (
                Colors.E, Colors.BOLD, Colors.E, Colors.B, datetime.now(), Colors.E, Colors.BOLD, Colors.E,
                Colors.BOLD, Colors.E, Colors.C, agent, Colors.E, Colors.C, self.__class__.__name__, Colors.E,
                Colors.BOLD, Colors.E, color, message, Colors.E
            )
        )
