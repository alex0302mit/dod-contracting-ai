/**
 * Type Definitions for Quick Generate Tab
 * 
 * This file contains all shared TypeScript interfaces and types used
 * throughout the Quick Generate wizard components.
 * 
 * Dependencies:
 * - Used by QuickGenerateTab, QuickUploadStep, ExtractionProgress, QuickReviewStep
 */

// ============================================
// Step Management Types
// ============================================

/**
 * Enum representing all possible steps in the Quick Generate wizard.
 * The wizard progresses through these steps sequentially.
 */
export type QuickGenerateStep = 
  | 'UPLOAD'        // Step 1: Upload source documents
  | 'EXTRACTING'    // Step 2: AI extraction in progress
  | 'ASSUMPTIONS'   // Step 3: Review extracted assumptions
  | 'TRACEABILITY'  // Step 4: View requirement mappings
  | 'SELECTION'     // Step 5: Select documents to generate
  | 'GENERATING'    // Step 6a: Generation in progress
  | 'REVIEW';       // Step 6b: Review generated content

/**
 * Configuration for each step in the wizard stepper UI.
 * Used to render the progress indicator at the top of the wizard.
 */
export interface StepConfig {
  // The step identifier
  step: QuickGenerateStep;
  // Display number shown to user (1-6)
  number: number;
  // Short title for the step
  title: string;
  // Longer description shown below title
  description: string;
}

/**
 * Step configuration array for rendering the progress stepper.
 * Note: EXTRACTING and GENERATING are sub-states, not shown as separate steps.
 */
export const WIZARD_STEPS: StepConfig[] = [
  { step: 'UPLOAD', number: 1, title: 'Upload', description: 'Add source documents' },
  { step: 'ASSUMPTIONS', number: 2, title: 'Assumptions', description: 'Review extracted data' },
  { step: 'TRACEABILITY', number: 3, title: 'Traceability', description: 'Map to requirements' },
  { step: 'SELECTION', number: 4, title: 'Documents', description: 'Select output types' },
  { step: 'REVIEW', number: 5, title: 'Generate', description: 'Review & export' },
];

// ============================================
// Document & Upload Types
// ============================================

/**
 * Category types for organizing uploaded documents.
 * These map to the backend's document classification system.
 */
export type DocumentCategory = 
  | 'strategy'        // Acquisition strategy documents
  | 'requirements'    // PWS, SOW, requirements docs
  | 'market_research' // Market research reports
  | 'templates';      // Reference templates

/**
 * Configuration for document category display.
 * Contains UI styling and labels for each category.
 */
export interface CategoryConfig {
  // Category identifier
  key: DocumentCategory;
  // Human-readable label
  label: string;
  // Tailwind CSS color class for badges
  color: string;
  // Background gradient for category cards
  bgGradient: string;
  // Brief description of what belongs in this category
  description: string;
}

/**
 * Category configuration map for UI display.
 */
export const CATEGORY_CONFIG: Record<DocumentCategory, CategoryConfig> = {
  strategy: {
    key: 'strategy',
    label: 'Acquisition Strategy',
    color: 'bg-blue-500',
    bgGradient: 'from-blue-500 to-blue-600',
    description: 'Strategy and planning documents'
  },
  requirements: {
    key: 'requirements',
    label: 'Requirements',
    color: 'bg-violet-500',
    bgGradient: 'from-violet-500 to-violet-600',
    description: 'PWS, SOW, and technical requirements'
  },
  market_research: {
    key: 'market_research',
    label: 'Market Research',
    color: 'bg-emerald-500',
    bgGradient: 'from-emerald-500 to-emerald-600',
    description: 'Market analysis and vendor research'
  },
  templates: {
    key: 'templates',
    label: 'Templates',
    color: 'bg-amber-500',
    bgGradient: 'from-amber-500 to-amber-600',
    description: 'Reference templates and forms'
  }
};

/**
 * Represents a file that has been uploaded to the system.
 * Tracks upload status and backend document ID.
 */
export interface UploadedFile {
  // Unique client-side ID for tracking
  id: string;
  // Original filename
  filename: string;
  // File size in bytes
  size: number;
  // MIME type of the file
  type: string;
  // Category assigned to the document
  category: DocumentCategory;
  // Upload status
  status: 'uploading' | 'processing' | 'ready' | 'error';
  // Error message if status is 'error'
  error?: string;
  // Backend document ID after successful upload
  documentId?: string;
  // Upload progress percentage (0-100)
  progress?: number;
}

