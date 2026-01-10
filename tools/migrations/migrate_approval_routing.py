"""
Migration Script: Add Smart Approval Routing Fields

This script adds the approval_routing and default_approver_id columns
to the project_documents table for the smart approval routing feature.

Dependencies:
- SQLAlchemy for database operations
- backend/database/base.py for database connection

Usage:
    python -m backend.scripts.migrate_approval_routing

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
    Execute the migration to add smart approval routing fields.
    
    Adds:
    - approval_routing: VARCHAR with default 'auto_co' for routing type
    - default_approver_id: UUID foreign key to users table (nullable)
    """
    print("=" * 60)
    print("Smart Approval Routing Migration")
    print("=" * 60)
    
    inspector = inspect(engine)
    
    # Check if project_documents table exists
    if 'project_documents' not in inspector.get_table_names():
        print("ERROR: project_documents table does not exist!")
        print("Please run init_db() first to create the base tables.")
        return False
    
    db = SessionLocal()
    changes_made = False
    
    try:
        # Check and add approval_routing column
        if not column_exists(inspector, 'project_documents', 'approval_routing'):
            print("\n[1/2] Adding 'approval_routing' column...")
            
            # Add the column with default value 'auto_co'
            db.execute(text("""
                ALTER TABLE project_documents 
                ADD COLUMN approval_routing VARCHAR(20) DEFAULT 'auto_co'
            """))
            
            # Update any NULL values to 'auto_co'
            db.execute(text("""
                UPDATE project_documents 
                SET approval_routing = 'auto_co' 
                WHERE approval_routing IS NULL
            """))
            
            print("   ✓ approval_routing column added with default 'auto_co'")
            changes_made = True
        else:
            print("\n[1/2] approval_routing column already exists - skipping")
        
        # Check and add default_approver_id column
        if not column_exists(inspector, 'project_documents', 'default_approver_id'):
            print("\n[2/2] Adding 'default_approver_id' column...")
            
            # Add the column as nullable UUID
            # Note: PostgreSQL uses UUID type, SQLite uses TEXT
            db.execute(text("""
                ALTER TABLE project_documents 
                ADD COLUMN default_approver_id UUID REFERENCES users(id)
            """))
            
            print("   ✓ default_approver_id column added (nullable FK to users)")
            changes_made = True
        else:
            print("\n[2/2] default_approver_id column already exists - skipping")
        
        # Commit the changes
        db.commit()
        
        if changes_made:
            print("\n" + "=" * 60)
            print("Migration completed successfully!")
            print("=" * 60)
            
            # Verify the changes
            result = db.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN approval_routing = 'auto_co' THEN 1 END) as auto_co_count
                FROM project_documents
            """))
            row = result.fetchone()
            print(f"\nVerification:")
            print(f"  - Total documents: {row[0]}")
            print(f"  - Documents with auto_co routing: {row[1]}")
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
    
    approval_routing_exists = column_exists(inspector, 'project_documents', 'approval_routing')
    default_approver_exists = column_exists(inspector, 'project_documents', 'default_approver_id')
    
    print(f"  - approval_routing column exists: {approval_routing_exists}")
    print(f"  - default_approver_id column exists: {default_approver_exists}")
    
    return approval_routing_exists and default_approver_exists


if __name__ == "__main__":
    print("\nStarting Smart Approval Routing Migration...")
    print(f"Database: {engine.url}\n")
    
    success = run_migration()
    
    if success:
        verify_migration()
    
    sys.exit(0 if success else 1)
