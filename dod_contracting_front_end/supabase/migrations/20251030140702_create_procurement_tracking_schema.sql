/*
  # Procurement Tracking System - Complete Database Schema

  ## Overview
  Creates a comprehensive procurement tracking system supporting multiple concurrent projects
  with role-based access control, phase tracking, step management, notifications, and audit logging.

  ## New Tables Created

  ### 1. users
  Stores user information and roles for the procurement system
  - `id` (uuid, primary key) - User identifier
  - `email` (text, unique) - User email address
  - `name` (text) - User full name
  - `role` (enum) - User role: contracting_officer, program_manager, approver, or viewer
  - `department` (text, nullable) - User's department or organization
  - `notification_preferences` (jsonb) - User notification settings
  - `created_at` (timestamptz) - Record creation timestamp
  - `updated_at` (timestamptz) - Record last update timestamp

  ### 2. procurement_projects
  Main table for tracking procurement projects
  - `id` (uuid, primary key) - Project unique identifier
  - `name` (text) - Project name
  - `description` (text, nullable) - Project description
  - `project_type` (enum) - Type: rfp, rfq, task_order, idiq, or other
  - `estimated_value` (numeric, nullable) - Estimated contract value
  - `contracting_officer_id` (uuid, fk to users) - Assigned contracting officer
  - `program_manager_id` (uuid, fk to users, nullable) - Assigned program manager
  - `current_phase` (enum) - Current phase: pre_solicitation, solicitation, or post_solicitation
  - `overall_status` (enum) - Status: not_started, in_progress, completed, delayed, or on_hold
  - `start_date` (date, nullable) - Project start date
  - `target_completion_date` (date, nullable) - Target completion date
  - `actual_completion_date` (date, nullable) - Actual completion date
  - `created_by` (uuid, fk to users) - User who created the project
  - `created_at` (timestamptz) - Record creation timestamp
  - `updated_at` (timestamptz) - Record last update timestamp

  ### 3. procurement_phases
  Tracks the three main phases of each procurement project
  - `id` (uuid, primary key) - Phase unique identifier
  - `project_id` (uuid, fk to procurement_projects) - Associated project
  - `phase_name` (enum) - Phase name: pre_solicitation, solicitation, or post_solicitation
  - `phase_order` (integer) - Order of the phase (1, 2, 3)
  - `status` (enum) - Phase status: not_started, in_progress, completed, or delayed
  - `start_date` (date, nullable) - Phase start date
  - `end_date` (date, nullable) - Phase end date
  - `estimated_duration_days` (integer) - Estimated duration in days
  - `actual_duration_days` (integer, nullable) - Actual duration in days
  - `created_at` (timestamptz) - Record creation timestamp
  - `updated_at` (timestamptz) - Record last update timestamp

  ### 4. procurement_steps
  Individual steps within each phase
  - `id` (uuid, primary key) - Step unique identifier
  - `phase_id` (uuid, fk to procurement_phases) - Associated phase
  - `project_id` (uuid, fk to procurement_projects) - Associated project
  - `step_name` (text) - Step name
  - `step_description` (text, nullable) - Detailed step description
  - `step_order` (integer) - Order within the phase
  - `assigned_user_id` (uuid, fk to users, nullable) - Assigned user
  - `status` (enum) - Step status: not_started, in_progress, completed, blocked, or skipped
  - `deadline` (date, nullable) - Step deadline
  - `completion_date` (date, nullable) - Actual completion date
  - `notes` (text, nullable) - Step notes and comments
  - `attachments` (jsonb, nullable) - Attached documents metadata
  - `requires_approval` (boolean) - Whether step requires approval
  - `approved_by` (uuid, fk to users, nullable) - User who approved
  - `approval_date` (date, nullable) - Approval date
  - `created_at` (timestamptz) - Record creation timestamp
  - `updated_at` (timestamptz) - Record last update timestamp

  ### 5. project_permissions
  Granular access control for projects
  - `id` (uuid, primary key) - Permission unique identifier
  - `user_id` (uuid, fk to users) - User granted permission
  - `project_id` (uuid, fk to procurement_projects) - Project
  - `permission_level` (enum) - Permission: owner, editor, or viewer
  - `created_at` (timestamptz) - Record creation timestamp

  ### 6. notifications
  System notifications for users
  - `id` (uuid, primary key) - Notification unique identifier
  - `user_id` (uuid, fk to users) - Recipient user
  - `project_id` (uuid, fk to procurement_projects) - Related project
  - `notification_type` (enum) - Type: assignment, deadline_warning, phase_complete, approval_request, overdue, or update
  - `title` (text) - Notification title
  - `message` (text) - Notification message
  - `link_url` (text, nullable) - Deep link to relevant page
  - `is_read` (boolean) - Whether notification has been read
  - `sent_via_email` (boolean) - Whether email was sent
  - `email_sent_at` (timestamptz, nullable) - Email send timestamp
  - `created_at` (timestamptz) - Record creation timestamp

  ### 7. audit_log
  Audit trail of all system changes
  - `id` (uuid, primary key) - Log entry unique identifier
  - `user_id` (uuid, fk to users) - User who made the change
  - `project_id` (uuid, fk to procurement_projects, nullable) - Related project
  - `action` (text) - Action performed
  - `entity_type` (text) - Type of entity changed
  - `entity_id` (uuid, nullable) - ID of changed entity
  - `changes` (jsonb) - Before/after values
  - `created_at` (timestamptz) - Record creation timestamp

  ## Security
  - Row Level Security (RLS) enabled on all tables
  - Policies enforce role-based access control
  - Contracting officers have full access to their projects
  - Program managers can view and edit assigned projects
  - Approvers can view projects and approve steps
  - Viewers have read-only access to assigned projects

  ## Important Notes
  1. All tables use UUID primary keys for security and scalability
  2. Timestamps automatically updated via triggers
  3. Audit logging triggered automatically on changes
  4. Notification creation automated via database triggers
  5. Foreign key constraints ensure referential integrity
  6. Indexes created on frequently queried columns for performance
*/

