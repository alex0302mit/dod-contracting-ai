#!/usr/bin/env python3
"""
Bootstrap Users Script

Creates test users with various roles for development and testing.
Run from the project root directory:
    PYTHONPATH=. python backend/scripts/bootstrap_users.py

All users are created with password: password123
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.base import SessionLocal, engine
from backend.models.user import User, UserRole
from backend.middleware.auth import get_password_hash


# Test users to create
TEST_USERS = [
    {
        "email": "admin@test.com",
        "name": "System Admin",
        "role": UserRole.ADMIN,
    },
    {
        "email": "co1@navy.mil",
        "name": "John Smith (CO)",
        "role": UserRole.CONTRACTING_OFFICER,
    },
    {
        "email": "co2@navy.mil",
        "name": "Jane Doe (CO)",
        "role": UserRole.CONTRACTING_OFFICER,
    },
    {
        "email": "pm1@navy.mil",
        "name": "Mike Johnson (PM)",
        "role": UserRole.PROGRAM_MANAGER,
    },
    {
        "email": "pm2@navy.mil",
        "name": "Sarah Wilson (PM)",
        "role": UserRole.PROGRAM_MANAGER,
    },
    {
        "email": "approver@navy.mil",
        "name": "Bob Approver",
        "role": UserRole.APPROVER,
    },
    {
        "email": "viewer@navy.mil",
        "name": "View Only User",
        "role": UserRole.VIEWER,
    },
]

DEFAULT_PASSWORD = "password123"


def bootstrap_users():
    """Create test users if they don't exist."""
    db = SessionLocal()
    
    try:
        created_count = 0
        skipped_count = 0
        
        print("\n" + "=" * 60)
        print("BOOTSTRAP USERS SCRIPT")
        print("=" * 60)
        print(f"\nDefault password for all users: {DEFAULT_PASSWORD}\n")
        
        for user_data in TEST_USERS:
            # Check if user already exists
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            
            if existing:
                print(f"⏭️  SKIP: {user_data['email']} (already exists as {existing.role.value})")
                skipped_count += 1
                continue
            
            # Create new user
            hashed_password = get_password_hash(DEFAULT_PASSWORD)
            new_user = User(
                email=user_data["email"],
                name=user_data["name"],
                hashed_password=hashed_password,
                role=user_data["role"],
            )
            db.add(new_user)
            db.commit()
            
            print(f"✅ CREATED: {user_data['email']} as {user_data['role'].value}")
            created_count += 1
        
        print("\n" + "-" * 60)
        print(f"Summary: {created_count} created, {skipped_count} skipped")
        print("-" * 60)
        
        # Show all users
        print("\n📋 All Users in Database:")
        print("-" * 60)
        all_users = db.query(User).order_by(User.role, User.name).all()
        for user in all_users:
            status = "🟢" if user.is_active else "🔴"
            print(f"  {status} {user.name:<25} | {user.email:<30} | {user.role.value}")
        
        print("\n" + "=" * 60)
        print("Bootstrap complete!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_users()

