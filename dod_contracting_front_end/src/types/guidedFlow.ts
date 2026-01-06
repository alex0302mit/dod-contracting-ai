/**
 * Guided Flow Type Definitions
 *
 * DocuSign-style guided completion flow for DoD contracting documents.
 * Supports field-by-field completion with:
 * - AI-powered suggestions
 * - Field-level permissions
 * - Conditional logic
 * - Real-time collaboration
 * - Auto-save on field completion
 */

import { z } from 'zod';

// ============================================================================
// Enums & Constants
// ============================================================================

/**
 * Supported field types for guided flow
 */
export type FieldType =
  | "checkbox"    // Boolean checkbox
  | "text"        // Single-line text input
  | "textarea"    // Multi-line text input
  | "date"        // Date picker
  | "signature"   // Signature block (name + title + date)
  | "select";     // Dropdown select

/**
 * Field completion status
 */
export type FieldStatus =
  | "pending"     // Not yet filled
  | "complete"    // Validated and complete
  | "invalid"     // Has validation errors
  | "locked"      // Being edited by another user
  | "hidden";     // Hidden by conditional logic

/**
 * Permission levels for field access
 */
export type PermissionLevel =
  | "none"        // Cannot view or edit
  | "view"        // Can view but not edit
  | "edit"        // Can edit (optional)
  | "required";   // Must edit (required)

/**
 * User roles for permission checking
 */
export type UserRole =
  | "admin"
  | "contracting_officer"
  | "contributor"
  | "viewer";

/**
 * Conditional operators for field visibility
 */
export type ConditionalOperator =
  | "equals"
  | "notEquals"
  | "contains"
  | "isEmpty"
  | "isNotEmpty";

/**
 * Animation speed preferences
 */
export type AnimationSpeed = "instant" | "fast" | "medium" | "slow";

// ============================================================================
// Core Interfaces
// ============================================================================

/**
 * User information for permissions and collaboration
 */
export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  companyName?: string;
}

/**
 * Field-level permissions
 */
export interface FieldPermissions {
  /** Role-based permissions (default for all users with this role) */
  roles: Record<UserRole, PermissionLevel>;

  /** User-specific overrides (takes precedence over role permissions) */
  users?: Record<string, PermissionLevel>;
}

/**
 * Conditional visibility rules for a field
 */
export interface ConditionalRule {
  /** ID of the field that controls visibility */
  fieldId: string;

  /** Comparison operator */
  operator: ConditionalOperator;

  /** Expected value (not needed for isEmpty/isNotEmpty) */
  value?: any;
}

/**
 * AI assistance configuration for a field
 */
export interface AIAssistConfig {
  /** Whether AI assistance is enabled for this field */
  enabled: boolean;

  /** Suggest value from user's previous contracts */
  suggestFromPrevious?: boolean;

  /** Suggest value from RAG knowledge base */
  suggestFromRAG?: boolean;

  /** Custom prompt for AI suggestion */
  customPrompt?: string;
}

/**
 * Field validation configuration
 */
export interface FieldValidation {
  /** Zod schema for validation (optional) */
  zodSchema?: z.ZodType;

  /** Regex pattern for validation */
  pattern?: RegExp;

  /** Minimum value (for numbers) or length (for strings) */
  min?: number;

  /** Maximum value (for numbers) or length (for strings) */
  max?: number;

  /** Custom validation error message */
  message?: string;
}

/**
 * A single field in the guided flow
 */
export interface GuidedField {
  /** Unique field identifier */
  id: string;

  /** ID of the section this field belongs to */
  sectionId: string;

  /** Display label for the field */
  label: string;

  /** Field input type */
  type: FieldType;

  /** Whether this field is required */
  required: boolean;

  /** Helper text explaining what to enter */
  helperText?: string;

  /** Current completion status */
  status: FieldStatus;

  /** React Hook Form field name (nested path, e.g., "k2.uei") */
  rfhName: string;

  /** Order in the guided flow (lower = earlier) */
  order: number;

  /** DOM selector for highlighting (e.g., "[data-field-id='k2-uei']") */
  selector?: string;

  /** Permissions controlling who can view/edit */
  permissions: FieldPermissions;

  /** Conditional visibility rule */
  conditionalOn?: ConditionalRule;

  /** Validation configuration */
  validation?: FieldValidation;

  /** AI assistance configuration */
  aiAssist?: AIAssistConfig;

  /** Options for select fields */
  options?: Array<{ label: string; value: string }>;
}

/**
 * A section grouping multiple fields
 */
export interface GuidedSection {
  /** Unique section identifier */
  id: string;

  /** Display name (e.g., "K.2 SAM.GOV REGISTRATION") */
  name: string;

  /** Optional description */
  description?: string;

