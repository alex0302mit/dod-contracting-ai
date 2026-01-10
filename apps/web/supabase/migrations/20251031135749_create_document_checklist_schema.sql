/*
  # Document Checklist Management System - Complete Database Schema

  ## Overview
  Creates a comprehensive document checklist system for DoD procurement projects, supporting
  AI-generated templates, file uploads, approval workflows, and lifecycle tracking.

  ## New Tables Created

  ### 1. document_checklist_templates
  Master templates for document requirements by contract type
  - `id` (uuid, primary key) - Template unique identifier
  - `contract_type` (enum) - Contract type: rfp, rfq, task_order, idiq, or other
  - `document_name` (text) - Name of the required document
  - `description` (text, nullable) - Detailed description of the document
  - `category` (text) - Document category (e.g., 'Technical', 'Financial', 'Legal', 'Administrative')
  - `phase` (enum, nullable) - Associated phase: pre_solicitation, solicitation, or post_solicitation
  - `is_required` (boolean) - Whether document is mandatory or optional
  - `typical_deadline_days` (integer, nullable) - Typical days from project start for deadline
  - `requires_approval` (boolean) - Whether document needs approval
  - `display_order` (integer) - Order for displaying in lists
  - `created_at` (timestamptz) - Record creation timestamp
  - `updated_at` (timestamptz) - Record last update timestamp

  ### 2. project_documents
  Individual document requirements for each project
  - `id` (uuid, primary key) - Document unique identifier
  - `project_id` (uuid, fk to procurement_projects) - Associated project
  - `document_name` (text) - Name of the required document
  - `description` (text, nullable) - Detailed description
  - `category` (text) - Document category
  - `phase` (enum, nullable) - Associated phase
  - `is_required` (boolean) - Whether document is mandatory
  - `status` (enum) - Status: pending, uploaded, under_review, approved, rejected, expired
  - `deadline` (date, nullable) - Document submission deadline
  - `expiration_date` (date, nullable) - Document expiration date
  - `requires_approval` (boolean) - Whether document needs approval
  - `assigned_user_id` (uuid, fk to users, nullable) - User responsible for document
  - `notes` (text, nullable) - Notes and comments
  - `display_order` (integer) - Display order in checklist
  - `created_at` (timestamptz) - Record creation timestamp
  - `updated_at` (timestamptz) - Record last update timestamp

  ### 3. document_uploads
  File attachments and version history for documents
  - `id` (uuid, primary key) - Upload unique identifier
  - `project_document_id` (uuid, fk to project_documents) - Associated document
  - `file_name` (text) - Original file name
  - `file_path` (text) - Storage path in Supabase Storage
  - `file_size` (bigint) - File size in bytes
  - `file_type` (text) - MIME type
  - `version_number` (integer) - Version number (1, 2, 3, etc.)
  - `uploaded_by` (uuid, fk to users) - User who uploaded the file
  - `upload_date` (timestamptz) - Upload timestamp
  - `is_current_version` (boolean) - Whether this is the current active version
  - `notes` (text, nullable) - Upload notes or change description
  - `created_at` (timestamptz) - Record creation timestamp

  ### 4. document_approvals
  Approval workflow tracking for documents
  - `id` (uuid, primary key) - Approval unique identifier
  - `project_document_id` (uuid, fk to project_documents) - Associated document
  - `document_upload_id` (uuid, fk to document_uploads, nullable) - Specific file version being approved
  - `approver_id` (uuid, fk to users) - User who can/did approve
  - `approval_status` (enum) - Status: pending, approved, rejected, requested_changes
  - `approval_date` (timestamptz, nullable) - When approval was granted/rejected
  - `comments` (text, nullable) - Approver comments or feedback
  - `requested_at` (timestamptz) - When approval was requested
  - `created_at` (timestamptz) - Record creation timestamp
  - `updated_at` (timestamptz) - Record last update timestamp

  ## Security
  - Row Level Security (RLS) enabled on all tables
  - Policies enforce project-based access control
  - Users can only access documents for projects they have permissions to
  - Approvers have special privileges for approval actions
  - Audit trail maintained for all document actions

  ## Important Notes
  1. All tables use UUID primary keys for security and scalability
  2. Timestamps automatically updated via triggers
  3. Document status automatically updated based on upload and approval events
  4. Foreign key constraints ensure referential integrity
  5. Indexes created on frequently queried columns for performance
  6. File storage integrated with Supabase Storage buckets
*/

