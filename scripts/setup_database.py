#!/usr/bin/env python3
"""Database setup and initialization script."""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.database import create_tables, drop_tables, engine
from src.models.config import BotConfig


async def setup_database():
    """Set up the database with initial tables and data."""
    print("🗄️  Setting up database...")
    
    try:
        # Create all tables
        print("📊 Creating database tables...")
        await create_tables()
        print("✅ Database tables created successfully")
        
        # Create default configuration
        print("⚙️  Creating default configuration...")
        await create_default_config()
        print("✅ Default configuration created")
        
        print("🎉 Database setup complete!")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        raise
    finally:
        await engine.dispose()


async def reset_database():
    """Reset the database by dropping and recreating all tables."""
    print("🔄 Resetting database...")
    
    try:
        print("🗑️  Dropping existing tables...")
        await drop_tables()
        print("✅ Tables dropped")
        
        await setup_database()
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        raise


async def create_default_config():
    """Create default bot configuration."""
    from src.utils.database import AsyncSessionLocal
    from sqlalchemy import text
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if config already exists
            existing_config = await session.execute(
                text("SELECT COUNT(*) FROM bot_config")
            )
            count = existing_config.scalar()
            
            if count > 0:
                print("ℹ️  Configuration already exists, skipping...")
                return
                
            # Create default configurations
            default_configs = BotConfig.create_default_configs()
            
            for config in default_configs:
                session.add(config)
            
            await session.commit()
            print(f"📝 Created {len(default_configs)} default configuration entries")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating default configuration: {e}")
            raise


def check_database_url():
    """Check if database URL is configured."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("📖 Please set DATABASE_URL in your .env file")
        print("Example: DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/database")
        return False
    
    print(f"🔗 Using database: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    return True


async def test_connection():
    """Test database connection."""
    print("🔍 Testing database connection...")
    
    try:
        from sqlalchemy import text
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and accessible")
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database setup and management")
    parser.add_argument(
        "action",
        choices=["setup", "reset", "test"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    if not check_database_url():
        sys.exit(1)
    
    if args.action == "setup":
        asyncio.run(setup_database())
    elif args.action == "reset":
        confirmation = input("⚠️  This will delete all data. Are you sure? (yes/no): ")
        if confirmation.lower() == "yes":
            asyncio.run(reset_database())
        else:
            print("❌ Operation cancelled")
    elif args.action == "test":
        asyncio.run(test_connection()) 