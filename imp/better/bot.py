from asyncpg import Pool, create_pool
from discord.ext.commands import Bot
from hashids import Hashids

from imp.better.logger import BetterLogger
from imp.classes import PollManager
from imp.database import database
from imp.translation.translator import Translator


class BetterBot(Bot, BetterLogger):
    pool: Pool
    config: dict
    database: database.Database
    translator: Translator
    manager: PollManager
    guild_hashids: Hashids
    poll_hashids: Hashids
    option_hashids: Hashids
    vote_hashids: Hashids

    async def init_pool(self):
        self.pool = await create_pool(
            **self.config["database"]
        )

    async def init_hash_ids(self):
        self.guild_hashids = Hashids(**self.config["guild_hash_ids"])
        self.poll_hashids = Hashids(**self.config["poll_hash_ids"])
        self.option_hashids = Hashids(**self.config["option_hash_ids"])
        self.vote_hashids = Hashids(**self.config["vote_hash_ids"])

    async def init_database(self):
        self.database = database.Database(
            self.guild_hashids,
            self.poll_hashids,
            self.option_hashids,
            self.vote_hashids
        )

    async def init_translator(self):
        self.translator = await Translator.load(self, "imp/translation/data")

    async def init_manager(self):
        self.manager = PollManager(self)
