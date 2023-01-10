import json
import os
from typing import List, Dict, TYPE_CHECKING

import aiofiles
from asyncpg import Connection

from imp.better.logger import BetterLogger
from imp.data.colors import Colors

if TYPE_CHECKING:
    from imp.better.bot import BetterBot


class AdvancedFormat(dict):
    def __missing__(self, key):
        return "{" + key + "}"


class Translator(BetterLogger):

    DEFAULT_LOCALE = "de-de"

    # noinspection PyTypeChecker
    def __init__(self, client: "BetterBot"):
        self.client = client
        self.available_locales: List[str] = None
        self.data: Dict[str, Dict[str, str]] = None
        self.default_locale: Dict[str, str] = None

    @classmethod
    async def load(cls, client: "BetterBot", locales_path: str):
        instance = cls(client)

        async with aiofiles.open(os.path.join(locales_path, "locales.json"), "rb") as f:
            _available_locales = (await f.read()).decode()
            available_locales: List[str] = json.loads(_available_locales)
            instance.log("load", f"{len(available_locales)} in locales.json")

        async with aiofiles.open(os.path.join(locales_path, "main.json"), "rb") as f:
            _main = (await f.read()).decode()
            main: List[str] = json.loads(_main)
            instance.log("load", f"{len(main)} translations in main.json")

        data: Dict[str, Dict[str, str]] = {}
        for locale in available_locales:
            async with aiofiles.open(os.path.join(locales_path, f"{locale}.json"), "rb") as f:
                _locale_data = (await f.read()).decode()
                locale_data: dict[str, str] = json.loads(_locale_data)

                if any(key not in locale_data for key in main):
                    instance.log("load", f"Missing translations in {locale}", Colors.YELLOW)

                else:
                    data[locale] = locale_data
                    instance.log("load", f"Locale {locale} loaded successfully")

        instance.log("load", f"{len(data)} locales available")
        instance.available_locales = list(data.keys())
        instance.data = data
        instance.default_locale = data.get(instance.DEFAULT_LOCALE)

        return instance

    async def __call__(self, cursor: Connection, /, guild: str, key: str, **format_args):
        return await self.translate(cursor, guild, key, **format_args)

    async def translate(
            self,
            cursor: Connection,
            /,
            guild_hid: str,
            key: str,
            **format_args
    ):
        guild_language = await self.client.database.get_guild_language(
            cursor,
            guild_hid=guild_hid
        )
        print(guild_hid, guild_language)
        if guild_hid is None or guild_language is None:
            raise ValueError("None")

        locale = self.data.get(guild_language, self.default_locale)
        _translation = locale.get(key, f"<TRANSLATION:{key}>")

        return _translation.format_map(AdvancedFormat(**format_args))
