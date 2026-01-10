/**
 * Guided Flow Context
 *
 * Central state management for DocuSign-style guided completion flow.
 * Integrates React Hook Form, Zod validation, and permissions.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { useForm, UseFormReturn } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type {
  GuidedDocument,
  GuidedField,
  GuidedFlowState,
  User,
  GuidedFieldValue,
  FieldStatus,
  PermissionLevel,
  NavigationResult,
  SaveResult,
  ProgressInfo
} from '@/types/guidedFlow';
import { evaluateConditional, generateDynamicSchema, addConditionalValidation } from '@/schemas/guidedFlowSchemas';

// ============================================================================
// Context Types
// ============================================================================

interface GuidedFlowContextValue {
  // State
  state: GuidedFlowState;

  // React Hook Form
  form: UseFormReturn<any>;

  // Navigation
  currentField: GuidedField | null;
  canAdvance: boolean;
  canGoBack: boolean;
  goToNextField: () => Promise<NavigationResult>;
  goToPreviousField: () => Promise<NavigationResult>;
  goToField: (fieldId: string) => Promise<NavigationResult>;

  // Field Operations
  updateFieldValue: (fieldId: string, value: any) => Promise<void>;
  getFieldValue: (fieldId: string) => any;
  getFieldStatus: (fieldId: string) => FieldStatus;
  isFieldVisible: (field: GuidedField) => boolean;
  getFieldPermission: (field: GuidedField) => PermissionLevel;

  // Progress
  progress: ProgressInfo;

  // Save
  saveProgress: () => Promise<SaveResult>;

  // AI Assistance
  requestAISuggestion: (fieldId: string) => Promise<any>;
}

const GuidedFlowContext = createContext<GuidedFlowContextValue | undefined>(undefined);

// ============================================================================
// Provider Props
// ============================================================================

interface GuidedFlowProviderProps {
  children: React.ReactNode;
  document: GuidedDocument;
  currentUser: User;
  initialValues?: Record<string, any>;
  onSave?: (values: Record<string, any>) => Promise<void>;
  onComplete?: (values: Record<string, any>) => void;
}

// ============================================================================
// Provider Component
// ============================================================================

export function GuidedFlowProvider({
  children,
  document,
  currentUser,
  initialValues = {},
  onSave,
  onComplete
}: GuidedFlowProviderProps) {
  // ========================================================================
  // State
  // ========================================================================

  const [currentFieldId, setCurrentFieldId] = useState<string | null>(null);
  const [fieldValues, setFieldValues] = useState<Record<string, GuidedFieldValue>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [collaborators, setCollaborators] = useState<any[]>([]);

  // ========================================================================
  // React Hook Form Setup
  // ========================================================================

  // Get all fields flattened
  const allFields = useMemo(() => {
    return document.sections.flatMap(section => section.fields);
  }, [document]);

  // Generate Zod schema dynamically from field definitions
  const validationSchema = useMemo(() => {
    const baseSchema = generateDynamicSchema(allFields);
    return addConditionalValidation(baseSchema, allFields);
  }, [allFields]);

  // Initialize React Hook Form
  const form = useForm({
    resolver: zodResolver(validationSchema),
    defaultValues: initialValues,
    mode: 'onChange' // Validate on every change
  });

  const { watch, getValues, setValue, trigger, formState } = form;

  // ========================================================================
  // Field Visibility & Permissions
  // ========================================================================

  /**
   * Check if field is visible based on conditional logic
   */
  const isFieldVisible = useCallback((field: GuidedField): boolean => {
    // If no conditional rule, always visible
    if (!field.conditionalOn) return true;

    // Evaluate conditional rule against current form values
    const formValues = getValues();
    return evaluateConditional(field.conditionalOn, formValues);
  }, [getValues]);

  /**
   * Get permission level for current user on this field
   */
  const getFieldPermission = useCallback((field: GuidedField): PermissionLevel => {
    // Check user-specific override first
    if (field.permissions.users && field.permissions.users[currentUser.id]) {
      return field.permissions.users[currentUser.id];
    }

    // Fall back to role-based permission
    return field.permissions.roles[currentUser.role];
  }, [currentUser]);

  /**
   * Get all visible and editable fields for current user
   */
  const accessibleFields = useMemo(() => {
    return allFields.filter(field => {
      const visible = isFieldVisible(field);
      const permission = getFieldPermission(field);
      return visible && (permission === 'edit' || permission === 'required');
    });
  }, [allFields, isFieldVisible, getFieldPermission]);

  // ========================================================================
  // Field Status Management
  // ========================================================================

  /**
   * Get status of a field (pending/complete/invalid/locked/hidden)
   */
  const getFieldStatus = useCallback((fieldId: string): FieldStatus => {
    const field = allFields.find(f => f.id === fieldId);
    if (!field) return 'pending';

    // Check visibility
    if (!isFieldVisible(field)) return 'hidden';

    // Check if locked by another user
    const lockedBy = collaborators.find(c => c.currentFieldId === fieldId);
    if (lockedBy && lockedBy.userId !== currentUser.id) return 'locked';

    // Check validation status
    const fieldErrors = formState.errors;
    const fieldPath = field.rfhName.split('.');
    let errorObj: any = fieldErrors;
    for (const part of fieldPath) {
      if (errorObj && errorObj[part]) {
        errorObj = errorObj[part];
      } else {
        errorObj = null;
        break;
      }
    }

    if (errorObj && typeof errorObj === 'object' && 'message' in errorObj) {
      return 'invalid';
    }

    // Check if has value (complete)
    const value = getValues(field.rfhName);
    if (value !== undefined && value !== null && value !== '') {
      return 'complete';
    }

    return 'pending';
  }, [allFields, isFieldVisible, collaborators, currentUser.id, formState.errors, getValues]);

  // ========================================================================
  // Navigation
  // ========================================================================

  /**
   * Get current field object
   */
  const currentField = useMemo(() => {
    if (!currentFieldId) return null;
    return allFields.find(f => f.id === currentFieldId) || null;
  }, [currentFieldId, allFields]);

  /**
   * Get next accessible field in order
   */
  const getNextField = useCallback((): GuidedField | null => {
    if (!currentField) {
      // Start from first accessible field
      return accessibleFields.length > 0 ? accessibleFields[0] : null;
    }

    // Find current field's index in accessible fields
    const currentIndex = accessibleFields.findIndex(f => f.id === currentField.id);
    if (currentIndex === -1 || currentIndex >= accessibleFields.length - 1) {
      return null; // No next field
    }

    return accessibleFields[currentIndex + 1];
  }, [currentField, accessibleFields]);

  /**
   * Get previous accessible field in order
   */
  const getPreviousField = useCallback((): GuidedField | null => {
    if (!currentField) return null;

    const currentIndex = accessibleFields.findIndex(f => f.id === currentField.id);
    if (currentIndex <= 0) {
      return null; // No previous field
    }

    return accessibleFields[currentIndex - 1];
  }, [currentField, accessibleFields]);

  /**
   * Check if can advance to next field
   */
  const canAdvance = useMemo(() => {
    if (!currentField) return true; // Can start

    // Current field must be valid
    const status = getFieldStatus(currentField.id);
    if (status === 'invalid') return false;

    // If required, must be complete
    if (currentField.required && status !== 'complete') return false;

    return true;
  }, [currentField, getFieldStatus]);

  /**
   * Check if can go back
   */
  const canGoBack = useMemo(() => {
    return getPreviousField() !== null;
  }, [getPreviousField]);

  /**
   * Navigate to next field
   */
  const goToNextField = useCallback(async (): Promise<NavigationResult> => {
    // Validate current field first
    if (currentField) {
      const isValid = await trigger(currentField.rfhName);
      if (!isValid) {
        return {
          success: false,
          error: 'Please fix validation errors before continuing'
        };
      }

      // Auto-save on field completion
      if (document.autoSave.enabled && document.autoSave.onFieldComplete) {
        await saveProgress();
      }
    }

    const nextField = getNextField();
    if (!nextField) {
      // Reached the end - check if all required fields are complete
      const allComplete = accessibleFields
        .filter(f => f.required)
        .every(f => getFieldStatus(f.id) === 'complete');

      if (allComplete && onComplete) {
        onComplete(getValues());
      }

      return {
        success: true,
        isLastField: true
      };
    }

    setCurrentFieldId(nextField.id);
    return {
      success: true,
      newFieldId: nextField.id,
      isLastField: false
    };
  }, [currentField, document.autoSave, getNextField, accessibleFields, getFieldStatus, trigger, getValues, onComplete]);

  /**
   * Navigate to previous field
   */
  const goToPreviousField = useCallback(async (): Promise<NavigationResult> => {
    const prevField = getPreviousField();
    if (!prevField) {
      return {
        success: false,
        error: 'Already at first field'
      };
    }

    setCurrentFieldId(prevField.id);
    return {
      success: true,
      newFieldId: prevField.id
    };
  }, [getPreviousField]);

  /**
   * Navigate to specific field by ID
   */
  const goToField = useCallback(async (fieldId: string): Promise<NavigationResult> => {
    const field = accessibleFields.find(f => f.id === fieldId);
    if (!field) {
      return {
        success: false,
        error: 'Field not found or not accessible'
      };
    }

    setCurrentFieldId(fieldId);
    return {
      success: true,
      newFieldId: fieldId
    };
  }, [accessibleFields]);

  // ========================================================================
  // Field Value Operations
  // ========================================================================

  /**
   * Update field value
   */
  const updateFieldValue = useCallback(async (fieldId: string, value: any) => {
    const field = allFields.find(f => f.id === fieldId);
    if (!field) return;

    // Update React Hook Form
    setValue(field.rfhName, value, {
      shouldValidate: true,
      shouldDirty: true,
      shouldTouch: true
    });

    // Update field values state
    setFieldValues(prev => ({
      ...prev,
      [fieldId]: {
        fieldId,
        value,
        status: getFieldStatus(fieldId),
        updatedAt: new Date().toISOString(),
        updatedBy: currentUser.id
      }
    }));

    // Auto-save if enabled
    if (document.autoSave.enabled && document.autoSave.onFieldComplete) {
      const isComplete = getFieldStatus(fieldId) === 'complete';
      if (isComplete) {
        await saveProgress();
      }
    }
  }, [allFields, setValue, getFieldStatus, currentUser.id, document.autoSave]);

  /**
   * Get field value
   */
  const getFieldValue = useCallback((fieldId: string): any => {
    const field = allFields.find(f => f.id === fieldId);
    if (!field) return undefined;
    return getValues(field.rfhName);
  }, [allFields, getValues]);

  // ========================================================================
  // Progress Calculation
  // ========================================================================

  const progress: ProgressInfo = useMemo(() => {
    const requiredFields = accessibleFields.filter(f => f.required);
    const optionalFields = accessibleFields.filter(f => !f.required);

    const completedRequired = requiredFields.filter(
      f => getFieldStatus(f.id) === 'complete'
    ).length;

    const completedOptional = optionalFields.filter(
      f => getFieldStatus(f.id) === 'complete'
    ).length;

    return {
      completed: completedRequired,
      total: requiredFields.length,
      percentage: requiredFields.length > 0
        ? Math.round((completedRequired / requiredFields.length) * 100)
        : 100,
      optionalCompleted: completedOptional,
      optionalTotal: optionalFields.length
    };
  }, [accessibleFields, getFieldStatus]);

  // ========================================================================
  // Save & API Operations
  // ========================================================================

  /**
   * Save current progress
   */
  const saveProgress = useCallback(async (): Promise<SaveResult> => {
    if (isSaving) {
      return {
        success: false,
        error: 'Save already in progress'
      };
    }

    setIsSaving(true);

    try {
      const values = getValues();

      if (onSave) {
        await onSave(values);
      }

      const savedAt = new Date().toISOString();

      setIsSaving(false);
      return {
        success: true,
        documentId: document.id,
        savedAt
      };
    } catch (error) {
      setIsSaving(false);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Save failed'
      };
    }
  }, [isSaving, getValues, onSave, document.id]);

  // ========================================================================
  // AI Assistance
  // ========================================================================

  /**
   * Request AI suggestion for a field
   */
  const requestAISuggestion = useCallback(async (fieldId: string): Promise<any> => {
    const field = allFields.find(f => f.id === fieldId);
    if (!field || !field.aiAssist?.enabled) {
      return null;
    }

    try {
      // Call backend AI suggestion API
      const response = await fetch('/api/guided-flow/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: document.id,
          field_id: fieldId,
          user_id: currentUser.id,
          company_name: currentUser.companyName,
          suggest_from_previous: field.aiAssist.suggestFromPrevious,
          suggest_from_rag: field.aiAssist.suggestFromRAG,
          custom_prompt: field.aiAssist.customPrompt
        })
      });

      if (!response.ok) {
        throw new Error('AI suggestion request failed');
      }

      const suggestion = await response.json();
      return suggestion;
    } catch (error) {
      console.error('AI suggestion error:', error);
      return null;
    }
  }, [allFields, document.id, currentUser]);

  // ========================================================================
  // Initialize Current Field
  // ========================================================================

  useEffect(() => {
    // Start at first accessible field if not set
    if (!currentFieldId && accessibleFields.length > 0) {
      setCurrentFieldId(accessibleFields[0].id);
    }
  }, [currentFieldId, accessibleFields]);

  // ========================================================================
  // Watch for Form Changes
  // ========================================================================

  useEffect(() => {
    // Watch all form values to trigger re-renders on conditional fields
    const subscription = watch(() => {
      // Form changed - this will trigger useMemo recalculations
    });

    return () => subscription.unsubscribe();
  }, [watch]);

  // ========================================================================
  // Context Value
  // ========================================================================

  const state: GuidedFlowState = {
    document,
    currentFieldId,
    fieldValues,
    currentUser,
    isLoading: false,
    isSaving,
    collaborators
  };

  const value: GuidedFlowContextValue = {
    state,
    form,
    currentField,
    canAdvance,
    canGoBack,
    goToNextField,
    goToPreviousField,
    goToField,
    updateFieldValue,
    getFieldValue,
    getFieldStatus,
    isFieldVisible,
    getFieldPermission,
    progress,
    saveProgress,
    requestAISuggestion
  };

  return (
    <GuidedFlowContext.Provider value={value}>
      {children}
    </GuidedFlowContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Use Guided Flow context
 *
 * Must be used within GuidedFlowProvider
 */
export function useGuidedFlow(): GuidedFlowContextValue {
  const context = useContext(GuidedFlowContext);

  if (!context) {
    throw new Error('useGuidedFlow must be used within GuidedFlowProvider');
  }

  return context;
}

// ============================================================================
// Helper Hook: Field-Specific
// ============================================================================

/**
 * Hook for accessing a specific field's state and operations
 *
 * @param fieldId - Field ID
 * @returns Field-specific helpers
 */
export function useGuidedField(fieldId: string) {
  const {
    getFieldValue,
    getFieldStatus,
    updateFieldValue,
    isFieldVisible,
    getFieldPermission,
    requestAISuggestion,
    currentField,
    form
  } = useGuidedFlow();

  const field = form.watch(); // Trigger re-render on form changes

  return {
    value: getFieldValue(fieldId),
    status: getFieldStatus(fieldId),
    isVisible: useMemo(() => {
      const f = form.getValues();
      return true; // Simplified - would need field object
    }, [field]),
    isCurrent: currentField?.id === fieldId,
    setValue: (value: any) => updateFieldValue(fieldId, value),
    requestSuggestion: () => requestAISuggestion(fieldId)
  };
}