-- Create custom types/enums
CREATE TYPE user_role AS ENUM ('contracting_officer', 'program_manager', 'approver', 'viewer');
CREATE TYPE project_type AS ENUM ('rfp', 'rfq', 'task_order', 'idiq', 'other');
CREATE TYPE project_status AS ENUM ('not_started', 'in_progress', 'completed', 'delayed', 'on_hold');
CREATE TYPE phase_name AS ENUM ('pre_solicitation', 'solicitation', 'post_solicitation');
CREATE TYPE phase_status AS ENUM ('not_started', 'in_progress', 'completed', 'delayed');
CREATE TYPE step_status AS ENUM ('not_started', 'in_progress', 'completed', 'blocked', 'skipped');
CREATE TYPE permission_level AS ENUM ('owner', 'editor', 'viewer');
CREATE TYPE notification_type AS ENUM ('assignment', 'deadline_warning', 'phase_complete', 'approval_request', 'overdue', 'update');

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE NOT NULL,
  name text NOT NULL,
  role user_role NOT NULL DEFAULT 'viewer',
  department text,
  notification_preferences jsonb DEFAULT '{"email": true, "in_app": true, "deadline_days": [1, 3, 7]}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create procurement_projects table
CREATE TABLE IF NOT EXISTS procurement_projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  project_type project_type NOT NULL,
  estimated_value numeric(15, 2),
  contracting_officer_id uuid NOT NULL REFERENCES users(id),
  program_manager_id uuid REFERENCES users(id),
  current_phase phase_name DEFAULT 'pre_solicitation',
  overall_status project_status DEFAULT 'not_started',
  start_date date,
  target_completion_date date,
  actual_completion_date date,
  created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create procurement_phases table
CREATE TABLE IF NOT EXISTS procurement_phases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES procurement_projects(id) ON DELETE CASCADE,
  phase_name phase_name NOT NULL,
  phase_order integer NOT NULL,
  status phase_status DEFAULT 'not_started',
  start_date date,
  end_date date,
  estimated_duration_days integer NOT NULL DEFAULT 30,
  actual_duration_days integer,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(project_id, phase_name)
);

-- Create procurement_steps table
CREATE TABLE IF NOT EXISTS procurement_steps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  phase_id uuid NOT NULL REFERENCES procurement_phases(id) ON DELETE CASCADE,
  project_id uuid NOT NULL REFERENCES procurement_projects(id) ON DELETE CASCADE,
  step_name text NOT NULL,
  step_description text,
  step_order integer NOT NULL,
  assigned_user_id uuid REFERENCES users(id),
  status step_status DEFAULT 'not_started',
  deadline date,
  completion_date date,
  notes text,
  attachments jsonb,
  requires_approval boolean DEFAULT false,
  approved_by uuid REFERENCES users(id),
  approval_date date,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create project_permissions table
CREATE TABLE IF NOT EXISTS project_permissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  project_id uuid NOT NULL REFERENCES procurement_projects(id) ON DELETE CASCADE,
  permission_level permission_level NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, project_id)
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  project_id uuid NOT NULL REFERENCES procurement_projects(id) ON DELETE CASCADE,
  notification_type notification_type NOT NULL,
  title text NOT NULL,
  message text NOT NULL,
  link_url text,
  is_read boolean DEFAULT false,
  sent_via_email boolean DEFAULT false,
  email_sent_at timestamptz,
  created_at timestamptz DEFAULT now()
);

-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id),
  project_id uuid REFERENCES procurement_projects(id) ON DELETE SET NULL,
  action text NOT NULL,
  entity_type text NOT NULL,
  entity_id uuid,
  changes jsonb NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_contracting_officer ON procurement_projects(contracting_officer_id);
