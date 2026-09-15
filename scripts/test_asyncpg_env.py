import asyncio
from urllib.parse import urlsplit, unquote

import asyncpg
from dotenv import dotenv_values


async def main():
    config = dotenv_values(".env")
    database_url = config.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL not found in .env")

    parsed = urlsplit(database_url)

    host = parsed.hostname
    port = parsed.port or 5432
    user = parsed.username
    password = unquote(parsed.password or "")
    database = parsed.path.lstrip("/")

    print("ASYNCpg ENV CONNECTION TEST")
    print("=" * 50)
    print(f"Host     : {host}")
    print(f"Port     : {port}")
    print(f"User     : {user}")
    print(f"Database : {database}")
    print(f"Password : CONFIGURED ({len(password)} chars)")

    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )

        result = await conn.fetchval("SELECT 1")
        version = await conn.fetchval("SELECT version()")

        await conn.close()

        print("asyncpg connection : PASS")
        print("SELECT 1           :", result)
        print("PostgreSQL         :", version)

    except Exception as exc:
        print("asyncpg connection : FAIL")
        print(type(exc).__name__)
        print(str(exc))
        raise


if __name__ == "__main__":
    asyncio.run(main())