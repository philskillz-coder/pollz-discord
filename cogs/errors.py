from discord import app_commands

from imp.better.cog import BetterCog
from imp.better.check import BetterCheckFailure

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from imp.better.bot import BetterBot
    from imp.better.interaction import BetterInteraction


class Errors(BetterCog):

    # -> Option 1 ---
    # attaching the handler when the cog is loaded
    # this is required for option 1
    def cog_load(self):
        tree = self.client.tree
        self.client._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error

    # -> Option 1 ---
    # detaching the handler when the cog is unloaded
    # this is optional for option 1
    def cog_unload(self):
        tree = self.client.tree
        tree.on_error = self.client._old_tree_error

    # -> Option 1 ---
    # the global error handler for all app commands (slash & ctx menus)
    async def on_app_command_error(
            self,
            interaction: "BetterInteraction",
            error: app_commands.AppCommandError
    ):
        if isinstance(error, BetterCheckFailure):
            async with self.client.pool.acquire() as cursor:
                guild_rid = await self.client.database.get_guild_rid(
                    cursor,
                    guild_id=error.guild_id
                )
                translation = await self.client.translator.translate(
                    cursor,
                    guild_rid=guild_rid,
                    key=error.key,
                    **error.format_args
                )
                return await interaction.response.send_message(
                    translation,
                    ephemeral=True
                )

        raise error


async def setup(client: "BetterBot"):
    await client.add_cog(Errors(client))