// ============================================
// Assumption Types
// ============================================

/**
 * Represents an assumption extracted from uploaded documents.
 * These are used to inform document generation.
 */
export interface Assumption {
  // Unique identifier (e.g., "a1", "a2")
  id: string;
  // The assumption text
  text: string;
  // Source document or reference
  source: string;
  // Review status
  status?: 'approved' | 'needs_review';
}

// ============================================
// Document Generation Types
// ============================================

/**
 * Represents a document type that can be generated.
 * Based on the Uniform Contract Format (UCF) sections.
 */
export interface GeneratedDocument {
  // Document name (e.g., "Section A - Solicitation/Contract Form")
  name: string;
  // Whether this document is required, recommended, or optional
  category: 'required' | 'recommended' | 'optional';
  // Brief description of the document
  description: string;
  // Justification for including this document
  justification: string;
  // IDs of assumptions linked to this document
  linkedAssumptions: string[];
  // UCF section letter if applicable
  section?: string;
}

/**
 * Result of document generation containing the generated content.
 */
export interface GeneratedSection {
  // Section name/title
  name: string;
  // Generated content (HTML or Markdown)
  content: string;
  // Quality score (0-100)
  qualityScore?: number;
  // Citations used in generation
  citations?: Citation[];
}

/**
 * Citation reference used in generated content.
 */
export interface Citation {
  // Citation ID
  id: number;
  // Source reference (e.g., "FAR 15.304")
  source: string;
  // Page number if applicable
  page?: number;
  // Cited text excerpt
  text: string;
}

// ============================================
// Wizard State Types
// ============================================

/**
 * Complete state object for the Quick Generate wizard.
 * Passed down to child components for state management.
 */
export interface QuickGenerateState {
  // Current step in the wizard
  currentStep: QuickGenerateStep;
  // Files that have been uploaded
  uploadedFiles: UploadedFile[];
  // Optional context provided by user
  userContext: string;
  // Extracted assumptions
  assumptions: Assumption[];
  // Documents selected for generation
  selectedDocuments: Set<string>;
  // Whether the generation plan is locked
  planLocked: boolean;
  // Generated content sections
  generatedSections: Record<string, string>;
  // Generation task ID for polling
  generationTaskId?: string;
  // Generation progress percentage
  generationProgress: number;
  // Quality analysis results
  qualityAnalysis?: Record<string, any>;
}

/**
 * Props for the main QuickGenerateTab component.
 */
export interface QuickGenerateTabProps {
  // Callback when generation is complete and user wants to open in full editor
  onOpenEditor: (sections: Record<string, string>) => void;
  // Callback when wizard is completed
  onComplete?: (sections: Record<string, string>) => void;
}

/**
 * Props for the QuickUploadStep component.
 */
export interface QuickUploadStepProps {
  // Currently uploaded files
  uploadedFiles: UploadedFile[];
  // Function to add new files
  onFilesAdded: (files: UploadedFile[]) => void;
  // Function to remove a file
  onFileRemoved: (fileId: string) => void;
  // User-provided context text
  userContext: string;
  // Function to update context
  onContextChange: (context: string) => void;
  // Function to proceed to next step
  onContinue: () => void;
  // Whether extraction is in progress
  isExtracting: boolean;
}

/**
 * Props for the ExtractionProgress component.
 */
export interface ExtractionProgressProps {
  // Current progress percentage (0-100)
  progress: number;
  // Current status message
  statusMessage: string;
  // Number of assumptions found so far
  assumptionsFound: number;
  // Function to cancel extraction
  onCancel: () => void;
}

/**
 * Props for the QuickReviewStep component.
 */
export interface QuickReviewStepProps {
  // Generated sections to display
  sections: Record<string, string>;
  // Quality analysis data
  qualityAnalysis?: Record<string, any>;
  // Function to open in full editor
  onOpenEditor: () => void;
  // Function to download as ZIP
  onDownload: () => void;
  // Function to go back to previous step
  onBack: () => void;
  // Function to regenerate documents
  onRegenerate: () => void;
}
