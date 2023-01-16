from discord import app_commands

from typing import TYPE_CHECKING

from imp.better.check import BetterCheckFailure
if TYPE_CHECKING:
    from imp.better.interaction import BetterInteraction


def poll_started(started: bool):
    async def check(interaction: "BetterInteraction"):
        async with interaction.client.pool.acquire() as cursor:
            poll_rid, *_ = interaction.client.database.save_unpack(
                interaction.client.poll_hashids.decode(interaction.namespace.poll)
            )
            poll = interaction.client.manager.get_poll(poll_rid)

            if await poll.started(cursor) != started:
                if started:
                    raise BetterCheckFailure(
                        interaction.guild.id,
                        "checks.poll_started.not_started"
                    )
                else:
                    raise BetterCheckFailure(
                        interaction.guild.id,
                        "checks.poll_started.already_started"
                    )

        return True
    return app_commands.check(check)


def poll_finished(finished: bool):
    async def check(interaction: "BetterInteraction"):
        async with interaction.client.pool.acquire() as cursor:
            poll_rid, *_ = interaction.client.database.save_unpack(
                interaction.client.poll_hashids.decode(interaction.namespace.poll)
            )
            poll = interaction.client.manager.get_poll(poll_rid)

            if await poll.finished(cursor) != finished:
                if finished:
                    raise BetterCheckFailure(
                        interaction.guild.id,
                        "checks.poll_finished.not_finished"
                    )
                else:
                    raise BetterCheckFailure(
                        interaction.guild.id,
                        "checks.poll_finished.already_finished"
                    )

        return True
    return app_commands.check(check)
