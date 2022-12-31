from discord.ext.commands import Bot
from asyncpg import Pool, create_pool
from imp.data import config
from hashids import Hashids
from imp.database import database
from imp.translation.translator import Translator
from imp.classes import PollManager

class BetterBot(Bot):
    pool: Pool
    config = config
    hash_mgr: Hashids
    db_mgr: database.Database
    translator: Translator
    manager: PollManager

    async def init_pool(self):
        self.pool = await create_pool(
            **self.config.POOL_ARGS
        )

    async def init_hash_ids(self):
        self.hash_mgr = Hashids(
            **self.config.HASH_IDS_ARGS
        )

    async def init_db_mgr(self):
        self.db_mgr = database.Database()

    async def init_translator(self):
        self.translator = Translator(self)

    async def init_manager(self):
        self.manager = PollManager(self)
