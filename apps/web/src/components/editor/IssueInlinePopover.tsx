/**
 * Issue Inline Popover Component
 *
 * Shows a popover when users click on highlighted issue text in the editor.
 * Provides quick access to issue details and "Fix with AI" button without using the sidebar.
 *
 * Features:
 * - Positioned at click coordinates using CSS position: fixed
 * - Shows severity icon + badge (color-coded by issue kind)
 * - Displays issue label (truncated if too long)
 * - "Fix with AI" button (purple gradient, opens FixPreviewModal)
 * - "Dismiss" button (closes popover)
 * - Click outside to close
 * - Escape key to close
 * - Viewport boundary detection for proper positioning
 */

import { useEffect, useRef, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { X, Sparkles, AlertCircle, AlertTriangle, Info, ShieldAlert } from 'lucide-react';

export interface InlinePopoverIssue {
  id: string;
  kind: 'error' | 'warning' | 'info' | 'compliance' | 'hallucination';
  label: string;
  pattern?: string;
}

interface IssueInlinePopoverProps {
  isOpen: boolean;
  onClose: () => void;
  issue: InlinePopoverIssue | null;
  position: { x: number; y: number };
  onFixWithAI: () => void;
  onDismiss: () => void;
}

/**
 * Get the appropriate icon for issue severity
 * Each issue kind has a distinct color for visual differentiation
 */
function getIssueIcon(kind: string) {
  switch (kind) {
    case 'error':
      return <AlertCircle className="h-4 w-4 text-red-600" />;
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-amber-600" />;
    case 'compliance':
      return <ShieldAlert className="h-4 w-4 text-purple-600" />;
    case 'hallucination':
      return <AlertTriangle className="h-4 w-4 text-orange-600" />;
    default:
      return <Info className="h-4 w-4 text-blue-600" />;
  }
}

/**
 * Get badge variant and className based on issue severity
 */
function getBadgeStyles(kind: string): { variant: 'destructive' | 'secondary' | 'default'; className: string } {
  switch (kind) {
    case 'error':
      return { variant: 'destructive', className: '' };
    case 'warning':
      return { variant: 'secondary', className: 'bg-amber-100 text-amber-800 border-amber-200' };
    case 'compliance':
      return { variant: 'secondary', className: 'bg-purple-100 text-purple-800 border-purple-200' };
    case 'hallucination':
      return { variant: 'secondary', className: 'bg-orange-100 text-orange-800 border-orange-200' };
    default:
      return { variant: 'default', className: '' };
  }
}

/**
 * Get kind display text with proper capitalization
 */
function getKindLabel(kind: string): string {
  const labels: Record<string, string> = {
    error: 'Error',
    warning: 'Warning',
    compliance: 'Compliance',
    hallucination: 'Hallucination',
    info: 'Info',
  };
  return labels[kind] || kind.charAt(0).toUpperCase() + kind.slice(1);
}

export function IssueInlinePopover({
  isOpen,
  onClose,
  issue,
  position,
  onFixWithAI,
  onDismiss,
}: IssueInlinePopoverProps) {
  const popoverRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      // Use setTimeout to avoid immediate triggering from the same click that opened the popover
      const timeoutId = setTimeout(() => {
        document.addEventListener('click', handleClickOutside);
      }, 0);

      return () => {
        clearTimeout(timeoutId);
        document.removeEventListener('click', handleClickOutside);
      };
    }
  }, [isOpen, onClose]);

  // Adjust position to stay within viewport
  const adjustedPosition = useMemo(() => {
    const padding = 16;
    const popoverWidth = 300;
    const popoverHeight = 180;

    let x = position.x;
    let y = position.y - popoverHeight - 10; // Position above the click point

    // Keep within horizontal bounds
    if (x + popoverWidth > window.innerWidth - padding) {
      x = window.innerWidth - popoverWidth - padding;
    }
    if (x < padding) {
      x = padding;
    }

    // If no room above, show below the click point
    if (y < padding) {
      y = position.y + 20;
    }

    // Ensure it doesn't go below viewport
    if (y + popoverHeight > window.innerHeight - padding) {
      y = window.innerHeight - popoverHeight - padding;
    }

    return { x, y };
  }, [position]);

  if (!isOpen || !issue) {
    return null;
  }

  const badgeStyles = getBadgeStyles(issue.kind);

  return (
    <div
      ref={popoverRef}
      data-inline-popover
      className="fixed z-50 w-[300px] bg-white border rounded-lg shadow-xl animate-in fade-in-0 zoom-in-95 duration-150"
      style={{
        left: adjustedPosition.x,
        top: adjustedPosition.y,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b bg-slate-50 rounded-t-lg">
        <div className="flex items-center gap-2">
          {getIssueIcon(issue.kind)}
          <Badge variant={badgeStyles.variant} className={badgeStyles.className}>
            {getKindLabel(issue.kind)}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 hover:bg-slate-200"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <div className="p-3">
        <p
          className="text-sm text-slate-700 line-clamp-3"
          title={issue.label}
        >
          {issue.label}
        </p>
        {issue.pattern && (
          <p className="text-xs text-slate-500 mt-2 font-mono truncate bg-slate-50 px-2 py-1 rounded">
            "{issue.pattern}"
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 p-3 border-t bg-slate-50 rounded-b-lg">
        <Button
          size="sm"
          className="flex-1 h-8 text-xs gap-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
          onClick={onFixWithAI}
        >
          <Sparkles className="h-3 w-3" />
          Fix with AI
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="h-8 text-xs"
          onClick={onDismiss}
        >
          Dismiss
        </Button>
      </div>
    </div>
  );
}
