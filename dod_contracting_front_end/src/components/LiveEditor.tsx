import { useState, useEffect, useMemo, useCallback, useRef } from "react";
// Icons - Loader2 added for bulk fix loading spinner, ChevronDown for collapsible panels
// AlertTriangle for hallucination, MessageSquare for vague language, RefreshCw for loading
// ChevronLeft/ChevronRight for collapsible sidebars (used for both expand and collapse)
import { ArrowLeft, Save, Sparkles, FileText, Clock, GitCompare, GitBranch, Tag, ShieldCheck, FormInput, MessageCircle, Layers, Loader2, Check, ChevronDown, ChevronLeft, ChevronRight, AlertTriangle, RefreshCw, Download } from "lucide-react";
// API services for AI-powered features
import { copilotApi, qualityApi, exportApi, QualityAnalysisResponse } from "@/services/api";
import { ComplianceGateDialog } from "@/components/ComplianceGateDialog";
import { performComplianceAnalysis } from "@/lib/complianceUtils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AgentBadge, AgentStats } from "@/components/AgentBadge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { computeQualityScore, computeIssues, autoImproveText, generateDiff, generateInlineDiff, DiffLine, detectFillableFields, replaceFillableField, FillableField, DocumentIssue } from "@/lib/editorUtils";
import { sanitizeHtml } from "@/lib/sanitizeHtml";
import { applyHighlightsWithEditor, clearHighlightsWithEditor, applyHighlightsDOM, clearHighlightsDOM, scrollToHighlight, getIssueColors, IssueKind } from "@/lib/issueHighlightUtils";
import { RichTextEditor } from "./editor/RichTextEditor";
import { FieldNavigator, FieldNavigatorButton } from "./editor/FieldNavigator";
import { QualityIssue } from "./editor/QualityIssueExtension";
import { DependencyGraph } from "./DependencyGraph";
import { SmartTagManager } from "./editor/SmartTagManager";
import { ValidationPanel } from "./editor/ValidationPanel";
import { GuidedFormPanel } from "./editor/GuidedFormPanel";
import { AnnotationPanel } from "./editor/AnnotationPanel";
import { AgentSelector } from "./comparison/AgentSelector";
import { ComparisonViewer } from "./comparison/ComparisonViewer";
import { FixPreviewModal } from "./editor/FixPreviewModal";
import { Editor } from '@tiptap/react';
import { ValidationEngine, ValidationResult } from '@/lib/ValidationEngine';
import { validationRules } from '@/lib/validationRules';
import { SmartFieldEngine } from '@/lib/SmartFieldEngine';
import { fieldTemplates, getTemplatesForSection } from '@/lib/fieldTemplates';
import { CommentThread, Comment } from '@/lib/commentTypes';
// Tooltip for hover labels on icon buttons
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
// DocumentLineagePanel for showing source documents that influenced AI generation
import { DocumentLineagePanel } from "@/components/documents/DocumentLineagePanel";

interface Citation {
  id: number;
  source: string;
  page: number;
  text: string;
  bbox: { x: number; y: number; w: number; h: number };
}

interface Assumption {
  id: string;
  text: string;
  source: string;
}

interface CollaborationMetadata {
  enabled: boolean;
  generation_order: string[];
  batch_count: number;
  batches: Array<{
    batch_number: number;
    documents: string[];
    generation_time_seconds: number;
  }>;
  cross_references: Array<{
    from: string;
    to: string;
    reference: string;
    created_at: string;
  }>;
  context_pool_stats: {
    document_count: number;
    total_words: number;
    total_characters: number;
    cross_reference_count: number;
    documents: string[];
  };
}

interface LiveEditorProps {
  lockedAssumptions: Assumption[];
  sections: Record<string, string>;
  setSections: (sections: Record<string, string>) => void;
  citations: Citation[];
  agentMetadata?: Record<string, any>;
  collaborationMetadata?: CollaborationMetadata | null;
  // Precomputed quality scores from document generation (for instant display)
  initialQualityScores?: Record<string, QualityAnalysisResponse>;
  // Optional document ID for showing source lineage panel
  documentId?: string;
  // Optional document name for display purposes
  documentName?: string;
  onExport: () => void;
  onBack: () => void;
}

