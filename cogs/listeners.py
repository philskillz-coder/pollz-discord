from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Guild

from imp.better.cog import BetterCog

if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class Listeners(BetterCog):

    @BetterCog.listener()
    async def on_guild_join(self, guild: Guild):
        async with self.client.pool.acquire() as cursor:
            guild_exists = await self.client.database.guild_id_exists(
                cursor,
                guild_id=guild.id
            )

            if not guild_exists:
                self.log("on_guild_join", f"Joined guild: {guild.id} | Not exists")
                await self.client.database.create_guild(
                    cursor,
                    guild_id=guild.id
                )

            else:
                self.log("on_guild_join", f"Joined guild: {guild.id} | Already exists")


async def setup(client: BetterBot):
    await client.add_cog(Listeners(client), guilds=client.config["guilds"])
