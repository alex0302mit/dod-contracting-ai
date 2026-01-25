/**
 * Batch Fix Preview Modal Component
 *
 * Shows all fixable issues with checkboxes, generates AI fixes in parallel,
 * and allows users to preview and select which fixes to apply.
 *
 * Features:
 * - Lists all fixable issues with checkboxes
 * - Generates AI fixes for all issues with progress indicator
 * - Before/after preview for each issue
 * - Select/deselect individual fixes
 * - "Apply Selected" and "Apply All" buttons
 * - Integrates with existing copilotApi for fix generation
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  AlertCircle,
  AlertTriangle,
  Check,
  X,
  Loader2,
  Sparkles,
  RefreshCw,
  CheckSquare,
  Square,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { copilotApi, CopilotAction } from '@/services/api';

/**
 * Issue fix definition - matches DocumentIssue from editorUtils
 */
interface IssueFix {
  label: string;
  apply?: (text: string) => string;
  requiresAI?: boolean;
  pattern?: string;
  occurrenceIndex?: number;
}

/**
 * Issue interface matching the DocumentIssue type from editorUtils
 */
interface Issue {
  id: string;
  kind: 'error' | 'warning' | 'info' | 'compliance' | 'hallucination';
  label: string;
  pattern?: string;
  context?: string;
  fix?: IssueFix;
}

/**
 * Internal state for tracking fix generation progress
 */
interface FixState {
  issueId: string;
  status: 'pending' | 'loading' | 'success' | 'error';
  originalPattern: string;
  suggestedFix: string | null;
  error: string | null;
  selected: boolean;
}

interface BatchFixPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  issues: Issue[];
  documentText: string;
  sectionName: string;
  onApplyFixes: (selectedIssueIds: string[], fixedText: string) => void;
}

/**
 * Get the appropriate icon for issue severity
 */
function getSeverityIcon(kind: string) {
  switch (kind) {
    case 'error':
    case 'compliance':
      return <AlertCircle className="h-4 w-4 text-red-600" />;
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-amber-600" />;
    case 'hallucination':
      return <AlertTriangle className="h-4 w-4 text-orange-600" />;
    default:
      return <AlertCircle className="h-4 w-4 text-blue-600" />;
  }
}

/**
 * Get badge color based on issue kind
 */
function getBadgeClass(kind: string): string {
  switch (kind) {
    case 'error':
    case 'compliance':
      return 'bg-red-100 text-red-700 border-red-200';
    case 'warning':
      return 'bg-amber-100 text-amber-700 border-amber-200';
    case 'hallucination':
      return 'bg-orange-100 text-orange-700 border-orange-200';
    default:
      return 'bg-blue-100 text-blue-700 border-blue-200';
  }
}

/**
 * Replace only the Nth occurrence of a pattern in text
 */
function replaceNthOccurrence(
  text: string,
  pattern: string,
  replacement: string,
  n: number
): string {
  let count = 0;
  const regex = new RegExp(pattern, 'gi');

  return text.replace(regex, (match) => {
    if (count === n) {
      count++;
      return replacement;
    }
    count++;
    return match;
  });
}

/**
 * Extract context around a specific occurrence for AI analysis
 */
function extractContextForAI(text: string, pattern: string, occurrenceIndex?: number): string {
  const plainText = text.replace(/<[^>]*>/g, '');
  let patternIndex: number;

  if (occurrenceIndex !== undefined) {
    const regex = new RegExp(pattern, 'gi');
    let match;
    let count = 0;
    while ((match = regex.exec(plainText)) !== null) {
      if (count === occurrenceIndex) {
        patternIndex = match.index;
        break;
      }
      count++;
    }
    patternIndex = patternIndex! ?? plainText.toLowerCase().indexOf(pattern.toLowerCase());
  } else {
    patternIndex = plainText.toLowerCase().indexOf(pattern.toLowerCase());
  }

  if (patternIndex === -1) return plainText.substring(0, 300);

  const contextPadding = 150;
  const start = Math.max(0, patternIndex - contextPadding);
  const end = Math.min(plainText.length, patternIndex + pattern.length + contextPadding);

  let context = plainText.substring(start, end);
  if (start > 0) context = '...' + context;
  if (end < plainText.length) context = context + '...';

  return context;
}

