"""
Migration Script: Add Approval Round Tracking Fields

This script adds the current_approval_round column to project_documents and
approval_round column to document_approvals for tracking approval cycles.

This enables the system to correctly show document status when a document
goes through multiple approve/reject/re-approve cycles.

Dependencies:
- SQLAlchemy for database operations
- backend/database/base.py for database connection

Usage:
    python -m tools.migrations.migrate_approval_rounds

The script is safe to run multiple times - it checks if columns exist before adding them.
"""
import sys
import os

# Add the project root to the path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text, inspect
from backend.database.base import engine, SessionLocal


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    """
    Check if a column exists in the specified table.
    
    Args:
        inspector: SQLAlchemy inspector instance
        table_name: Name of the table to check
        column_name: Name of the column to check for
        
    Returns:
        bool: True if column exists, False otherwise
    """
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def run_migration():
    """
    Execute the migration to add approval round tracking fields.
    
    Adds:
    - project_documents.current_approval_round: INTEGER with default 1
      Tracks which approval cycle the document is currently on
      
    - document_approvals.approval_round: INTEGER with default 1
      Links each approval request to a specific round on the document
    """
    print("=" * 60)
    print("Approval Round Tracking Migration")
    print("=" * 60)
    
    inspector = inspect(engine)
    
    # Check if required tables exist
    if 'project_documents' not in inspector.get_table_names():
        print("ERROR: project_documents table does not exist!")
        print("Please run init_db() first to create the base tables.")
        return False
    
    if 'document_approvals' not in inspector.get_table_names():
        print("ERROR: document_approvals table does not exist!")
        print("Please run init_db() first to create the base tables.")
        return False
    
    db = SessionLocal()
    changes_made = False
    
    try:
        # Check and add current_approval_round column to project_documents
        if not column_exists(inspector, 'project_documents', 'current_approval_round'):
            print("\n[1/2] Adding 'current_approval_round' column to project_documents...")
            
            # Add the column with default value 1
            db.execute(text("""
                ALTER TABLE project_documents 
                ADD COLUMN current_approval_round INTEGER DEFAULT 1
            """))
            
            # Update any NULL values to 1 (for existing documents)
            db.execute(text("""
                UPDATE project_documents 
                SET current_approval_round = 1 
                WHERE current_approval_round IS NULL
            """))
            
            print("   ✓ current_approval_round column added with default 1")
            changes_made = True
        else:
            print("\n[1/2] current_approval_round column already exists - skipping")
        
        # Check and add approval_round column to document_approvals
        if not column_exists(inspector, 'document_approvals', 'approval_round'):
            print("\n[2/2] Adding 'approval_round' column to document_approvals...")
            
            # Add the column with default value 1
            db.execute(text("""
                ALTER TABLE document_approvals 
                ADD COLUMN approval_round INTEGER DEFAULT 1
            """))
            
            # Update any NULL values to 1 (for existing approvals)
            db.execute(text("""
                UPDATE document_approvals 
                SET approval_round = 1 
                WHERE approval_round IS NULL
            """))
            
            print("   ✓ approval_round column added with default 1")
            changes_made = True
        else:
            print("\n[2/2] approval_round column already exists - skipping")
        
        # Commit the changes
        db.commit()
        
        if changes_made:
            print("\n" + "=" * 60)
            print("Migration completed successfully!")
            print("=" * 60)
            
            # Verify the changes for project_documents
            result = db.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN current_approval_round = 1 THEN 1 END) as round_1_count
                FROM project_documents
            """))
            row = result.fetchone()
            print(f"\nVerification (project_documents):")
            print(f"  - Total documents: {row[0]}")
            print(f"  - Documents on round 1: {row[1]}")
            
            # Verify the changes for document_approvals
            result = db.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN approval_round = 1 THEN 1 END) as round_1_count
                FROM document_approvals
            """))
            row = result.fetchone()
            print(f"\nVerification (document_approvals):")
            print(f"  - Total approvals: {row[0]}")
            print(f"  - Approvals on round 1: {row[1]}")
        else:
            print("\n" + "=" * 60)
            print("No changes needed - all columns already exist.")
            print("=" * 60)
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\nERROR: Migration failed!")
        print(f"Error details: {str(e)}")
        return False
        
    finally:
        db.close()


def verify_migration():
    """
    Verify the migration was successful by checking column existence.
    """
    print("\nVerifying migration...")
    inspector = inspect(engine)
    
    current_round_exists = column_exists(inspector, 'project_documents', 'current_approval_round')
    approval_round_exists = column_exists(inspector, 'document_approvals', 'approval_round')
    
    print(f"  - current_approval_round column exists: {current_round_exists}")
    print(f"  - approval_round column exists: {approval_round_exists}")
    
    return current_round_exists and approval_round_exists


if __name__ == "__main__":
    print("\nStarting Approval Round Tracking Migration...")
    print(f"Database: {engine.url}\n")
    
    success = run_migration()
    
    if success:
        verify_migration()
    
    sys.exit(0 if success else 1)
