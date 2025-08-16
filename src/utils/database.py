"""Database configuration and session management."""

import os
from typing import AsyncGenerator, Optional

import asyncpg
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.models.base import Base

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://googley_bot:googley_bot_password@127.0.0.1:5432/googley_bot_dev")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG_MODE", "false").lower() == "true",
    poolclass=NullPool if "test" in DATABASE_URL else None,  # Use NullPool for tests
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
    pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),
    pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_trigger_if_missing():
    """
    Initializes PostgreSQL NOTIFY triggers on the `notion_tasks` table:
    - 'task_update' triggers on UPDATE (status change, but not to 'completed')
    - 'task_completed' triggers when status becomes 'completed'
    - 'task_assigned' triggers on INSERT or change of assignee_discord_id
    """
    conn = None
    try:
        fixed_dsn = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        conn = await asyncpg.connect(dsn=fixed_dsn)

        logger.info("🔌 Connected to PostgreSQL for trigger setup.")

        # Drop old triggers and functions
        await conn.execute("DROP TRIGGER IF EXISTS task_update_trigger ON notion_tasks;")
        await conn.execute("DROP TRIGGER IF EXISTS task_completed_trigger ON notion_tasks;")
        await conn.execute("DROP TRIGGER IF EXISTS task_assigned_trigger ON notion_tasks;")
        await conn.execute("DROP FUNCTION IF EXISTS notify_task_update();")
        await conn.execute("DROP FUNCTION IF EXISTS notify_task_completed();")
        await conn.execute("DROP FUNCTION IF EXISTS notify_task_assignment();")

        # 1. notify_task_update
        await conn.execute("""
        CREATE OR REPLACE FUNCTION notify_task_update()
        RETURNS trigger AS $$
        DECLARE
            payload TEXT;
        BEGIN
            IF NEW.status != 'completed' AND OLD.status IS DISTINCT FROM NEW.status THEN
                payload := json_build_object(
                    'discord_id', NEW.assignee_discord_id,
                    'message', json_build_object(
                        'title', NEW.title,
                        'description', NEW.description,
                        'status', NEW.status,
                        'notion_id', NEW.notion_id,
                        'due_date', NEW.due_date
                    )
                )::text;
                PERFORM pg_notify('task_update', payload);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # 2. notify_task_completed
        await conn.execute("""
        CREATE OR REPLACE FUNCTION notify_task_completed()
        RETURNS trigger AS $$
        DECLARE
            payload TEXT;
        BEGIN
            IF NEW.status = 'completed' AND OLD.status IS DISTINCT FROM NEW.status THEN
                payload := json_build_object(
                    'discord_id', NEW.assignee_discord_id,
                    'message', json_build_object(
                        'title', NEW.title,
                        'description', NEW.description,
                        'status', NEW.status,
                        'notion_id', NEW.notion_id,
                        'due_date', NEW.due_date
                    )
                )::text;
                PERFORM pg_notify('task_completed', payload);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # --- 3. Task assigned (new assignee on insert/update) ---
        await conn.execute("""
        CREATE OR REPLACE FUNCTION notify_task_assigned()
        RETURNS trigger AS $$
        DECLARE
            payload TEXT;
        BEGIN
            -- Either a new row with an assignee, or a change in assignee
            IF (
                TG_OP = 'INSERT' AND NEW.assignee_discord_id IS NOT NULL
            ) OR (
                TG_OP = 'UPDATE' AND OLD.assignee_discord_id IS DISTINCT FROM NEW.assignee_discord_id AND NEW.assignee_discord_id IS NOT NULL
            ) THEN
                payload := json_build_object(
                    'discord_id', NEW.assignee_discord_id,
                    'message', json_build_object(
                        'title', NEW.title,
                        'description', NEW.description,
                        'status', NEW.status,
                        'notion_id', NEW.notion_id,
                        'due_date', NEW.due_date
                    )
                )::text;

                PERFORM pg_notify('task_assigned', payload);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # --- 4. Create trigger for assignment ---
        await conn.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'task_assigned_trigger'
            ) THEN
                CREATE TRIGGER task_assigned_trigger
                AFTER INSERT OR UPDATE ON notion_tasks
                FOR EACH ROW
                EXECUTE FUNCTION notify_task_assigned();
            END IF;
        END;
        $$;
        """)

        # Create triggers
        await conn.execute("""
        DO $$
        BEGIN
            -- Update trigger
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'task_update_trigger'
            ) THEN
                CREATE TRIGGER task_update_trigger
                AFTER UPDATE ON notion_tasks
                FOR EACH ROW
                EXECUTE FUNCTION notify_task_update();
            END IF;

            -- Completion trigger
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'task_completed_trigger'
            ) THEN
                CREATE TRIGGER task_completed_trigger
                AFTER UPDATE ON notion_tasks
                FOR EACH ROW
                WHEN (NEW.status = 'completed' AND OLD.status IS DISTINCT FROM NEW.status)
                EXECUTE FUNCTION notify_task_completed();
            END IF;

            -- Assignment trigger
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'task_assigned_trigger'
            ) THEN
                CREATE TRIGGER task_assigned_trigger
                AFTER INSERT OR UPDATE ON notion_tasks
                FOR EACH ROW
                EXECUTE FUNCTION notify_task_assignment();
            END IF;
        END;
        $$;
        """)

        logger.success("✅ PostgreSQL triggers initialized.")

    except Exception as e:
        logger.error(f"❌ Failed to initialize triggers: {e}")

    finally:
        if conn:
            await conn.close()
            logger.info("🔒 PostgreSQL connection closed.")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency for FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_database(test_mode: bool = False) -> AsyncSession:
    """Get database session for testing or direct use."""
    if test_mode:
        # Use test database URL if available
        test_url = os.getenv("TEST_DATABASE_URL")
        if test_url:
            test_engine = create_async_engine(test_url, poolclass=NullPool)
            TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession)
            return TestSessionLocal()
    
    return AsyncSessionLocal()


# Add this to the bottom of src/utils/database.py
def get_db_session() -> async_sessionmaker[AsyncSession]:
    """Alias for getting the async session maker (used by commands, not FastAPI)."""
    return AsyncSessionLocal


async def close_db_connections() -> None:
    """Close all database connections."""
    await engine.dispose()