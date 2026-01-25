/**
 * IssueFloatingNav - Floating navigation bar for issues
 *
 * Provides Previous/Next navigation for issues with keyboard shortcuts.
 * Shows current position (e.g., "Issue 3 of 12") and issue type.
 */

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DocumentIssue } from "@/lib/editorUtils";

interface IssueFloatingNavProps {
  currentIndex: number;
  totalCount: number;
  currentIssue: DocumentIssue | null;
  onPrevious: () => void;
  onNext: () => void;
  visible: boolean;
  className?: string;
}

/**
 * Get a human-readable label for an issue kind
 */
function getIssueKindLabel(kind: string): string {
  switch (kind) {
    case 'error':
      return 'Error';
    case 'warning':
      return 'Warning';
    case 'info':
      return 'Info';
    case 'compliance':
      return 'Compliance';
    case 'hallucination':
      return 'Hallucination';
    default:
      return 'Issue';
  }
}

export function IssueFloatingNav({
  currentIndex,
  totalCount,
  currentIssue,
  onPrevious,
  onNext,
  visible,
  className = "",
}: IssueFloatingNavProps) {
  if (!visible || totalCount === 0) {
    return null;
  }

  const kindLabel = currentIssue ? getIssueKindLabel(currentIssue.kind) : 'Issue';

  return (
    <div
      className={`
        flex items-center justify-between gap-4 px-4 py-2
        bg-white/95 backdrop-blur-sm border rounded-lg shadow-lg
        text-sm
        ${className}
      `}
    >
      <Button
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0"
        onClick={onPrevious}
        disabled={currentIndex === 0}
        title="Previous issue (Ctrl+[)"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>

      <div className="flex items-center gap-2 text-muted-foreground">
        <span>
          Issue <strong className="text-foreground">{currentIndex + 1}</strong> of{" "}
          <strong className="text-foreground">{totalCount}</strong>
        </span>
        {currentIssue && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100">
            {kindLabel}
          </span>
        )}
      </div>

      <Button
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0"
        onClick={onNext}
        disabled={currentIndex === totalCount - 1}
        title="Next issue (Ctrl+])"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}
