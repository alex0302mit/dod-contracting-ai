/**
 * API Service Layer
 * Handles all communication with the Python FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// ============================================================================
// API Error Class
// ============================================================================

/**
 * Custom error class for API responses with status codes.
 * Allows components to handle specific error types (locked, rate limited, etc.)
 */
export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

// ============================================================================
// Authentication Helpers
// ============================================================================

function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

function setAuthToken(token: string): void {
  localStorage.setItem('auth_token', token);
}

export function clearAuthToken(): void {
  localStorage.removeItem('auth_token');
}

// ============================================================================
// Generic API Request Handler
// ============================================================================

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    // Try to parse JSON error response for detail field
    let detail = response.statusText;
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      // If JSON parsing fails, try text
      try {
        detail = await response.text() || detail;
      } catch {
        // Use statusText as fallback
      }
    }

    // Handle specific status codes
    if (response.status === 401) {
      // Unauthorized - clear token and redirect to login (unless it's the login endpoint)
      if (!endpoint.includes('/auth/login')) {
        clearAuthToken();
        window.location.href = '/login';
      }
      throw new ApiError(401, detail);
    }

    if (response.status === 423) {
      // Account locked
      throw new ApiError(423, detail);
    }

    if (response.status === 429) {
      // Rate limited
      throw new ApiError(429, detail);
    }

    if (response.status === 400) {
      // Validation error
      throw new ApiError(400, detail);
    }

    throw new ApiError(response.status, detail);
  }

  return response.json();
}

// ============================================================================
// Authentication API
// ============================================================================

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'contracting_officer' | 'program_manager' | 'approver' | 'viewer';
  department?: string;
  notification_preferences: {
    email: boolean;
    in_app: boolean;
    deadline_days: number[];
  };
  is_active: boolean;
  created_at: string;
}

/**
 * User personal analytics stats returned from /api/users/me/stats
 * Used in profile dropdown to show activity summary
 */
export interface UserStats {
  documents_generated: number;      // Count of AI-generated documents this month
  estimated_hours_saved: number;    // Estimated hours saved by AI generation
  projects_contributed: number;     // Distinct projects with generated docs
  period: string;                   // Time period (currently "month")
}

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    // Backend expects query parameters, not JSON body
    const params = new URLSearchParams({ email, password });
    const response = await apiRequest<LoginResponse>(`/api/auth/login?${params}`, {
      method: 'POST',
    });
    setAuthToken(response.access_token);
    return response;
  },

  register: async (email: string, password: string, name: string, role: string): Promise<{ message: string; user: User }> => {
    // Backend expects query parameters, not JSON body
    const params = new URLSearchParams({ email, password, name, role });
    return apiRequest(`/api/auth/register?${params}`, {
      method: 'POST',
    });
  },

  me: async (): Promise<User> => {
    return apiRequest('/api/auth/me');
  },

  // Get users, optionally filtered by role
  getUsers: async (role?: string): Promise<{ users: User[] }> => {
    const url = role ? `/api/users?role=${role}` : '/api/users';
    return apiRequest(url);
  },

  /**
   * Get personal analytics for the current user.
   * Returns documents generated, time saved, and projects contributed
   * for the current calendar month.
   */
  getUserStats: async (): Promise<UserStats> => {
    return apiRequest('/api/users/me/stats');
  },

  logout: (): void => {
    clearAuthToken();
  },
};

// ============================================================================
// Admin API - User Management
// ============================================================================

export const adminApi = {
  // List all users (admin only)
  listUsers: async (): Promise<{ users: User[] }> => {
    return apiRequest('/api/admin/users');
  },

  // Update a user's role (admin only)
  updateUserRole: async (userId: string, role: string): Promise<{ message: string; user: User }> => {
    return apiRequest(`/api/admin/users/${userId}/role?role=${role}`, {
      method: 'PUT',
    });
  },

  // Deactivate a user (admin only)
  deactivateUser: async (userId: string): Promise<{ message: string }> => {
    return apiRequest(`/api/admin/users/${userId}`, {
      method: 'DELETE',
    });
  },

  // Create a new user with a specific role (admin only)
  createUser: async (
    email: string, 
    password: string, 
    name: string, 
    role: string
  ): Promise<{ message: string; user: User }> => {
    const params = new URLSearchParams({ email, password, name, role });
    return apiRequest(`/api/admin/users?${params}`, {
      method: 'POST',
    });
  },

  // Activate a user account (admin only) - approves pending registrations
  activateUser: async (userId: string): Promise<{ message: string; user: User }> => {
    return apiRequest(`/api/admin/users/${userId}/activate`, {
      method: 'PUT',
    });
  },

  // Bootstrap first admin (only works if no admin exists)
  bootstrapAdmin: async (email: string, password: string, name: string): Promise<{ message: string; user: User }> => {
    const params = new URLSearchParams({ email, password, name });
    return apiRequest(`/api/admin/bootstrap?${params}`, {
      method: 'POST',
    });
  },
};

// ============================================================================
// Admin Analytics API - Organization-wide metrics dashboard
// ============================================================================

/**
 * Analytics period information
 */
export interface AnalyticsPeriod {
  start: string;
  end: string;
  days: number;
}

/**
 * Summary statistics for the analytics dashboard
 */
export interface AnalyticsSummary {
  total_documents_generated: number;
  success_rate: number;
  failed_generations: number;
  total_hours_saved: number;
  projects_active: number;
  avg_phase_days: number;
}

/**
 * Document type breakdown with counts and hours saved
 */
export interface DocumentTypeStats {
  type: string;
  count: number;
  hours_saved: number;
}

/**
 * Daily trend data point for charts
 */
export interface DailyTrendPoint {
  date: string;
  generated: number;
  failed: number;
  hours_saved: number;
}

/**
 * Phase velocity statistics
 */
export interface PhaseVelocityStats {
  avg_days: number;
  count: number;
}

/**
 * Top contributor user data
 */
export interface TopContributor {
  user_id: string;
  name: string;
  documents: number;
  hours_saved: number;
}

/**
 * Complete admin analytics response from /api/admin/analytics
 */
export interface AdminAnalyticsData {
  period: AnalyticsPeriod;
  summary: AnalyticsSummary;
  documents_by_type: DocumentTypeStats[];
  daily_trend: DailyTrendPoint[];
  phase_velocity: {
    pre_solicitation: PhaseVelocityStats;
    solicitation: PhaseVelocityStats;
    post_solicitation: PhaseVelocityStats;
  };
  top_contributors: TopContributor[];
}

/**
 * Admin Analytics API functions
 */
export const analyticsApi = {
  /**
   * Get organization-wide analytics for the admin dashboard.
   * Returns summary stats, daily trends, documents by type, phase velocity,
   * and top contributors for the specified time period.
   * 
   * @param days - Number of days to include (7-365, default 30)
   */
  getAnalytics: async (days: number = 30): Promise<AdminAnalyticsData> => {
    return apiRequest(`/api/admin/analytics?days=${days}`);
  },
};

// ============================================================================
// Agent Feedback API
// ============================================================================

