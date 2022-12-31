import discord

from imp.better import BetterBot
from imp.views.poll import PollView
from typing import List, Tuple
import asyncio


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
        for guild in self.config.GUILD_IDS:
            await self.tree.sync(guild=guild)

    async def prepare_polls(self):
        async with self.pool.acquire() as cursor:
            poll_ids: List[Tuple[int, ]] = await cursor.fetch("SELECT id FROM polls")
            for poll_id, in poll_ids:
                poll = self.manager.init_poll(poll_id)
                view = PollView(self, poll)
                poll.set_view(view)

                self.add_view(view)
                self.manager.set_poll(poll)

    async def on_ready(self):
        print(str(self.user), "ONLINE")

    async def setup_hook(self) -> None:
        await self.init_pool()
        await self.init_hash_ids()
        await self.init_db_mgr()
        await self.init_translator()
        await self.init_manager()

        await self.prepare_polls()

        await self.load_cogs()
        await self.sync()


async def main():
    async with Bot("iv", application_id=914581317709070346, intents=discord.Intents.default()) as bot:
        await bot.start(token=bot.config.TOKEN, reconnect=True)

asyncio.run(main())
