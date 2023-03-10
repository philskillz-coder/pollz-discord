from __future__ import annotations

import io
from typing import TYPE_CHECKING

import discord
from discord import app_commands, Embed

from imp.better.cog import BetterCog
from imp.transformers import POLL_TRANSFORMER, LANGUAGE_TRANSFORMER
from imp.views.poll import PollView
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from imp.better.bot import BetterBot
    from imp.better.interaction import BetterInteraction


class Main(BetterCog):

    @app_commands.command(
        name="create",
        description="Create a new poll"
    )
    @app_commands.describe(
        title="The name of the poll",
        description="Some info for the poll"
    )
    async def create_poll(self, interaction: BetterInteraction, title: str, description: str = None):
        async with self.client.pool.acquire() as cursor:
            _guild_hid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )

            message = await interaction.channel.send(
                embed=Embed(
                    title=await self.client.translator.translate(
                        cursor,
                        guild_rid=_guild_hid,
                        key="poll.title",
                        name=title
                    ),
                    description=f"```\n{description}```",
                    colour=discord.Colour.yellow()
                )
                .set_footer(
                    text=await self.client.translator.translate(
                        cursor,
                        guild_rid=_guild_hid,
                        key="poll.footer",
                        id="#~"
                    )
                )
            )

            poll_id = await self.client.database.create_poll(
                cursor,
                guild_rid=_guild_hid,
                channel_id=message.channel.id,
                message_id=message.id,
                poll_title=title.upper(),
                poll_description=description
            )
            poll = self.client.manager.get_poll(poll_id)
            view = await PollView(poll).run(cursor)
            poll.set_view(view)

            self.client.manager.set_poll(poll)

            await message.edit(
                embed=(message.embeds[0].set_footer(
                    text=await self.client.translator.translate(
                        cursor,
                        guild_rid=_guild_hid,
                        key="poll.footer",
                        id=poll.hid
                    )
                )),
                view=view
            )

            return await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor,
                    guild_rid=_guild_hid,
                    key="poll.create.success",
                    title=title,
                    id=poll.hid
                ),
                ephemeral=True
            )

    @app_commands.command(
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
            name: str
    ):
        async with self.client.pool.acquire() as cursor:
            _guild_hid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )

            if await poll.started(cursor):
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor,
                        guild_rid=_guild_hid,
                        key="poll.add_option.already_started",
                        id=poll.hid
                    ),
                    ephemeral=True
                )

            if await poll.option_count(cursor) > poll.POLL_MAX_OPTIONS:
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor,
                        guild_rid=_guild_hid,
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
                    guild_rid=_guild_hid,
                    key="poll.add_option.success",
                    id=poll.hid,
                    option=name
                ),
                ephemeral=True
            )

    @app_commands.command(
        name="start",
        description="Start a poll"
    )
    @app_commands.describe(
        poll="The poll you want to start"
    )
    async def start_poll(
            self,
            interaction: BetterInteraction,
            poll: POLL_TRANSFORMER
    ):
        async with self.client.pool.acquire() as cursor:
            _guild_hid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )

            if await poll.started(cursor):
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor,
                        guild_rid=_guild_hid,
                        key="poll.start.already_started",
                        id=poll.hid
                    ),
                    ephemeral=True
                )

            await poll.start(cursor)
            self.client.manager.set_poll(poll)

            await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor,
                    guild_rid=_guild_hid,
                    key="poll.start.success",
                    id=poll.hid
                ),
                ephemeral=True
            )

    @app_commands.command(
        name="stop",
        description="Stop a poll"
    )
    @app_commands.describe(
        poll="The poll you want to stop"
    )
    async def stop_poll(
            self,
            interaction: BetterInteraction,
            poll: POLL_TRANSFORMER
    ):
        async with self.client.pool.acquire() as cursor:
            _guild_hid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )

            if not (await poll.started(cursor)):
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor,
                        guild_rid=_guild_hid,
                        key="poll.stop.not_started",
                        id=poll.hid
                    ),
                    ephemeral=True
                )

            await poll.stop(cursor)
            self.client.manager.set_poll(poll)

            await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor,
                    guild_rid=_guild_hid,
                    key="poll.stop.success",
                    id=poll.hid
                ),
                ephemeral=True
            )

    @app_commands.command(
        name="stats",
        description="Get the statistics of a poll"
    )
    @app_commands.describe(
        poll="The poll of which you want to get the statistics"
    )
    async def get_stats(
            self,
            interaction: BetterInteraction,
            poll: POLL_TRANSFORMER
    ):
        async with self.client.pool.acquire() as cursor:
            total_votes = await poll.total_votes(cursor)
            _labels = await self.client.database.poll_options(
                cursor,
                poll_rid=poll.rid
            )
            labels = [
                await self.client.database.poll_option_name(
                    cursor,
                    option_rid=_option_hid
                ) for _option_hid in _labels
            ]

            sizes = [
                round(await self.client.database.option_vote_count(
                    cursor,
                    option_rid=option_hid
                ) / total_votes, 2) if total_votes >= 1 else 0.00 for option_hid in _labels
            ]

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)

        file = discord.File(buf, filename="stats.png")
        buf.close()

        await interaction.response.send_message(
            file=file,
            ephemeral=True
        )

        file.close()

    @app_commands.command(
        name="list",
        description="List all your polls"
    )
    async def list(self, interaction: BetterInteraction):
        async with self.client.pool.acquire() as cursor:
            _guild_hid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )

            poll_data = []
            _polls = await self.client.database.guild_poll_ids(
                cursor,
                guild_rid=_guild_hid
            )

            embed = discord.Embed(
                title=await self.client.translator.translate(
                    cursor,
                    guild_rid=_guild_hid,
                    key="poll.list.title"
                )
            )

            for poll_hid in _polls:
                poll = self.client.manager.get_poll(poll_hid)

                poll_data.append(
                    f"**{await poll.title(cursor)}** ({poll.hid})\n"
                    f"[message]({(await poll.message_id(cursor)).jump_url})"
                )

            embed.description = "\n".join(poll_data)

            await interaction.response.send_message(
                embed=embed
            )

    group = app_commands.Group(
        name="settings",
        description="Guild settings"
    )

    @group.command(
        name="language",
        description="Set your guilds language"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def language(
            self,
            interaction: BetterInteraction,
            language: LANGUAGE_TRANSFORMER
    ):
        async with self.client.pool.acquire() as cursor:
            _guild_hid = await self.client.database.get_guild_rid(
                cursor,
                guild_id=interaction.guild.id
            )
            await self.client.database.set_guild_language(
                cursor,
                guild_rid=_guild_hid,
                language=language
            )

            return await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor,
                    guild_rid=_guild_hid,
                    key="settings.set_language.success",
                    language=language
                )
            )


async def setup(client: BetterBot):
    await client.add_cog(Main(client), guilds=client.config["guilds"])
