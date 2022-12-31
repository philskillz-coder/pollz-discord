from discord import app_commands

from imp.transformers.poll import Poll_Transformer, Poll
from imp.transformers.option import Option_Transformer, PollOption

POLL_TRANSFORMER = app_commands.Transform[Poll, Poll_Transformer]
OPTION_TRANSFORMER = app_commands.Transform[PollOption, Option_Transformer]