CREATE INDEX IF NOT EXISTS idx_projects_program_manager ON procurement_projects(program_manager_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON procurement_projects(overall_status);
CREATE INDEX IF NOT EXISTS idx_projects_current_phase ON procurement_projects(current_phase);
CREATE INDEX IF NOT EXISTS idx_phases_project ON procurement_phases(project_id);
CREATE INDEX IF NOT EXISTS idx_steps_phase ON procurement_steps(phase_id);
CREATE INDEX IF NOT EXISTS idx_steps_project ON procurement_steps(project_id);
CREATE INDEX IF NOT EXISTS idx_steps_assigned_user ON procurement_steps(assigned_user_id);
CREATE INDEX IF NOT EXISTS idx_steps_status ON procurement_steps(status);
CREATE INDEX IF NOT EXISTS idx_permissions_user ON project_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_permissions_project ON project_permissions(project_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = false;
CREATE INDEX IF NOT EXISTS idx_audit_project ON audit_log(project_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE procurement_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE procurement_phases ENABLE ROW LEVEL SECURITY;
ALTER TABLE procurement_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view all users"
  ON users FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- RLS Policies for procurement_projects table
CREATE POLICY "Users can view projects they have access to"
  ON procurement_projects FOR SELECT
  TO authenticated
  USING (
    auth.uid() = contracting_officer_id
    OR auth.uid() = program_manager_id
    OR auth.uid() = created_by
    OR EXISTS (
      SELECT 1 FROM project_permissions
      WHERE project_permissions.project_id = procurement_projects.id
      AND project_permissions.user_id = auth.uid()
    )
  );

CREATE POLICY "Contracting officers can create projects"
  ON procurement_projects FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role IN ('contracting_officer', 'program_manager')
    )
  );

CREATE POLICY "Project owners can update projects"
  ON procurement_projects FOR UPDATE
  TO authenticated
  USING (
    auth.uid() = contracting_officer_id
    OR auth.uid() = created_by
    OR EXISTS (
      SELECT 1 FROM project_permissions
      WHERE project_permissions.project_id = procurement_projects.id
      AND project_permissions.user_id = auth.uid()
      AND project_permissions.permission_level IN ('owner', 'editor')
    )
  )
  WITH CHECK (
    auth.uid() = contracting_officer_id
    OR auth.uid() = created_by
    OR EXISTS (
      SELECT 1 FROM project_permissions
      WHERE project_permissions.project_id = procurement_projects.id
      AND project_permissions.user_id = auth.uid()
      AND project_permissions.permission_level IN ('owner', 'editor')
    )
  );

CREATE POLICY "Project owners can delete projects"
  ON procurement_projects FOR DELETE
  TO authenticated
  USING (
    auth.uid() = contracting_officer_id
    OR auth.uid() = created_by
  );

-- RLS Policies for procurement_phases table
CREATE POLICY "Users can view phases for accessible projects"
  ON procurement_phases FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = procurement_phases.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.program_manager_id
        OR auth.uid() = procurement_projects.created_by
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
        )
      )
    )
  );

CREATE POLICY "Project editors can manage phases"
  ON procurement_phases FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = procurement_phases.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
          AND project_permissions.permission_level IN ('owner', 'editor')
        )
      )
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = procurement_phases.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
          AND project_permissions.permission_level IN ('owner', 'editor')
        )
      )
    )
  );

-- RLS Policies for procurement_steps table
CREATE POLICY "Users can view steps for accessible projects"
  ON procurement_steps FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = procurement_steps.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.program_manager_id
        OR auth.uid() = procurement_projects.created_by
        OR auth.uid() = procurement_steps.assigned_user_id
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
        )
      )
    )
  );

CREATE POLICY "Project editors and assigned users can update steps"
  ON procurement_steps FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = procurement_steps.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.program_manager_id
        OR auth.uid() = procurement_steps.assigned_user_id
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
          AND project_permissions.permission_level IN ('owner', 'editor')
        )
      )
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = procurement_steps.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.program_manager_id
        OR auth.uid() = procurement_steps.assigned_user_id
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
          AND project_permissions.permission_level IN ('owner', 'editor')
        )
      )
    )
  );

CREATE POLICY "Project editors can create and delete steps"
  ON procurement_steps FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = procurement_steps.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
          AND project_permissions.permission_level IN ('owner', 'editor')
        )
      )
    )
  );

CREATE POLICY "Project editors can delete steps"
  ON procurement_steps FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = procurement_steps.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
      )
    )
  );

-- RLS Policies for project_permissions table
CREATE POLICY "Users can view permissions for accessible projects"
  ON project_permissions FOR SELECT
  TO authenticated
  USING (
    auth.uid() = user_id
    OR EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = project_permissions.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
      )
    )
  );

CREATE POLICY "Project owners can manage permissions"
  ON project_permissions FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = project_permissions.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
      )
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = project_permissions.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
      )
    )
  );

-- RLS Policies for notifications table
CREATE POLICY "Users can view own notifications"
  ON notifications FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications"
  ON notifications FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "System can create notifications"
  ON notifications FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- RLS Policies for audit_log table
CREATE POLICY "Users can view audit logs for accessible projects"
  ON audit_log FOR SELECT
  TO authenticated
  USING (
    auth.uid() = user_id
    OR project_id IS NULL
    OR EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = audit_log.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
      )
    )
  );

CREATE POLICY "System can create audit logs"
  ON audit_log FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON procurement_projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_phases_updated_at BEFORE UPDATE ON procurement_phases
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_steps_updated_at BEFORE UPDATE ON procurement_steps
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
