import discord

from imp.better import BetterBot
from imp.views.poll import PollView
from imp.data import config
from typing import List, Tuple
import asyncio
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument(
    "-c", "--configuration",
    type=str,
    required=False,
    metavar="configuration"
)
parser.add_argument(
    "--sync",
    action="store_true"
)

sys_args = parser.parse_args()

discord.utils.setup_logging()


class Bot(BetterBot):
    INIT_COGS = [
        "cogs.main",
        "cogs.listeners"
    ]

    async def load_cogs(self):
        for cog in self.INIT_COGS:
            await self.load_extension(cog)

    async def sync(self):
        # await self.tree.sync()
        # for guild in self.config["guilds"]:
        #     await self.tree.sync(guild=guild)
        pass

    async def prepare_polls(self):
        async with self.pool.acquire() as cursor:
            # noinspection SpellCheckingInspection
            poll_hids: List[Tuple[int, ]] = await cursor.fetch("SELECT id FROM polls")

            for _poll_hid, in poll_hids:
                poll = self.manager.init_poll(self.poll_hashids.encode(_poll_hid))
                self.log("prepare_polls", f"Added poll: {await poll.title(cursor)}@{poll.rid}")
                view = await PollView(poll=poll).run(cursor)
                poll.set_view(view)

                self.add_view(view)
                self.manager.set_poll(poll)

    async def on_ready(self):
        self.log("on_ready", f"Running as {self.user} with {sys_args.configuration} configuration")
        self.log("on_ready", "Online")

        for guild in self.guilds:
            self.log("on_ready", f"Guild: {guild.name}:{guild.id}")

    def prepare_config(self):
        if (_config := getattr(config, sys_args.configuration, None)) is None:
            self.log("setup_hook", "Invalid configuration!")
            raise ValueError("Invalid configuration")
        self.config = _config

    async def setup_hook(self) -> None:
        await self.init_pool()
        await self.init_hash_ids()
        await self.init_database()
        await self.init_translator()
        await self.init_manager()
        await self.init_hash_ids()

        await self.prepare_polls()

        await self.load_cogs()
        await self.sync()


async def main():
    async with Bot("iv", application_id=914581317709070346, intents=discord.Intents.default(), log_handler=None) as bot:
        bot.prepare_config()
        await bot.start(token=bot.config["token"], reconnect=True)

asyncio.run(main())
