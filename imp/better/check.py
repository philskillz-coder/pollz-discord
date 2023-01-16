from discord import app_commands


class BetterCheckFailure(app_commands.CheckFailure):
    def __init__(self, guild_id: int, key: str, **format_args):
        self.guild_id = guild_id
        self.key = key
        self.format_args = format_args