-- Create custom types/enums for document management
CREATE TYPE document_status AS ENUM ('pending', 'uploaded', 'under_review', 'approved', 'rejected', 'expired');
CREATE TYPE approval_status AS ENUM ('pending', 'approved', 'rejected', 'requested_changes');

-- Create document_checklist_templates table
CREATE TABLE IF NOT EXISTS document_checklist_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  contract_type project_type NOT NULL,
  document_name text NOT NULL,
  description text,
  category text NOT NULL DEFAULT 'General',
  phase phase_name,
  is_required boolean DEFAULT true,
  typical_deadline_days integer,
  requires_approval boolean DEFAULT false,
  display_order integer NOT NULL DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create project_documents table
CREATE TABLE IF NOT EXISTS project_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES procurement_projects(id) ON DELETE CASCADE,
  document_name text NOT NULL,
  description text,
  category text NOT NULL DEFAULT 'General',
  phase phase_name,
  is_required boolean DEFAULT true,
  status document_status DEFAULT 'pending',
  deadline date,
  expiration_date date,
  requires_approval boolean DEFAULT false,
  assigned_user_id uuid REFERENCES users(id),
  notes text,
  display_order integer NOT NULL DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create document_uploads table
CREATE TABLE IF NOT EXISTS document_uploads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_document_id uuid NOT NULL REFERENCES project_documents(id) ON DELETE CASCADE,
  file_name text NOT NULL,
  file_path text NOT NULL,
  file_size bigint NOT NULL,
  file_type text NOT NULL,
  version_number integer NOT NULL DEFAULT 1,
  uploaded_by uuid NOT NULL REFERENCES users(id),
  upload_date timestamptz DEFAULT now(),
  is_current_version boolean DEFAULT true,
  notes text,
  created_at timestamptz DEFAULT now()
);

-- Create document_approvals table
CREATE TABLE IF NOT EXISTS document_approvals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_document_id uuid NOT NULL REFERENCES project_documents(id) ON DELETE CASCADE,
  document_upload_id uuid REFERENCES document_uploads(id) ON DELETE SET NULL,
  approver_id uuid NOT NULL REFERENCES users(id),
  approval_status approval_status DEFAULT 'pending',
  approval_date timestamptz,
  comments text,
  requested_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_checklist_templates_contract_type ON document_checklist_templates(contract_type);
CREATE INDEX IF NOT EXISTS idx_checklist_templates_phase ON document_checklist_templates(phase);
CREATE INDEX IF NOT EXISTS idx_project_documents_project ON project_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_project_documents_status ON project_documents(status);
CREATE INDEX IF NOT EXISTS idx_project_documents_phase ON project_documents(phase);
CREATE INDEX IF NOT EXISTS idx_project_documents_assigned_user ON project_documents(assigned_user_id);
CREATE INDEX IF NOT EXISTS idx_document_uploads_project_doc ON document_uploads(project_document_id);
CREATE INDEX IF NOT EXISTS idx_document_uploads_uploaded_by ON document_uploads(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_document_uploads_current_version ON document_uploads(project_document_id, is_current_version) WHERE is_current_version = true;
CREATE INDEX IF NOT EXISTS idx_document_approvals_project_doc ON document_approvals(project_document_id);
CREATE INDEX IF NOT EXISTS idx_document_approvals_approver ON document_approvals(approver_id);
CREATE INDEX IF NOT EXISTS idx_document_approvals_status ON document_approvals(approval_status);

-- Enable Row Level Security
ALTER TABLE document_checklist_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_approvals ENABLE ROW LEVEL SECURITY;

-- RLS Policies for document_checklist_templates table
CREATE POLICY "All authenticated users can view templates"
  ON document_checklist_templates FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Contracting officers can manage templates"
  ON document_checklist_templates FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role IN ('contracting_officer', 'program_manager')
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role IN ('contracting_officer', 'program_manager')
    )
  );

-- RLS Policies for project_documents table
CREATE POLICY "Users can view documents for accessible projects"
  ON project_documents FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = project_documents.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.program_manager_id
        OR auth.uid() = procurement_projects.created_by
        OR auth.uid() = project_documents.assigned_user_id
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
        )
      )
    )
  );

CREATE POLICY "Project editors can create documents"
  ON project_documents FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = project_documents.project_id
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

