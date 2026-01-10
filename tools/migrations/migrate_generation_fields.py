"""
Migration script to add AI generation fields to project_documents table.

This adds:
- generation_status: Enum for tracking AI generation progress
- generated_content: Text field for AI-generated markdown content
- generated_at: Timestamp of when content was generated
- generation_task_id: Task ID for async generation tracking
- ai_quality_score: Quality score from AI generation (0-100)

Run with: python -m backend.scripts.migrate_generation_fields
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from backend.database.base import engine


def migrate_generation_fields():
    """Add AI generation fields to project_documents table."""
    
    with engine.connect() as conn:
        # Step 1: Create the GenerationStatus enum type if it doesn't exist
        print("Creating generationstatus enum type...")
        try:
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'generationstatus') THEN
                        CREATE TYPE generationstatus AS ENUM (
                            'not_generated',
                            'generating',
                            'generated',
                            'failed'
                        );
                    END IF;
                END
                $$;
            """))
            conn.commit()
            print("✓ Created generationstatus enum type")
        except Exception as e:
            print(f"⚠ Enum type creation: {e}")
            conn.rollback()
        
        # Step 2: Add generation_status column
        print("Adding generation_status column...")
        try:
            conn.execute(text("""
                ALTER TABLE project_documents 
                ADD COLUMN IF NOT EXISTS generation_status generationstatus DEFAULT 'not_generated';
            """))
            conn.commit()
            print("✓ Added generation_status column")
        except Exception as e:
            print(f"⚠ generation_status column: {e}")
            conn.rollback()
        
        # Step 3: Add generated_content column
        print("Adding generated_content column...")
        try:
            conn.execute(text("""
                ALTER TABLE project_documents 
                ADD COLUMN IF NOT EXISTS generated_content TEXT;
            """))
            conn.commit()
            print("✓ Added generated_content column")
        except Exception as e:
            print(f"⚠ generated_content column: {e}")
            conn.rollback()
        
        # Step 4: Add generated_at column
        print("Adding generated_at column...")
        try:
            conn.execute(text("""
                ALTER TABLE project_documents 
                ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP WITH TIME ZONE;
            """))
            conn.commit()
            print("✓ Added generated_at column")
        except Exception as e:
            print(f"⚠ generated_at column: {e}")
            conn.rollback()
        
        # Step 5: Add generation_task_id column
        print("Adding generation_task_id column...")
        try:
            conn.execute(text("""
                ALTER TABLE project_documents 
                ADD COLUMN IF NOT EXISTS generation_task_id VARCHAR;
            """))
            conn.commit()
            print("✓ Added generation_task_id column")
        except Exception as e:
            print(f"⚠ generation_task_id column: {e}")
            conn.rollback()
        
        # Step 6: Add ai_quality_score column
        print("Adding ai_quality_score column...")
        try:
            conn.execute(text("""
                ALTER TABLE project_documents 
                ADD COLUMN IF NOT EXISTS ai_quality_score INTEGER;
            """))
            conn.commit()
            print("✓ Added ai_quality_score column")
        except Exception as e:
            print(f"⚠ ai_quality_score column: {e}")
            conn.rollback()
    
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("Restart your backend server to pick up the changes.")
    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("Migrating AI Generation Fields to project_documents")
    print("=" * 60)
    migrate_generation_fields()
