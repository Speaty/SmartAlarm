from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL
from backend.models import Base


def main() -> None:
    engine = create_async_engine(DATABASE_URL, future=True)
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio
    asyncio.run(create_tables())

    data_dir = Path(DATABASE_URL.replace("sqlite://", ""))
    print(f"Database initialized at {data_dir}")


if __name__ == "__main__":
    main()