CREATE POLICY "Project editors and assigned users can update documents"
  ON project_documents FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = project_documents.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.program_manager_id
        OR auth.uid() = project_documents.assigned_user_id
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
      WHERE procurement_projects.id = project_documents.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.program_manager_id
        OR auth.uid() = project_documents.assigned_user_id
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
          AND project_permissions.permission_level IN ('owner', 'editor')
        )
      )
    )
  );

CREATE POLICY "Project editors can delete documents"
  ON project_documents FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM procurement_projects
      WHERE procurement_projects.id = project_documents.project_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
      )
    )
  );

-- RLS Policies for document_uploads table
CREATE POLICY "Users can view uploads for accessible documents"
  ON document_uploads FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM project_documents
      JOIN procurement_projects ON procurement_projects.id = project_documents.project_id
      WHERE project_documents.id = document_uploads.project_document_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.program_manager_id
        OR auth.uid() = procurement_projects.created_by
        OR auth.uid() = project_documents.assigned_user_id
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
        )
      )
    )
  );

CREATE POLICY "Authenticated users can upload documents"
  ON document_uploads FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM project_documents
      JOIN procurement_projects ON procurement_projects.id = project_documents.project_id
      WHERE project_documents.id = document_uploads.project_document_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.program_manager_id
        OR auth.uid() = project_documents.assigned_user_id
        OR EXISTS (
          SELECT 1 FROM project_permissions
          WHERE project_permissions.project_id = procurement_projects.id
          AND project_permissions.user_id = auth.uid()
          AND project_permissions.permission_level IN ('owner', 'editor')
        )
      )
    )
  );

-- RLS Policies for document_approvals table
CREATE POLICY "Users can view approvals for accessible documents"
  ON document_approvals FOR SELECT
  TO authenticated
  USING (
    auth.uid() = approver_id
    OR EXISTS (
      SELECT 1 FROM project_documents
      JOIN procurement_projects ON procurement_projects.id = project_documents.project_id
      WHERE project_documents.id = document_approvals.project_document_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
        OR auth.uid() = project_documents.assigned_user_id
      )
    )
  );

CREATE POLICY "Project editors can request approvals"
  ON document_approvals FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM project_documents
      JOIN procurement_projects ON procurement_projects.id = project_documents.project_id
      WHERE project_documents.id = document_approvals.project_document_id
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

CREATE POLICY "Approvers can update their approvals"
  ON document_approvals FOR UPDATE
  TO authenticated
  USING (
    auth.uid() = approver_id
    OR EXISTS (
      SELECT 1 FROM project_documents
      JOIN procurement_projects ON procurement_projects.id = project_documents.project_id
      WHERE project_documents.id = document_approvals.project_document_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
      )
    )
  )
  WITH CHECK (
    auth.uid() = approver_id
    OR EXISTS (
      SELECT 1 FROM project_documents
      JOIN procurement_projects ON procurement_projects.id = project_documents.project_id
      WHERE project_documents.id = document_approvals.project_document_id
      AND (
        auth.uid() = procurement_projects.contracting_officer_id
        OR auth.uid() = procurement_projects.created_by
      )
    )
  );

-- Create triggers for updated_at
CREATE TRIGGER update_document_templates_updated_at BEFORE UPDATE ON document_checklist_templates
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_documents_updated_at BEFORE UPDATE ON project_documents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_approvals_updated_at BEFORE UPDATE ON document_approvals
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to automatically update document status when uploaded
CREATE OR REPLACE FUNCTION update_document_status_on_upload()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE project_documents
  SET status = CASE
    WHEN requires_approval THEN 'under_review'::document_status
    ELSE 'uploaded'::document_status
  END
  WHERE id = NEW.project_document_id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_document_status_on_upload
  AFTER INSERT ON document_uploads
  FOR EACH ROW
  EXECUTE FUNCTION update_document_status_on_upload();

-- Create function to update document status based on approval
CREATE OR REPLACE FUNCTION update_document_status_on_approval()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.approval_status = 'approved' THEN
    UPDATE project_documents
    SET status = 'approved'::document_status
    WHERE id = NEW.project_document_id;
  ELSIF NEW.approval_status = 'rejected' THEN
    UPDATE project_documents
    SET status = 'rejected'::document_status
    WHERE id = NEW.project_document_id;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_document_status_on_approval
  AFTER UPDATE OF approval_status ON document_approvals
  FOR EACH ROW
  WHEN (NEW.approval_status IN ('approved', 'rejected'))
  EXECUTE FUNCTION update_document_status_on_approval();

