import asyncio
from asyncpg import connect
from imp.data.config import CONNECTION_ARGS

from typing import List, Tuple

async def main():
    cursor = await connect(**CONNECTION_ARGS)
    done = False

    while not done:
        key = input("Enter a translation key >>> ")

        if key == "":
            done = True

        languages: List[Tuple[str, str, str]] = await cursor.fetch("SELECT id, name, code FROM languages;")

        key_exists, = await cursor.fetchrow("SELECT EXISTS(SELECT 1 FROM keys WHERE code = $1)", key)

        if key_exists:
            print("KEY EXISTS")
            key_id, = await cursor.fetchrow("SELECT id FROM keys WHERE code = $1", key)
            print()

        else:
            print("KEY DOES NOT EXIST -- CREATING")
            key_id, = await cursor.fetchrow("INSERT INTO keys(code) VALUES($1) RETURNING id", key)
            print()
            correct_key = key.replace("\"", '\\"')

        for l_id, l_full, l_key in languages:
            print(f"SELECTED LANGUAGE: {l_full.upper()} ({l_key.upper()})")
            translation = input("Enter the translation >>> ")
            translation = translation.replace("\\n", "\n")

            if not translation:
                finished = True

            else:
                await cursor.execute("INSERT INTO translations(language, code, translation) VALUES ($1, $2, $3)", l_id, key_id, translation)

asyncio.run(main())
