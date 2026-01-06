/**
 * Fix Preview Modal Component
 * 
 * Shows a before/after diff preview when users click to fix an issue.
 * Prevents accidental modifications and gives users visibility into changes.
 * 
 * Features:
 * - Before text (highlighted in red/strikethrough)
 * - After text (highlighted in green)
 * - Issue description and severity badge
 * - Optional edit mode to modify fix before applying
 * - Apply Fix and Cancel buttons
 * - AI-powered contextual fix generation for placeholders like TBD
 * - Fullscreen toggle for long content
 * - Rich text editor for edit mode with table support
 * - Individual occurrence replacement (fixes only the specific instance clicked)
 * 
 * Dependencies:
 * - Shadcn Dialog components
 * - Tailwind CSS for styling
 * - copilotApi for AI-powered fixes
 * - TipTap for rich text editing
 * - ScrollArea for proper scrolling of long content
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
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
// Icons - including Maximize2 and Minimize2 for fullscreen toggle
import { 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  Check, 
  X, 
  Edit3, 
  Loader2, 
  Sparkles, 
  RefreshCw,
  Maximize2,
  Minimize2 
} from 'lucide-react';
import { copilotApi } from '@/services/api';
// TipTap imports for rich text editing in fix mode
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
// Table extensions for handling complex HTML content with tables
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableHeader } from '@tiptap/extension-table-header';
import { TableCell } from '@tiptap/extension-table-cell';

// Issue type matching the structure used in LiveEditor and editorUtils
// Supports both static fixes (apply function) and AI-powered fixes (requiresAI flag)
interface IssueFix {
  label: string;
  // Static fix function (for simple, predictable replacements)
  apply?: (text: string) => string;
  // Flag indicating this fix requires AI-powered contextual generation
  requiresAI?: boolean;
  // The pattern/text that needs to be replaced (used by AI to understand what to fix)
  pattern?: string;
  // Which occurrence of the pattern to replace (0-indexed)
  // When set, only the Nth occurrence will be replaced instead of all occurrences
  occurrenceIndex?: number;
}

/**
 * Issue interface matching the DocumentIssue type from editorUtils
 * Includes hallucination kind for potentially unsourced claims
 */
interface Issue {
  id: string;
  kind: 'error' | 'warning' | 'info' | 'compliance' | 'hallucination';
  label: string;
  pattern?: string;
  // Surrounding text context for display
  context?: string;
  fix?: IssueFix;
}

interface FixPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApply: (fixedText: string) => void;
  issue: Issue | null;
  originalText: string;
  // Section name for AI context (helps generate more relevant fixes)
  sectionName?: string;
}

/**
 * Get the appropriate icon for issue severity
 * Each issue kind has a distinct color for visual differentiation
 */
function getSeverityIcon(kind: string) {
  switch (kind) {
    case 'error':
      return <AlertCircle className="h-4 w-4 text-red-600" />;
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-amber-600" />;
    case 'compliance':
      // Purple color for compliance issues (FAR/DFARS)
      return <AlertCircle className="h-4 w-4 text-purple-600" />;
    case 'hallucination':
      // Orange color for potentially unsourced or fabricated claims
      return <AlertTriangle className="h-4 w-4 text-orange-600" />;
    default:
      return <Info className="h-4 w-4 text-blue-600" />;
  }
}

/**
 * Get badge variant based on issue severity
 * Hallucination uses secondary styling with orange theme
 */
function getSeverityVariant(kind: string): 'destructive' | 'secondary' | 'default' {
  switch (kind) {
    case 'error':
      return 'destructive';
    case 'warning':
    case 'compliance':
    case 'hallucination':
      // Compliance and hallucination use secondary styling
      return 'secondary';
    default:
      return 'default';
  }
}

