"""
Migration: Add standalone document support to project_documents table.

Changes:
- Make project_id nullable (was NOT NULL)
- Add owner_id column (FK to users.id)
- Add is_standalone column (boolean, default false)
- Add generation_context column (JSON, nullable)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import text
from backend.database.base import SessionLocal, engine


def run_migration():
    """Run the standalone documents migration."""
    db = SessionLocal()
    try:
        with engine.connect() as conn:
            # Check which columns already exist
            if engine.dialect.name == 'sqlite':
                result = conn.execute(text("PRAGMA table_info(project_documents)"))
                existing_columns = {row[1] for row in result.fetchall()}
            else:
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'project_documents'"
                ))
                existing_columns = {row[0] for row in result.fetchall()}

            print(f"Existing columns: {existing_columns}")

            # SQLite doesn't support ALTER COLUMN for nullability changes,
            # but new rows will work with the updated model definition.
            # For PostgreSQL, we'd alter the column.
            if engine.dialect.name != 'sqlite':
                print("Making project_id nullable...")
                conn.execute(text(
                    "ALTER TABLE project_documents ALTER COLUMN project_id DROP NOT NULL"
                ))

            if 'owner_id' not in existing_columns:
                print("Adding owner_id column...")
                conn.execute(text(
                    "ALTER TABLE project_documents ADD COLUMN owner_id VARCHAR REFERENCES users(id)"
                ))

            if 'is_standalone' not in existing_columns:
                print("Adding is_standalone column...")
                conn.execute(text(
                    "ALTER TABLE project_documents ADD COLUMN is_standalone BOOLEAN DEFAULT FALSE"
                ))

            if 'generation_context' not in existing_columns:
                print("Adding generation_context column...")
                if engine.dialect.name == 'sqlite':
                    conn.execute(text(
                        "ALTER TABLE project_documents ADD COLUMN generation_context TEXT"
                    ))
                else:
                    conn.execute(text(
                        "ALTER TABLE project_documents ADD COLUMN generation_context JSON"
                    ))

            conn.commit()
            print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
