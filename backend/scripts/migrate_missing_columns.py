"""
Migration script to add missing database columns:
- document_approvals.delegated_from_id (UUID, FK to users) - Tracks original approver when approval is delegated
- notifications.data (JSON) - Stores additional notification context/metadata

Run with: python -m backend.scripts.migrate_missing_columns
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend directory
backend_dir = Path(__file__).parent.parent
load_dotenv(backend_dir / ".env")

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dod_procurement")


def run_migration():
    """
    Execute the migration to add missing columns to document_approvals and notifications tables.
    This migration is idempotent - it checks if columns exist before adding them.
    """
    print("\n" + "="*60)
    print("Starting Missing Columns Migration...")
    print("="*60)
    # Print database location without exposing credentials
    print(f"Database: {DATABASE_URL.split('@')[-1]}")

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as connection:
            inspector = inspect(engine)
            
            # ============================================
            # 1. Add delegated_from_id to document_approvals
            # Purpose: Track original approver when an approval is delegated to another user
            # ============================================
            approvals_columns = [col['name'] for col in inspector.get_columns('document_approvals')]
            
            if 'delegated_from_id' not in approvals_columns:
                print("\n[1/2] Adding 'delegated_from_id' column to document_approvals...")
                connection.execute(text(
                    "ALTER TABLE document_approvals ADD COLUMN delegated_from_id UUID REFERENCES users(id)"
                ))
                connection.commit()
                print("   ✓ delegated_from_id column added (nullable FK to users)")
            else:
                print("\n[1/2] 'delegated_from_id' column already exists. Skipping.")
            
            # ============================================
            # 2. Add data column to notifications
            # Purpose: Store additional JSON context for notifications (e.g., transition_request_id, phase info)
            # ============================================
            notifications_columns = [col['name'] for col in inspector.get_columns('notifications')]
            
            if 'data' not in notifications_columns:
                print("\n[2/2] Adding 'data' column to notifications...")
                # Using JSONB for better indexing and query performance in PostgreSQL
                connection.execute(text(
                    "ALTER TABLE notifications ADD COLUMN data JSONB"
                ))
                connection.commit()
                print("   ✓ data column added (JSONB type for JSON storage)")
            else:
                print("\n[2/2] 'data' column already exists. Skipping.")
            
            # ============================================
            # Verification
            # ============================================
            print("\n" + "="*60)
            print("Migration completed successfully!")
            print("="*60)
            
            # Refresh inspector to verify columns were added
            inspector = inspect(engine)
            
            print("\nVerification:")
            approvals_cols = [col['name'] for col in inspector.get_columns('document_approvals')]
            notifications_cols = [col['name'] for col in inspector.get_columns('notifications')]
            
            print(f"  - document_approvals.delegated_from_id exists: {'delegated_from_id' in approvals_cols}")
            print(f"  - notifications.data exists: {'data' in notifications_cols}")
            
    except Exception as e:
        print(f"\nERROR during migration: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
