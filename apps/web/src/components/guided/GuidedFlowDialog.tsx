/**
 * Guided Flow Dialog
 *
 * Main dialog component for DocuSign-style guided completion.
 * Split layout: Left (document preview) | Right (guidance panel)
 */

import { useEffect, useRef } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Save,
  X,
  Sparkles
} from 'lucide-react';
import { GuidedFlowProvider, useGuidedFlow } from '@/contexts/GuidedFlowContext';
import { GuidedFieldHighlighter } from './GuidedFieldHighlighter';
import { GuidedAssistantPanel } from './GuidedAssistantPanel';
import { GuidedFieldForm } from './GuidedFieldForm';
import type { GuidedDocument, User } from '@/types/guidedFlow';
import '@/styles/guidedFlow.css';

// ============================================================================
// Props
// ============================================================================

interface GuidedFlowDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  document: GuidedDocument;
  currentUser: User;
  initialValues?: Record<string, any>;
  onSave?: (values: Record<string, any>) => Promise<void>;
  onComplete?: (values: Record<string, any>) => void;
  documentPreview?: React.ReactNode; // Optional preview component
}

// ============================================================================
// Inner Component (has access to context)
// ============================================================================

function GuidedFlowDialogContent({
  onClose,
  documentPreview
}: {
  onClose: () => void;
  documentPreview?: React.ReactNode;
}) {
  const {
    state,
    form,
    currentField,
    canAdvance,
    canGoBack,
    goToNextField,
    goToPreviousField,
    progress,
    saveProgress
  } = useGuidedFlow();

  const { document, isSaving } = state;
  const dialogContentRef = useRef<HTMLDivElement>(null);

  // ========================================================================
  // Keyboard Navigation
  // ========================================================================

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't interfere with input typing
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      switch (e.key) {
        case 'ArrowRight':
        case 'Enter':
          if (canAdvance) {
            e.preventDefault();
            goToNextField();
          }
          break;

        case 'ArrowLeft':
          if (canGoBack) {
            e.preventDefault();
            goToPreviousField();
          }
          break;

        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [canAdvance, canGoBack, goToNextField, goToPreviousField, onClose]);

  // ========================================================================
  // Auto-Save Handler
  // ========================================================================

  const handleSave = async () => {
    await saveProgress();
  };

  // ========================================================================
  // Render
  // ========================================================================

  const isComplete = progress.percentage === 100;

  return (
    <div className="flex h-full">
      {/* ================================================================
          LEFT SIDE: Document Preview + Field Highlighter
          ================================================================ */}
      <div className="flex-1 bg-slate-50 overflow-auto p-6" ref={dialogContentRef}>
        {/* Progress Bar */}
        <div className="mb-4 sticky top-0 bg-slate-50 pb-4 z-10">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Badge variant={isComplete ? "default" : "secondary"} className="font-medium">
                {isComplete ? (
                  <>
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Complete
                  </>
                ) : (
                  `${progress.completed} of ${progress.total}`
                )}
              </Badge>
              {document.autoSave.enabled && (
                <Badge variant="outline" className="text-xs">
                  <Save className="h-3 w-3 mr-1" />
                  Auto-save
                </Badge>
              )}
            </div>
            <span className="text-sm text-slate-600 font-medium">
              {progress.percentage}% Complete
            </span>
          </div>
          <div className="guided-progress-bar">
            <div
              className="guided-progress-fill"
              style={{ width: `${progress.percentage}%` }}
            />
          </div>
        </div>

        {/* Document Preview or Placeholder */}
        {documentPreview ? (
          <div className="relative">
            {documentPreview}
            <GuidedFieldHighlighter />
          </div>
        ) : (
          <Card className="p-8">
            <div className="text-center text-slate-500">
              <div className="text-4xl mb-4">📄</div>
              <h3 className="text-lg font-semibold mb-2">{document.name}</h3>
              <p className="text-sm">{document.description}</p>
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-900">
                  <Sparkles className="h-4 w-4 inline mr-1" />
                  Follow the guided steps on the right to complete all required fields
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Completion Message */}
        {isComplete && (
          <Card className="mt-4 p-6 bg-green-50 border-green-200">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-8 w-8 text-green-600 completion-badge" />
              <div>
                <h3 className="font-semibold text-green-900">All Fields Complete!</h3>
                <p className="text-sm text-green-700">
                  You've completed all required fields. Review your work and save when ready.
                </p>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* ================================================================
          RIGHT SIDE: Guidance Panel
          ================================================================ */}
      <div className="w-[420px] border-l bg-white flex flex-col">
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold text-sm text-slate-700">
              {currentField?.label || 'Guided Completion'}
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {currentField && (
            <div className="flex items-center gap-2">
              <Badge
                variant={
                  currentField.required ? 'destructive' : 'secondary'
                }
                className="text-xs"
              >
                {currentField.required ? 'Required' : 'Optional'}
              </Badge>
              <span className="text-xs text-slate-500">
                Step {progress.completed + 1} of {progress.total}
              </span>
            </div>
          )}
        </div>

        {/* Field Form (scrollable) */}
        <div className="flex-1 overflow-auto p-4">
          {currentField ? (
            <div className="space-y-4">
              {/* Helper Text */}
              {currentField.helperText && (
                <Card className="p-4 bg-blue-50 border-blue-200">
                  <p className="text-sm text-blue-900">
                    {currentField.helperText}
                  </p>
                </Card>
              )}

              {/* Field Input */}
              <GuidedFieldForm field={currentField} />

              {/* AI Assistant Panel */}
              {currentField.aiAssist?.enabled && (
                <GuidedAssistantPanel fieldId={currentField.id} />
              )}
            </div>
          ) : (
            <div className="text-center text-slate-500 py-12">
              <p className="text-sm">No field selected</p>
            </div>
          )}
        </div>

        {/* Footer: Navigation Buttons */}
        <div className="p-4 border-t bg-slate-50">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={goToPreviousField}
              disabled={!canGoBack}
              className="flex-1"
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>

            {!isComplete ? (
              <Button
                size="sm"
                onClick={goToNextField}
                disabled={!canAdvance}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={handleSave}
                disabled={isSaving}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                <Save className="h-4 w-4 mr-1" />
                {isSaving ? 'Saving...' : 'Save & Close'}
              </Button>
            )}
          </div>

          {/* Keyboard Shortcuts Hint */}
          <div className="mt-2 text-xs text-center text-slate-500">
            <kbd className="px-1.5 py-0.5 bg-slate-200 rounded text-xs">←</kbd>
            {' '}Previous{' '}
            <kbd className="px-1.5 py-0.5 bg-slate-200 rounded text-xs">→</kbd>
            {' '}Next{' '}
            <kbd className="px-1.5 py-0.5 bg-slate-200 rounded text-xs">Esc</kbd>
            {' '}Close
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Exported Component
// ============================================================================

export function GuidedFlowDialog({
  open,
  onOpenChange,
  document,
  currentUser,
  initialValues = {},
  onSave,
  onComplete,
  documentPreview
}: GuidedFlowDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] h-[90vh] p-0 gap-0">
        <DialogHeader className="sr-only">
          <DialogTitle>Guided Document Completion</DialogTitle>
          <DialogDescription>
            Complete all required fields with guided assistance
          </DialogDescription>
        </DialogHeader>

        <GuidedFlowProvider
          document={document}
          currentUser={currentUser}
          initialValues={initialValues}
          onSave={onSave}
          onComplete={(values) => {
            onComplete?.(values);
            onOpenChange(false);
          }}
        >
          <GuidedFlowDialogContent
            onClose={() => onOpenChange(false)}
            documentPreview={documentPreview}
          />
        </GuidedFlowProvider>
      </DialogContent>
    </Dialog>
  );
}