export function BatchFixPreviewModal({
  isOpen,
  onClose,
  issues,
  documentText,
  sectionName,
  onApplyFixes,
}: BatchFixPreviewModalProps) {
  // State for tracking fix generation progress
  const [fixStates, setFixStates] = useState<Map<string, FixState>>(new Map());
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState({ current: 0, total: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Initialize fix states when modal opens or issues change
  useEffect(() => {
    if (isOpen && issues.length > 0) {
      const initialStates = new Map<string, FixState>();
      issues.forEach((issue) => {
        initialStates.set(issue.id, {
          issueId: issue.id,
          status: 'pending',
          originalPattern: issue.fix?.pattern || issue.pattern || '',
          suggestedFix: null,
          error: null,
          selected: true, // Default to selected
        });
      });
      setFixStates(initialStates);
      setGenerationProgress({ current: 0, total: issues.length });
    }
  }, [isOpen, issues]);

  /**
   * Generate AI fix for a single issue
   */
  const generateFixForIssue = useCallback(async (issue: Issue, currentText: string): Promise<string | null> => {
    if (!issue.fix?.pattern) return null;

    const pattern = issue.fix.pattern;
    const occurrenceIndex = issue.fix.occurrenceIndex;
    const context = extractContextForAI(currentText, pattern, occurrenceIndex);

    // Determine the appropriate action based on issue kind
    let action: CopilotAction = 'fix_issue';
    if (issue.kind === 'hallucination') {
      action = 'fix_hallucination';
    } else if (issue.kind === 'compliance') {
      action = 'fix_compliance';
    } else if (issue.kind === 'warning' && issue.label.toLowerCase().includes('vague')) {
      action = 'fix_vague_language';
    }

    try {
      const response = await copilotApi.assist(
        action,
        pattern,
        context,
        sectionName
      );
      return response.result.trim();
    } catch (error) {
      console.error(`Failed to generate fix for issue ${issue.id}:`, error);
      throw error;
    }
  }, [sectionName]);

  /**
   * Generate fixes for all issues in parallel (with concurrency limit)
   */
  const generateAllFixes = useCallback(async () => {
    setIsGenerating(true);
    setGenerationProgress({ current: 0, total: issues.length });

    // Process issues with limited concurrency to avoid overwhelming the API
    const concurrencyLimit = 3;
    const queue = [...issues];
    let completed = 0;

    const processNext = async (): Promise<void> => {
      if (queue.length === 0) return;

      const issue = queue.shift()!;

      // Update state to loading
      setFixStates((prev) => {
        const next = new Map(prev);
        const current = next.get(issue.id);
        if (current) {
          next.set(issue.id, { ...current, status: 'loading' });
        }
        return next;
      });

      try {
        const fix = await generateFixForIssue(issue, documentText);

        // Update state with success
        setFixStates((prev) => {
          const next = new Map(prev);
          const current = next.get(issue.id);
          if (current) {
            next.set(issue.id, {
              ...current,
              status: 'success',
              suggestedFix: fix,
              error: null,
            });
          }
          return next;
        });
      } catch (error) {
        // Update state with error
        setFixStates((prev) => {
          const next = new Map(prev);
          const current = next.get(issue.id);
          if (current) {
            next.set(issue.id, {
              ...current,
              status: 'error',
              error: error instanceof Error ? error.message : 'Failed to generate fix',
            });
          }
          return next;
        });
      }

      completed++;
      setGenerationProgress({ current: completed, total: issues.length });

      // Process next item in queue
      await processNext();
    };

    // Start concurrent workers
    const workers = Array(Math.min(concurrencyLimit, issues.length))
      .fill(null)
      .map(() => processNext());

    await Promise.all(workers);
    setIsGenerating(false);
  }, [issues, documentText, generateFixForIssue]);

  // Auto-generate fixes when modal opens
  useEffect(() => {
    if (isOpen && issues.length > 0 && fixStates.size > 0) {
      // Check if all fixes are pending (fresh open)
      const allPending = Array.from(fixStates.values()).every(s => s.status === 'pending');
      if (allPending) {
        generateAllFixes();
      }
    }
  }, [isOpen, issues.length, fixStates.size, generateAllFixes]);

  /**
   * Toggle selection for a specific issue
   */
  const toggleSelection = (issueId: string) => {
    setFixStates((prev) => {
      const next = new Map(prev);
      const current = next.get(issueId);
      if (current) {
        next.set(issueId, { ...current, selected: !current.selected });
      }
      return next;
    });
  };

  /**
   * Select all fixes
   */
  const selectAll = () => {
    setFixStates((prev) => {
      const next = new Map(prev);
      next.forEach((value, key) => {
        if (value.status === 'success') {
          next.set(key, { ...value, selected: true });
        }
      });
      return next;
    });
  };

  /**
   * Deselect all fixes
   */
  const deselectAll = () => {
    setFixStates((prev) => {
      const next = new Map(prev);
      next.forEach((value, key) => {
        next.set(key, { ...value, selected: false });
      });
      return next;
    });
  };

  /**
   * Apply selected fixes to the document
   */
  const applySelectedFixes = () => {
    let resultText = documentText;
    const appliedIds: string[] = [];

    // Get selected successful fixes in order
    const selectedFixes = issues
      .filter((issue) => {
        const state = fixStates.get(issue.id);
        return state?.selected && state?.status === 'success' && state?.suggestedFix;
      })
      .map((issue) => ({
        issue,
        state: fixStates.get(issue.id)!,
      }));

    // Apply fixes in order
    for (const { issue, state } of selectedFixes) {
      if (!issue.fix?.pattern || !state.suggestedFix) continue;

      const pattern = issue.fix.pattern;
      const occurrenceIndex = issue.fix.occurrenceIndex;

      if (occurrenceIndex !== undefined) {
        resultText = replaceNthOccurrence(resultText, pattern, state.suggestedFix, occurrenceIndex);
      } else {
        const regex = new RegExp(pattern, 'gi');
        resultText = resultText.replace(regex, state.suggestedFix);
      }

      appliedIds.push(issue.id);
    }

    onApplyFixes(appliedIds, resultText);
    onClose();
  };

  // Calculate counts
  const successCount = Array.from(fixStates.values()).filter(s => s.status === 'success').length;
  const selectedCount = Array.from(fixStates.values()).filter(s => s.selected && s.status === 'success').length;
  const errorCount = Array.from(fixStates.values()).filter(s => s.status === 'error').length;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className={`${
          isFullscreen
            ? 'max-w-[95vw] h-[95vh]'
            : 'sm:max-w-[800px] max-h-[85vh]'
        } flex flex-col overflow-hidden`}
      >
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
              Preview All Fixes
              <Badge variant="outline" className="ml-2">
                {issues.length} issues
              </Badge>
            </DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="h-8 w-8"
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
          </div>
          <DialogDescription>
            AI is generating fixes for each issue. Review and select which fixes to apply.
          </DialogDescription>
        </DialogHeader>

        {/* Progress indicator */}
        {isGenerating && (
          <div className="flex-shrink-0 px-1 py-2">
            <div className="flex items-center gap-2 mb-2">
              <Loader2 className="h-4 w-4 animate-spin text-purple-500" />
              <span className="text-sm text-muted-foreground">
                Generating fixes... {generationProgress.current}/{generationProgress.total}
              </span>
            </div>
            <Progress
              value={(generationProgress.current / generationProgress.total) * 100}
              className="h-2"
            />
          </div>
        )}

        {/* Selection controls */}
        {!isGenerating && successCount > 0 && (
          <div className="flex-shrink-0 flex items-center justify-between px-1 py-2 border-b">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAll}
                className="h-7 text-xs gap-1"
              >
                <CheckSquare className="h-3 w-3" />
                Select All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={deselectAll}
                className="h-7 text-xs gap-1"
              >
                <Square className="h-3 w-3" />
                Deselect All
              </Button>
            </div>
            <div className="text-xs text-muted-foreground">
              {selectedCount} of {successCount} selected
              {errorCount > 0 && (
                <span className="text-red-500 ml-2">({errorCount} failed)</span>
              )}
            </div>
          </div>
        )}

        {/* Issues list */}
        <ScrollArea className="flex-1 overflow-auto">
          <div className="space-y-3 pr-4 py-2">
            {issues.map((issue) => {
              const state = fixStates.get(issue.id);
              if (!state) return null;

              return (
                <div
                  key={issue.id}
                  className={`border rounded-lg p-3 transition-all ${
                    state.selected && state.status === 'success'
                      ? 'border-purple-300 bg-purple-50/50'
                      : 'border-gray-200 bg-white'
                  }`}
                >
                  {/* Issue header */}
                  <div className="flex items-start gap-3">
                    {/* Checkbox */}
                    <Checkbox
                      checked={state.selected && state.status === 'success'}
                      onCheckedChange={() => toggleSelection(issue.id)}
                      disabled={state.status !== 'success'}
                      className="mt-1"
                    />

                    <div className="flex-1 min-w-0">
                      {/* Issue info */}
                      <div className="flex items-center gap-2 mb-2">
                        {getSeverityIcon(issue.kind)}
                        <Badge variant="outline" className={`text-[10px] ${getBadgeClass(issue.kind)}`}>
                          {issue.kind.toUpperCase()}
                        </Badge>
                        {/* Status indicator */}
                        {state.status === 'loading' && (
                          <Loader2 className="h-3 w-3 animate-spin text-purple-500" />
                        )}
                        {state.status === 'success' && (
                          <Check className="h-3 w-3 text-green-500" />
                        )}
                        {state.status === 'error' && (
                          <X className="h-3 w-3 text-red-500" />
                        )}
                      </div>

                      {/* Issue label */}
                      <p className="text-sm text-gray-700 mb-2 line-clamp-2">
                        {issue.label}
                      </p>

                      {/* Before/After preview */}
                      {state.status === 'success' && state.suggestedFix && (
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          <div className="bg-red-50 border border-red-200 rounded p-2">
                            <div className="text-[10px] font-medium text-red-700 mb-1 flex items-center gap-1">
                              <X className="h-2.5 w-2.5" /> BEFORE
                            </div>
                            <p className="text-xs text-red-900 font-mono line-through opacity-60">
                              {state.originalPattern}
                            </p>
                          </div>
                          <div className="bg-green-50 border border-green-200 rounded p-2">
                            <div className="text-[10px] font-medium text-green-700 mb-1 flex items-center gap-1">
                              <Check className="h-2.5 w-2.5" /> AFTER
                            </div>
                            <p className="text-xs text-green-900 font-mono">
                              {state.suggestedFix}
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Error state */}
                      {state.status === 'error' && (
                        <div className="bg-red-50 border border-red-200 rounded p-2 mt-2">
                          <p className="text-xs text-red-700">{state.error}</p>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 text-xs mt-1 text-red-600"
                            onClick={() => {
                              // Reset and retry
                              setFixStates((prev) => {
                                const next = new Map(prev);
                                next.set(issue.id, { ...state, status: 'pending', error: null });
                                return next;
                              });
                              // Trigger regeneration for this issue
                              generateFixForIssue(issue, documentText).then((fix) => {
                                setFixStates((prev) => {
                                  const next = new Map(prev);
                                  next.set(issue.id, {
                                    ...state,
                                    status: fix ? 'success' : 'error',
                                    suggestedFix: fix,
                                    error: fix ? null : 'Failed to generate fix',
                                  });
                                  return next;
                                });
                              });
                            }}
                          >
                            <RefreshCw className="h-3 w-3 mr-1" />
                            Retry
                          </Button>
                        </div>
                      )}

                      {/* Loading state */}
                      {state.status === 'loading' && (
                        <div className="bg-purple-50 border border-purple-200 rounded p-2 mt-2 flex items-center gap-2">
                          <Loader2 className="h-3 w-3 animate-spin text-purple-500" />
                          <p className="text-xs text-purple-700">Generating fix...</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>

        <Separator />

        {/* Footer with action buttons */}
        <DialogFooter className="flex-shrink-0 gap-2 sm:gap-0 pt-4">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={applySelectedFixes}
            disabled={isGenerating || selectedCount === 0}
            className="gap-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
          >
            <Check className="h-4 w-4" />
            Apply Selected ({selectedCount})
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
