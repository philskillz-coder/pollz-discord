from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands, Embed

from imp.better.cog import BetterCog
from imp.transformers import POLL_TRANSFORMER
from imp.views.poll import PollView

if TYPE_CHECKING:
    from imp.better.bot import BetterBot
    from imp.better.interaction import BetterInteraction


class Main(BetterCog):

    @app_commands.command(
        name="create",
        description="Create a new poll"
    )
    @app_commands.describe(
        name="The name of the poll",
        info="Some info for the poll"
    )
    async def create_poll(self, interaction: BetterInteraction, name: str, info: str = None):
        async with self.client.pool.acquire() as cursor:
            guild_hid = await self.client.database.get_guild_hid(
                cursor,
                guild_id=interaction.guild.id
            )

            message = await interaction.channel.send(
                embed=Embed(
                    title=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_hid,
                        key="poll.title",
                        name=name.upper()
                    ),
                    description=f"```\n{info}```",
                    colour=discord.Colour.yellow()
                )
                .set_footer(
                    text=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_hid,
                        key="poll.footer",
                        id="#~"
                    )
                )
            )

            poll_id = await self.client.database.create_poll(
                cursor,
                guild_hid=guild_hid,
                channel_id=message.channel.id,
                message_id=message.id,
                poll_title=name.upper(),
                poll_description=info
            )
            poll = self.client.manager.get_poll(poll_id)
            view = await PollView(poll).run(cursor)
            poll.set_view(view)

            self.client.manager.set_poll(poll)

            await message.edit(
                embed=(message.embeds[0].set_footer(
                    text=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_hid,
                        key="poll.footer",
                        id=poll.poll_hid
                    )
                )),
                view=view
            )

            return await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor=cursor,
                    guild=interaction.guild,
                    key="main.create_poll.response.success",
                    name=name,
                    id=poll.poll_hid
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
        # TODO: check if poll option exists
        async with self.client.pool.acquire() as cursor:
            guild_uuid = await self.client.database.get_guild_hid(
                cursor,
                guild_id=interaction.guild.id
            )

            if await poll.started(cursor):
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="main.add_option.response.poll_started"  # TODO: create translation
                    ),
                    ephemeral=True
                )
            await poll.add_option(cursor, name)

            await poll.update(cursor)
            self.client.manager.set_poll(poll)

            await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor=cursor,
                    guild=guild_uuid,
                    key="main.add_option.response.success"  # TODO: Create translation
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
            guild_uuid = await self.client.database.get_guild_hid(
                cursor,
                guild_id=interaction.guild.id
            )

            if await poll.started(cursor):
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="main.start_poll.response.started"
                    ),
                    ephemeral=True
                )

            await poll.start(cursor)
            self.client.manager.set_poll(poll)

            await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor=cursor,
                    guild=guild_uuid,
                    key="main.start_poll.response.success",
                    id=poll.poll_hid
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
            guild_uuid = await self.client.database.get_guild_hid(
                cursor,
                guild_id=interaction.guild.id
            )
            if not (await poll.started(cursor)):
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="main.stop_poll.response.not_started"
                    ),
                    ephemeral=True
                )

            await poll.stop(cursor)
            self.client.manager.set_poll(poll)

            await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor=cursor,
                    guild=guild_uuid,
                    key="main.stop_poll.response.success",
                    id=poll.poll_hid
                ),
                ephemeral=True
            )

    # @app_commands.command(
    #     name="vote",
    #     description="vote for a poll"
    # )
    # async def vote(
    #         self,
    #         interaction: BetterInteraction,
    #         poll: POLL_TRANSFORMER,
    #         option: OPTION_TRANSFORMER
    # ):
    #     async with self.client.pool.acquire() as cursor:
    #         guild_hid = await interaction.client.database.get_guild_hid(
    #             cursor,
    #             guild_id=interaction.guild.id
    #         )
    #
    #         if not await poll.started(cursor):
    #             return await interaction.response.send_message(
    #                 content=await self.client.translator.translate(
    #                     cursor=cursor,
    #                     guild=guild_hid,
    #                     key="main.vote.response.not_started"
    #                 )
    #             )
    #
    #         if await poll.user_voted(cursor, interaction.user.id):
    #             # if await poll.has_flag(cursor, 1):
    #             #     translation = await self.client.translator.translate(
    #             #         cursor=cursor,
    #             #         guild=guild_uuid,
    #             #         key="main.vote.response.voted.reconsider"
    #             #     )
    #             # else:
    #             #     translation = await self.client.translator.translate(
    #             #         cursor=cursor,
    #             #         guild=guild_uuid,
    #             #         key="main.vote.response.voted.no_reconsider"
    #             #     )
    #             translation = "<TRANSLATION:main.vote.response.voted.no_reconsider>"
    #
    #             return await interaction.response.send_message(
    #                 content=translation,
    #                 ephemeral=True
    #             )
    #
    #         await interaction.response.send_message(
    #             content=await poll.client.translator.translate(
    #                 cursor,
    #                 guild=interaction.guild,
    #                 key="poll.voted",
    #                 option=await option.name(cursor)
    #             ),
    #             ephemeral=True
    #         )
    #
    #         await option.poll.add_vote(
    #             cursor,
    #             PollVote(interaction.user.id, option.poll.poll_hid, option.option_hid)
    #         )
    #         # self.client.manager.set_poll(poll)
    #
    #         await asyncio.sleep(poll.UPDATE_TIME)
    #         if poll.update_ready():
    #             await poll.update(cursor)


async def setup(client: BetterBot):
    await client.add_cog(Main(client), guilds=client.config.GUILD_IDS)
