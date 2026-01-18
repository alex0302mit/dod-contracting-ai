"""
Simple database seeding script - bypasses bcrypt issues
Creates test users and sample project directly via API
"""
import requests
import json

API_BASE = "http://localhost:8000"

def create_user_direct():
    """Create users directly using API"""
    print("📝 Creating test users via API...")

    users = [
        # Contracting Officers (can create/manage projects)
        {
            "email": "john.contracting@navy.mil",
            "password": "SecureTest123!",
            "name": "John Smith",
            "role": "contracting_officer"
        },
        {
            "email": "jane.co@navy.mil",
            "password": "SecureTest123!",
            "name": "Jane Doe",
            "role": "contracting_officer"
        },
        {
            "email": "robert.co@navy.mil",
            "password": "SecureTest123!",
            "name": "Robert Chen",
            "role": "contracting_officer"
        },
        # Program Managers (can create/manage projects)
        {
            "email": "sarah.pm@navy.mil",
            "password": "SecureTest123!",
            "name": "Sarah Johnson",
            "role": "program_manager"
        },
        {
            "email": "michael.pm@navy.mil",
            "password": "SecureTest123!",
            "name": "Michael Torres",
            "role": "program_manager"
        },
        # Approvers (can approve documents)
        {
            "email": "mike.approver@navy.mil",
            "password": "SecureTest123!",
            "name": "Mike Wilson",
            "role": "approver"
        },
        # Viewers (read-only access)
        {
            "email": "viewer@navy.mil",
            "password": "SecureTest123!",
            "name": "Demo Viewer",
            "role": "viewer"
        }
    ]

    created_users = []
    for user_data in users:
        try:
            response = requests.post(
                f"{API_BASE}/api/auth/register",
                params=user_data
            )
            if response.status_code == 200:
                print(f"   ✅ Created user: {user_data['email']}")
                created_users.append(user_data)
            else:
                print(f"   ⚠️  User {user_data['email']} might already exist")
        except Exception as e:
            print(f"   ❌ Error creating {user_data['email']}: {e}")

    return created_users


def create_sample_project(token):
    """Create a sample project"""
    print("\n🚀 Creating sample project...")

    project_data = {
        "name": "Advanced Navy Training System (ANTS)",
        "description": "Procurement for next-generation pilot training simulation system with AI-enhanced capabilities",
        "project_type": "rfp",
        "estimated_value": 25000000.0
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/projects",
            params=project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            print(f"   ✅ Created project: {project_data['name']}")
            return response.json()
        else:
            print(f"   ❌ Failed to create project: {response.text}")
    except Exception as e:
        print(f"   ❌ Error creating project: {e}")

    return None


def login(email, password):
    """Login and get token"""
    try:
        response = requests.post(
            f"{API_BASE}/api/auth/login",
            params={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
    except Exception as e:
        print(f"   ❌ Login error: {e}")
    return None


def main():
    print("🌱 Starting simple database seeding...")
    print("=" * 60)

    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code != 200:
            print("❌ Backend API is not running!")
            print("   Please start it first: python backend/main.py")
            return
    except:
        print("❌ Cannot connect to backend API!")
        print("   Please start it first: python backend/main.py")
        return

    print("✅ Backend API is running\n")

    # Create users
    users = create_user_direct()

    if not users:
        print("\n❌ No users created. Database might already be seeded.")
        print("   Try logging in with: john.contracting@navy.mil / SecureTest123!")
        return

    # Login with first user (contracting officer)
    print("\n🔐 Logging in as contracting officer...")
    token = login(users[0]["email"], users[0]["password"])

    if not token:
        print("❌ Could not login")
        return

    print("   ✅ Login successful")

    # Create sample project
    project = create_sample_project(token)

    print("\n" + "=" * 60)
    print("✅ Database seeding completed successfully!\n")
    print("📧 Test User Credentials:")
    print("   Contracting Officers:")
    print("     - john.contracting@navy.mil / SecureTest123! (John Smith)")
    print("     - jane.co@navy.mil / SecureTest123! (Jane Doe)")
    print("     - robert.co@navy.mil / SecureTest123! (Robert Chen)")
    print("   Program Managers:")
    print("     - sarah.pm@navy.mil / SecureTest123! (Sarah Johnson)")
    print("     - michael.pm@navy.mil / SecureTest123! (Michael Torres)")
    print("   Approver:")
    print("     - mike.approver@navy.mil / SecureTest123! (Mike Wilson)")
    print("   Viewer:")
    print("     - viewer@navy.mil / SecureTest123! (Demo Viewer)")
    print("\n🚀 You can now:")
    print("   1. Visit http://localhost:8000/docs to test the API")
    print("   2. Start the frontend and login with the credentials above")
    print("   3. Create projects and assign contracting officers")


if __name__ == "__main__":
    main()