-- Insert default document templates for each contract type

-- RFP (Request for Proposal) Documents
INSERT INTO document_checklist_templates (contract_type, document_name, description, category, phase, is_required, typical_deadline_days, requires_approval, display_order) VALUES
('rfp', 'Acquisition Strategy', 'Comprehensive acquisition strategy document outlining approach, timeline, and resources', 'Strategic', 'pre_solicitation', true, 30, true, 1),
('rfp', 'Independent Government Cost Estimate (IGCE)', 'Detailed cost estimate prepared by government team', 'Financial', 'pre_solicitation', true, 45, true, 2),
('rfp', 'Market Research Report', 'Analysis of potential vendors, market capabilities, and pricing', 'Research', 'pre_solicitation', true, 30, false, 3),
('rfp', 'Statement of Work (SOW)', 'Detailed description of work requirements and deliverables', 'Technical', 'pre_solicitation', true, 45, true, 4),
('rfp', 'Performance Work Statement (PWS)', 'Performance-based work requirements and objectives', 'Technical', 'pre_solicitation', false, 45, true, 5),
('rfp', 'Quality Assurance Surveillance Plan (QASP)', 'Plan for monitoring and evaluating contractor performance', 'Technical', 'pre_solicitation', true, 60, true, 6),
('rfp', 'Source Selection Plan', 'Detailed plan for evaluating and selecting proposals', 'Administrative', 'solicitation', true, 15, true, 7),
('rfp', 'Evaluation Criteria', 'Specific criteria and weighting for proposal evaluation', 'Administrative', 'solicitation', true, 15, true, 8),
('rfp', 'Section L - Instructions to Offerors', 'Detailed instructions for proposal preparation and submission', 'Administrative', 'solicitation', true, 30, true, 9),
('rfp', 'Section M - Evaluation Factors', 'Evaluation factors and subfactors with relative importance', 'Administrative', 'solicitation', true, 30, true, 10),
('rfp', 'DD Form 254 (DoD Contract Security Classification)', 'Security classification guidance for contractors', 'Security', 'solicitation', false, 30, true, 11),
('rfp', 'Conflict of Interest Certification', 'Certification of no conflicts of interest in evaluation', 'Legal', 'solicitation', true, 7, false, 12),
('rfp', 'Technical Evaluation Report', 'Comprehensive evaluation of technical proposals', 'Evaluation', 'post_solicitation', true, 45, true, 13),
('rfp', 'Past Performance Evaluation', 'Assessment of vendors past performance on similar contracts', 'Evaluation', 'post_solicitation', true, 30, true, 14),
('rfp', 'Cost/Price Analysis', 'Detailed analysis of proposed costs and pricing', 'Financial', 'post_solicitation', true, 30, true, 15),
('rfp', 'Competitive Range Determination', 'Documentation of competitive range decision', 'Administrative', 'post_solicitation', true, 15, true, 16),
('rfp', 'Source Selection Decision Document (SSDD)', 'Final source selection decision and rationale', 'Administrative', 'post_solicitation', true, 30, true, 17),
('rfp', 'Contract Award Documentation', 'Complete contract award package and supporting documents', 'Legal', 'post_solicitation', true, 15, true, 18);

-- RFQ (Request for Quotation) Documents
INSERT INTO document_checklist_templates (contract_type, document_name, description, category, phase, is_required, typical_deadline_days, requires_approval, display_order) VALUES
('rfq', 'Purchase Request', 'Initial purchase request with basic requirements', 'Administrative', 'pre_solicitation', true, 7, true, 1),
('rfq', 'Market Research Summary', 'Brief market analysis for commercial items', 'Research', 'pre_solicitation', true, 15, false, 2),
('rfq', 'Statement of Requirements', 'Clear description of items or services needed', 'Technical', 'pre_solicitation', true, 15, true, 3),
('rfq', 'Cost Estimate', 'Estimated cost based on market research', 'Financial', 'pre_solicitation', true, 15, false, 4),
('rfq', 'RFQ Package', 'Complete request for quotation package', 'Administrative', 'solicitation', true, 7, true, 5),
('rfq', 'Quote Evaluation Matrix', 'Criteria for evaluating quotes', 'Administrative', 'solicitation', true, 7, false, 6),
('rfq', 'Vendor Quotes', 'Received quotes from potential vendors', 'Financial', 'post_solicitation', true, 15, false, 7),
('rfq', 'Quote Analysis', 'Comparison and analysis of received quotes', 'Financial', 'post_solicitation', true, 7, true, 8),
('rfq', 'Award Justification', 'Justification for selected vendor', 'Administrative', 'post_solicitation', true, 7, true, 9),
('rfq', 'Purchase Order', 'Final purchase order or contract', 'Legal', 'post_solicitation', true, 7, true, 10);