  /** Order in the document (lower = earlier) */
  order: number;

  /** Fields in this section */
  fields: GuidedField[];

  /** Section-level permissions (optional, defaults to field permissions) */
  permissions?: {
    roles: Record<UserRole, PermissionLevel>;
  };
}

/**
 * Auto-save configuration
 */
export interface AutoSaveConfig {
  /** Whether auto-save is enabled */
  enabled: boolean;

  /** Save after each field completion */
  onFieldComplete: boolean;

  /** Optional debounce delay in milliseconds */
  debounceMs?: number;
}

/**
 * Animation configuration
 */
export interface AnimationConfig {
  /** Animation speed (user chose "fast") */
  speed: AnimationSpeed;

  /** Duration of highlight animation in ms */
  highlightDuration: number;

  /** Duration of scroll animation in ms */
  scrollDuration: number;
}

/**
 * Complete guided document structure
 */
export interface GuidedDocument {
  /** Unique document identifier */
  id: string;

  /** Document name/title */
  name: string;

  /** Optional description */
  description?: string;

  /** Sections in this document */
  sections: GuidedSection[];

  /** Auto-save configuration */
  autoSave: AutoSaveConfig;

  /** Animation configuration */
  animations: AnimationConfig;
}

/**
 * Runtime field value with metadata
 */
export interface GuidedFieldValue {
  /** Field identifier */
  fieldId: string;

  /** Current value */
  value: any;

  /** Current status */
  status: FieldStatus;

  /** Timestamp of last update */
  updatedAt: string;

  /** User ID who last updated */
  updatedBy: string;

  /** Whether value was suggested by AI */
  aiSuggested?: boolean;
}

/**
 * AI suggestion response from backend
 */
export interface AISuggestion {
  /** Suggested value */
  value: any;

  /** Source of suggestion (e.g., "previous_contract", "rag_knowledge") */
  source: string;

  /** Confidence score (0-1) */
  confidence: number;

  /** Optional explanation */
  explanation?: string;

  /** Contract ID if from previous contract */
  contractId?: string;
}

/**
 * Collaborator presence information
 */
export interface Collaborator {
  /** User ID */
  userId: string;

  /** User name */
  userName: string;

  /** Field they're currently editing (null if none) */
  currentFieldId: string | null;

  /** Timestamp of last activity */
  lastActiveAt: string;
}

/**
 * Overall guided flow state
 */
export interface GuidedFlowState {
  /** The document structure */
  document: GuidedDocument;

  /** Currently focused field ID */
  currentFieldId: string | null;

  /** All field values */
  fieldValues: Record<string, GuidedFieldValue>;

  /** Current user */
  currentUser: User;

  /** Whether initial data is loading */
  isLoading: boolean;

  /** Whether auto-save is in progress */
  isSaving: boolean;

  /** Active collaborators */
  collaborators: Collaborator[];
}

/**
 * Progress calculation result
 */
export interface ProgressInfo {
  /** Number of completed required fields */
  completed: number;

  /** Total number of required fields (visible & editable) */
  total: number;

  /** Completion percentage (0-100) */
  percentage: number;

  /** Number of optional fields completed */
  optionalCompleted?: number;

  /** Total number of optional fields */
  optionalTotal?: number;
}

/**
 * WebSocket message types
 */
export interface WSFieldUpdateMessage {
  event: 'field_update';
  documentId: string;
  fieldId: string;
  value: any;
  status: FieldStatus;
  userId: string;
  timestamp: string;
}

export interface WSCollaboratorJoinedMessage {
  event: 'collaborator_joined';
  documentId: string;
  collaborator: Collaborator;
}

export interface WSCollaboratorLeftMessage {
  event: 'collaborator_left';
  documentId: string;
  userId: string;
}

export interface WSFieldLockedMessage {
  event: 'field_locked';
  documentId: string;
  fieldId: string;
  userId: string;
  userName: string;
}

export type WSMessage =
  | WSFieldUpdateMessage
  | WSCollaboratorJoinedMessage
  | WSCollaboratorLeftMessage
  | WSFieldLockedMessage;

// ============================================================================
// Helper Types
// ============================================================================

/**
 * Navigation direction
 */
export type NavigationDirection = 'next' | 'previous' | 'specific';

/**
 * Navigation result
 */
export interface NavigationResult {
  /** Success status */
  success: boolean;

  /** New current field ID (if successful) */
  newFieldId?: string;

  /** Error message (if failed) */
  error?: string;

  /** Whether this is the last field */
  isLastField?: boolean;
}

/**
 * Save operation result
 */
export interface SaveResult {
  /** Success status */
  success: boolean;

  /** Saved document ID */
  documentId?: string;

  /** Error message (if failed) */
  error?: string;

  /** Timestamp of save */
  savedAt?: string;
}
