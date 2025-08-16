#!/usr/bin/env python3
"""Script to create Alembic migrations."""

import os
import subprocess
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_alembic_command(args: list[str]):
    """Run an Alembic command with proper environment."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if database URL is set
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable not set")
        print("📖 Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    try:
        result = subprocess.run(
            ["alembic"] + args,
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings/Info:", result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Alembic command failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Alembic not found. Please install dependencies first:")
        print("pip install -r requirements.txt")
        print("💡 Make sure your virtual environment is activated")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Alembic migration helper")
    parser.add_argument(
        "action",
        choices=["init", "generate", "upgrade", "downgrade", "history", "current"],
        help="Migration action to perform"
    )
    parser.add_argument(
        "-m", "--message",
        help="Migration message (for generate action)"
    )
    parser.add_argument(
        "revision",
        nargs="?",
        help="Revision to upgrade/downgrade to (default: head)"
    )
    
    args = parser.parse_args()
    
    if args.action == "init":
        print("🚀 Initializing Alembic (already done in project setup)")
        
    elif args.action == "generate":
        if not args.message:
            args.message = input("📝 Enter migration message: ")
        
        print(f"📄 Generating migration: {args.message}")
        run_alembic_command(["revision", "--autogenerate", "-m", args.message])
        
    elif args.action == "upgrade":
        revision = args.revision or "head"
        print(f"⬆️  Upgrading to revision: {revision}")
        run_alembic_command(["upgrade", revision])
        
    elif args.action == "downgrade":
        if not args.revision:
            args.revision = input("⬇️  Enter revision to downgrade to (or -1 for previous): ")
        
        print(f"⬇️  Downgrading to revision: {args.revision}")
        run_alembic_command(["downgrade", args.revision])
        
    elif args.action == "history":
        print("📜 Migration history:")
        run_alembic_command(["history"])
        
    elif args.action == "current":
        print("📍 Current revision:")
        run_alembic_command(["current"]) 