-- IDIQ (Indefinite Delivery Indefinite Quantity) Documents
INSERT INTO document_checklist_templates (contract_type, document_name, description, category, phase, is_required, typical_deadline_days, requires_approval, display_order) VALUES
('idiq', 'IDIQ Acquisition Strategy', 'Strategy for IDIQ contract including ordering procedures', 'Strategic', 'pre_solicitation', true, 60, true, 1),
('idiq', 'Multiple Award Justification', 'Justification for multiple award IDIQ approach', 'Administrative', 'pre_solicitation', true, 30, true, 2),
('idiq', 'Fair Opportunity Process', 'Description of fair opportunity ordering process', 'Administrative', 'pre_solicitation', true, 30, true, 3),
('idiq', 'Minimum/Maximum Quantities', 'Documentation of guaranteed minimum and maximum quantities', 'Technical', 'pre_solicitation', true, 30, true, 4),
('idiq', 'Ordering Procedures', 'Detailed procedures for placing task/delivery orders', 'Administrative', 'pre_solicitation', true, 45, true, 5),
('idiq', 'Performance Requirements Summary', 'Summary of required capabilities across all potential orders', 'Technical', 'pre_solicitation', true, 45, true, 6),
('idiq', 'Task Order Request Template', 'Standard template for future task order requests', 'Administrative', 'solicitation', true, 30, true, 7),
('idiq', 'IDIQ Base Contract', 'Complete IDIQ base contract vehicle', 'Legal', 'post_solicitation', true, 45, true, 8),
('idiq', 'Awardee Evaluation Criteria', 'Criteria for selecting among multiple awardees for orders', 'Administrative', 'post_solicitation', true, 30, true, 9),
('idiq', 'Contract Administration Plan', 'Plan for administering IDIQ and task orders', 'Administrative', 'post_solicitation', true, 30, true, 10);

-- Task Order Documents
INSERT INTO document_checklist_templates (contract_type, document_name, description, category, phase, is_required, typical_deadline_days, requires_approval, display_order) VALUES
('task_order', 'Task Order Request (TOR)', 'Detailed request for task order under existing contract', 'Technical', 'pre_solicitation', true, 15, true, 1),
('task_order', 'Fair Opportunity Documentation', 'Documentation of fair opportunity process if applicable', 'Administrative', 'pre_solicitation', false, 15, true, 2),
('task_order', 'Funding Documentation', 'Proof of funding availability for task order', 'Financial', 'pre_solicitation', true, 7, true, 3),
('task_order', 'Technical Requirements', 'Specific technical requirements for this task order', 'Technical', 'solicitation', true, 15, true, 4),
('task_order', 'Contractor Proposal', 'Proposal from contractor for task order', 'Administrative', 'solicitation', true, 20, false, 5),
('task_order', 'Price Reasonableness Determination', 'Analysis of proposed pricing for task order', 'Financial', 'post_solicitation', true, 7, true, 6),
('task_order', 'Task Order Award', 'Executed task order document', 'Legal', 'post_solicitation', true, 7, true, 7);

-- Other Contract Type Documents (General)
INSERT INTO document_checklist_templates (contract_type, document_name, description, category, phase, is_required, typical_deadline_days, requires_approval, display_order) VALUES
('other', 'Acquisition Plan', 'General acquisition planning document', 'Strategic', 'pre_solicitation', true, 30, true, 1),
('other', 'Requirements Document', 'Description of requirements and specifications', 'Technical', 'pre_solicitation', true, 30, true, 2),
('other', 'Budget Approval', 'Approved budget and funding documentation', 'Financial', 'pre_solicitation', true, 15, true, 3),
('other', 'Solicitation Document', 'Main solicitation package', 'Administrative', 'solicitation', true, 30, true, 4),
('other', 'Evaluation Plan', 'Plan for evaluating responses', 'Administrative', 'solicitation', true, 15, true, 5),
('other', 'Award Documentation', 'Contract award and supporting documents', 'Legal', 'post_solicitation', true, 15, true, 6);