export function LiveEditor({ lockedAssumptions, sections, setSections, citations, agentMetadata, collaborationMetadata, initialQualityScores, documentId, documentName, onExport, onBack }: LiveEditorProps) {
  const sectionNames = Object.keys(sections);
  const [activeSection, setActiveSection] = useState(sectionNames[0]);
  const [viewMode, setViewMode] = useState<"edit" | "compare" | "history" | "dependencies">("edit");
  const [showCitationPreview, setShowCitationPreview] = useState<number | null>(null);
  const [versionHistory, setVersionHistory] = useState([
    {
      id: "v0",
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      message: "Initial generation",
      sections: { ...sections },
      author: "AI Agent",
    },
  ]);
  const [compareVersion, setCompareVersion] = useState<typeof versionHistory[0] | null>(null);
  const [proposedChanges, setProposedChanges] = useState<any>(null);
  const [showAutoImprove, setShowAutoImprove] = useState(false);
  const [currentEditor, setCurrentEditor] = useState<Editor | null>(null);
  // Sidebar tab state - includes "sources" for document lineage when documentId is available
  const [sidebarTab, setSidebarTab] = useState<"context" | "tags" | "validation" | "fields" | "comments" | "sources">("context");
  // Quality score details panel expansion state
  const [showQualityDetails, setShowQualityDetails] = useState(false);
  // API-powered quality analysis state - cached per section for consistent scores across UI
  // Key: section name, Value: QualityAnalysisResponse from backend QualityAgent
  // Initialize with precomputed scores from generation if available
  const [apiQualityBySection, setApiQualityBySection] = useState<Record<string, QualityAnalysisResponse>>(
    initialQualityScores || {}
  );
  const [isLoadingQuality, setIsLoadingQuality] = useState(false);
  const [qualityError, setQualityError] = useState<string | null>(null);
  // Track which sections have been edited since their quality was computed
  // Sections in this set have "stale" quality scores that need refresh
  const [staleSections, setStaleSections] = useState<Set<string>>(new Set());
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [commentThreads, setCommentThreads] = useState<CommentThread[]>([]);
  const currentUser = "Current User"; // In real app, from auth context

  // Phase 6: Agent Comparison
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const [comparisonResults, setComparisonResults] = useState<any>(null);
  const [showComparisonViewer, setShowComparisonViewer] = useState(false);
  
  // Fix Preview Modal state - stores the issue selected for preview
  // Supports both static fixes (apply function) and AI-powered fixes (requiresAI flag)
  const [fixPreviewIssue, setFixPreviewIssue] = useState<{
    id: string;
    kind: 'error' | 'warning' | 'info' | 'compliance';
    label: string;
    pattern?: string;
    fix?: { 
      label: string; 
      apply?: (text: string) => string;
      requiresAI?: boolean;
      pattern?: string;
    };
  } | null>(null);

  // Field Navigator state - DocuSign-style guided field filling
  // Detects fillable fields (underscores, brackets, TBD) and guides users through each
  const [showFieldNavigator, setShowFieldNavigator] = useState(false);

  // Bulk fix state - tracks progress when fixing all issues at once
  // isFixingAll: prevents multiple bulk fix operations and shows loading UI
  // fixProgress: tracks current issue being fixed for progress display
  const [isFixingAll, setIsFixingAll] = useState(false);
  const [fixProgress, setFixProgress] = useState<{
    current: number;
    total: number;
    currentLabel: string;
  } | null>(null);

  // Issue highlight state - tracks which issue card is selected for highlighting
  // When an issue is selected, all instances are highlighted and we scroll to the target
  const [selectedIssue, setSelectedIssue] = useState<{
    id: string;
    pattern: string;
    kind: IssueKind;
    occurrenceIndex?: number;
  } | null>(null);

  // Collapsible sidebar state - allows users to hide/show sidebars for more editing space
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);

  // Compliance gate dialog state - shown before export
  const [showComplianceGate, setShowComplianceGate] = useState(false);
  const [pendingExportFormat, setPendingExportFormat] = useState<"pdf" | "docx">("pdf");

  // Ref to the editor container for DOM-based highlighting
  const editorContainerRef = useRef<HTMLDivElement>(null);

  const currentText = sections[activeSection] || "";
  // Local quality score (fast, client-side fallback)
  const quality = computeQualityScore(currentText, citations);
  // Local issues from text analysis (TBD placeholders, compliance, etc.)
  const localIssues = computeIssues(currentText);
  
  // Fetch comprehensive API quality analysis when section or content changes
  // This calls the backend QualityAgent for AI-powered 5-category analysis
  // Results are cached per section so scores stay consistent across UI
  // Skip fetching if we have fresh precomputed scores (not stale)
  useEffect(() => {
    // Skip if we already have a fresh precomputed score for this section
    // Only fetch if the section is marked stale (user edited it) or no score exists
    const hasPrecomputedScore = apiQualityBySection[activeSection];
    const isSectionStale = staleSections.has(activeSection);
    
    if (hasPrecomputedScore && !isSectionStale) {
      // Use precomputed score - no API call needed
      return;
    }
    
    // Debounce: don't call API for very short content or empty sections
    if (currentText.replace(/<[^>]*>/g, '').trim().length < 50) {
      return;
    }
    
    // Debounce API calls - wait 1.5s after typing stops
    const timeoutId = setTimeout(async () => {
      setIsLoadingQuality(true);
      setQualityError(null);
      
      try {
        const result = await qualityApi.analyze(currentText, activeSection);
        // Cache result by section name for consistent scores across UI
        setApiQualityBySection(prev => ({
          ...prev,
          [activeSection]: result
        }));
        // Clear stale flag - we now have a fresh score for this section
        setStaleSections(prev => {
          const next = new Set(prev);
          next.delete(activeSection);
          return next;
        });
      } catch (error) {
        console.error('Quality API error:', error);
        setQualityError(error instanceof Error ? error.message : 'Failed to analyze quality');
      } finally {
        setIsLoadingQuality(false);
      }
    }, 1500);
    
    return () => clearTimeout(timeoutId);
  }, [currentText, activeSection, staleSections]);
  
  // Derive current section's API quality from cache
  const apiQuality = apiQualityBySection[activeSection] || null;
  
  /**
   * Combine local issues with hallucination issues from the API response
   * 
   * Hallucination issues are extracted from apiQuality.breakdown.hallucination.examples
   * and converted to DocumentIssue format with kind: 'hallucination'.
   * Each suspicious text snippet becomes a separate issue with AI-powered fix support.
   */
  const issues: DocumentIssue[] = useMemo(() => {
    // Start with local issues (TBD placeholders, compliance issues, etc.)
    const allIssues: DocumentIssue[] = [...localIssues];
    
    // Add hallucination issues from API if available
    // These are potentially unsourced or fabricated claims detected by the QualityAgent
    if (apiQuality?.breakdown?.hallucination) {
      const hallucinationData = apiQuality.breakdown.hallucination;
      
      // Convert each example (suspicious text snippet) to a DocumentIssue
      // Examples are text snippets flagged by the QualityAgent as potential hallucinations
      const examples: string[] = hallucinationData.examples || [];
      
      examples.forEach((example: string, index: number) => {
        // Clean the example text (remove ellipsis markers from backend)
        const cleanExample = example.replace(/^\.\.\./, '').replace(/\.\.\.$/, '').trim();
        
        // Extract a pattern from the example for highlighting
        // Use the middle portion to avoid context ellipsis
        const pattern = cleanExample.length > 60 
          ? cleanExample.substring(0, 60) 
          : cleanExample;
        
        allIssues.push({
          id: `hallucination-${index}`,
          kind: 'hallucination',
          label: `Potentially unsourced claim: "${cleanExample.substring(0, 80)}${cleanExample.length > 80 ? '...' : ''}"`,
          pattern: pattern,
          context: cleanExample,
          fix: {
            label: 'Add citation or rewrite with AI',
            requiresAI: true,
            pattern: pattern,
            occurrenceIndex: 0, // Target the first occurrence
          },
        });
      });
      
      // Also add generic issues from the hallucination check as actionable warnings
      // These provide high-level warnings from the QualityAgent analysis
      // Made clickable with AI-powered fixes to scan and improve the document
      const hallucinationIssues: string[] = hallucinationData.issues || [];
      
      // Common vague phrases that often indicate potential hallucinations
      // Used as patterns for highlighting when user clicks summary warnings
      const vaguePatterns = [
        'according to', 'research shows', 'studies indicate', 'experts say',
        'it is well known', 'industry reports', 'generally accepted'
      ];
      
      // Add generic warnings if risk is MEDIUM or HIGH (alongside examples, not instead of)
      if (hallucinationData.risk_level !== 'LOW' && hallucinationIssues.length > 0) {
        // Strip HTML and get plain text for pattern matching
        const plainText = currentText.replace(/<[^>]*>/g, '').toLowerCase();
        
        hallucinationIssues.forEach((issue: string, index: number) => {
          // Try to find a vague pattern in the text to highlight
          const foundPattern = vaguePatterns.find(p => plainText.includes(p.toLowerCase()));
          const pattern = foundPattern || 'the'; // Fallback to common word if no vague pattern found
          
          allIssues.push({
            id: `hallucination-warning-${index}`,
            kind: 'hallucination', // Orange styling for hallucination warnings
            label: `⚠️ ${issue}`,
            pattern: pattern,
            context: issue,
            fix: {
              label: 'Fix hallucination issues with AI',
              requiresAI: true,
              pattern: pattern,
              occurrenceIndex: 0,
            },
          });
        });
      }
    }
    
    return allIssues;
  }, [localIssues, apiQuality]);
  
  // Detect fillable fields in current section (memoized for performance)
  // Updates when document content changes
  const fillableFields = useMemo(() => {
    return detectFillableFields(currentText);
  }, [currentText]);

  // Initialize validation engine
  const validationEngine = useMemo(() => {
    const engine = new ValidationEngine();
    engine.registerRules(validationRules);
    return engine;
  }, []);

  // Initialize smart field engine
  const smartFieldEngine = useMemo(() => {
    const engine = new SmartFieldEngine();
    engine.registerTemplates(fieldTemplates);
    return engine;
  }, []);

  // Get all templates (showing all regardless of section for better UX)
  const availableTemplates = useMemo(() => {
    return fieldTemplates; // Show all 6 templates
  }, []);

  // Run validation when content or section changes
  useEffect(() => {
    if (currentText) {
      const result = validationEngine.validate(currentText, activeSection);
      setValidationResult(result);
    }
  }, [currentText, activeSection, validationEngine]);

  const handleTextChange = (newText: string) => {
    setSections({ ...sections, [activeSection]: newText });
    // Mark this section's quality score as stale (needs refresh)
    setStaleSections(prev => new Set(prev).add(activeSection));
  };

  const commitVersion = () => {
    const message = prompt("Version commit message:", "Manual edit");
    if (!message) return;

    const newVersion = {
      id: `v${versionHistory.length}`,
      timestamp: new Date().toISOString(),
      message,
      sections: { ...sections },
      author: "User",
    };
    setVersionHistory([...versionHistory, newVersion]);
  };

  const restoreVersion = (version: typeof versionHistory[0]) => {
    if (confirm(`Restore version "${version.message}"? Current changes will be lost.`)) {
      setSections({ ...version.sections });
      setViewMode("edit");
      setCompareVersion(null);
    }
  };

  const generateAutoImprove = () => {
    const improvements = {
      before: currentText,
      after: autoImproveText(currentText, quality, issues),
      changes: [
        { type: "fix", text: "Replaced 'TBD' with concrete date", line: 2 },
        { type: "enhance", text: "Clarified evaluation factor references", line: 1 },
        { type: "compliance", text: "Added FAR citation for timeline", line: 2 },
      ],
    };
    setProposedChanges(improvements);
    setShowAutoImprove(true);
  };

  const acceptChanges = () => {
    if (proposedChanges) {
      handleTextChange(proposedChanges.after);
      setProposedChanges(null);
      setShowAutoImprove(false);
    }
  };

  const rejectChanges = () => {
    setProposedChanges(null);
    setShowAutoImprove(false);
  };

  const handleApplyFix = (issue: any) => {
    if (issue.autoFix) {
      const fixedContent = issue.autoFix.apply(currentText);
      handleTextChange(fixedContent);
    }
  };

  const handleApplyAllFixes = () => {
    if (validationResult) {
      const fixedContent = validationEngine.applyAllFixes(currentText, validationResult.issues);
      handleTextChange(fixedContent);
    }
  };

  /**
   * Handle clicking on an issue card to highlight all instances in the editor
   * Uses TipTap's native highlight marks for reliable highlighting
   */
  const handleIssueClick = useCallback((issue: DocumentIssue) => {
    if (!issue.pattern) return;

    // Set selected issue state
    setSelectedIssue({
      id: issue.id,
      pattern: issue.pattern,
      kind: issue.kind,
      occurrenceIndex: issue.fix?.occurrenceIndex,
    });

    // Try TipTap native highlighting first (if editor is available)
    if (currentEditor) {
      // Cast issue.kind to IssueKind for type safety when calling highlight functions
      const result = applyHighlightsWithEditor(
        currentEditor,
        issue.pattern,
        issue.kind as IssueKind,
        issue.fix?.occurrenceIndex
      );

      // Scroll to target if found
      if (result.targetPosition) {
        currentEditor.commands.focus();
        currentEditor.commands.setTextSelection(result.targetPosition.from);
        // Scroll the selection into view
        const { node } = currentEditor.view.domAtPos(result.targetPosition.from);
        if (node && node.parentElement) {
          node.parentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      } else if (result.positions.length > 0) {
        currentEditor.commands.focus();
        currentEditor.commands.setTextSelection(result.positions[0].from);
      }
    } else if (editorContainerRef.current) {
      // Fallback to DOM manipulation
      const editorElement = editorContainerRef.current.querySelector('.ProseMirror') as HTMLElement;
      if (editorElement) {
        // Cast issue.kind to IssueKind for type safety when calling highlight functions
        applyHighlightsDOM(
          editorElement,
          issue.pattern,
          issue.kind as IssueKind,
          issue.fix?.occurrenceIndex
        );
        setTimeout(() => scrollToHighlight(editorElement), 100);
      }
    }
  }, [currentEditor]);

  /**
   * Clear highlights when clicking outside issue cards or highlighted text
   */
  const handleClearHighlights = useCallback(() => {
    // Try TipTap native clear first
    if (currentEditor) {
      clearHighlightsWithEditor(currentEditor);
    } else if (editorContainerRef.current) {
      // Fallback to DOM
      const editorElement = editorContainerRef.current.querySelector('.ProseMirror') as HTMLElement;
      if (editorElement) {
        clearHighlightsDOM(editorElement);
      }
    }
    setSelectedIssue(null);
  }, [currentEditor]);

  // Click-away detection to clear highlights
  useEffect(() => {
    if (!selectedIssue) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;

      // Don't clear if clicking on an issue card or within a highlight
      // Check for both DOM highlights and TipTap native marks
      if (
        target.closest('[data-issue-card]') ||
        target.closest('.issue-highlight') ||
        target.closest('[data-fix-button]') ||
        target.closest('mark')  // TipTap's native highlight uses <mark> element
      ) {
        return;
      }

      handleClearHighlights();
    };

    // Add listener with a small delay to avoid immediate triggering
    const timeoutId = setTimeout(() => {
      document.addEventListener('click', handleClickOutside);
    }, 100);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [selectedIssue, handleClearHighlights]);

  // Clear highlights when section changes
  useEffect(() => {
    handleClearHighlights();
  }, [activeSection, handleClearHighlights]);

  /**
   * Handle fixing all issues with AI sequentially
   * 
   * Processes each fixable issue one by one, using AI to generate
   * contextual replacements. Updates the document incrementally.
   * Each fix is applied before the next to ensure proper context.
   */
  const handleFixAllIssues = async () => {
    // Get only issues that have AI fixes (requiresAI flag set)
    const fixableIssues = issues.filter(i => i.fix?.requiresAI);
    
    if (fixableIssues.length === 0) return;
    
    // Save current state to version history for undo capability
    const newVersion = {
      id: `v${versionHistory.length}`,
      timestamp: new Date().toISOString(),
      message: `Before bulk fix: ${fixableIssues.length} issues`,
      sections: { ...sections },
      author: "User",
    };
    setVersionHistory([...versionHistory, newVersion]);
    
    setIsFixingAll(true);
    
    // Start with current text and update incrementally
    // Each fix modifies the text, so subsequent fixes work on updated content
    let workingText = currentText;
    
    try {
      for (let i = 0; i < fixableIssues.length; i++) {
        const issue = fixableIssues[i];
        
        // Update progress state for UI feedback
        setFixProgress({
          current: i + 1,
          total: fixableIssues.length,
          currentLabel: issue.label.slice(0, 50) + (issue.label.length > 50 ? '...' : ''),
        });
        
        if (!issue.fix?.pattern) continue;
        
        const pattern = issue.fix.pattern;
        const occurrenceIndex = issue.fix.occurrenceIndex;
        
        // Extract context around the specific occurrence for AI to understand
        const plainText = workingText.replace(/<[^>]*>/g, '');
        let contextForAI = '';
        
        if (occurrenceIndex !== undefined) {
          // Find the Nth occurrence and extract surrounding context
          const regex = new RegExp(pattern, 'gi');
          let match;
          let count = 0;
          while ((match = regex.exec(plainText)) !== null) {
            if (count === occurrenceIndex) {
              // Get ~200 characters before and after for context
              const start = Math.max(0, match.index - 200);
              const end = Math.min(plainText.length, match.index + 200);
              contextForAI = plainText.substring(start, end);
              break;
            }
            count++;
          }
        } else {
          // Use first 500 chars as general context
          contextForAI = plainText.substring(0, 500);
        }
        
        try {
          // Call AI API to generate contextual fix
          const response = await copilotApi.assist(
            'fix_issue',
            pattern,
            contextForAI,
            activeSection
          );
          
          const suggestedValue = response.result.trim();
          
          // Apply fix to working text using occurrence-aware replacement
          if (occurrenceIndex !== undefined) {
            // Replace only the specific occurrence (0-indexed)
            let count = 0;
            const regex = new RegExp(pattern, 'gi');
            workingText = workingText.replace(regex, (match) => {
              if (count === occurrenceIndex) {
                count++;
                return suggestedValue;
              }
              count++;
              return match;
            });
          } else {
            // Replace all occurrences (fallback for backward compatibility)
            const regex = new RegExp(pattern, 'gi');
            workingText = workingText.replace(regex, suggestedValue);
          }
          
          // Update document after each fix for visual feedback
          handleTextChange(workingText);
          
          // Small delay to prevent API rate limiting and allow UI to update
          await new Promise(resolve => setTimeout(resolve, 100));
          
        } catch (error) {
          // Log error but continue with remaining issues
          console.error(`Failed to fix issue ${i + 1}:`, error);
        }
      }
      
    } catch (error) {
      console.error('Bulk fix failed:', error);
    } finally {
      // Reset state when done (success or failure)
      setIsFixingAll(false);
      setFixProgress(null);
    }
  };

  /**
   * Handle applying a value to a fillable field
   * Uses the replaceFillableField utility to target only the specific field instance
   * 
   * @param field - The fillable field being filled
   * @param value - The value to insert (e.g., typed text, signature, formatted date)
   */
  const handleFieldApply = (field: FillableField, value: string) => {
    // Save current state to version history before applying (enables undo)
    const newVersion = {
      id: `v${versionHistory.length}`,
      timestamp: new Date().toISOString(),
      message: `Filled field: ${field.name}`,
      sections: { ...sections },
      author: "User",
    };
    setVersionHistory([...versionHistory, newVersion]);
    
    // Apply the field value
    const updatedText = replaceFillableField(currentText, field, value);
    handleTextChange(updatedText);
  };

  const handleInsertSmartField = (templateId: string, values: Record<string, string>) => {
    if (!currentEditor) return;

    const template = smartFieldEngine.getTemplate(templateId);
    if (!template) return;

    // Generate formatted output
    const output = template.outputFormat ? template.outputFormat(values) : '';

    // Insert as HTML content
    currentEditor.chain().focus().insertContent(`<p>${output}</p>`).run();
  };

  const handleAddCommentThread = (thread: CommentThread) => {
    setCommentThreads([...commentThreads, thread]);
  };

  const handleAddComment = (threadId: string, comment: Comment) => {
    setCommentThreads(
      commentThreads.map((thread) =>
        thread.id === threadId
          ? { ...thread, comments: [...thread.comments, comment] }
          : thread
      )
    );
  };

  const handleResolveThread = (threadId: string) => {
    setCommentThreads(
      commentThreads.map((thread) =>
        thread.id === threadId
          ? {
              ...thread,
              status: 'resolved' as const,
              resolvedAt: new Date().toISOString(),
              resolvedBy: currentUser,
            }
          : thread
      )
    );
  };

  const handleDeleteThread = (threadId: string) => {
    setCommentThreads(commentThreads.filter((thread) => thread.id !== threadId));

    // Remove comment mark from editor
    if (currentEditor) {
      currentEditor.chain().focus().removeComment(threadId).run();
    }
  };

  // Phase 6: Agent Comparison Handlers
  const handleStartComparison = async (selectedVariants: any[]) => {
    try {
      // Start comparison via API
      const response = await fetch('/api/comparison/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documentName: activeSection,
          requirements: currentText,
          variants: selectedVariants,
          context: ''
        })
      });

      const { task_id } = await response.json();

      // Poll for results
      const pollInterval = setInterval(async () => {
        const statusRes = await fetch(`/api/comparison/status/${task_id}`);
        const status = await statusRes.json();

        if (status.status === 'completed') {
          clearInterval(pollInterval);

          // Get full results
          const resultsRes = await fetch(`/api/comparison/results/${task_id}`);
          const results = await resultsRes.json();

          setComparisonResults(results);
          setShowComparisonViewer(true);
        }
      }, 2000);
    } catch (error) {
      console.error('Comparison failed:', error);
      alert('Failed to start comparison. Please try again.');
    }
  };

  const handleSelectWinner = (variantId: string) => {
    if (!comparisonResults) return;

    const winner = comparisonResults.results.find((r: any) => r.variant_id === variantId);
    if (winner) {
      handleTextChange(winner.content);
      setShowComparisonViewer(false);
      setComparisonResults(null);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="border-b bg-white/80 backdrop-blur-sm px-6 py-4 flex items-center gap-4 flex-wrap">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>

        <Separator orientation="vertical" className="h-6" />

        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as "edit" | "compare" | "history" | "dependencies")} className="flex-1">
          <TabsList>
            <TabsTrigger value="edit" className="gap-2">
              <FileText className="h-4 w-4" />
              Edit
            </TabsTrigger>
            <TabsTrigger value="compare" className="gap-2">
              <GitCompare className="h-4 w-4" />
              Compare
            </TabsTrigger>
            <TabsTrigger value="history" className="gap-2">
              <Clock className="h-4 w-4" />
              History
            </TabsTrigger>
            {collaborationMetadata?.enabled && (
              <TabsTrigger value="dependencies" className="gap-2">
                <GitBranch className="h-4 w-4" />
                Dependencies
              </TabsTrigger>
            )}
          </TabsList>
        </Tabs>

        <div className="flex items-center gap-2 ml-auto">
          <Button variant="outline" size="sm" onClick={commitVersion}>
            <Save className="h-4 w-4 mr-2" />
            Commit
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAgentSelector(true)}
            className="bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200 hover:from-blue-100 hover:to-cyan-100"
          >
            <Layers className="h-4 w-4 mr-2" />
            Compare Agents
          </Button>

          {/* Field Navigator Button - shows when fillable fields are detected */}
          <FieldNavigatorButton
            fieldCount={fillableFields.length}
            onClick={() => setShowFieldNavigator(true)}
          />

          {agentMetadata && Object.keys(agentMetadata).length > 0 && (
            <AgentStats agentMetadata={agentMetadata} />
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  setPendingExportFormat("pdf");
                  setShowComplianceGate(true);
                }}
              >
                <FileText className="h-4 w-4 mr-2" />
                Export PDF
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setPendingExportFormat("docx");
                  setShowComplianceGate(true);
                }}
              >
                <FileText className="h-4 w-4 mr-2" />
                Export DOCX
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={async () => {
                  try {
                    const analysis = performComplianceAnalysis(sections, citations);
                    const blob = await exportApi.downloadComplianceReport(analysis);
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "compliance_report.pdf";
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch (error) {
                    console.error("Failed to download compliance report:", error);
                  }
                }}
              >
                <ShieldCheck className="h-4 w-4 mr-2" />
                Download Compliance Report
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Collapsible Document Sections */}
        <aside className={`border-r bg-white flex flex-col transition-all duration-300 ${leftSidebarOpen ? 'w-64' : 'w-10'}`}>
          {leftSidebarOpen ? (
            <>
              <div className="p-4 border-b bg-gradient-to-r from-slate-50 to-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-sm">Document Sections</h3>
                  <p className="text-xs text-muted-foreground mt-1">{sectionNames.length} sections</p>
                </div>
                {/* Collapse button with tooltip for visual hover label */}
                {/* Collapse button - ChevronLeft points toward collapse direction */}
                <TooltipProvider delayDuration={100}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => setLeftSidebarOpen(false)}
                        aria-label="Collapse sections panel"
                      >
                        <ChevronLeft className="h-5 w-5 text-slate-500" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p>Collapse sections</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <ScrollArea className="flex-1">
                <div className="p-2 space-y-1">
                  {sectionNames.map((name) => {
                    const metadata = agentMetadata?.[name];
                    return (
                      <Button
                        key={name}
                        variant={activeSection === name ? "secondary" : "ghost"}
                        className="w-full justify-start h-auto py-3"
                        onClick={() => setActiveSection(name)}
                      >
                        <div className="flex items-start gap-2 w-full">
                          <div className="flex-1 text-left min-w-0">
                            <div className="flex items-center gap-2">
                              <div className="font-medium text-sm truncate">{name}</div>
                              {metadata && <AgentBadge metadata={metadata} compact />}
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {sections[name].replace(/<[^>]*>/g, '').split(/\s+/).filter(Boolean).length} words
                            </div>
                          </div>
                        </div>
                      </Button>
                    );
                  })}
                </div>
              </ScrollArea>
            </>
          ) : (
            /* Collapsed state - show expand button with tooltip */
            <div className="flex flex-col items-center pt-4">
              <TooltipProvider delayDuration={100}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setLeftSidebarOpen(true)}
                      aria-label="Expand sections panel"
                    >
                      <ChevronRight className="h-5 w-5 text-slate-500" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>Expand sections</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              {/* Vertical text indicator */}
              <div className="mt-4 writing-mode-vertical text-xs text-muted-foreground" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}>
                Sections
              </div>
            </div>
          )}
        </aside>

        <main className="flex-1 overflow-hidden">
          {viewMode === "edit" && (
            <div ref={editorContainerRef} className="h-full">
              <EditView
                sectionName={activeSection}
                text={currentText}
                onTextChange={handleTextChange}
                issues={issues}
                citations={citations}
                onEditorReady={setCurrentEditor}
              />
            </div>
          )}
          {viewMode === "compare" && (
            <CompareView
              sections={sections}
              versionHistory={versionHistory}
              compareVersion={compareVersion}
              setCompareVersion={setCompareVersion}
              activeSection={activeSection}
            />
          )}
          {viewMode === "history" && (
            <HistoryView
              versionHistory={versionHistory}
              onRestore={restoreVersion}
              onCompare={(v: typeof versionHistory[0]) => {
                setCompareVersion(v);
                setViewMode("compare");
              }}
            />
          )}
          {viewMode === "dependencies" && (
            <DependenciesView collaborationMetadata={collaborationMetadata} />
          )}
        </main>

        {/* Right Sidebar - Collapsible Quality & Context Panel */}
        <aside className={`border-l bg-white flex flex-col overflow-hidden transition-all duration-300 ${rightSidebarOpen ? 'w-80' : 'w-10'}`}>
          {rightSidebarOpen ? (
            <>
              <div className="p-4 border-b bg-gradient-to-r from-slate-50 to-slate-100">
                <div className="flex items-center justify-between mb-2">
                  {/* Collapse button - ChevronRight points toward collapse direction */}
                  <TooltipProvider delayDuration={100}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => setRightSidebarOpen(false)}
                          aria-label="Collapse info panel"
                        >
                          <ChevronRight className="h-5 w-5 text-slate-500" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="bottom">
                        <p>Collapse panel</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  <span className="text-xs text-muted-foreground">Quality & Context</span>
                </div>
                <Tabs value={sidebarTab} onValueChange={(v) => setSidebarTab(v as "context" | "tags" | "validation" | "fields" | "comments" | "sources")} className="w-full">
                  {/* Show 6 columns if documentId is available for lineage, otherwise 5 */}
                  <TabsList className={`grid w-full ${documentId ? 'grid-cols-6' : 'grid-cols-5'}`}>
                    <TabsTrigger value="context" className="gap-1 text-[10px] px-1">
                      <FileText className="h-3 w-3" />
                      Info
                    </TabsTrigger>
                    <TabsTrigger value="tags" className="gap-1 text-[10px] px-1">
                      <Tag className="h-3 w-3" />
                      Tags
                    </TabsTrigger>
                    <TabsTrigger value="validation" className="gap-1 text-[10px] px-1">
                      <ShieldCheck className="h-3 w-3" />
                      Valid
                    </TabsTrigger>
                    <TabsTrigger value="fields" className="gap-1 text-[10px] px-1">
                      <FormInput className="h-3 w-3" />
                      Fields
                    </TabsTrigger>
                    <TabsTrigger value="comments" className="gap-1 text-[10px] px-1">
                      <MessageCircle className="h-3 w-3" />
                      Notes
                    </TabsTrigger>
                    {/* Sources tab - shows document lineage for explainability */}
                    {documentId && (
                      <TabsTrigger value="sources" className="gap-1 text-[10px] px-1">
                        <GitBranch className="h-3 w-3" />
                        Src
                      </TabsTrigger>
                    )}
                  </TabsList>
                </Tabs>
              </div>

              <ScrollArea className="flex-1 p-4 space-y-4">
            {sidebarTab === "context" && (
            <>
            {/* Enhanced Quality Score Card - Shows API data (5 categories) or local fallback (4 categories) */}
            <Card className="overflow-hidden">
              <CardHeader className="pb-2 bg-gradient-to-r from-slate-50 to-slate-100/50">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm flex items-center gap-2">
                      Quality Score
                      {isLoadingQuality && <RefreshCw className="h-3 w-3 animate-spin text-muted-foreground" />}
                    </CardTitle>
                    <CardDescription className="text-xs flex items-center gap-1.5">
                      {apiQuality ? (
                        staleSections.has(activeSection) ? (
                          <>
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-amber-100 text-amber-700 border border-amber-200">
                              <AlertTriangle className="w-2.5 h-2.5 mr-0.5" />
                              Outdated
                            </span>
                            <span>• Grade: {apiQuality.grade}</span>
                          </>
                        ) : (
                          <>
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-green-100 text-green-700 border border-green-200">
                              <ShieldCheck className="w-2.5 h-2.5 mr-0.5" />
                              AI Verified
                            </span>
                            <span>• Grade: {apiQuality.grade}</span>
                          </>
                        )
                      ) : isLoadingQuality ? (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-slate-100 text-slate-600 border border-slate-200 animate-pulse">
                          Analyzing...
                        </span>
                      ) : (
                        'Document health'
                      )}
                    </CardDescription>
                  </div>
                  {/* Circular overall score indicator - uses API score if available */}
                  <div className="relative w-14 h-14">
                    <svg className="w-14 h-14 -rotate-90">
                      <circle cx="28" cy="28" r="24" stroke="#e5e7eb" strokeWidth="4" fill="none" />
                      <circle 
                        cx="28" cy="28" r="24" 
                        stroke={(apiQuality?.score ?? quality.total) >= 80 ? '#22c55e' : (apiQuality?.score ?? quality.total) >= 60 ? '#eab308' : '#ef4444'}
                        strokeWidth="4" 
                        fill="none"
                        strokeDasharray={`${((apiQuality?.score ?? quality.total) / 100) * 151} 151`}
                        strokeLinecap="round"
                        className="transition-all duration-700"
                      />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-sm font-bold">
                      {Math.round(apiQuality?.score ?? quality.total)}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                {/* API Quality: 5 categories from backend QualityAgent */}
                {apiQuality ? (
                  <>
                    {/* 5 Metric tiles - compact grid layout */}
                    <div className="space-y-2">
                      {/* Row 1: Hallucination (most critical) - full width */}
                      <div className={`p-2 rounded-lg border ${
                        apiQuality.breakdown.hallucination.risk_level === 'HIGH' 
                          ? 'bg-red-50/80 border-red-200' 
                          : apiQuality.breakdown.hallucination.risk_level === 'MEDIUM'
                          ? 'bg-orange-50/80 border-orange-200'
                          : 'bg-green-50/80 border-green-200'
                      }`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <AlertTriangle className={`h-3 w-3 ${
                              apiQuality.breakdown.hallucination.risk_level === 'HIGH' ? 'text-red-500' :
                              apiQuality.breakdown.hallucination.risk_level === 'MEDIUM' ? 'text-orange-500' : 'text-green-500'
                            }`} />
                            <div className="text-[10px] font-medium text-slate-600">Hallucination</div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className={`text-[9px] px-1.5 py-0 ${
                              apiQuality.breakdown.hallucination.risk_level === 'HIGH' ? 'border-red-300 text-red-600' :
                              apiQuality.breakdown.hallucination.risk_level === 'MEDIUM' ? 'border-orange-300 text-orange-600' : 'border-green-300 text-green-600'
                            }`}>
                              {apiQuality.breakdown.hallucination.risk_level}
                            </Badge>
                            <div className="text-sm font-bold">{apiQuality.breakdown.hallucination.score}</div>
                          </div>
                        </div>
                        <div className="mt-1.5 h-1 bg-slate-200 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full transition-all ${
                            apiQuality.breakdown.hallucination.risk_level === 'HIGH' ? 'bg-red-500' :
                            apiQuality.breakdown.hallucination.risk_level === 'MEDIUM' ? 'bg-orange-500' : 'bg-green-500'
                          }`} style={{ width: `${apiQuality.breakdown.hallucination.score}%` }} />
                        </div>
                      </div>

                      {/* Row 2: Vague Language + Citations */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="p-2 rounded-lg bg-orange-50/80 border border-orange-100">
                          <div className="flex items-center gap-1 text-[10px] text-orange-600 font-medium">
                            <MessageCircle className="h-3 w-3" />
                            Vague Lang.
                          </div>
                          <div className="text-lg font-bold text-orange-700">{apiQuality.breakdown.vague_language.score}</div>
                          <div className="mt-1 h-1 bg-orange-200 rounded-full overflow-hidden">
                            <div className="h-full bg-orange-500 rounded-full transition-all" style={{ width: `${apiQuality.breakdown.vague_language.score}%` }} />
                          </div>
                        </div>
                        <div className="p-2 rounded-lg bg-purple-50/80 border border-purple-100">
                          <div className="text-[10px] text-purple-600 font-medium">Citations</div>
                          <div className="text-lg font-bold text-purple-700">{apiQuality.breakdown.citations.score}</div>
                          <div className="mt-1 h-1 bg-purple-200 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 rounded-full transition-all" style={{ width: `${apiQuality.breakdown.citations.score}%` }} />
                          </div>
                        </div>
                      </div>

                      {/* Row 3: Compliance + Completeness */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="p-2 rounded-lg bg-amber-50/80 border border-amber-100">
                          <div className="flex items-center gap-1 text-[10px] text-amber-600 font-medium">
                            <ShieldCheck className="h-3 w-3" />
                            Compliance
                          </div>
                          <div className="text-lg font-bold text-amber-700">{apiQuality.breakdown.compliance.score}</div>
                          <div className="mt-1 h-1 bg-amber-200 rounded-full overflow-hidden">
                            <div className="h-full bg-amber-500 rounded-full transition-all" style={{ width: `${apiQuality.breakdown.compliance.score}%` }} />
                          </div>
                        </div>
                        <div className="p-2 rounded-lg bg-emerald-50/80 border border-emerald-100">
                          <div className="flex items-center gap-1 text-[10px] text-emerald-600 font-medium">
                            <Check className="h-3 w-3" />
                            Completeness
                          </div>
                          <div className="text-lg font-bold text-emerald-700">{apiQuality.breakdown.completeness.score}</div>
                          <div className="mt-1 h-1 bg-emerald-200 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${apiQuality.breakdown.completeness.score}%` }} />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Expandable API Quality Details Panel */}
                    <Collapsible open={showQualityDetails} onOpenChange={setShowQualityDetails} className="mt-3">
                      <CollapsibleTrigger className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-slate-700 transition-colors w-full justify-center py-1">
                        <ChevronDown className={`h-3 w-3 transition-transform duration-200 ${showQualityDetails ? 'rotate-180' : ''}`} />
                        <span>How is this calculated?</span>
                      </CollapsibleTrigger>
                      <CollapsibleContent className="mt-2">
                        <div className="bg-slate-50 rounded-lg p-3 space-y-3 text-xs">
                          {/* Overall Formula */}
                          <div>
                            <div className="font-medium text-slate-700 mb-1">AI Quality Analysis Formula</div>
                            <div className="font-mono text-[10px] text-slate-600 bg-white px-2 py-1 rounded border">
                              Halluc.×30% + Vague×15% + Cite×20% + Compl.×25% + Complete×10% = <span className="font-bold">{apiQuality.score}</span>
                            </div>
                          </div>

                          {/* Per-metric explanations */}
                          <div className="space-y-2">
                            <div className="flex items-start gap-2">
                              <div className="w-2 h-2 rounded-full bg-red-500 mt-1 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-red-700">Hallucination (30%)</span>
                                <p className="text-[10px] text-muted-foreground">AI detects fabricated facts, unsupported claims, and suspicious patterns.</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-2">
                              <div className="w-2 h-2 rounded-full bg-orange-500 mt-1 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-orange-700">Vague Language (15%)</span>
                                <p className="text-[10px] text-muted-foreground">Detects imprecise terms: "several", "many", "possibly", "might".</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-2">
                              <div className="w-2 h-2 rounded-full bg-purple-500 mt-1 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-purple-700">Citations (20%)</span>
                                <p className="text-[10px] text-muted-foreground">Validates DoD-compliant citations (FAR/DFARS references).</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-2">
                              <div className="w-2 h-2 rounded-full bg-amber-500 mt-1 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-amber-700">Compliance (25%)</span>
                                <p className="text-[10px] text-muted-foreground">Checks for legal issues, anti-competitive language, discrimination.</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-2">
                              <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-emerald-700">Completeness (10%)</span>
                                <p className="text-[10px] text-muted-foreground">Evaluates word count ({apiQuality.breakdown.completeness.word_count} words) and structure.</p>
                              </div>
                            </div>
                          </div>

                          {/* Issues summary if any */}
                          {apiQuality.issues.length > 0 && (
                            <div className="pt-2 border-t">
                              <div className="font-medium text-slate-700 mb-1">Issues Found ({apiQuality.issues.length})</div>
                              <ul className="text-[10px] text-muted-foreground space-y-0.5">
                                {apiQuality.issues.slice(0, 3).map((issue, i) => (
                                  <li key={i} className="truncate">• {issue}</li>
                                ))}
                                {apiQuality.issues.length > 3 && (
                                  <li className="text-slate-400">...and {apiQuality.issues.length - 3} more</li>
                                )}
                              </ul>
                            </div>
                          )}
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  </>
                ) : (
                  <>
                    {/* Fallback: Local quality score (4 categories) */}
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 rounded-lg bg-blue-50/80 border border-blue-100">
                        <div className="text-[10px] text-blue-600 font-medium">Readability</div>
                        <div className="text-lg font-bold text-blue-700">{quality.breakdown.readability}</div>
                        <div className="mt-1 h-1 bg-blue-200 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${quality.breakdown.readability}%` }} />
                        </div>
                      </div>
                      <div className="p-2 rounded-lg bg-purple-50/80 border border-purple-100">
                        <div className="text-[10px] text-purple-600 font-medium">Citations</div>
                        <div className="text-lg font-bold text-purple-700">{quality.breakdown.citations}</div>
                        <div className="mt-1 h-1 bg-purple-200 rounded-full overflow-hidden">
                          <div className="h-full bg-purple-500 rounded-full transition-all" style={{ width: `${quality.breakdown.citations}%` }} />
                        </div>
                      </div>
                      <div className="p-2 rounded-lg bg-amber-50/80 border border-amber-100">
                        <div className="text-[10px] text-amber-600 font-medium">Compliance</div>
                        <div className="text-lg font-bold text-amber-700">{quality.breakdown.compliance}</div>
                        <div className="mt-1 h-1 bg-amber-200 rounded-full overflow-hidden">
                          <div className="h-full bg-amber-500 rounded-full transition-all" style={{ width: `${quality.breakdown.compliance}%` }} />
                        </div>
                      </div>
                      <div className="p-2 rounded-lg bg-emerald-50/80 border border-emerald-100">
                        <div className="text-[10px] text-emerald-600 font-medium">Length</div>
                        <div className="text-lg font-bold text-emerald-700">{quality.breakdown.length}</div>
                        <div className="mt-1 h-1 bg-emerald-200 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${quality.breakdown.length}%` }} />
                        </div>
                      </div>
                    </div>

                    {/* Loading indicator or error */}
                    {isLoadingQuality && (
                      <div className="mt-3 text-center text-[10px] text-muted-foreground">
                        <RefreshCw className="h-3 w-3 animate-spin inline mr-1" />
                        Running AI quality analysis...
                      </div>
                    )}
                    {qualityError && (
                      <div className="mt-3 text-center text-[10px] text-red-500">
                        AI analysis unavailable
                      </div>
                    )}

                    {/* Expandable Local Quality Details Panel */}
                    <Collapsible open={showQualityDetails} onOpenChange={setShowQualityDetails} className="mt-3">
                      <CollapsibleTrigger className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-slate-700 transition-colors w-full justify-center py-1">
                        <ChevronDown className={`h-3 w-3 transition-transform duration-200 ${showQualityDetails ? 'rotate-180' : ''}`} />
                        <span>How is this calculated?</span>
                      </CollapsibleTrigger>
                      <CollapsibleContent className="mt-2">
                        <div className="bg-slate-50 rounded-lg p-3 space-y-3 text-xs">
                          <div>
                            <div className="font-medium text-slate-700 mb-1">Local Score Formula (Fallback)</div>
                            <div className="font-mono text-[10px] text-slate-600 bg-white px-2 py-1 rounded border">
                              {quality.breakdown.readability}×0.30 + {quality.breakdown.citations}×0.20 + {quality.breakdown.compliance}×0.30 + {quality.breakdown.length}×0.20 = <span className="font-bold">{Math.round(quality.total)}</span>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-start gap-2">
                              <div className="w-2 h-2 rounded-full bg-blue-500 mt-1 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-blue-700">Readability (30%)</span>
                                <p className="text-[10px] text-muted-foreground">Based on average sentence length.</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-2">
                              <div className="w-2 h-2 rounded-full bg-purple-500 mt-1 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-purple-700">Citations (20%)</span>
                                <p className="text-[10px] text-muted-foreground">Measures [#] citation density.</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-2">
                              <div className="w-2 h-2 rounded-full bg-amber-500 mt-1 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-amber-700">Compliance (30%)</span>
                                <p className="text-[10px] text-muted-foreground">Checks for FAR/DFARS refs and TBD placeholders.</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-2">
                              <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-emerald-700">Length (20%)</span>
                                <p className="text-[10px] text-muted-foreground">Word count thresholds.</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Enhanced Issues Card with Compact Cards */}
            {issues.length > 0 && (
              <Card className="border-red-100">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                      Issues
                    </CardTitle>
                    <Badge variant="destructive" className="text-xs px-2">
                      {issues.length}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  {issues.map((issue, index) => {
                    const colors = getIssueColors(issue.kind);
                    const isSelected = selectedIssue?.id === issue.id;

                    return (
                      <div
                        key={issue.id}
                        data-issue-card
                        onClick={() => handleIssueClick(issue)}
                        className={`group relative p-3 rounded-xl cursor-pointer transition-all
                          ${isSelected
                            ? `ring-2 ring-offset-2 shadow-lg ${colors.ring} ${colors.bgLight}`
                            : `bg-gradient-to-r ${colors.gradient} border ${colors.border} hover:shadow-md`
                          }
                        `}
                        title="Click to highlight in document"
                      >
                        {/* Issue number indicator - color coded */}
                        <div className={`absolute -left-1 top-3 w-5 h-5 ${colors.bg} text-white text-[10px] rounded-full flex items-center justify-center font-bold shadow-sm`}>
                          {index + 1}
                        </div>

                        <div className="ml-4">
                          <p className="text-xs text-slate-700 line-clamp-2 mb-2 leading-relaxed">
                            {issue.label}
                          </p>

                          {/* Fix button with AI styling - all issues now have AI fixes */}
                          {issue.fix && (
                            <Button
                              size="sm"
                              data-fix-button
                              className="h-7 text-xs bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white gap-1 shadow-sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                setFixPreviewIssue(issue);
                              }}
                            >
                              <Sparkles className="h-3 w-3" />
                              Fix with AI
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  
                  {/* Fix All button when multiple issues - triggers bulk AI fix */}
                  {issues.filter(i => i.fix).length > 1 && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full text-xs mt-2 border-dashed border-purple-300 text-purple-600 hover:bg-purple-50 hover:border-purple-400 disabled:opacity-50"
                      onClick={handleFixAllIssues}
                      disabled={isFixingAll}
                    >
                      {isFixingAll ? (
                        <>
                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                          Fixing {fixProgress?.current || 1} of {fixProgress?.total || issues.filter(i => i.fix).length}...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-3 w-3 mr-1" />
                          Fix All {issues.filter(i => i.fix).length} Issues
                        </>
                      )}
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}

            {/* No issues state */}
            {issues.length === 0 && (
              <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-100 text-center">
                <div className="w-8 h-8 mx-auto mb-2 rounded-full bg-emerald-100 flex items-center justify-center">
                  <Check className="h-4 w-4 text-emerald-600" />
                </div>
                <p className="text-xs text-emerald-700 font-medium">No issues found</p>
                <p className="text-[10px] text-emerald-600">Your document looks great!</p>
              </div>
            )}

            {/* Citations Card */}
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">Citations</CardTitle>
                  <Badge variant="outline" className="text-xs">{citations.length}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {citations.map((cite) => (
                  <Button
                    key={cite.id}
                    variant={showCitationPreview === cite.id ? "secondary" : "ghost"}
                    className="w-full h-auto py-2 text-left justify-start hover:bg-blue-50"
                    onClick={() => setShowCitationPreview(cite.id)}
                  >
                    <div className="w-full">
                      <div className="font-semibold text-xs mb-1 flex items-center gap-1">
                        <span className="text-blue-600">[{cite.id}]</span>
                        <span className="text-slate-700">{cite.source}</span>
                      </div>
                      <div className="text-[11px] text-muted-foreground line-clamp-2">{cite.text}</div>
                    </div>
                  </Button>
                ))}
                {citations.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-2">No citations available</p>
                )}
              </CardContent>
            </Card>
            </>
            )}

            {sidebarTab === "tags" && (
              <SmartTagManager
                editor={currentEditor}
                content={sections[activeSection] || ""}
              />
            )}

            {sidebarTab === "validation" && (
              <ValidationPanel
                validationResult={validationResult}
                onApplyFix={handleApplyFix}
                onApplyAllFixes={handleApplyAllFixes}
              />
            )}

            {sidebarTab === "fields" && (
              <GuidedFormPanel
                templates={availableTemplates}
                onInsertField={handleInsertSmartField}
              />
            )}

            {sidebarTab === "comments" && (
              <AnnotationPanel
                editor={currentEditor}
                threads={commentThreads}
                currentUser={currentUser}
                onAddThread={handleAddCommentThread}
                onAddComment={handleAddComment}
                onResolveThread={handleResolveThread}
                onDeleteThread={handleDeleteThread}
              />
            )}
            {/* Sources Tab - Document Lineage Panel showing source documents */}
            {sidebarTab === "sources" && documentId && (
              <DocumentLineagePanel
                documentId={documentId}
                documentName={documentName}
                compact={true}
              />
            )}
              </ScrollArea>
            </>
          ) : (
            /* Collapsed state - show expand button */
            <div className="flex flex-col items-center pt-4">
              <TooltipProvider delayDuration={100}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setRightSidebarOpen(true)}
                      aria-label="Expand info panel"
                    >
                      <ChevronLeft className="h-5 w-5 text-slate-500" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="left">
                    <p>Expand panel</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              {/* Vertical text indicator */}
              <div className="mt-4 text-xs text-muted-foreground" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}>
                Quality
              </div>
            </div>
          )}
        </aside>
      </div>

      {showAutoImprove && proposedChanges && (
        <AutoImproveModal before={proposedChanges.before} after={proposedChanges.after} changes={proposedChanges.changes} onAccept={acceptChanges} onReject={rejectChanges} />
      )}

      {/* Phase 6: Agent Comparison */}
      {showAgentSelector && (
        <AgentSelector
          documentName={activeSection}
          isOpen={showAgentSelector}
          onClose={() => setShowAgentSelector(false)}
          onStartComparison={handleStartComparison}
        />
      )}

      {showComparisonViewer && comparisonResults && (
        <Dialog open={showComparisonViewer} onOpenChange={setShowComparisonViewer}>
          <DialogContent className="max-w-[95vw] max-h-[95vh] overflow-auto">
            <DialogHeader>
              <DialogTitle>Agent Comparison Results</DialogTitle>
              <DialogDescription>
                Compare different AI models and configurations for {activeSection}
              </DialogDescription>
            </DialogHeader>
            <ComparisonViewer
              comparisonData={comparisonResults}
              onSelectWinner={handleSelectWinner}
            />
          </DialogContent>
        </Dialog>
      )}

      {/* Fix Preview Modal - shows before/after diff before applying fixes */}
      {/* Supports both static fixes and AI-powered contextual fixes */}
      <FixPreviewModal
        isOpen={fixPreviewIssue !== null}
        onClose={() => setFixPreviewIssue(null)}
        onApply={(fixedText) => {
          // Save current state to version history before applying fix (enables undo)
          const newVersion = {
            id: `v${versionHistory.length}`,
            timestamp: new Date().toISOString(),
            message: `Before fix: ${fixPreviewIssue?.label || 'Issue fix'}`,
            sections: { ...sections },
            author: "User",
          };
          setVersionHistory([...versionHistory, newVersion]);
          
          // Apply the fix
          handleTextChange(fixedText);
          setFixPreviewIssue(null);
        }}
        issue={fixPreviewIssue}
        originalText={currentText}
        sectionName={activeSection}
      />

      {/* DocuSign-style Field Navigator - guides users through fillable fields */}
      {/* Provides floating nav bar, field-specific inputs (text/signature/date), and progress tracking */}
      <FieldNavigator
        fields={fillableFields}
        content={currentText}
        onFieldApply={handleFieldApply}
        onClose={() => setShowFieldNavigator(false)}
        isOpen={showFieldNavigator}
      />

      {/* Compliance Gate Dialog - shown before export */}
      <ComplianceGateDialog
        open={showComplianceGate}
        onOpenChange={setShowComplianceGate}
        sections={sections}
        citations={citations}
        exportFormat={pendingExportFormat}
        onProceed={() => {
          setShowComplianceGate(false);
          onExport();
        }}
        onDownloadReport={async () => {
          try {
            const analysis = performComplianceAnalysis(sections, citations);
            const blob = await exportApi.downloadComplianceReport(analysis);
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "compliance_report.pdf";
            a.click();
            URL.revokeObjectURL(url);
          } catch (error) {
            console.error("Failed to download compliance report:", error);
          }
        }}
      />
    </div>
  );
}