/**
 * Replace only the Nth occurrence of a pattern in text
 * 
 * This function is crucial for individual issue fixing - it ensures that
 * when a user fixes TBD #2, only that specific TBD is replaced, not all TBDs.
 * 
 * @param text - The original text to search in
 * @param pattern - The pattern to find (e.g., "TBD")
 * @param replacement - The value to replace with
 * @param n - Which occurrence to replace (0-indexed)
 * @returns The text with only the Nth occurrence replaced
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
 * Find the position of the Nth occurrence of a pattern
 * 
 * Used to extract context around a specific occurrence for AI analysis.
 * 
 * @param text - The text to search in
 * @param pattern - The pattern to find
 * @param n - Which occurrence (0-indexed)
 * @returns The index position, or -1 if not found
 */
function findNthOccurrenceIndex(text: string, pattern: string, n: number): number {
  const regex = new RegExp(pattern, 'gi');
  let match;
  let count = 0;
  
  while ((match = regex.exec(text)) !== null) {
    if (count === n) {
      return match.index;
    }
    count++;
  }
  
  return -1;
}

/**
 * Extract context around a change (shows surrounding text)
 * No longer used for display but kept for hasChanges detection
 */
function extractChangeContext(original: string, fixed: string): {
  beforeSnippet: string;
  afterSnippet: string;
  hasChanges: boolean;
} {
  // Find the first difference between original and fixed
  let startDiff = 0;
  const minLen = Math.min(original.length, fixed.length);
  
  while (startDiff < minLen && original[startDiff] === fixed[startDiff]) {
    startDiff++;
  }
  
  // Find the last difference (from the end)
  let endDiffOriginal = original.length;
  let endDiffFixed = fixed.length;
  
  while (
    endDiffOriginal > startDiff &&
    endDiffFixed > startDiff &&
    original[endDiffOriginal - 1] === fixed[endDiffFixed - 1]
  ) {
    endDiffOriginal--;
    endDiffFixed--;
  }
  
  // Extract context (30 chars before and after the change)
  const contextPadding = 30;
  const contextStart = Math.max(0, startDiff - contextPadding);
  const contextEndOriginal = Math.min(original.length, endDiffOriginal + contextPadding);
  const contextEndFixed = Math.min(fixed.length, endDiffFixed + contextPadding);
  
  // Build snippets with ellipsis if truncated
  let beforeSnippet = original.substring(contextStart, contextEndOriginal);
  let afterSnippet = fixed.substring(contextStart, contextEndFixed);
  
  if (contextStart > 0) {
    beforeSnippet = '...' + beforeSnippet;
    afterSnippet = '...' + afterSnippet;
  }
  if (contextEndOriginal < original.length) {
    beforeSnippet = beforeSnippet + '...';
  }
  if (contextEndFixed < fixed.length) {
    afterSnippet = afterSnippet + '...';
  }
  
  return {
    beforeSnippet,
    afterSnippet,
    hasChanges: original !== fixed,
  };
}

/**
 * Mini Rich Text Editor for Fix Editing
 * 
 * A lightweight TipTap editor specifically for editing fixes.
 * Supports tables and basic formatting to handle complex content.
 * 
 * Dependencies:
 * - TipTap core (@tiptap/react)
 * - StarterKit for basic formatting
 * - Table extensions for HTML table support
 */
