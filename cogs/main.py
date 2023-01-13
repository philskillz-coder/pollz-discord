from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands, Embed, Permissions

from imp.better.cog import BetterCog
from imp.classes import Poll
from imp.transformers import POLL_TRANSFORMER, LANGUAGE_TRANSFORMER
from imp.views.poll import PollView

if TYPE_CHECKING:
    from imp.better.bot import BetterBot
    from imp.better.interaction import BetterInteraction


class Main(BetterCog):

    polls = app_commands.Group(
        name="poll",
        description="Everything you need for managing polls",
        guild_only=True,
        default_permissions=Permissions(
            administrator=True
        )
    )

    @polls.command(
        name="create",
        description="Create a new poll"
    )
    @app_commands.describe(
        title="The name of the poll",
        description="Some info for the poll"
    )
    async def create_poll(
            self,
            interaction: BetterInteraction,
            title: app_commands.Range[str, 1, 50],
            description: Optional[app_commands.Range[str, 1, 250]] = None
    ):
        # todo: send_messages check
        # todo: move checks in separate decorator checks
        async with self.client.pool.acquire() as cursor:
            guild_rid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )

            if await self.client.database.guild_poll_count(cursor, guild_rid) > Poll.GUILD_MAX_POLLS:
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor,
                        guild_rid=guild_rid,
                        key="poll.create.maximum_reached",
                        count=Poll.GUILD_MAX_POLLS
                    ),
                    ephemeral=True
                )

            message = await interaction.channel.send(
                embed=discord.Embed(
                    title="#"
                )
            )

            poll_rid = await self.client.database.create_poll(
                cursor,
                guild_rid=guild_rid,
                channel_id=message.channel.id,
                message_id=message.id,
                poll_title=title,
                poll_description=description
            )
            poll = self.client.manager.get_poll(poll_rid)
            view = await PollView(poll).run(cursor)
            poll.set_view(view)

            self.client.manager.set_poll(poll)

            await poll.update(cursor)

            return await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor,
                    guild_rid=guild_rid,
                    key="poll.create.success",
                    title=title,
                    id=poll.hid
                ),
                ephemeral=True
            )

    @polls.command(
        name="delete",
        description="Delete a poll"
    )
    @app_commands.describe(
        poll="The poll to delete"
    )
    async def delete_poll(self, interaction: BetterInteraction, poll: POLL_TRANSFORMER):
        async with self.client.pool.acquire() as cursor:
            guild_rid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )

            await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor,
                    guild_rid=guild_rid,
                    key="poll.delete.success",
                    id=poll.hid
                ),
                ephemeral=True
            )
            await poll.stop(cursor)

    @polls.command(
        name="add_option",
        description="Add a option to a poll"
    )
    @app_commands.describe(
        poll="The poll to which the option should be added",
        name="The option name"
    )
    async def add_option(
            self,
            interaction: BetterInteraction,
            poll: POLL_TRANSFORMER,
            name: app_commands.Range[str, 1, 50]
    ):
        # todo: make check in separate decorator check
        async with self.client.pool.acquire() as cursor:
            guild_rid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )

            if await poll.started(cursor):
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor,
                        guild_rid=guild_rid,
                        key="poll.add_option.already_started",
                        id=poll.hid
                    ),
                    ephemeral=True
                )

            if await poll.option_count(cursor) > poll.POLL_MAX_OPTIONS:
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor,
                        guild_rid=guild_rid,
                        key="poll.add_option.maximum_reached",
                        count=poll.POLL_MAX_OPTIONS
                    ),
                    ephemeral=True
                )

            await poll.add_option(cursor, name)

            await poll.update(cursor)
            self.client.manager.set_poll(poll)

            await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor,
                    guild_rid=guild_rid,
                    key="poll.add_option.success",
                    id=poll.hid,
                    option=name
                ),
                ephemeral=True
            )

    @polls.command(
        name="list",
        description="List all your polls"
    )
    async def list(self, interaction: BetterInteraction):
        # todo: grid arrangement (not vertical)
        async with self.client.pool.acquire() as cursor:
            guild_rid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )

            poll_data = []
            poll_rids = await self.client.database.guild_poll_ids(
                cursor,
                guild_rid=guild_rid
            )

            for poll_rid in poll_rids:
                poll = self.client.manager.get_poll(poll_rid)
                channel = self.client.get_partial_messageable(
                    await poll.channel_id(cursor)
                )
                message = channel.get_partial_message(
                    await poll.message_id(cursor)
                )

                poll_data.append(
                    f"**{await poll.title(cursor)}** ({poll.hid})\n"
                    f"[message]({message.jump_url})"
                )

            embed = discord.Embed(
                title=await self.client.translator.translate(
                    cursor,
                    guild_rid=guild_rid,
                    key="poll.list.title"
                ),
                description="\n\n".join(poll_data)
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

    settings = app_commands.Group(
        name="settings",
        description="Your guild settings",
        guild_only=True,
        default_permissions=Permissions(
            administrator=True
        )
    )

    @settings.command(
        name="language",
        description="Set or get your guilds language"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def language(
            self,
            interaction: BetterInteraction,
            language: Optional[LANGUAGE_TRANSFORMER]
    ):
        async with self.client.pool.acquire() as cursor:
            guild_rid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )
            if language is None:
                guild_language = await self.client.database.guild_language(
                    cursor,
                    guild_rid=guild_rid
                )
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor,
                        guild_rid=guild_rid,
                        key="settings.language.get",
                        language=guild_language
                    ),
                    ephemeral=True
                )

            await self.client.database.set_guild_language(
                cursor,
                guild_rid=guild_rid,
                language=language
            )

            return await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor,
                    guild_rid=guild_rid,
                    key="settings.language.success",
                    language=language
                ),
                ephemeral=True
            )


async def setup(client: BetterBot):
    await client.add_cog(Main(client), guilds=client.config["guilds"])
