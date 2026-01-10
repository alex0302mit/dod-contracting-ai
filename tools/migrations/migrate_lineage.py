"""
Migration script to create document lineage tables.

This adds:
- document_lineage: Tracks source-to-derived document relationships
- knowledge_documents: Project-scoped knowledge base metadata
- rag_chunk_ids column to project_documents for lineage tracking
- source column to project_documents for origin tracking

Run with: python -m backend.scripts.migrate_lineage
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text, inspect
from backend.database.base import engine


def table_exists(conn, table_name: str) -> bool:
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_lineage():
    """Create document lineage tracking tables."""
    
    with engine.connect() as conn:
        # Step 1: Create influence_type enum (PostgreSQL only, SQLite ignores)
        print("Creating influence_type enum type...")
        try:
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'influencetype') THEN
                        CREATE TYPE influencetype AS ENUM (
                            'context',
                            'template',
                            'regulation',
                            'data_source',
                            'reference'
                        );
                    END IF;
                END
                $$;
            """))
            conn.commit()
            print("✓ Created influencetype enum type")
        except Exception as e:
            # SQLite doesn't support ENUMs, so this is expected to fail
            print(f"⚠ Enum type creation (expected for SQLite): {e}")
            conn.rollback()
        
        # Step 2: Create document_source enum (PostgreSQL only)
        print("Creating document_source enum type...")
        try:
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'documentsource') THEN
                        CREATE TYPE documentsource AS ENUM (
                            'uploaded',
                            'ai_generated',
                            'manual',
                            'imported'
                        );
                    END IF;
                END
                $$;
            """))
            conn.commit()
            print("✓ Created documentsource enum type")
        except Exception as e:
            print(f"⚠ Enum type creation (expected for SQLite): {e}")
            conn.rollback()
        
        # Step 3: Create document_lineage table
        print("Creating document_lineage table...")
        if not table_exists(conn, 'document_lineage'):
            try:
                conn.execute(text("""
                    CREATE TABLE document_lineage (
                        id VARCHAR(36) PRIMARY KEY,
                        source_document_id VARCHAR(36),
                        source_filename VARCHAR(500),
                        derived_document_id VARCHAR(36) NOT NULL,
                        influence_type VARCHAR(50) DEFAULT 'data_source',
                        relevance_score REAL DEFAULT 0.0,
                        chunk_ids_used TEXT,
                        chunks_used_count INTEGER DEFAULT 0,
                        context TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (source_document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
                        FOREIGN KEY (derived_document_id) REFERENCES project_documents(id) ON DELETE CASCADE
                    );
                """))
                conn.commit()
                print("✓ Created document_lineage table")
            except Exception as e:
                print(f"⚠ document_lineage table: {e}")
                conn.rollback()
        else:
            print("⚠ document_lineage table already exists")
        
        # Step 4: Create indexes for document_lineage
        print("Creating indexes for document_lineage...")
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_lineage_source 
                ON document_lineage(source_document_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_lineage_derived 
                ON document_lineage(derived_document_id);
            """))
            conn.commit()
            print("✓ Created indexes for document_lineage")
        except Exception as e:
            print(f"⚠ document_lineage indexes: {e}")
            conn.rollback()
        
        # Step 5: Create knowledge_documents table
        print("Creating knowledge_documents table...")
        if not table_exists(conn, 'knowledge_documents'):
            try:
                conn.execute(text("""
                    CREATE TABLE knowledge_documents (
                        id VARCHAR(36) PRIMARY KEY,
                        project_id VARCHAR(36) NOT NULL,
                        filename VARCHAR(500) NOT NULL,
                        original_filename VARCHAR(500) NOT NULL,
                        file_type VARCHAR(20) NOT NULL,
                        file_size BIGINT DEFAULT 0,
                        file_path VARCHAR(1000),
                        phase VARCHAR(50),
                        purpose VARCHAR(50),
                        rag_indexed BOOLEAN DEFAULT 0,
                        chunk_count INTEGER DEFAULT 0,
                        chunk_ids TEXT,
                        uploaded_by VARCHAR(36),
                        upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES procurement_projects(id) ON DELETE CASCADE,
                        FOREIGN KEY (uploaded_by) REFERENCES users(id)
                    );
                """))
                conn.commit()
                print("✓ Created knowledge_documents table")
            except Exception as e:
                print(f"⚠ knowledge_documents table: {e}")
                conn.rollback()
        else:
            print("⚠ knowledge_documents table already exists")
        
        # Step 6: Create indexes for knowledge_documents
        print("Creating indexes for knowledge_documents...")
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_project 
                ON knowledge_documents(project_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_phase 
                ON knowledge_documents(phase);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_purpose 
                ON knowledge_documents(purpose);
            """))
            conn.commit()
            print("✓ Created indexes for knowledge_documents")
        except Exception as e:
            print(f"⚠ knowledge_documents indexes: {e}")
            conn.rollback()
        
        # Step 7: Add rag_chunk_ids column to project_documents (for lineage tracking)
        print("Adding rag_chunk_ids column to project_documents...")
        try:
            if not column_exists(conn, 'project_documents', 'rag_chunk_ids'):
                conn.execute(text("""
                    ALTER TABLE project_documents 
                    ADD COLUMN rag_chunk_ids TEXT;
                """))
                conn.commit()
                print("✓ Added rag_chunk_ids column to project_documents")
            else:
                print("⚠ rag_chunk_ids column already exists")
        except Exception as e:
            print(f"⚠ rag_chunk_ids column: {e}")
            conn.rollback()
        
        # Step 8: Add source column to project_documents
        print("Adding source column to project_documents...")
        try:
            if not column_exists(conn, 'project_documents', 'source'):
                conn.execute(text("""
                    ALTER TABLE project_documents 
                    ADD COLUMN source VARCHAR(50) DEFAULT 'manual';
                """))
                conn.commit()
                print("✓ Added source column to project_documents")
            else:
                print("⚠ source column already exists")
        except Exception as e:
            print(f"⚠ source column: {e}")
            conn.rollback()
    
    print("\n" + "=" * 60)
    print("Lineage Migration Complete!")
    print("=" * 60)
    print("\nTables created:")
    print("  - document_lineage (tracks source → derived relationships)")
    print("  - knowledge_documents (project-scoped RAG document metadata)")
    print("\nColumns added to project_documents:")
    print("  - rag_chunk_ids (JSON array of RAG chunk IDs)")
    print("  - source (uploaded/ai_generated/manual/imported)")
    print("\nRestart your backend server to pick up the changes.")
    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("Migrating Document Lineage Tables")
    print("=" * 60)
    migrate_lineage()