function FixEditor({ 
  content, 
  onChange, 
  isFullscreen 
}: { 
  content: string; 
  onChange: (content: string) => void;
  isFullscreen: boolean;
}) {
  // Create a lightweight TipTap editor for fix editing
  // @ts-expect-error - TipTap table extensions have version compatibility issues
  const editor = useEditor({
    extensions: [
      // StarterKit provides basic formatting: bold, italic, headings, lists, etc.
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      // Include table support for complex content like the CLIN structure tables
      Table.configure({
        resizable: true,
        HTMLAttributes: { class: 'tiptap-table' },
      }),
      TableRow,
      TableHeader,
      TableCell,
    ],
    content: content,
    // Update parent state when editor content changes
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    editorProps: {
      attributes: {
        // Apply prose styling for consistent appearance with main editor
        class: 'prose prose-sm max-w-none focus:outline-none min-h-[200px] p-4',
      },
    },
  });

  // Update editor content when prop changes (e.g., when AI generates new content)
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content, false);
    }
  }, [content, editor]);

  return (
    <div className={`border rounded-md bg-white overflow-hidden ${isFullscreen ? 'h-[40vh]' : ''}`}>
      {/* Simple formatting toolbar with essential buttons */}
      <div className="border-b bg-muted/30 px-2 py-1 flex items-center gap-1 flex-wrap">
        {/* Bold button */}
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 w-7 p-0 ${editor?.isActive('bold') ? 'bg-muted' : ''}`}
          onClick={() => editor?.chain().focus().toggleBold().run()}
        >
          <span className="font-bold text-sm">B</span>
        </Button>
        {/* Italic button */}
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 w-7 p-0 ${editor?.isActive('italic') ? 'bg-muted' : ''}`}
          onClick={() => editor?.chain().focus().toggleItalic().run()}
        >
          <span className="italic text-sm">I</span>
        </Button>
        {/* Bullet list button */}
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 w-7 p-0 ${editor?.isActive('bulletList') ? 'bg-muted' : ''}`}
          onClick={() => editor?.chain().focus().toggleBulletList().run()}
        >
          <span className="text-sm">•</span>
        </Button>
        {/* Ordered list button */}
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 w-7 p-0 ${editor?.isActive('orderedList') ? 'bg-muted' : ''}`}
          onClick={() => editor?.chain().focus().toggleOrderedList().run()}
        >
          <span className="text-sm">1.</span>
        </Button>
        {/* Heading buttons */}
        <div className="h-4 w-px bg-border mx-1" />
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 px-2 ${editor?.isActive('heading', { level: 2 }) ? 'bg-muted' : ''}`}
          onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
        >
          <span className="text-xs font-semibold">H2</span>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 px-2 ${editor?.isActive('heading', { level: 3 }) ? 'bg-muted' : ''}`}
          onClick={() => editor?.chain().focus().toggleHeading({ level: 3 }).run()}
        >
          <span className="text-xs font-semibold">H3</span>
        </Button>
      </div>
      
      {/* Editor content area with scrolling for long content */}
      <ScrollArea className={isFullscreen ? 'h-[calc(40vh-36px)]' : 'max-h-[300px]'}>
        <EditorContent editor={editor} />
      </ScrollArea>
    </div>
  );
}

