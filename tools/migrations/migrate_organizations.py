"""
Migration script to create organization, team management, and activity tables.

This adds:
- organizations: Hierarchical org structure with materialized path
- organization_members: User-org association with roles
- cross_org_shares: Cross-org project sharing
- project_activities: User-facing activity feed
- organization_id column to procurement_projects
- granted_by column to project_permissions
- Seeds a "Default Organization" and assigns all existing users/projects

Idempotent — safe to run multiple times.

Run with: python tools/migrations/migrate_organizations.py
"""

import sys
import os
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text, inspect
from backend.database.base import engine

# Well-known UUID for Default Organization (deterministic for idempotency)
DEFAULT_ORG_ID = "00000000-0000-4000-a000-000000000001"
DEFAULT_ORG_SLUG = "default"


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_organizations():
    """Create organization tables and seed default data."""

    with engine.connect() as conn:
        # =====================================================================
        # Step 1: Create organizations table
        # =====================================================================
        if not table_exists("organizations"):
            print("Creating organizations table...")
            conn.execute(text("""
                CREATE TABLE organizations (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    slug VARCHAR NOT NULL UNIQUE,
                    description TEXT,
                    parent_id VARCHAR(36) REFERENCES organizations(id),
                    path VARCHAR NOT NULL DEFAULT '',
                    depth INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX ix_organizations_slug ON organizations(slug)"))
            conn.execute(text("CREATE INDEX ix_organizations_path ON organizations(path)"))
            conn.execute(text("CREATE INDEX ix_organizations_parent_id ON organizations(parent_id)"))
            conn.commit()
            print("  Created organizations table")
        else:
            print("  organizations table already exists, skipping")

        # =====================================================================
        # Step 2: Create organization_members table
        # =====================================================================
        if not table_exists("organization_members"):
            print("Creating organization_members table...")
            conn.execute(text("""
                CREATE TABLE organization_members (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    organization_id VARCHAR(36) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                    org_role VARCHAR NOT NULL DEFAULT 'member',
                    is_primary BOOLEAN DEFAULT FALSE,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_user_org UNIQUE (user_id, organization_id)
                )
            """))
            conn.execute(text("CREATE INDEX ix_orgmembers_user ON organization_members(user_id)"))
            conn.execute(text("CREATE INDEX ix_orgmembers_org ON organization_members(organization_id)"))
            conn.commit()
            print("  Created organization_members table")
        else:
            print("  organization_members table already exists, skipping")

        # =====================================================================
        # Step 3: Create project_activities table
        # =====================================================================
        if not table_exists("project_activities"):
            print("Creating project_activities table...")
            conn.execute(text("""
                CREATE TABLE project_activities (
                    id VARCHAR(36) PRIMARY KEY,
                    project_id VARCHAR(36) NOT NULL REFERENCES procurement_projects(id) ON DELETE CASCADE,
                    user_id VARCHAR(36) REFERENCES users(id),
                    activity_type VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    description TEXT,
                    activity_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX ix_activities_project ON project_activities(project_id)"))
            conn.execute(text("CREATE INDEX ix_activities_created ON project_activities(created_at)"))
            conn.commit()
            print("  Created project_activities table")
        else:
            print("  project_activities table already exists, skipping")

        # =====================================================================
        # Step 4: Create cross_org_shares table
        # =====================================================================
        if not table_exists("cross_org_shares"):
            print("Creating cross_org_shares table...")
            conn.execute(text("""
                CREATE TABLE cross_org_shares (
                    id VARCHAR(36) PRIMARY KEY,
                    project_id VARCHAR(36) NOT NULL REFERENCES procurement_projects(id) ON DELETE CASCADE,
                    source_org_id VARCHAR(36) NOT NULL REFERENCES organizations(id),
                    target_org_id VARCHAR(36) NOT NULL REFERENCES organizations(id),
                    permission_level VARCHAR NOT NULL DEFAULT 'viewer',
                    shared_by VARCHAR(36) NOT NULL REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX ix_shares_project ON cross_org_shares(project_id)"))
            conn.execute(text("CREATE INDEX ix_shares_target ON cross_org_shares(target_org_id)"))
            conn.commit()
            print("  Created cross_org_shares table")
        else:
            print("  cross_org_shares table already exists, skipping")

        # =====================================================================
        # Step 5: Add organization_id column to procurement_projects
        # =====================================================================
        if not column_exists("procurement_projects", "organization_id"):
            print("Adding organization_id to procurement_projects...")
            conn.execute(text(
                "ALTER TABLE procurement_projects ADD COLUMN organization_id UUID REFERENCES organizations(id)"
            ))
            conn.commit()
            print("  Added organization_id column")
        else:
            print("  organization_id column already exists, skipping")

        # =====================================================================
        # Step 6: Add granted_by column to project_permissions
        # =====================================================================
        if table_exists("project_permissions") and not column_exists("project_permissions", "granted_by"):
            print("Adding granted_by to project_permissions...")
            conn.execute(text(
                "ALTER TABLE project_permissions ADD COLUMN granted_by UUID REFERENCES users(id)"
            ))
            conn.commit()
            print("  Added granted_by column")
        else:
            print("  granted_by column already exists or table missing, skipping")

        # =====================================================================
        # Step 7: Seed Default Organization
        # =====================================================================
        print("Seeding Default Organization...")
        existing = conn.execute(
            text("SELECT id FROM organizations WHERE id = :id"),
            {"id": DEFAULT_ORG_ID}
        ).fetchone()

        if not existing:
            conn.execute(text("""
                INSERT INTO organizations (id, name, slug, description, path, depth, is_active)
                VALUES (:id, :name, :slug, :desc, '', 0, TRUE)
            """), {
                "id": DEFAULT_ORG_ID,
                "name": "Default Organization",
                "slug": DEFAULT_ORG_SLUG,
                "desc": "Default organization for all existing users and projects"
            })
            conn.commit()
            print("  Created Default Organization")
        else:
            print("  Default Organization already exists, skipping")

        # =====================================================================
        # Step 8: Assign all existing users to Default Org
        # =====================================================================
        print("Assigning existing users to Default Organization...")
        users = conn.execute(text("SELECT id FROM users")).fetchall()
        assigned_count = 0
        for (user_id,) in users:
            existing_membership = conn.execute(text(
                "SELECT id FROM organization_members WHERE user_id = :uid AND organization_id = :oid"
            ), {"uid": str(user_id), "oid": DEFAULT_ORG_ID}).fetchone()

            if not existing_membership:
                conn.execute(text("""
                    INSERT INTO organization_members (id, user_id, organization_id, org_role, is_primary)
                    VALUES (:id, :uid, :oid, 'MEMBER', TRUE)
                """), {
                    "id": str(uuid.uuid4()),
                    "uid": str(user_id),
                    "oid": DEFAULT_ORG_ID
                })
                assigned_count += 1

        conn.commit()
        print(f"  Assigned {assigned_count} users to Default Organization")

        # =====================================================================
        # Step 9: Assign all existing projects to Default Org
        # =====================================================================
        print("Assigning existing projects to Default Organization...")
        result = conn.execute(text(
            "UPDATE procurement_projects SET organization_id = :oid WHERE organization_id IS NULL"
        ), {"oid": DEFAULT_ORG_ID})
        conn.commit()
        print(f"  Updated {result.rowcount} projects with Default Organization")

        # =====================================================================
        # Step 10: Create OWNER permissions for project creators
        # =====================================================================
        if table_exists("project_permissions"):
            print("Creating OWNER permissions for existing project creators...")
            projects = conn.execute(text(
                "SELECT id, created_by, contracting_officer_id FROM procurement_projects"
            )).fetchall()
            perm_count = 0
            for project_id, created_by, co_id in projects:
                # Check if creator already has permission
                existing = conn.execute(text(
                    "SELECT id FROM project_permissions WHERE user_id = :uid AND project_id = :pid"
                ), {"uid": str(created_by), "pid": str(project_id)}).fetchone()

                if not existing:
                    conn.execute(text("""
                        INSERT INTO project_permissions (id, user_id, project_id, permission_level)
                        VALUES (:id, :uid, :pid, 'OWNER')
                    """), {
                        "id": str(uuid.uuid4()),
                        "uid": str(created_by),
                        "pid": str(project_id)
                    })
                    perm_count += 1

                # Also ensure CO has permission if different from creator
                if co_id and str(co_id) != str(created_by):
                    existing_co = conn.execute(text(
                        "SELECT id FROM project_permissions WHERE user_id = :uid AND project_id = :pid"
                    ), {"uid": str(co_id), "pid": str(project_id)}).fetchone()

                    if not existing_co:
                        conn.execute(text("""
                            INSERT INTO project_permissions (id, user_id, project_id, permission_level)
                            VALUES (:id, :uid, :pid, 'OWNER')
                        """), {
                            "id": str(uuid.uuid4()),
                            "uid": str(co_id),
                            "pid": str(project_id)
                        })
                        perm_count += 1

            conn.commit()
            print(f"  Created {perm_count} OWNER permission entries")

    print("\nOrganization migration completed successfully!")


if __name__ == "__main__":
    migrate_organizations()