function EditView({ sectionName, text, onTextChange, issues, citations, onEditorReady }: any) {
  // Don't try to highlight specific text positions - TipTap will handle this
  // Just pass issue metadata for display purposes
  const qualityIssues: QualityIssue[] = [];

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Sticky Header - Section title and stats */}
      <div className="sticky top-0 z-10 bg-white border-b px-6 py-4 shadow-sm">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
            {sectionName}
          </h2>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span>{
              // Strip HTML tags for accurate word count
              text.replace(/<[^>]*>/g, '').split(/\s+/).filter(Boolean).length
            } words</span>
            <Separator orientation="vertical" className="h-4" />
            <span>{
              // Strip HTML tags for accurate character count
              text.replace(/<[^>]*>/g, '').length
            } chars</span>
            <Separator orientation="vertical" className="h-4" />
            <span>{issues.length} issues</span>
          </div>
        </div>
      </div>
      
      {/* Scrollable Editor Content */}
      <ScrollArea className="flex-1">
        <div className="p-6 max-w-5xl mx-auto">
          {/* Rich Text Editor - toolbar is sticky within this container */}
          <Card className="overflow-visible">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Document Editor</CardTitle>
                <CardDescription className="text-xs">
                  Live markdown rendering with quality feedback
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <RichTextEditor
                content={text}
                onChange={onTextChange}
                citations={citations}
                qualityIssues={qualityIssues}
                placeholder={`Start writing ${sectionName}...`}
                onEditorReady={onEditorReady}
                sectionName={sectionName}  // Pass section name for Copilot context
              />
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}