export function FixPreviewModal({
  isOpen,
  onClose,
  onApply,
  issue,
  originalText,
  sectionName = '',
}: FixPreviewModalProps) {
  // State for edit mode and editable fix text
  const [isEditMode, setIsEditMode] = useState(false);
  const [editableFixedText, setEditableFixedText] = useState('');
  
  // State for AI-powered fixes
  const [isLoadingAI, setIsLoadingAI] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiGeneratedValue, setAiGeneratedValue] = useState<string | null>(null);
  
  // State for fullscreen mode - allows expanding modal for long content
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Determine if this fix requires AI
  const requiresAI = issue?.fix?.requiresAI === true;
  
  /**
   * Extract context around the placeholder for AI analysis
   * 
   * When occurrenceIndex is provided, finds the specific occurrence and extracts
   * context around it. This ensures AI generates a contextually appropriate value.
   * 
   * @param text - The full document text
   * @param pattern - The pattern to find (e.g., "TBD")
   * @param occurrenceIndex - Which occurrence to find context for (optional)
   * @returns Context string with surrounding text
   */
  const extractContextForAI = useCallback((
    text: string, 
    pattern: string,
    occurrenceIndex?: number
  ): string => {
    let patternIndex: number;
    
    // If occurrenceIndex is provided, find that specific occurrence
    if (occurrenceIndex !== undefined) {
      patternIndex = findNthOccurrenceIndex(text, pattern, occurrenceIndex);
    } else {
      // Fallback to first occurrence
      patternIndex = text.toLowerCase().indexOf(pattern.toLowerCase());
    }
    
    if (patternIndex === -1) return text.substring(0, 300);
    
    // Extract 150 chars before and after for AI context
    const contextPadding = 150;
    const start = Math.max(0, patternIndex - contextPadding);
    const end = Math.min(text.length, patternIndex + pattern.length + contextPadding);
    
    let context = text.substring(start, end);
    if (start > 0) context = '...' + context;
    if (end < text.length) context = context + '...';
    
    return context;
  }, []);
  
  /**
   * Generate AI fix when modal opens for AI-required fixes
   * 
   * This function:
   * 1. Extracts context around the specific occurrence
   * 2. Calls the AI copilot API for a contextual suggestion
   * 3. Applies the replacement to only the targeted occurrence
   * 
   * For hallucination issues, uses 'fix_hallucination' action which provides
   * options to add citations, rewrite claims, or flag for verification.
   */
  const generateAIFix = useCallback(async () => {
    if (!issue?.fix?.pattern || !isOpen) return;
    
    setIsLoadingAI(true);
    setAiError(null);
    setAiGeneratedValue(null);
    
    try {
      const pattern = issue.fix.pattern;
      const occurrenceIndex = issue.fix.occurrenceIndex;
      
      // Extract context around the SPECIFIC occurrence for better AI suggestions
      const context = extractContextForAI(originalText, pattern, occurrenceIndex);
      
      // Use different action based on issue kind
      // fix_hallucination: adds citations, rewrites unsourced claims, or flags for verification
      // fix_compliance: adds proper FAR/DFARS regulatory citations
      // fix_issue: generates contextual replacement values for TBD placeholders
      let action = 'fix_issue';
      if (issue.kind === 'hallucination') {
        action = 'fix_hallucination';
      } else if (issue.kind === 'compliance') {
        action = 'fix_compliance';
      }
      
      const response = await copilotApi.assist(
        action,
        pattern,  // The suspicious/placeholder text
        context,  // Surrounding context for AI to understand the claim
        sectionName  // Section name for additional context
      );
      
      // The AI returns the replacement value in response.result
      const suggestedValue = response.result.trim();
      setAiGeneratedValue(suggestedValue);
      
      // Apply the AI suggestion to the original text
      // Check if we should replace a specific occurrence or all
      if (occurrenceIndex !== undefined) {
        // Replace only the specific occurrence using our helper function
        const fixedText = replaceNthOccurrence(
          originalText, 
          pattern, 
          suggestedValue, 
          occurrenceIndex
        );
        setEditableFixedText(fixedText);
      } else {
        // Fallback: replace all occurrences (for backward compatibility)
        const regex = new RegExp(pattern, 'gi');
        const fixedText = originalText.replace(regex, suggestedValue);
        setEditableFixedText(fixedText);
      }
      
    } catch (error) {
      console.error('AI fix generation failed:', error);
      setAiError(error instanceof Error ? error.message : 'Failed to generate AI suggestion');
    } finally {
      setIsLoadingAI(false);
    }
  }, [issue, originalText, sectionName, isOpen, extractContextForAI]);
  
  // Compute the fixed text for static fixes
  const computedFixedText = (issue?.fix?.apply && !requiresAI) 
    ? issue.fix.apply(originalText) 
    : originalText;
  
  // Reset state when modal opens/closes or issue changes
  useEffect(() => {
    if (isOpen && issue?.fix) {
      setIsEditMode(false);
      setAiError(null);
      setIsFullscreen(false); // Reset fullscreen when modal opens
      
      if (requiresAI) {
        // For AI fixes, trigger generation
        generateAIFix();
      } else {
        // For static fixes, use the computed value
        setEditableFixedText(computedFixedText);
        setAiGeneratedValue(null);
      }
    }
  }, [isOpen, issue, computedFixedText, requiresAI, generateAIFix]);
  
  // If no issue or no fix, don't render
  if (!issue || !issue.fix) {
    return null;
  }
  
  // Get the text to display (either computed/AI-generated or user-edited)
  const displayFixedText = isEditMode ? editableFixedText : (requiresAI ? editableFixedText : computedFixedText);
  
  // Extract change context for hasChanges detection
  const { hasChanges } = extractChangeContext(
    originalText,
    displayFixedText
  );
  
  // Handle apply button click
  const handleApply = () => {
    onApply(displayFixedText);
    onClose();
  };
  
  // Handle retry for AI generation
  const handleRetryAI = () => {
    generateAIFix();
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      {/* Increased max-width from 600px to 900px, added fullscreen support with flex layout */}
      <DialogContent 
        className={`${
          isFullscreen 
            ? 'max-w-[95vw] h-[95vh]' 
            : 'sm:max-w-[900px] max-h-[90vh]'
        } flex flex-col overflow-hidden`}
      >
        {/* Header section - flex-shrink-0 keeps it fixed at top */}
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              {getSeverityIcon(issue.kind)}
              Fix Issue
              {requiresAI && (
                <Badge variant="outline" className="ml-2 text-purple-600 border-purple-300 bg-purple-50">
                  <Sparkles className="h-3 w-3 mr-1" />
                  AI-Powered
                </Badge>
              )}
            </DialogTitle>
            {/* Fullscreen toggle button for expanding modal with long content */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="h-8 w-8"
              title={isFullscreen ? 'Exit fullscreen' : 'Expand to fullscreen'}
            >
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
          </div>
          <DialogDescription>
            {requiresAI 
              ? 'AI will analyze context and suggest an appropriate replacement for this specific instance'
              : 'Review the proposed changes before applying'}
          </DialogDescription>
        </DialogHeader>
        
        {/* Scrollable content area - flex-1 makes it fill available space */}
        <ScrollArea className="flex-1 overflow-auto">
          <div className="space-y-4 pr-4">
            {/* Issue Badge and Label */}
            <div className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg border">
              <Badge variant={getSeverityVariant(issue.kind)} className="mt-0.5">
                {issue.kind.toUpperCase()}
              </Badge>
              <div className="flex-1">
                <p className="text-sm font-medium">{issue.label}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Fix action: {issue.fix.label}
                </p>
                {/* Show occurrence info if available */}
                {issue.fix.occurrenceIndex !== undefined && (
                  <p className="text-xs text-blue-600 mt-1">
                    Targeting occurrence #{issue.fix.occurrenceIndex + 1} only
                  </p>
                )}
              </div>
            </div>
            
            {/* AI Loading State */}
            {isLoadingAI && (
              <div className="flex items-center justify-center p-8 bg-purple-50 border border-purple-200 rounded-md">
                <div className="text-center space-y-3">
                  <Loader2 className="h-8 w-8 animate-spin text-purple-600 mx-auto" />
                  <div>
                    <p className="text-sm font-medium text-purple-900">
                      Analyzing context...
                    </p>
                    <p className="text-xs text-purple-700 mt-1">
                      AI is generating a contextual replacement for this specific instance
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* AI Error State */}
            {aiError && !isLoadingAI && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-900">
                      AI generation failed
                    </p>
                    <p className="text-xs text-red-700 mt-1">
                      {aiError}
                    </p>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handleRetryAI}
                      className="mt-2 gap-1"
                    >
                      <RefreshCw className="h-3 w-3" />
                      Retry
                    </Button>
                  </div>
                </div>
              </div>
            )}
            
            {/* AI Generated Value Display */}
            {requiresAI && aiGeneratedValue && !isLoadingAI && !aiError && (
              <div className="p-3 bg-purple-50 border border-purple-200 rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="h-4 w-4 text-purple-600" />
                  <span className="text-xs font-medium text-purple-900">AI Suggested Value:</span>
                </div>
                <p className="text-sm font-mono text-purple-900 bg-white px-2 py-1 rounded border border-purple-100">
                  {aiGeneratedValue}
                </p>
              </div>
            )}
            
            {/* Before/After Preview - Now with proper scrolling and HTML rendering */}
            {!isLoadingAI && !aiError && hasChanges ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Before Section - with fixed height for proper scrolling */}
                <div className="space-y-1">
                  <Label className="text-xs font-medium text-red-700 flex items-center gap-1">
                    <X className="h-3 w-3" /> BEFORE
                  </Label>
                  {/* Fixed height container enables ScrollArea scrolling */}
                  <div className={`bg-red-50 border border-red-200 rounded-md overflow-hidden ${isFullscreen ? 'h-[40vh]' : 'h-[300px]'}`}>
                    <ScrollArea className="h-full">
                      {/* Render HTML content properly with prose styling */}
                      <div 
                        className="p-3 prose prose-sm max-w-none text-red-900 [&_*]:text-red-900 opacity-60 [&_table]:w-full [&_th]:border [&_th]:p-2 [&_th]:bg-red-100 [&_td]:border [&_td]:p-2"
                        dangerouslySetInnerHTML={{ __html: originalText }}
                      />
                    </ScrollArea>
                  </div>
                </div>
                
                {/* After Section - with fixed height for proper scrolling */}
                <div className="space-y-1">
                  <Label className="text-xs font-medium text-green-700 flex items-center gap-1">
                    <Check className="h-3 w-3" /> AFTER
                  </Label>
                  {/* Fixed height container enables ScrollArea scrolling */}
                  <div className={`bg-green-50 border border-green-200 rounded-md overflow-hidden ${isFullscreen ? 'h-[40vh]' : 'h-[300px]'}`}>
                    <ScrollArea className="h-full">
                      {/* Render HTML content properly with prose styling */}
                      <div 
                        className="p-3 prose prose-sm max-w-none text-green-900 [&_*]:text-green-900 [&_table]:w-full [&_th]:border [&_th]:p-2 [&_th]:bg-green-100 [&_td]:border [&_td]:p-2"
                        dangerouslySetInnerHTML={{ __html: displayFixedText }}
                      />
                    </ScrollArea>
                  </div>
                </div>
              </div>
            ) : !isLoadingAI && !aiError && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-md">
                <p className="text-sm text-amber-800">
                  No changes detected. The fix may have already been applied or the pattern was not found.
                </p>
              </div>
            )}
            
            {/* Edit Mode Toggle - Only show when not loading and no error */}
            {!isLoadingAI && !aiError && (
              <div className="flex items-center justify-between pt-2 border-t">
                <div className="flex items-center gap-2">
                  <Switch
                    id="edit-mode"
                    checked={isEditMode}
                    onCheckedChange={setIsEditMode}
                  />
                  <Label htmlFor="edit-mode" className="text-sm cursor-pointer flex items-center gap-1">
                    <Edit3 className="h-3.5 w-3.5" />
                    Edit fix before applying
                  </Label>
                </div>
                {requiresAI && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={handleRetryAI}
                    className="gap-1 text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Regenerate
                  </Button>
                )}
              </div>
            )}
            
            {/* Rich Text Editor for edit mode - replaces basic Textarea */}
            {isEditMode && !isLoadingAI && (
              <div className="space-y-2">
                <Label className="text-xs font-medium">
                  Full document text (edit as needed):
                </Label>
                {/* FixEditor component with TipTap for rich text editing */}
                <FixEditor
                  content={editableFixedText}
                  onChange={setEditableFixedText}
                  isFullscreen={isFullscreen}
                />
                <p className="text-xs text-muted-foreground">
                  You can modify the content using the rich text editor above. Changes will be applied when you click "Apply Fix".
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
        
        {/* Action Buttons - flex-shrink-0 keeps them fixed at bottom */}
        <DialogFooter className="flex-shrink-0 gap-2 sm:gap-0 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleApply}
            disabled={isLoadingAI || !!aiError || (!hasChanges && !isEditMode)}
            className="gap-1"
          >
            <Check className="h-4 w-4" />
            Apply Fix
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
