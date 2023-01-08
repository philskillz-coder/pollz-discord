import discord

from imp.better import BetterBot
from imp.views.poll import PollView
from typing import List, Tuple
import asyncio

discord.utils.setup_logging()


class Bot(BetterBot):
    INIT_COGS = [
        "cogs.main",
        "cogs.listeners"
    ]
    MESSAGE_COMMANDS_DISABLED = True

    # async def on_message(self, message: Message, /) -> None:
    #     self.MESSAGE_COMMANDS_DISABLED or await self.process_commands(message)

    async def load_cogs(self):
        for cog in self.INIT_COGS:
            await self.load_extension(cog)

    async def sync(self):
        # await self.tree.sync()
        # for guild in self.config.GUILD_IDS:
        #     await self.tree.sync(guild=guild)
        pass

    async def prepare_polls(self):
        async with self.pool.acquire() as cursor:
            # noinspection SpellCheckingInspection
            poll_hids: List[Tuple[int, ]] = await cursor.fetch("SELECT id FROM polls")

            for _poll_hid, in poll_hids:
                poll = self.manager.init_poll(self.poll_hashids.encode(_poll_hid))
                self.log("prepare_polls", f"Added poll: {await poll.title(cursor)}@{poll.poll_hid}")
                view = await PollView(poll=poll).run(cursor)
                poll.set_view(view)

                self.add_view(view)
                self.manager.set_poll(poll)

    async def on_ready(self):
        self.log("on_ready", f"Running as {self.user}")
        self.log("on_ready", "Online")

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
        await bot.start(token=bot.config.TOKEN, reconnect=True)

asyncio.run(main())