/**
 * CompareView - GitHub-style inline diff comparison
 * 
 * Displays version comparison with single-column inline diff and color highlighting.
 * Features:
 * - Green highlighting for added content
 * - Red highlighting with strikethrough for removed content
 * - Proper HTML rendering (no raw tags)
 * - Color legend for easy understanding
 * 
 * Dependencies:
 * - generateInlineDiff from editorUtils.ts for structured diff output
 * - sanitizeHtml from sanitizeHtml.ts for safe HTML rendering
 */
function CompareView({ sections, versionHistory, compareVersion, setCompareVersion, activeSection }: any) {
  const currentText = sections[activeSection] || "";
  const versionText = compareVersion ? compareVersion.sections[activeSection] || "" : currentText;
  
  // Generate structured diff for inline display
  const diffLines = useMemo(() => {
    return generateInlineDiff(versionText, currentText);
  }, [versionText, currentText]);

  // Count changes for summary
  const addedCount = diffLines.filter(l => l.type === 'added').length;
  const removedCount = diffLines.filter(l => l.type === 'removed').length;
  const hasChanges = addedCount > 0 || removedCount > 0;

  return (
    <ScrollArea className="h-full">
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Header with version selector */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold">Compare Versions</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Comparing: <span className="font-medium">{activeSection}</span>
            </p>
          </div>
          <Select value={compareVersion?.id || "current"} onValueChange={(v) => setCompareVersion(versionHistory.find((h: any) => h.id === v) || null)}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select version to compare" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="current">Current (unsaved)</SelectItem>
              {versionHistory.map((v: any) => (
                <SelectItem key={v.id} value={v.id}>
                  {v.message} — {new Date(v.timestamp).toLocaleTimeString()}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Color legend and summary */}
        <div className="flex items-center justify-between bg-slate-50 rounded-lg p-3">
          <div className="flex gap-6 text-sm">
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-100 border border-green-300 rounded" />
              <span className="text-green-700">Added</span>
              {hasChanges && <Badge variant="secondary" className="bg-green-100 text-green-700">{addedCount}</Badge>}
            </span>
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-100 border border-red-300 rounded" />
              <span className="text-red-700">Removed</span>
              {hasChanges && <Badge variant="secondary" className="bg-red-100 text-red-700">{removedCount}</Badge>}
            </span>
          </div>
          {!hasChanges && (
            <span className="text-sm text-muted-foreground">No changes detected</span>
          )}
        </div>

        {/* Single-column inline diff */}
        <Card className="overflow-hidden">
          <CardHeader className="pb-3 bg-gradient-to-r from-slate-50 to-slate-100/50">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-medium">Inline Diff</CardTitle>
                <CardDescription className="text-xs">
                  {compareVersion ? `Comparing with: ${compareVersion.message}` : 'Select a version to compare'}
                </CardDescription>
              </div>
              {hasChanges && (
                <Badge variant="outline" className="text-xs">
                  {addedCount + removedCount} changes
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[500px]">
              <div className="divide-y divide-slate-100">
                {diffLines.length > 0 ? (
                  diffLines.map((line, idx) => (
                    <div 
                      key={idx}
                      className={`px-4 py-3 text-sm transition-colors ${
                        line.type === 'added' 
                          ? 'bg-green-50 border-l-4 border-l-green-400' 
                          : line.type === 'removed' 
                            ? 'bg-red-50 border-l-4 border-l-red-400' 
                            : 'bg-white hover:bg-slate-50'
                      }`}
                    >
                      {/* Line number indicator */}
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-12 text-xs text-muted-foreground font-mono">
                          {line.type === 'added' && (
                            <span className="text-green-600">+{line.lineNumber?.after || ''}</span>
                          )}
                          {line.type === 'removed' && (
                            <span className="text-red-600">-{line.lineNumber?.before || ''}</span>
                          )}
                          {line.type === 'unchanged' && (
                            <span>{line.lineNumber?.after || ''}</span>
                          )}
                        </div>
                        {/* Content with proper HTML rendering */}
                        <div 
                          className={`flex-1 prose prose-sm max-w-none ${
                            line.type === 'added' 
                              ? 'text-green-800' 
                              : line.type === 'removed' 
                                ? 'text-red-800 line-through opacity-75' 
                                : 'text-slate-700'
                          }`}
                          dangerouslySetInnerHTML={{ 
                            __html: sanitizeHtml(line.content) || '<span class="text-muted-foreground italic">(empty)</span>' 
                          }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-8 text-center text-muted-foreground">
                    <p>No content to compare</p>
                    <p className="text-sm mt-1">Select a version from the dropdown above</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Version info footer */}
        {compareVersion && (
          <div className="text-xs text-muted-foreground text-center">
            Comparing <span className="font-medium">{compareVersion.message}</span> ({new Date(compareVersion.timestamp).toLocaleString()}) 
            with current unsaved version
          </div>
        )}
      </div>
    </ScrollArea>
  );
}

function HistoryView({ versionHistory, onRestore, onCompare }: any) {
  return (
    <ScrollArea className="h-full">
      <div className="p-6 space-y-6">
        <h2 className="text-3xl font-bold">Version History</h2>

        <div className="space-y-3">
          {versionHistory
            .slice()
            .reverse()
            .map((version: any, idx: number) => (
              <Card key={version.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-base">{version.message}</CardTitle>
                      <CardDescription className="mt-1">
                        {new Date(version.timestamp).toLocaleString()} • by {version.author}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => onCompare(version)}>
                        Compare
                      </Button>
                      {idx > 0 && (
                        <Button size="sm" onClick={() => onRestore(version)}>
                          Restore
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    {Object.keys(version.sections).length} sections • {Object.values(version.sections).reduce((sum: number, s: any) => sum + s.split(/\s+/).length, 0)} total words
                  </p>
                </CardContent>
              </Card>
            ))}
        </div>
      </div>
    </ScrollArea>
  );
}

function AutoImproveModal({ before, after, changes, onAccept, onReject }: any) {
  return (
    <Dialog open onOpenChange={onReject}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            Auto-Improve Suggestions
          </DialogTitle>
          <DialogDescription>Review proposed changes to improve quality score to 85+</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <div>
            <h4 className="font-semibold mb-3">Proposed Changes ({changes.length})</h4>
            <div className="space-y-2">
              {changes.map((change: any, idx: number) => (
                <div key={idx} className="flex items-start gap-3 text-sm border rounded-lg p-3 bg-muted/50">
                  <Badge variant={change.type === "fix" ? "destructive" : change.type === "enhance" ? "default" : "secondary"} className="text-[10px]">
                    {change.type.toUpperCase()}
                  </Badge>
                  <span className="flex-1">{change.text}</span>
                  <span className="text-muted-foreground text-xs">Line {change.line}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Card className="border-destructive/50 bg-destructive/5">
              <CardHeader>
                <CardTitle className="text-sm">Before</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-64">
                  <pre className="text-xs font-mono whitespace-pre-wrap">{before}</pre>
                </ScrollArea>
              </CardContent>
            </Card>

            <Card className="border-green-500/50 bg-green-50">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  After
                  <Badge className="bg-green-600">IMPROVED</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-64">
                  <pre className="text-xs font-mono whitespace-pre-wrap">{after}</pre>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onReject}>
            Reject Changes
          </Button>
          <Button onClick={onAccept} className="bg-green-600 hover:bg-green-700">
            Accept All Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function QualityBar({ label, score }: { label: string; score: number }) {
  const percentage = Math.max(0, Math.min(100, score));

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-xs font-medium">{label}</span>
        <span className="text-xs font-bold">{Math.round(percentage)}</span>
      </div>
      <Progress value={percentage} className="h-2" />
    </div>
  );
}

function DependenciesView({ collaborationMetadata }: { collaborationMetadata?: CollaborationMetadata | null }) {
  return (
    <ScrollArea className="h-full">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
              Document Dependencies
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Phase 4: Agent collaboration and cross-referencing
            </p>
          </div>
        </div>

        <DependencyGraph collaborationMetadata={collaborationMetadata} />
      </div>
    </ScrollArea>
  );
}
