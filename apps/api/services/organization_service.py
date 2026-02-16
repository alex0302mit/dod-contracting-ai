"""
Organization service for org tree traversal and access control.

Handles:
- Materialized path queries for org hierarchy
- User visibility rules (downward from memberships, no upward/sibling)
- Project access control combining org scope + permissions + direct assignments + cross-org shares
"""
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime

from backend.models.user import User, UserRole
from backend.models.procurement import ProcurementProject, ProjectPermission, PermissionLevel
from backend.models.organization import (
    Organization, OrganizationMember, CrossOrgShare, OrgRole
)


class OrganizationService:

    @staticmethod
    def get_org_subtree_ids(db: Session, org_id: str) -> List[str]:
        """Get all org IDs in the subtree rooted at org_id (including itself).

        Uses materialized path LIKE query for efficient subtree retrieval.
        Works on both SQLite and PostgreSQL.
        """
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return []

        # The org's own path prefix — all descendants will have paths starting with this
        prefix = f"{org.path}/{str(org.id)}" if org.path else str(org.id)

        # Get all orgs whose path starts with this prefix (descendants)
        descendants = db.query(Organization.id).filter(
            Organization.path.like(f"{prefix}%"),
            Organization.is_active == True
        ).all()

        # Include the org itself + all descendants
        result = [str(org.id)]
        for (desc_id,) in descendants:
            if str(desc_id) != str(org.id):
                result.append(str(desc_id))
        return result

    @staticmethod
    def get_user_visible_org_ids(db: Session, user_id: str) -> Set[str]:
        """Get all org IDs visible to a user (union of subtrees for all memberships)."""
        memberships = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == user_id
        ).all()

        visible = set()
        for membership in memberships:
            subtree = OrganizationService.get_org_subtree_ids(db, str(membership.organization_id))
            visible.update(subtree)
        return visible

    @staticmethod
    def get_user_accessible_project_ids(db: Session, user: User) -> Optional[Set[str]]:
        """Get project IDs accessible to a user. Returns None for system admins (no filter).

        Combines:
        1. Projects in user's visible orgs (org membership + downward visibility)
        2. Projects shared to user's orgs (cross-org shares)
        3. Projects with direct ProjectPermission for user
        4. Projects where user is CO, PM, or creator
        """
        # System admins see everything
        if user.role == UserRole.ADMIN:
            return None

        accessible = set()
        user_id = str(user.id)

        # 1. Org-scoped projects
        visible_org_ids = OrganizationService.get_user_visible_org_ids(db, user_id)
        if visible_org_ids:
            org_projects = db.query(ProcurementProject.id).filter(
                ProcurementProject.organization_id.in_(visible_org_ids)
            ).all()
            accessible.update(str(p) for (p,) in org_projects)

        # 2. Cross-org shares to user's direct orgs
        user_org_ids = [
            str(m.organization_id) for m in
            db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).all()
        ]
        if user_org_ids:
            shared_projects = db.query(CrossOrgShare.project_id).filter(
                CrossOrgShare.target_org_id.in_(user_org_ids),
                or_(
                    CrossOrgShare.expires_at == None,
                    CrossOrgShare.expires_at > datetime.utcnow()
                )
            ).all()
            accessible.update(str(p.project_id) for p in shared_projects)

        # 3. Direct ProjectPermission entries
        perm_projects = db.query(ProjectPermission.project_id).filter(
            ProjectPermission.user_id == user_id
        ).all()
        accessible.update(str(p.project_id) for p in perm_projects)

        # 4. Direct assignment (CO, PM, or creator)
        assigned_projects = db.query(ProcurementProject.id).filter(
            or_(
                ProcurementProject.contracting_officer_id == user_id,
                ProcurementProject.program_manager_id == user_id,
                ProcurementProject.created_by == user_id,
            )
        ).all()
        accessible.update(str(p) for (p,) in assigned_projects)

        return accessible

    @staticmethod
    def check_project_access(db: Session, user: User, project_id: str, min_permission: PermissionLevel = None) -> bool:
        """Check if a user can access a specific project.

        Returns True if user has access, False otherwise.
        For permission level checks, OWNER > EDITOR > VIEWER.
        """
        if user.role == UserRole.ADMIN:
            return True

        user_id = str(user.id)

        # Check direct assignment (CO/PM/creator always have access)
        project = db.query(ProcurementProject).filter(ProcurementProject.id == project_id).first()
        if not project:
            return False

        is_co = str(project.contracting_officer_id) == user_id
        is_pm = project.program_manager_id and str(project.program_manager_id) == user_id
        is_creator = str(project.created_by) == user_id

        if is_co or is_pm or is_creator:
            # CO/PM/creator get at least EDITOR level
            if min_permission and min_permission == PermissionLevel.OWNER:
                # Only explicit OWNER permission or creator
                if is_creator:
                    return True
                perm = db.query(ProjectPermission).filter(
                    ProjectPermission.user_id == user_id,
                    ProjectPermission.project_id == project_id,
                    ProjectPermission.permission_level == PermissionLevel.OWNER
                ).first()
                return perm is not None
            return True

        # Check direct permission
        perm = db.query(ProjectPermission).filter(
            ProjectPermission.user_id == user_id,
            ProjectPermission.project_id == project_id
        ).first()
        if perm:
            if min_permission:
                level_order = {PermissionLevel.VIEWER: 0, PermissionLevel.EDITOR: 1, PermissionLevel.OWNER: 2}
                return level_order.get(perm.permission_level, 0) >= level_order.get(min_permission, 0)
            return True

        # Check org visibility
        if project.organization_id:
            visible_org_ids = OrganizationService.get_user_visible_org_ids(db, user_id)
            if str(project.organization_id) in visible_org_ids:
                # Org visibility grants VIEWER access
                if min_permission and min_permission != PermissionLevel.VIEWER:
                    return False
                return True

        # Check cross-org shares
        user_org_ids = [
            str(m.organization_id) for m in
            db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).all()
        ]
        if user_org_ids:
            share = db.query(CrossOrgShare).filter(
                CrossOrgShare.project_id == project_id,
                CrossOrgShare.target_org_id.in_(user_org_ids),
                or_(
                    CrossOrgShare.expires_at == None,
                    CrossOrgShare.expires_at > datetime.utcnow()
                )
            ).first()
            if share:
                if min_permission:
                    from backend.models.organization import SharePermission
                    share_level = {SharePermission.VIEWER: 0, SharePermission.EDITOR: 1}
                    perm_level = {PermissionLevel.VIEWER: 0, PermissionLevel.EDITOR: 1, PermissionLevel.OWNER: 2}
                    return share_level.get(share.permission_level, 0) >= perm_level.get(min_permission, 0)
                return True

        return False

    @staticmethod
    def update_materialized_path(db: Session, org: Organization):
        """Recalculate materialized path for an org and all descendants."""
        if org.parent_id:
            parent = db.query(Organization).filter(Organization.id == org.parent_id).first()
            if parent:
                org.path = f"{parent.path}/{str(parent.id)}" if parent.path else str(parent.id)
                org.depth = parent.depth + 1
            else:
                org.path = ""
                org.depth = 0
        else:
            org.path = ""
            org.depth = 0

        # Recursively update children
        children = db.query(Organization).filter(Organization.parent_id == org.id).all()
        for child in children:
            OrganizationService.update_materialized_path(db, child)

    @staticmethod
    def check_org_admin(db: Session, user: User, org_id: str) -> bool:
        """Check if user is an org_admin for the given org or any ancestor."""
        if user.role == UserRole.ADMIN:
            return True

        # Check if user is org_admin in this org
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == org_id,
            OrganizationMember.org_role == OrgRole.ORG_ADMIN
        ).first()
        if membership:
            return True

        # Check if user is org_admin in any ancestor org (they manage subtree)
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if org and org.path:
            ancestor_ids = org.path.split("/")
            for ancestor_id in ancestor_ids:
                if ancestor_id:
                    ancestor_membership = db.query(OrganizationMember).filter(
                        OrganizationMember.user_id == user.id,
                        OrganizationMember.organization_id == ancestor_id,
                        OrganizationMember.org_role == OrgRole.ORG_ADMIN
                    ).first()
                    if ancestor_membership:
                        return True

        return False


def log_project_activity(
    db: Session,
    project_id: str,
    user_id: Optional[str],
    activity_type: str,
    title: str,
    description: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Helper to log a project activity."""
    from backend.models.activity import ProjectActivity
    activity = ProjectActivity(
        project_id=project_id,
        user_id=user_id,
        activity_type=activity_type,
        title=title,
        description=description,
        activity_metadata=metadata
    )
    db.add(activity)
    # Don't commit — caller manages the transaction