/**
 * Feedback submission request
 */
export interface FeedbackSubmitRequest {
  document_id: string;
  section_name?: string;
  agent_name: string;
  rating: 'positive' | 'negative';
  comment?: string;
}

/**
 * Single feedback entry
 */
export interface FeedbackEntry {
  id: string;
  document_id: string;
  section_name?: string;
  agent_name: string;
  rating: string;
  comment?: string;
  user_id: string;
  project_id?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Agent performance stats
 */
export interface AgentPerformanceStats {
  name: string;
  positive_count: number;
  negative_count: number;
  total: number;
  rating_percentage: number;
}

/**
 * Agent performance response
 */
export interface AgentPerformanceResponse {
  agents: AgentPerformanceStats[];
  period_days: number;
  total_feedback: number;
}

/**
 * Agent feedback comments response
 */
export interface AgentFeedbackCommentsResponse {
  comments: FeedbackEntry[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/**
 * Agent Feedback API - for rating AI-generated content
 */
export const feedbackApi = {
  /**
   * Submit feedback (thumbs up/down) for AI-generated content
   */
  submit: async (data: FeedbackSubmitRequest): Promise<{ success: boolean; feedback_id: string }> => {
    return apiRequest('/api/feedback', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get all feedback for a specific document
   */
  getForDocument: async (documentId: string): Promise<{ feedback: FeedbackEntry[] }> => {
    return apiRequest(`/api/documents/${documentId}/feedback`);
  },

  /**
   * Get aggregated agent performance stats (Admin only)
   */
  getAgentPerformance: async (days: number = 30): Promise<AgentPerformanceResponse> => {
    return apiRequest(`/api/admin/agent-performance?days=${days}`);
  },

  /**
   * Get feedback comments for a specific agent (Admin only)
   */
  getAgentComments: async (agentName: string, page: number = 1, limit: number = 20): Promise<AgentFeedbackCommentsResponse> => {
    return apiRequest(`/api/admin/agent-feedback/${encodeURIComponent(agentName)}?page=${page}&limit=${limit}`);
  },
};

// ============================================================================
// Audit Logs API
// ============================================================================

/**
 * Single audit log entry from the backend
 */
export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  user_email?: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  details: string | null;
  ip_address: string | null;
  user_agent: string | null;
  changes: Record<string, unknown> | null;
  created_at: string;
}

/**
 * Response from the audit logs endpoint
 */
export interface AuditLogsResponse {
  total: number;
  limit: number;
  offset: number;
  logs: AuditLogEntry[];
}

export const auditLogsApi = {
  /**
   * Get audit logs with optional filters (Admin only)
   *
   * @param action - Filter by action type (login_success, login_failed, user_registered, etc.)
   * @param entityType - Filter by entity type (user, document, project)
   * @param limit - Maximum number of results (default 100, max 1000)
   * @param offset - Number of results to skip for pagination
   */
  getLogs: async (
    action?: string,
    entityType?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<AuditLogsResponse> => {
    const params = new URLSearchParams();
    if (action) params.append('action', action);
    if (entityType) params.append('entity_type', entityType);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const url = `/api/admin/audit-logs?${params}`;
    return apiRequest<AuditLogsResponse>(url);
  },

  /**
   * Export audit logs as CSV file (Admin only)
   * Downloads the file directly to the browser
   *
   * @param action - Filter by action type
   * @param entityType - Filter by entity type
   */
  exportCsv: async (action?: string, entityType?: string): Promise<void> => {
    const token = getAuthToken();
    const params = new URLSearchParams();
    if (action) params.append('action', action);
    if (entityType) params.append('entity_type', entityType);

    const response = await fetch(`${API_BASE_URL}/api/admin/audit-logs/export?${params}`, {
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearAuthToken();
        window.location.href = '/login';
      }
      const error = await response.text();
      throw new ApiError(response.status, error || 'Export failed');
    }

    // Download the CSV file
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    // Extract filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'audit_logs.csv';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=(.+)/);
      if (match) {
        filename = match[1].replace(/['"]/g, '');
      }
    }

    // Create download link and trigger download
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};

// ============================================================================
// Projects API
// ============================================================================

export interface Project {
  id: string;
  name: string;
  description: string;
  project_type: 'rfp' | 'rfq' | 'rfi' | 'bpa' | 'idiq';
  estimated_value: number;
  contracting_officer_id: string;
  // Nested object with officer details for display
  contracting_officer?: { id: string; name: string };
  program_manager_id?: string;
  // Nested object with program manager details for display
  program_manager?: { id: string; name: string };
  current_phase: string;
  overall_status: string;
  start_date?: string;
  target_completion_date?: string;
  actual_completion_date?: string;
  created_by: string;
  created_at: string;
  updated_at?: string;
}

export interface Phase {
  id: string;
  project_id: string;
  phase_name: string;
  status: string;
  start_date?: string;
  target_completion_date?: string;
  actual_completion_date?: string;
  completion_percentage: number;
  created_at: string;
  updated_at?: string;
}

export interface Document {
  id: string;
  project_id: string;
  phase_id?: string;
  document_name: string;
  document_type?: string;
  file_path?: string;
  status: string;
  uploaded_by: string;
  uploaded_at: string;
  version: number;
}

export interface Step {
  id: string;
  phase_id: string;
  project_id: string;
  step_name: string;
  step_description?: string;
  step_order: number;
  assigned_user_id?: string;
  assigned_user?: {
    name: string;
    email: string;
  };
  status: string;
  deadline?: string;
  completion_date?: string;
  notes?: string;
  attachments?: any;
  requires_approval: boolean;
  approved_by?: string;
  approval_date?: string;
}

export const projectsApi = {
  list: async (): Promise<{ projects: Project[] }> => {
    return apiRequest('/api/projects');
  },

  get: async (id: string): Promise<Project> => {
    return apiRequest(`/api/projects/${id}`);
  },

  create: async (data: {
    name: string;
    description: string;
    project_type: string;
    estimated_value: number;
  }): Promise<{ message: string; project: Project }> => {
    // Backend expects query parameters, not JSON body
    const params = new URLSearchParams({
      name: data.name,
      description: data.description,
      project_type: data.project_type,
      ...(data.estimated_value && { estimated_value: data.estimated_value.toString() }),
    });
    return apiRequest(`/api/projects?${params}`, {
      method: 'POST',
    });
  },

  update: async (id: string, data: Partial<Project>): Promise<{ message: string; project: Project }> => {
    return apiRequest(`/api/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<{ message: string }> => {
    return apiRequest(`/api/projects/${id}`, {
      method: 'DELETE',
    });
  },

  getPhases: async (id: string): Promise<{ phases: Phase[] }> => {
    return apiRequest(`/api/projects/${id}/phases`);
  },

  getDocuments: async (id: string): Promise<{ documents: Document[] }> => {
    return apiRequest(`/api/projects/${id}/documents`);
  },

  updateDocument: async (documentId: string, data: {
    status?: string;
    notes?: string;
    deadline?: string;
    expiration_date?: string;
  }): Promise<{ message: string; document: Document }> => {
    const params = new URLSearchParams();
    if (data.status) params.append('status', data.status);
    if (data.notes !== undefined) params.append('notes', data.notes);
    if (data.deadline) params.append('deadline', data.deadline);
    if (data.expiration_date) params.append('expiration_date', data.expiration_date);

    return apiRequest(`/api/documents/${documentId}?${params}`, {
      method: 'PATCH',
    });
  },

  generateDocument: async (id: string, documentType: string): Promise<{ message: string; task_id?: string }> => {
    return apiRequest(`/api/projects/${id}/generate-document`, {
      method: 'POST',
      body: JSON.stringify({ document_type: documentType }),
    });
  },

  getSteps: async (id: string): Promise<{ steps: Step[] }> => {
    return apiRequest(`/api/projects/${id}/steps`);
  },

  /**
   * Initialize document checklist for a project from templates.
   * 
   * Creates ProjectDocument records based on DocumentChecklistTemplate entries
   * that match the project's contract type. Useful for projects created before
   * auto-initialization was implemented, or to add documents for a specific phase.
   * 
   * @param projectId - UUID of the project
   * @param phase - Optional phase filter (pre_solicitation, solicitation, post_solicitation)
   * @param force - If true, initialize even if documents already exist (will skip duplicates)
   * @returns List of created documents and count of existing documents
   */
  initializeDocuments: async (
    projectId: string,
    phase?: string,
    force?: boolean
  ): Promise<{
    message: string;
    existing_count: number;
    created_count?: number;
    documents?: Document[];
    created?: Document[];
  }> => {
    const params = new URLSearchParams();
    if (phase) params.append('phase', phase);
    if (force) params.append('force', 'true');
    
    const queryString = params.toString();
    const url = `/api/projects/${projectId}/initialize-documents${queryString ? `?${queryString}` : ''}`;
    
    return apiRequest(url, {
      method: 'POST',
    });
  },

  /**
   * Generate multiple documents in batch using AI.
   * Documents are sorted by dependencies and generated sequentially.
   */
  generateBatch: async (
    projectId: string,
    documentIds: string[],
    assumptions: Array<{ id: string; text: string; source: string }>
  ): Promise<{
    message: string;
    task_id: string;
    document_count: number;
    documents: Array<{ id: string; name: string }>;
  }> => {
    return apiRequest(`/api/projects/${projectId}/generate-batch`, {
      method: 'POST',
      body: JSON.stringify({
        document_ids: documentIds,
        assumptions,
      }),
    });
  },
};

// ============================================================================
// Document Generation API
// ============================================================================

export type GenerationStatus = 'not_generated' | 'generating' | 'generated' | 'failed';

export interface GenerationTaskInfo {
  task_id: string;
  document_id?: string;
  document_name?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  result?: {
    content: string;
    quality_score?: number;
    metadata?: Record<string, unknown>;
  };
  error?: string;
  // Batch-specific fields
  completed_documents?: Array<{ id: string; name: string; quality_score?: number }>;
  failed_documents?: Array<{ id: string; name: string; error: string }>;
  current_document?: string;
}

export interface DependencyCheckResult {
  document_id: string;
  document_name: string;
  dependencies_met: boolean;
  missing_dependencies: string[];
  available_dependencies: string[];
  can_generate: boolean;
  estimated_minutes: number;
}

export const documentGenerationApi = {
  /**
   * Start AI content generation for a single document.
   */
  generate: async (
    documentId: string,
    assumptions: Array<{ id: string; text: string; source: string }>,
    additionalContext?: string
  ): Promise<{
    message: string;
    task_id: string;
    document_id: string;
    document_name: string;
  }> => {
    return apiRequest(`/api/documents/${documentId}/generate`, {
      method: 'POST',
      body: JSON.stringify({
        assumptions,
        additional_context: additionalContext,
      }),
    });
  },

  /**
   * Get generation status for a document.
   */
  getDocumentStatus: async (documentId: string): Promise<{
    document_id: string;
    document_name: string;
    generation_status: GenerationStatus;
    generated_content: string | null;
    generated_at: string | null;
    ai_quality_score: number | null;
    task_id: string | null;
    task_info: GenerationTaskInfo | null;
  }> => {
    return apiRequest(`/api/documents/${documentId}/generation-status`);
  },

  /**
   * Get status of a specific generation task (for polling).
   */
  getTaskStatus: async (taskId: string): Promise<GenerationTaskInfo> => {
    return apiRequest(`/api/generation-tasks/${taskId}`);
  },

  /**
   * Save generated content to a document.
   */
  saveContent: async (
    documentId: string,
    content: string,
    qualityScore?: number
  ): Promise<{ message: string; document: Document }> => {
    const params = new URLSearchParams({ content });
    // Use != null to catch both null and undefined
    if (qualityScore != null) {
      params.append('quality_score', qualityScore.toString());
    }
    return apiRequest(`/api/documents/${documentId}/save-generated?${params}`, {
      method: 'POST',
    });
  },

  /**
   * Check if a document's dependencies are met for generation.
   */
  checkDependencies: async (documentId: string): Promise<DependencyCheckResult> => {
    return apiRequest(`/api/documents/${documentId}/check-dependencies`);
  },

  /**
   * Batch export multiple generated documents as a ZIP file.
   * Downloads the ZIP directly to the browser.
   * 
   * @param projectId - The project ID containing the documents
   * @param documentIds - List of document IDs to export
   * @param format - Export format: 'pdf', 'docx', or 'markdown'
   */
  exportBatch: async (
    projectId: string,
    documentIds: string[],
    format: 'pdf' | 'docx' | 'markdown'
  ): Promise<void> => {
    // Get auth token for authorization header
    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/export-generated-batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: JSON.stringify({
        document_ids: documentIds,
        format: format,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Export failed' }));
      throw new Error(error.detail || 'Export failed');
    }

    // Download the ZIP file
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    
    // Extract filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'generated_documents.zip';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=(.+)/);
      if (match) {
        filename = match[1].replace(/['"]/g, '');
      }
    }
    
    // Create download link and trigger download
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  deleteDocument: async (documentId: string): Promise<{ message: string }> => {
    return apiRequest(`/api/documents/${documentId}`, { method: 'DELETE' });
  },

  /**
   * Clear AI-generated content, resetting the document back to pending state.
   * Unlike deleteDocument, this preserves the checklist entry so the document
   * can be regenerated later. Associated artifacts (versions, lineage, reasoning,
   * feedback) are also removed for a clean slate.
   * @param documentId - The document whose generation should be cleared
   */
  clearGeneration: async (documentId: string): Promise<{ message: string; document_id: string; document_name: string }> => {
    return apiRequest(`/api/documents/${documentId}/clear-generation`, { method: 'POST' });
  },
};

export const stepsApi = {
  update: async (stepId: string, data: {
    status?: string;
    completion_date?: string;
    notes?: string;
    assigned_user_id?: string;
  }): Promise<{ message: string; step: Step }> => {
    const params = new URLSearchParams();
    if (data.status) params.append('status', data.status);
    if (data.completion_date) params.append('completion_date', data.completion_date);
    if (data.notes !== undefined) params.append('notes', data.notes);
    if (data.assigned_user_id) params.append('assigned_user_id', data.assigned_user_id);

    return apiRequest(`/api/steps/${stepId}?${params}`, {
      method: 'PATCH',
    });
  },
};

export const phasesApi = {
  update: async (phaseId: string, data: {
    status?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<{ message: string; phase: Phase }> => {
    const params = new URLSearchParams();
    if (data.status) params.append('status', data.status);
    if (data.start_date) params.append('start_date', data.start_date);
    if (data.end_date) params.append('end_date', data.end_date);

    return apiRequest(`/api/phases/${phaseId}?${params}`, {
      method: 'PATCH',
    });
  },

  createDefaultSteps: async (phaseId: string): Promise<{ message: string; created: boolean; steps?: Step[] }> => {
    return apiRequest(`/api/phases/${phaseId}/create-default-steps`, {
      method: 'POST',
    });
  },
};

// ============================================================================
// Phase Transitions API - Gate Enforcement
// ============================================================================

/**
 * Document status for a required document in a phase
 */
export interface DocumentValidationStatus {
  exists: boolean;
  status: string | null;
  approved: boolean;
  document_id: string | null;
}

/**
 * Eligible gatekeeper for a phase transition
 */
export interface EligibleGatekeeper {
  id: string;
  name: string;
  role: string;
}

/**
 * Validation result for phase transition
 */
export interface TransitionValidation {
  can_transition: boolean;
  blocking_issues: string[];
  warnings: string[];
  document_status: Record<string, DocumentValidationStatus>;
  required_gatekeeper: string | null;
  user_can_request: boolean;
  from_phase: string;
  to_phase: string | null;
  eligible_gatekeepers?: EligibleGatekeeper[];
  validation_checks?: string[];
}

/**
 * Phase transition request model
 */
export interface PhaseTransitionRequest {
  id: string;
  project_id: string;
  from_phase: string;
  to_phase: string;
  requested_by: string;
  requested_at: string;
  gatekeeper_id: string | null;
  status: 'pending' | 'approved' | 'rejected';
  validation_results: TransitionValidation | null;
  gatekeeper_comments: string | null;
  resolved_at: string | null;
  // Nested objects for display
  requester?: { id: string; name: string };
  gatekeeper?: { id: string; name: string };
  project?: { id: string; name: string };
}

export const phaseTransitionsApi = {
  /**
   * Validate if a phase transition is allowed
   * Returns document approval status and any blocking issues
   */
  validateTransition: async (phaseId: string): Promise<TransitionValidation> => {
    return apiRequest(`/api/phases/${phaseId}/validate-transition`);
  },

  /**
   * Request approval to transition to the next phase
   * Creates a pending transition request for gatekeeper approval
   */
  requestTransition: async (
    phaseId: string,
    gatekeeperId?: string
  ): Promise<{ message: string; transition_request: PhaseTransitionRequest }> => {
    const params = new URLSearchParams();
    if (gatekeeperId) params.append('gatekeeper_id', gatekeeperId);
    
    return apiRequest(`/api/phases/${phaseId}/request-transition?${params}`, {
      method: 'POST',
    });
  },

  /**
   * Get all pending phase transitions for the current user
   * Returns transitions where user is gatekeeper or eligible to approve
   */
  getPendingTransitions: async (): Promise<{ 
    pending_transitions: PhaseTransitionRequest[]; 
    count: number 
  }> => {
    return apiRequest('/api/phase-transitions/pending');
  },

  /**
   * Approve a phase transition request
   * Updates project phase and marks transition as approved
   */
  approveTransition: async (
    transitionId: string,
    comments?: string
  ): Promise<{ message: string; transition_request: PhaseTransitionRequest }> => {
    const params = new URLSearchParams();
    if (comments) params.append('comments', comments);
    
    return apiRequest(`/api/phase-transitions/${transitionId}/approve?${params}`, {
      method: 'POST',
    });
  },

  /**
   * Reject a phase transition request
   * Requires comments explaining the rejection reason
   */
  rejectTransition: async (
    transitionId: string,
    comments: string
  ): Promise<{ message: string; transition_request: PhaseTransitionRequest }> => {
    const params = new URLSearchParams();
    params.append('comments', comments);
    
    return apiRequest(`/api/phase-transitions/${transitionId}/reject?${params}`, {
      method: 'POST',
    });
  },

  /**
   * Get the history of phase transitions for a project
   */
  getProjectHistory: async (projectId: string): Promise<{ 
    project_id: string;
    transitions: PhaseTransitionRequest[]; 
    count: number 
  }> => {
    return apiRequest(`/api/projects/${projectId}/transition-history`);
  },
};

// ============================================================================
// Approvals API
// ============================================================================

export interface ApprovalAuditLog {
  id: string;
  approval_id: string;
  action: string;
  performed_by: string;
  performed_by_user?: {
    id: string;
    name: string;
    email: string;
    role?: string;
  };
  details?: string;
  timestamp: string;
}

/**
 * Approval routing types for smart document approval routing
 * - manual: User manually selects approvers from a list
 * - auto_co: Automatically route to project's assigned Contracting Officer
 * - default: Route to document's configured default approver
 */
export type ApprovalRouting = 'manual' | 'auto_co' | 'default';

export interface Approval {
  id: string;
  project_document_id: string;
  document_upload_id?: string;
  approver_id: string;
  delegated_from_id?: string;
  approval_status: 'pending' | 'approved' | 'rejected' | 'requested_changes';
  approval_date?: string;
  comments?: string;
  requested_at: string;
  approver?: {
    id: string;
    name: string;
    email: string;
    role?: string;
  };
  delegated_from?: {
    id: string;
    name: string;
    email: string;
  };
  document?: {
    id: string;
    name: string;
    description?: string;
    status: string;
    category: string;
  };
  project?: {
    id: string;
    name: string;
  };
  audit_trail?: ApprovalAuditLog[];
}

export const approvalsApi = {
  /**
   * Request approval for a document using smart routing
   * 
   * @param documentId - The document to request approval for
   * @param approverIds - Optional list of approver IDs (required for manual routing)
   * @param uploadId - Optional upload ID if approving a specific version
   * @param overrideRouting - Optional override for routing type (manual, auto_co, default)
   * @returns Response with routing method used and created approvals
   */
  requestApproval: async (
    documentId: string,
    approverIds?: string[],
    uploadId?: string,
    overrideRouting?: ApprovalRouting
  ): Promise<{ 
    message: string; 
    routing_method: string;
    routing_info: string;
    approvals: Approval[] 
  }> => {
    const params = new URLSearchParams();
    // Only add approver_ids if provided (for manual routing)
    if (approverIds && approverIds.length > 0) {
    approverIds.forEach(id => params.append('approver_ids', id));
    }
    if (uploadId) params.append('upload_id', uploadId);
    // Add routing override if specified
    if (overrideRouting) params.append('override_routing', overrideRouting);

    return apiRequest(`/api/documents/${documentId}/request-approval?${params}`, {
      method: 'POST',
    });
  },

  /**
   * Update approval routing settings for a document
   * 
   * @param documentId - The document to update routing for
   * @param routing - The routing type (manual, auto_co, default)
   * @param defaultApproverId - Required if routing is 'default' - the user ID to route to
   * @returns Updated document info
   */
  updateDocumentRouting: async (
    documentId: string,
    routing: ApprovalRouting,
    defaultApproverId?: string
  ): Promise<{ message: string; document: any }> => {
    const params = new URLSearchParams();
    params.append('approval_routing', routing);
    if (defaultApproverId) params.append('default_approver_id', defaultApproverId);

    return apiRequest(`/api/documents/${documentId}/routing?${params}`, {
      method: 'PATCH',
    });
  },

  approve: async (
    approvalId: string,
    comments?: string
  ): Promise<{ message: string; approval: Approval; document_status: string }> => {
    const params = new URLSearchParams();
    if (comments) params.append('comments', comments);

    return apiRequest(`/api/approvals/${approvalId}/approve?${params}`, {
      method: 'POST',
    });
  },

  reject: async (
    approvalId: string,
    comments: string
  ): Promise<{ message: string; approval: Approval; document_status: string }> => {
    const params = new URLSearchParams();
    params.append('comments', comments);

    return apiRequest(`/api/approvals/${approvalId}/reject?${params}`, {
      method: 'POST',
    });
  },

  getDocumentApprovals: async (documentId: string): Promise<{ approvals: Approval[] }> => {
    return apiRequest(`/api/documents/${documentId}/approvals`);
  },

  getPendingApprovals: async (): Promise<{ approvals: Approval[]; count: number }> => {
    return apiRequest(`/api/approvals/pending`);
  },

  delegate: async (
    approvalId: string,
    delegateToUserId: string,
    reason?: string
  ): Promise<{ message: string; approval: Approval }> => {
    const params = new URLSearchParams();
    params.append('delegate_to_user_id', delegateToUserId);
    if (reason) params.append('reason', reason);

    return apiRequest(`/api/approvals/${approvalId}/delegate?${params}`, {
      method: 'POST',
    });
  },

  getApprovalHistory: async (
    documentId: string
  ): Promise<{ document_id: string; document_name: string; history: Approval[] }> => {
    return apiRequest(`/api/documents/${documentId}/approval-history`);
  },

  getAuditTrail: async (
    approvalId: string
  ): Promise<{ approval_id: string; audit_trail: ApprovalAuditLog[] }> => {
    return apiRequest(`/api/approvals/${approvalId}/audit-trail`);
  },
};

// ============================================================================
// Notifications API
// ============================================================================

export interface Notification {
  id: string;
  user_id: string;
  notification_type: string;
  title: string;
  message: string;
  related_project_id?: string;
  related_document_id?: string;
  is_read: boolean;
  created_at: string;
}

export const notificationsApi = {
  list: async (unreadOnly: boolean = false): Promise<{ notifications: Notification[] }> => {
    const params = unreadOnly ? '?unread_only=true' : '';
    return apiRequest(`/api/notifications${params}`);
  },

  markAsRead: async (notificationId: string): Promise<{ message: string }> => {
    return apiRequest(`/api/notifications/${notificationId}/read`, {
      method: 'PATCH',
    });
  },

  markAllAsRead: async (): Promise<{ message: string }> => {
    return apiRequest('/api/notifications/read-all', {
      method: 'PATCH',
    });
  },

  delete: async (notificationId: string): Promise<{ message: string }> => {
    return apiRequest(`/api/notifications/${notificationId}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// RAG (Document Upload for Generation) API
// ============================================================================

export interface RAGDocument {
  filename: string;
  file_path: string;
  file_size: number;
  upload_date: string;
  file_type: string;
}

export interface RAGUploadResponse {
  message: string;
  filename: string;
  chunks_created: number;
  file_size: number;
}

export interface RAGStats {
  total_chunks: number;
  embedding_dimension: number;
  index_path: string;
  uploaded_documents_count: number;
}

export interface RAGSearchResult {
  content: string;
  metadata: Record<string, string>;
  score: number;
  chunk_id: string;
}

export interface Assumption {
  id: string;
  text: string;
  source: string;
}

export interface ExtractAssumptionsResponse {
  assumptions: Assumption[];
  total: number;
  documents_analyzed: number;
  message: string;
}

export const ragApi = {
  /**
   * Upload a document to the RAG system for document generation
   */
  uploadDocument: async (file: File, category?: string): Promise<RAGUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    // Build URL with category parameter if provided
    let url = `${API_BASE_URL}/api/rag/upload`;
    if (category) {
      url += `?category=${encodeURIComponent(category)}`;
    }

    const token = getAuthToken();
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearAuthToken();
        window.location.href = '/login';
      }
      const error = await response.text();
      throw new Error(`Upload failed: ${error}`);
    }

    return response.json();
  },

  /**
   * List all documents uploaded to the RAG system
   */
  listDocuments: async (): Promise<{ documents: RAGDocument[]; total: number }> => {
    return apiRequest('/api/rag/documents');
  },

  /**
   * Delete a document from the RAG system
   * Removes the document file and its associated chunks from the vector store
   */
  deleteDocument: async (documentId: string): Promise<{
    message: string;
    deleted_chunks: number;
    document_id: string;
  }> => {
    return apiRequest(`/api/rag/documents/${encodeURIComponent(documentId)}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get statistics about the RAG system
   */
  getStats: async (): Promise<RAGStats> => {
    return apiRequest('/api/rag/stats');
  },

  /**
   * Search for relevant document chunks
   */
  search: async (query: string, k: number = 5): Promise<{ query: string; results: RAGSearchResult[]; total: number }> => {
    return apiRequest(`/api/rag/search?query=${encodeURIComponent(query)}&k=${k}`, {
      method: 'POST',
    });
  },

  /**
   * Extract assumptions from uploaded documents using AI
   */
  extractAssumptions: async (): Promise<ExtractAssumptionsResponse> => {
    return apiRequest('/api/extract-assumptions', {
      method: 'POST',
    });
  },

  /**
   * Analyze generation plan before generating (Phase 2+)
   * Provides phase detection, recommendations, and completeness validation
   */
  analyzeGenerationPlan: async (documentNames: string[]): Promise<{
    status: string;
    analysis: {
      phase_detection_enabled: boolean;
      primary_phase?: string;
      confidence?: number;
      mixed_phases?: boolean;
      phase_breakdown?: Record<string, number>;
      document_phase_map?: Record<string, string>;
      warnings?: string[];
      recommendations?: string[];
      phase_info?: {
        name: string;
        description: string;
        required_documents: string[];
        orchestrator: string | null;
      };
      validation?: {
        is_complete: boolean;
        completeness_percentage: number;
        missing_required: string[];
        missing_recommended: string[];
      };
    };
  }> => {
    return apiRequest('/api/analyze-generation-plan', {
      method: 'POST',
      body: JSON.stringify({ document_names: documentNames }),
    });
  },

  /**
   * Generate documents based on selected document types and assumptions
   */
  generateDocuments: async (data: {
    assumptions: Assumption[];
    documents: Array<{
      name: string;
      section?: string;
      category: string;
      linkedAssumptions: string[];
    }>;
  }): Promise<{
    message: string;
    task_id: string;
    documents_requested: number;
  }> => {
    return apiRequest('/api/generate-documents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get generation task status (enhanced with Phase 2 metadata)
   */
  getGenerationStatus: async (taskId: string): Promise<{
    task_id: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    progress: number;
    message?: string;
    result?: {
      sections: Record<string, string>;
      citations: Array<{
        id: number;
        source: string;
        page: number;
        text: string;
      }>;
      agent_metadata?: Record<string, {
        agent: string;
        method: 'specialized_agent' | 'generic_generation';
        agent_info?: any;
      }>;
      phase_info?: {
        primary_phase?: string;
        confidence?: number;
      };
    };
    errors?: string[];
  }> => {
    return apiRequest(`/api/generation-status/${taskId}`);
  },
};

// ============================================================================
// Knowledge API - Project-Scoped Document Management
// ============================================================================

/**
 * KnowledgeDocument represents a document in a project's knowledge base.
 * These documents are indexed into RAG and used for AI-powered generation.
 * 
 * Each document is associated with:
 * - A specific project (project_id)
 * - A procurement phase (phase)
 * - A purpose/category (purpose)
 * - RAG indexing status
 */
export interface KnowledgeDocument {
  id: string;
  project_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  phase?: string;
  purpose?: string;
  upload_date: string;
  uploaded_by: string;
  rag_indexed: boolean;
  chunk_count?: number;
  chunk_ids?: string[];
}

export interface KnowledgeUploadResponse {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunks_created: number;
  chunk_ids: string[];
  message: string;
}

/**
 * Knowledge document statistics for a project.
 * 
 * Used for summary displays and filter badges showing
 * document counts by phase and purpose.
 */
export interface KnowledgeStats {
  /** Total number of knowledge documents in the project */
  total: number;
  /** Number of documents successfully indexed in RAG */
  indexed_count: number;
  /** Counts by procurement phase */
  by_phase: {
    pre_solicitation: number;
    solicitation: number;
    post_solicitation: number;
    unassigned: number;
  };
  /** Counts by document purpose/category */
  by_purpose: {
    regulation: number;
    template: number;
    market_research: number;
    prior_award: number;
    strategy_memo: number;
    other: number;
  };
}

export const knowledgeApi = {
  /**
   * Get all knowledge documents for a specific project
   * Returns documents filtered by project_id from the RAG system
   */
  getProjectKnowledge: async (projectId: string): Promise<{ 
    documents: KnowledgeDocument[]; 
    total: number 
  }> => {
    return apiRequest(`/api/projects/${projectId}/knowledge`);
  },

  /**
   * Upload a document to a project's knowledge base
   * The document is tagged with phase and purpose, then indexed into RAG
   * 
   * @param projectId - The project to associate this document with
   * @param file - The file to upload
   * @param phase - The procurement phase (pre_solicitation, solicitation, post_solicitation)
   * @param purpose - The document purpose (regulation, template, market_research, prior_award, strategy_memo)
   */
  uploadToProject: async (
    projectId: string, 
    file: File, 
    phase: string, 
    purpose: string
  ): Promise<KnowledgeUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams({
      phase,
      purpose,
    });

    const token = getAuthToken();
    const response = await fetch(
      `${API_BASE_URL}/api/projects/${projectId}/knowledge/upload?${params}`, 
      {
        method: 'POST',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: formData,
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        clearAuthToken();
        window.location.href = '/login';
      }
      const error = await response.text();
      throw new Error(`Upload failed: ${error}`);
    }

    return response.json();
  },

  /**
   * Delete a document from a project's knowledge base
   * Also removes associated chunks from the RAG vector store
   */
  deleteFromProject: async (
    projectId: string, 
    documentId: string
  ): Promise<{
    message: string;
    deleted_chunks: number;
  }> => {
    return apiRequest(`/api/projects/${projectId}/knowledge/${documentId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get knowledge documents filtered by phase within a project
   */
  getByPhase: async (
    projectId: string, 
    phase: string
  ): Promise<{ documents: KnowledgeDocument[] }> => {
    return apiRequest(`/api/projects/${projectId}/knowledge?phase=${phase}`);
  },

  /**
   * Get knowledge documents filtered by purpose within a project
   */
  getByPurpose: async (
    projectId: string, 
    purpose: string
  ): Promise<{ documents: KnowledgeDocument[] }> => {
    return apiRequest(`/api/projects/${projectId}/knowledge?purpose=${purpose}`);
  },

  /**
   * Get knowledge document statistics for a project
   * 
   * Returns counts grouped by phase and purpose for summary displays
   * and filter badges throughout the UI.
   * 
   * @param projectId - The project to get stats for
   * @returns Stats object with total, by_phase, by_purpose counts
   */
  getStats: async (projectId: string): Promise<KnowledgeStats> => {
    return apiRequest(`/api/projects/${projectId}/knowledge/stats`);
  },
};

// ============================================================================
// Lineage API - Document Source Tracking and Explainability
// ============================================================================

/**
 * Influence types that describe how a source document affected generation.
 * 
 * - context: General context provided to the AI
 * - template: Used as a structural template
 * - regulation: FAR/DFARS or policy reference
 * - data_source: Primary data (market research, prior awards)
 * - reference: Cited in the generated content
 */
export type InfluenceType = 'context' | 'template' | 'regulation' | 'data_source' | 'reference';

/**
 * Represents a lineage relationship between source and derived documents.
 * Used to track which uploaded documents influenced AI-generated content.
 */
export interface DocumentLineage {
  id: string;
  source_document_id?: string;
  source_filename?: string;
  derived_document_id: string;
  influence_type: InfluenceType;
  relevance_score: number;
  chunk_ids_used: string[];
  chunks_used_count: number;
  context?: string;
  created_at: string;
  source_document?: {
    id: string;
    document_name: string;
    category: string;
  };
}

/**
 * Request body for creating a lineage record
 */
export interface LineageRecordRequest {
  source_document_id?: string;
  source_filename?: string;
  influence_type?: InfluenceType;
  relevance_score?: number;
  chunk_ids_used?: string[];
  context?: string;
}

/**
 * Response from the lineage endpoint for a document
 */
export interface DocumentLineageResponse {
  document_id: string;
  sources: DocumentLineage[];
  derived_from_this: DocumentLineage[];
  total_sources: number;
  total_derived: number;
}

// ============================================================================
// Phase 3A: Advanced Document Lifecycle Types
// ============================================================================

/**
 * Timeline event types for document lifecycle tracking
 */
export type TimelineEventType = 'uploaded' | 'indexed' | 'generated' | 'used_as_source';

/**
 * Represents a single event in a document's lifecycle timeline
 */
export interface TimelineEvent {
  type: TimelineEventType;
  timestamp: string;
  actor?: string;
  details: Record<string, unknown>;
}

/**
 * Response from the document timeline endpoint
 */
export interface DocumentTimelineResponse {
  document_id: string;
  document_name: string;
  events: TimelineEvent[];
  total_events: number;
}

/**
 * Node in the influence graph visualization
 */
export interface GraphNode {
  id: string;
  label: string;
  type: 'source' | 'generated';
  metadata: Record<string, unknown>;
}

/**
 * Edge (relationship) in the influence graph visualization
 */
export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  chunks_count: number;
  influence_type: string;
}

/**
 * Response from the influence graph endpoint
 */
export interface InfluenceGraphResponse {
  document_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  node_count: number;
  edge_count: number;
}

/**
 * Represents a single RAG chunk with content and metadata
 * Used for chunk-level traceability in the lineage view
 */
export interface ChunkContent {
  chunk_id: string;
  content: string;
  source_document: string;
  original_filename?: string;
  chunk_index: number;
  total_chunks: number;
  project_id?: string;
  phase?: string;
  purpose?: string;
  metadata: Record<string, unknown>;
}

/**
 * Response from the chunks endpoint
 */
export interface ChunksResponse {
  chunks: ChunkContent[];
  requested_count: number;
  found_count: number;
}

export const lineageApi = {
  /**
   * Get lineage information for a document
   * 
   * For AI-generated documents: Returns source documents that influenced generation
   * For uploaded documents: Returns documents that were derived from this source
   */
  getLineage: async (documentId: string): Promise<DocumentLineageResponse> => {
    return apiRequest(`/api/documents/${documentId}/lineage`);
  },

  /**
   * Record a single lineage relationship
   * Called after AI generation to track which sources were used
   */
  recordLineage: async (
    derivedDocumentId: string,
    source: LineageRecordRequest
  ): Promise<{
    id: string;
    message: string;
    derived_document_id: string;
    source: string;
  }> => {
    return apiRequest(`/api/documents/${derivedDocumentId}/lineage`, {
      method: 'POST',
      body: JSON.stringify(source),
    });
  },

  /**
   * Record multiple lineage relationships at once
   * More efficient for bulk lineage recording after AI generation
   */
  recordBatchLineage: async (
    derivedDocumentId: string,
    sources: LineageRecordRequest[]
  ): Promise<{
    message: string;
    derived_document_id: string;
    lineage_ids: string[];
    sources_count: number;
  }> => {
    return apiRequest(`/api/documents/${derivedDocumentId}/lineage/batch`, {
      method: 'POST',
      body: JSON.stringify(sources),
    });
  },

  // ============================================================================
  // Phase 3A: Advanced Document Lifecycle API Methods
  // ============================================================================

  /**
   * Get lifecycle timeline events for a document
   * 
   * Returns chronological events: upload, indexing, generation, usage
   * Useful for audit trails and compliance documentation
   */
  getTimeline: async (documentId: string): Promise<DocumentTimelineResponse> => {
    return apiRequest(`/api/documents/${documentId}/timeline`);
  },

  /**
   * Get influence graph data for visualization
   * 
   * Returns nodes (documents) and edges (relationships) for rendering
   * an interactive graph showing document influence chains
   */
  getInfluenceGraph: async (documentId: string): Promise<InfluenceGraphResponse> => {
    return apiRequest(`/api/documents/${documentId}/influence-graph`);
  },

  /**
   * Get chunk content by IDs for traceability view
   * 
   * Retrieves the actual content of RAG chunks that influenced generation
   * Limited to 50 chunks per request
   */
  getChunkContent: async (chunkIds: string[]): Promise<ChunksResponse> => {
    return apiRequest(`/api/chunks?ids=${chunkIds.join(',')}`);
  },
};

// ============================================================================
// Copilot AI Assistant API
// ============================================================================

// Type definitions for Copilot actions
// fix_issue: AI-powered contextual fix for placeholders like TBD
// fix_hallucination: AI-powered fix for potentially unsourced claims
// fix_compliance: AI-powered fix to add FAR/DFARS citations
// fix_vague_language: AI-powered fix to replace vague terms with specific language
export type CopilotAction = 'answer' | 'rewrite' | 'expand' | 'summarize' | 'citations' | 'compliance' | 'custom' | 'web_search' | 'fix_issue' | 'fix_hallucination' | 'fix_compliance' | 'fix_vague_language';

// Type definitions for web search types
export type WebSearchType = 'general' | 'vendor' | 'pricing' | 'awards' | 'small_business';

export interface CopilotAssistRequest {
  action: CopilotAction;
  selected_text: string;
  context?: string;
  custom_prompt?: string;
  section_name?: string;
  search_type?: WebSearchType;  // For web_search action
}

export interface CopilotAssistResponse {
  action: string;
  result: string;
  selected_text: string;
  section: string;
  tokens_used?: number;
  search_type?: string;  // Returned for web_search action
}

export const copilotApi = {
  /**
   * Request AI assistance for document editing
   * 
   * Available actions:
   * - answer: Answer questions about the highlighted text
   * - rewrite: Improve/rewrite the selected text
   * - expand: Elaborate on the selected content
   * - summarize: Summarize the selected text
   * - citations: Add FAR/DFARS citations to the selection
   * - compliance: Check selection for compliance issues
   * - custom: Execute custom user prompt on selection
   * - web_search: Search the web for information about the selected text
   */
  assist: async (
    action: CopilotAction,
    selectedText: string,
    context?: string,
    sectionName?: string,
    customPrompt?: string,
    searchType?: WebSearchType
  ): Promise<CopilotAssistResponse> => {
    return apiRequest('/api/copilot/assist', {
      method: 'POST',
      body: JSON.stringify({
        action,
        selected_text: selectedText,
        context: context || '',
        section_name: sectionName || '',
        custom_prompt: customPrompt,
        search_type: searchType,
      }),
    });
  },
};

// ============================================================================
// WebSocket Connection for Real-time Updates
// ============================================================================

export interface WebSocketMessage {
  type: 'generation_started' | 'progress' | 'generation_complete' | 'error' | 'phase_update';
  message?: string;
  percentage?: number;
  document_type?: string;
  document_url?: string;
  phase?: string;
  status?: string;
}

export function createWebSocket(projectId: string): WebSocket {
  const ws = new WebSocket(`${WS_BASE_URL}/ws/${projectId}`);
  return ws;
}

// ============================================================================
// Quality Analysis API
// ============================================================================

/**
 * Quality analysis breakdown for each category
 * Matches the backend QualityAgent's 5 evaluation categories
 */
export interface QualityBreakdown {
  hallucination: {
    score: number;
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
    issues: string[];
    suggestions: string[];
    // Examples of suspicious text snippets flagged as potential hallucinations
    // These are used to create individual hallucination issues in the sidebar
    examples?: string[];
  };
  vague_language: {
    score: number;
    count: number;
    issues: string[];
    suggestions: string[];
  };
  citations: {
    score: number;
    valid: number;
    invalid: number;
    issues: string[];
    suggestions: string[];
  };
  compliance: {
    score: number;
    level: 'COMPLIANT' | 'MINOR ISSUES' | 'MAJOR ISSUES';
    issues: string[];
    suggestions: string[];
  };
  completeness: {
    score: number;
    word_count: number;
    paragraph_count: number;
    issues: string[];
    suggestions: string[];
  };
}

/**
 * Full quality analysis response from the backend QualityAgent
 */
export interface QualityAnalysisResponse {
  score: number;
  grade: string;
  breakdown: QualityBreakdown;
  issues: string[];
  suggestions: string[];
  weights: {
    hallucination: number;
    vague_language: number;
    citations: number;
    compliance: number;
    completeness: number;
  };
}

/**
 * Quality Analysis API
 * 
 * Provides comprehensive document quality evaluation using the backend QualityAgent.
 * Returns scores for 5 categories: Hallucination, Vague Language, Citations, Compliance, Completeness.
 */
export const qualityApi = {
  /**
   * Analyze document content for quality issues
   * 
   * @param content - The document content to analyze
   * @param sectionName - Name of the section being analyzed (for context)
   * @param projectInfo - Optional project information for cross-validation
   * @returns Comprehensive quality analysis with all 5 categories
   */
  analyze: async (
    content: string,
    sectionName: string = 'Document',
    projectInfo: Record<string, unknown> = {}
  ): Promise<QualityAnalysisResponse> => {
    return apiRequest('/api/quality/analyze', {
      method: 'POST',
      body: JSON.stringify({
        content,
        section_name: sectionName,
        project_info: projectInfo,
      }),
    });
  },
};

// ============================================================================
// Export API
// ============================================================================

export const exportApi = {
  /**
   * Download compliance report as PDF
   *
   * @param complianceAnalysis - The compliance analysis data
   * @returns Blob of the PDF file
   */
  downloadComplianceReport: async (complianceAnalysis: Record<string, unknown>): Promise<Blob> => {
    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/export/compliance-report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ compliance_analysis: complianceAnalysis }),
    });

    if (!response.ok) {
      throw new Error('Failed to generate compliance report');
    }

    return response.blob();
  },
};

// ============================================================================
// Document Version API
// ============================================================================

/**
 * Represents a version snapshot of document content
 */
export interface DocumentVersion {
  id: string;
  project_document_id: string;
  version_number: number;
  is_current: boolean;
  content: string;
  sections_json?: string;
  message?: string;
  author?: string;
  created_by?: string;
  created_at: string;
  ai_quality_score?: number;
  word_count?: number;
}

/**
 * Paginated response for version listing
 */
export interface DocumentVersionsResponse {
  versions: DocumentVersion[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Version History API for managing document content snapshots
 */
export const versionApi = {
  /**
   * Create a new version snapshot for a document
   *
   * @param documentId - The document ID
   * @param data - Version data including content and optional metadata
   * @returns The created version
   */
  create: async (
    documentId: string,
    data: {
      content: string;
      sections?: Record<string, string>;
      message?: string;
      author?: string;
    }
  ): Promise<DocumentVersion> => {
    return apiRequest(`/api/documents/${documentId}/versions`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get paginated version history for a document
   *
   * @param documentId - The document ID
   * @param limit - Maximum versions to return (default 50)
   * @param offset - Offset for pagination (default 0)
   * @returns Paginated list of versions
   */
  list: async (
    documentId: string,
    limit = 50,
    offset = 0
  ): Promise<DocumentVersionsResponse> => {
    return apiRequest(`/api/documents/${documentId}/versions?limit=${limit}&offset=${offset}`);
  },

  /**
   * Get a specific version by ID
   *
   * @param documentId - The document ID
   * @param versionId - The version ID
   * @returns The version details including content
   */
  get: async (documentId: string, versionId: string): Promise<DocumentVersion> => {
    return apiRequest(`/api/documents/${documentId}/versions/${versionId}`);
  },

  /**
   * Restore document to a previous version
   *
   * Creates a new version with the restored content and updates the document.
   *
   * @param documentId - The document ID
   * @param versionId - The version ID to restore
   * @returns The newly created version (with restored content)
   */
  restore: async (documentId: string, versionId: string): Promise<DocumentVersion> => {
    return apiRequest(`/api/documents/${documentId}/versions/${versionId}/restore`, {
      method: 'POST',
    });
  },
};

// ============================================================================
// Reasoning API - Chain-of-Thought Display
// ============================================================================

/**
 * Single reasoning step in the generation timeline
 */
export interface ReasoningStep {
  step_type: string;
  description: string;
  timestamp: string;
  duration_ms: number;
  details?: Record<string, any>;
}

/**
 * Complete reasoning data for a document generation
 */
export interface ReasoningData {
  id: string;
  document_id: string;
  agent_name: string;
  model_used: string;
  temperature?: number;
  input_tokens: number;
  output_tokens: number;
  total_cost_usd: number;
  rag_chunks_retrieved: number;
  rag_chunk_ids: string[];
  rag_query?: string;
  rag_phase_filter?: string;
  confidence_score?: number;
  generation_time_ms: number;
  reasoning_steps: ReasoningStep[];
  created_at: string;
  // Debug fields (admin only)
  full_prompt?: string;
  full_response?: string;
  // When no data exists
  message?: string;
  document_name?: string;
}

/**
 * Response from reasoning history endpoint
 */
export interface ReasoningHistoryResponse {
  document_id: string;
  document_name: string;
  total: number;
  records: ReasoningData[];
}

/**
 * Reasoning API - Chain-of-Thought transparency for AI document generation
 *
 * Provides insight into:
 * - Token usage and cost
 * - RAG chunks used as sources
 * - Step-by-step reasoning timeline
 * - Debug data for admins
 */
export const reasoningApi = {
  /**
   * Get reasoning data for a document's most recent generation
   *
   * @param documentId - The document ID
   * @param includeDebug - Request full prompt/response (admin only)
   * @returns Reasoning data or message if none available
   */
  get: async (documentId: string, includeDebug = false): Promise<ReasoningData> => {
    return apiRequest(`/api/documents/${documentId}/reasoning?include_debug=${includeDebug}`);
  },

  /**
   * Get reasoning history for all generations of a document
   *
   * @param documentId - The document ID
   * @param limit - Maximum records to return (1-50)
   * @returns List of reasoning records
   */
  getHistory: async (documentId: string, limit = 10): Promise<ReasoningHistoryResponse> => {
    return apiRequest(`/api/documents/${documentId}/reasoning/history?limit=${limit}`);
  },
};

// ============================================================================
// Export all APIs
// ============================================================================

export default {
  auth: authApi,
  projects: projectsApi,
  steps: stepsApi,
  phases: phasesApi,
  phaseTransitions: phaseTransitionsApi,
  approvals: approvalsApi,
  notifications: notificationsApi,
  export: exportApi,
  rag: ragApi,
  knowledge: knowledgeApi,
  lineage: lineageApi,
  copilot: copilotApi,
  quality: qualityApi,
  version: versionApi,
  reasoning: reasoningApi,
  createWebSocket,
};
