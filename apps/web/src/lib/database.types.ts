export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          name: string
          role: 'contracting_officer' | 'program_manager' | 'approver' | 'viewer'
          department: string | null
          notification_preferences: Json
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          name: string
          role: 'contracting_officer' | 'program_manager' | 'approver' | 'viewer'
          department?: string | null
          notification_preferences?: Json
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          name?: string
          role?: 'contracting_officer' | 'program_manager' | 'approver' | 'viewer'
          department?: string | null
          notification_preferences?: Json
          created_at?: string
          updated_at?: string
        }
      }
      procurement_projects: {
        Row: {
          id: string
          name: string
          description: string | null
          project_type: 'rfp' | 'rfq' | 'task_order' | 'idiq' | 'other'
          estimated_value: number | null
          contracting_officer_id: string
          program_manager_id: string | null
          current_phase: 'pre_solicitation' | 'solicitation' | 'post_solicitation'
          overall_status: 'not_started' | 'in_progress' | 'completed' | 'delayed' | 'on_hold'
          start_date: string | null
          target_completion_date: string | null
          actual_completion_date: string | null
          created_by: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          name: string
          description?: string | null
          project_type: 'rfp' | 'rfq' | 'task_order' | 'idiq' | 'other'
          estimated_value?: number | null
          contracting_officer_id: string
          program_manager_id?: string | null
          current_phase?: 'pre_solicitation' | 'solicitation' | 'post_solicitation'
          overall_status?: 'not_started' | 'in_progress' | 'completed' | 'delayed' | 'on_hold'
          start_date?: string | null
          target_completion_date?: string | null
          actual_completion_date?: string | null
          created_by: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          name?: string
          description?: string | null
          project_type?: 'rfp' | 'rfq' | 'task_order' | 'idiq' | 'other'
          estimated_value?: number | null
          contracting_officer_id?: string
          program_manager_id?: string | null
          current_phase?: 'pre_solicitation' | 'solicitation' | 'post_solicitation'
          overall_status?: 'not_started' | 'in_progress' | 'completed' | 'delayed' | 'on_hold'
          start_date?: string | null
          target_completion_date?: string | null
          actual_completion_date?: string | null
          created_by?: string
          created_at?: string
          updated_at?: string
        }
      }
      procurement_phases: {
        Row: {
          id: string
          project_id: string
          phase_name: 'pre_solicitation' | 'solicitation' | 'post_solicitation'
          phase_order: number
          status: 'not_started' | 'in_progress' | 'completed' | 'delayed'
          start_date: string | null
          end_date: string | null
          estimated_duration_days: number
          actual_duration_days: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          phase_name: 'pre_solicitation' | 'solicitation' | 'post_solicitation'
          phase_order: number
          status?: 'not_started' | 'in_progress' | 'completed' | 'delayed'
          start_date?: string | null
          end_date?: string | null
          estimated_duration_days: number
          actual_duration_days?: number | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          phase_name?: 'pre_solicitation' | 'solicitation' | 'post_solicitation'
          phase_order?: number
          status?: 'not_started' | 'in_progress' | 'completed' | 'delayed'
          start_date?: string | null
          end_date?: string | null
          estimated_duration_days?: number
          actual_duration_days?: number | null
          created_at?: string
          updated_at?: string
        }
      }
      procurement_steps: {
        Row: {
          id: string
          phase_id: string
          project_id: string
          step_name: string
          step_description: string | null
          step_order: number
          assigned_user_id: string | null
          status: 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'skipped'
          deadline: string | null
          completion_date: string | null
          notes: string | null
          attachments: Json | null
          requires_approval: boolean
          approved_by: string | null
          approval_date: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          phase_id: string
          project_id: string
          step_name: string
          step_description?: string | null
          step_order: number
          assigned_user_id?: string | null
          status?: 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'skipped'
          deadline?: string | null
          completion_date?: string | null
          notes?: string | null
          attachments?: Json | null
          requires_approval?: boolean
          approved_by?: string | null
          approval_date?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          phase_id?: string
          project_id?: string
          step_name?: string
          step_description?: string | null
          step_order?: number
          assigned_user_id?: string | null
          status?: 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'skipped'
          deadline?: string | null
          completion_date?: string | null
          notes?: string | null
          attachments?: Json | null
          requires_approval?: boolean
          approved_by?: string | null
          approval_date?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      project_permissions: {
        Row: {
          id: string
          user_id: string
          project_id: string
          permission_level: 'owner' | 'editor' | 'viewer'
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          project_id: string
          permission_level: 'owner' | 'editor' | 'viewer'
          created_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          project_id?: string
          permission_level?: 'owner' | 'editor' | 'viewer'
          created_at?: string
        }
      }
      notifications: {
        Row: {
          id: string
          user_id: string
          project_id: string
          notification_type: 'assignment' | 'deadline_warning' | 'phase_complete' | 'approval_request' | 'overdue' | 'update'
          title: string
          message: string
          link_url: string | null
          is_read: boolean
          sent_via_email: boolean
          email_sent_at: string | null
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          project_id: string
          notification_type: 'assignment' | 'deadline_warning' | 'phase_complete' | 'approval_request' | 'overdue' | 'update'
          title: string
          message: string
          link_url?: string | null
          is_read?: boolean
          sent_via_email?: boolean
          email_sent_at?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          project_id?: string
          notification_type?: 'assignment' | 'deadline_warning' | 'phase_complete' | 'approval_request' | 'overdue' | 'update'
          title?: string
          message?: string
          link_url?: string | null
          is_read?: boolean
          sent_via_email?: boolean
          email_sent_at?: string | null
          created_at?: string
        }
      }
      audit_log: {
        Row: {
          id: string
          user_id: string
          project_id: string | null
          action: string
          entity_type: string
          entity_id: string | null
          changes: Json
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          project_id?: string | null
          action: string
          entity_type: string
          entity_id?: string | null
          changes: Json
          created_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          project_id?: string | null
          action?: string
          entity_type?: string
          entity_id?: string | null
          changes?: Json
          created_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      user_role: 'contracting_officer' | 'program_manager' | 'approver' | 'viewer'
      project_type: 'rfp' | 'rfq' | 'task_order' | 'idiq' | 'other'
      project_status: 'not_started' | 'in_progress' | 'completed' | 'delayed' | 'on_hold'
      phase_name: 'pre_solicitation' | 'solicitation' | 'post_solicitation'
      step_status: 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'skipped'
      notification_type: 'assignment' | 'deadline_warning' | 'phase_complete' | 'approval_request' | 'overdue' | 'update'
    }
  }
}
