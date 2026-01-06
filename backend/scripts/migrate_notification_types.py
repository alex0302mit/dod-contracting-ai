"""
Migration script to add missing notification types to PostgreSQL enum.

This fixes the error:
  invalid input value for enum notificationtype: "phase_transition_approved"

Run this script once to add the new enum values:
  python -m backend.scripts.migrate_notification_types
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from backend.database.base import engine


def migrate_notification_types():
    """Add missing notification type enum values to PostgreSQL."""
    
    # New notification types needed for phase transitions
    new_types = [
        'phase_transition_request',
        'phase_transition_approved', 
        'phase_transition_rejected',
    ]
    
    with engine.connect() as conn:
        for notification_type in new_types:
            try:
                # PostgreSQL requires special handling for adding enum values
                # We use a transaction and check if the value already exists
                conn.execute(text(f"""
                    DO $$
                    BEGIN
                        ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS '{notification_type}';
                    EXCEPTION
                        WHEN duplicate_object THEN
                            RAISE NOTICE 'Enum value {notification_type} already exists, skipping';
                    END
                    $$;
                """))
                conn.commit()
                print(f"✓ Added notification type: {notification_type}")
            except Exception as e:
                print(f"⚠ Could not add {notification_type}: {e}")
                # Continue with other types even if one fails
                conn.rollback()
    
    print("\nMigration complete!")
    print("Restart your backend server to pick up the changes.")


if __name__ == "__main__":
    print("=" * 60)
    print("Migrating Notification Types")
    print("=" * 60)
    migrate_notification_types()
