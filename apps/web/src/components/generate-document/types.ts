/**
 * Type definitions for the Generate Document wizard.
 */

export type WizardStep = 'SELECT_TYPES' | 'FILL_CONTEXT' | 'GENERATING';

export interface FormFieldOption {
  value: string;
  label: string;
}

export interface FormField {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'select' | 'date';
  required: boolean;
  placeholder?: string;
  options?: FormFieldOption[];
}

export interface DocumentTypeSchema {
  name: string;
  description: string;
  phase: string;
  estimated_minutes: number;
  complexity: 'low' | 'medium' | 'high';
  fields: FormField[];
}

export interface DocumentTypeSchemas {
  [key: string]: DocumentTypeSchema;
}

export interface SelectedDocument {
  docType: string;
  schema: DocumentTypeSchema;
  context: Record<string, string>;
}
