from discord import app_commands

from imp.transformers.poll import Poll_Transformer, Poll
from imp.transformers.option import Option_Transformer, PollOption
from imp.transformers.language import Language_Transformer

POLL_TRANSFORMER = app_commands.Transform[Poll, Poll_Transformer]
OPTION_TRANSFORMER = app_commands.Transform[PollOption, Option_Transformer]
LANGUAGE_TRANSFORMER = app_commands.Transform[str, Language_Transformer]
