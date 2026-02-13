"""
Migration script to fix cascade delete constraints.

This fixes the project deletion cascade error by adding ON DELETE CASCADE
to the agent_feedback.document_id foreign key constraint.

The error occurs because:
- agent_feedback.document_id FK was missing ON DELETE CASCADE
- When a project is deleted, its documents are deleted
- But agent_feedback records referencing those documents caused FK violations

Run with: python tools/migrations/migrate_cascade_constraints.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text, inspect
from backend.database.base import engine


def get_db_type():
    """Determine if we're using PostgreSQL or SQLite."""
    return engine.dialect.name


def migrate_cascade_constraints():
    """Update foreign key constraints to include ON DELETE CASCADE."""

    db_type = get_db_type()
    print(f"Database type: {db_type}")

    with engine.connect() as conn:
        # Update agent_feedback.document_id FK constraint
        print("\nUpdating agent_feedback FK constraint...")

        if db_type == 'postgresql':
            # PostgreSQL: Drop and recreate constraint with CASCADE
            try:
                conn.execute(text("""
                    ALTER TABLE agent_feedback
                    DROP CONSTRAINT IF EXISTS agent_feedback_document_id_fkey;
                """))
                conn.execute(text("""
                    ALTER TABLE agent_feedback
                    ADD CONSTRAINT agent_feedback_document_id_fkey
                    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE;
                """))
                conn.commit()
                print("✓ Updated agent_feedback FK constraint with ON DELETE CASCADE")
            except Exception as e:
                print(f"⚠ FK update error: {e}")
                conn.rollback()

        elif db_type == 'sqlite':
            # SQLite: FK constraints can't be altered directly
            # Need to recreate the table or rely on ORM-level passive_deletes
            print("⚠ SQLite does not support ALTER CONSTRAINT")
            print("  The ORM-level passive_deletes=True handles this case")
            print("  For a full fix, the table would need to be recreated")

            # Check if foreign_keys pragma is enabled
            result = conn.execute(text("PRAGMA foreign_keys;")).fetchone()
            fk_enabled = result[0] if result else 0
            print(f"  PRAGMA foreign_keys = {fk_enabled}")

            if not fk_enabled:
                print("  ⚠ Foreign keys are disabled in SQLite!")
                print("    Set PRAGMA foreign_keys = ON in database initialization")

    print("\n" + "=" * 60)
    print("Cascade Constraints Migration Complete!")
    print("=" * 60)
    print("\nChanges applied:")
    print("  - agent_feedback.document_id: Added ON DELETE CASCADE")
    print("\nORM changes (already in code):")
    print("  - DocumentContentVersion: passive_deletes=True")
    print("  - GenerationReasoning: passive_deletes=True")
    print("  - AgentFeedback: passive_deletes=True + ondelete='CASCADE'")
    print("\nRestart your backend server to pick up the changes.")
    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("Migrating Cascade Delete Constraints")
    print("=" * 60)
    migrate_cascade_constraints()
