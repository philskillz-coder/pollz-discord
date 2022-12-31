from __future__ import annotations

from discord import app_commands, Embed

from imp.better.cog import BetterCog
from imp.classes.vote import PollVote
from imp.views.poll import PollView
from imp.transformers import POLL_TRANSFORMER, OPTION_TRANSFORMER

from typing import TYPE_CHECKING
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
            guild_uuid = await self.client.db_mgr.get_guild_uuid(
                cursor=cursor,
                guild_id=interaction.guild.id
            )

            name_exists = await self.client.db_mgr.poll_name_exists(
                cursor=cursor,
                guild_uuid=guild_uuid,
                poll_name=name
            )
            if name_exists:
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="main.create_poll.response.name_exists",
                        name=name
                    ),
                    ephemeral=True
                )

            message = await interaction.channel.send(
                embed=Embed(
                    title=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="poll.title",
                        name=name.upper()
                    ),
                    description=f"```\n{info}```"
                )
                .set_footer(
                    text=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="poll.footer",
                        id="#~"
                    )
                )
            )

            poll_id = await self.client.db_mgr.create_poll(
                cursor=cursor,
                guild_uuid=guild_uuid,
                channel_id=message.channel.id,
                message_id=message.id,
                poll_name=name.upper(),
                poll_info=info
            )
            poll = self.client.manager.get_poll(poll_id)
            view = await PollView(self.client, poll).run(cursor)
            poll.set_view(view)

            self.client.manager.set_poll(poll)

            await message.edit(
                embed=(message.embeds[0].set_footer(
                    text=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="poll.footer",
                        id=poll.clean_poll_id
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
                    id=poll.clean_poll_id
                ),
                ephemeral=True
            )


    @app_commands.command(
        name="add_option",
        description="Add a option to a poll"
    )
    @app_commands.describe(
        poll="The poll to wich the option should be added",
        name="The option name",
        info="The option description"
    )
    async def add_option(
            self,
            interaction: BetterInteraction,
            poll: POLL_TRANSFORMER,
            name: str,
            info: str = None
    ):
        # TODO: check if poll option exists
        async with self.client.pool.acquire() as cursor:
            guild_uuid = await self.client.db_mgr.get_guild_uuid(
                cursor=cursor,
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
            opt_id = await poll.add_option(name.upper(), info)

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
            guild_uuid = await self.client.db_mgr.get_guild_uuid(
                cursor=cursor,
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
                    id=poll.clean_poll_id
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
            guild_uuid = await self.client.db_mgr.get_guild_uuid(
                cursor=cursor,
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

            await poll.stop()
            self.client.manager.set_poll(poll)

            await interaction.response.send_message(
                content=await self.client.translator.translate(
                    cursor=cursor,
                    guild=guild_uuid,
                    key="main.stop_poll.response.success",
                    id=poll.clean_poll_id
                ),
                ephemeral=True
            )

    @app_commands.command(
        name="vote",
        description="vote for a poll"
    )
    async def vote(
        self,
        interaction: BetterInteraction,
        poll: POLL_TRANSFORMER,
        option: OPTION_TRANSFORMER
    ):
        async with self.client.pool.acquire() as cursor:
            guild_uuid = await interaction.client.db_mgr.get_guild_uuid(
                cursor=cursor,
                guild_id=interaction.guild.id
            )

            if not await poll.started(cursor):
                return await interaction.response.send_message(
                    content=await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="main.vote.response.not_started"
                    )
                )

            if await poll.user_voted(cursor, interaction.user.id):
                if await poll.has_flag(cursor, 1):
                    translation = await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="main.vote.response.voted.reconsider"
                    )
                else:
                    translation = await self.client.translator.translate(
                        cursor=cursor,
                        guild=guild_uuid,
                        key="main.vote.response.voted.no_reconsider"
                    )

                return await interaction.response.send_message(
                    content=translation,
                    ephemeral=True
                )


            vote = PollVote(interaction.user.id, poll.poll_id, option.option_id)
            _id = await poll.add_vote(cursor, vote)
            await poll.update(cursor)
            self.client.manager.set_poll(poll)

            await interaction.response.send_message(
                content=self.client.hash_mgr.encode(_id)
            )



async def setup(client: BetterBot):
    await client.add_cog(Main(client), guilds=client.config.GUILD_IDS)
