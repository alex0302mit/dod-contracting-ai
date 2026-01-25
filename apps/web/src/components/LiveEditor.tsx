import { useState, useEffect, useMemo, useCallback, useRef } from "react";
// Icons - Loader2 added for bulk fix loading spinner, ChevronDown for collapsible panels
// AlertTriangle for hallucination, MessageSquare for vague language, RefreshCw for loading
// ChevronLeft/ChevronRight for collapsible sidebars (used for both expand and collapse)
import { ArrowLeft, Save, Sparkles, FileText, Clock, GitCompare, GitBranch, Tag, ShieldCheck, FormInput, MessageCircle, Layers, Loader2, Check, ChevronDown, ChevronLeft, ChevronRight, ChevronUp, AlertTriangle, RefreshCw, Download, X, Filter, Eye, EyeOff } from "lucide-react";
// API services for AI-powered features
import { copilotApi, qualityApi, exportApi, versionApi, QualityAnalysisResponse, DocumentVersion } from "@/services/api";
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
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
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
import { BatchFixPreviewModal } from "./editor/BatchFixPreviewModal";
import { IssueInlinePopover, InlinePopoverIssue } from "./editor/IssueInlinePopover";
import { FeedbackButtons } from "./editor/FeedbackButtons";
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
// File import components for drag-and-drop document import
import { FileDropZone } from "./editor/FileDropZone";
import { ImportOptionsDialog } from "./editor/ImportOptionsDialog";
import { ImportedDocumentsList, ImportedDocument } from "./editor/ImportedDocumentsList";
import { useDocumentImport, ImportResult, ImportPlacement } from "@/hooks/useDocumentImport";
import { toast } from "sonner";
// Alert dialog for delete confirmation
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

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
  // Version API integration state
  const [isLoadingVersions, setIsLoadingVersions] = useState(false);
  const [versionSaveInProgress, setVersionSaveInProgress] = useState(false);
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

  // Batch fix preview modal state - shows all fixable issues with preview before applying
  const [showBatchFixPreview, setShowBatchFixPreview] = useState(false);

  // Inline popover state - tracks which highlighted text was clicked in the editor
  // Shows a popover with issue details and "Fix with AI" button at click coordinates
  const [inlinePopover, setInlinePopover] = useState<{
    issue: InlinePopoverIssue;
    position: { x: number; y: number };
  } | null>(null);

  // Issue highlight state - tracks which issue card is selected for highlighting
  // When an issue is selected, all instances are highlighted and we scroll to the target
  const [selectedIssue, setSelectedIssue] = useState<{
    id: string;
    pattern: string;
    kind: IssueKind;
    occurrenceIndex?: number;
  } | null>(null);

  // Issue finder toggle - allows users to enable/disable issue detection
  const [issueFinderEnabled, setIssueFinderEnabled] = useState(true);

  // Dismissed issues - session-only tracking of false positives
  const [dismissedIssueIds, setDismissedIssueIds] = useState<Set<string>>(new Set());

  // Issue filter state - filter by type (all, tbd, hallucination, compliance)
  const [issueFilter, setIssueFilter] = useState<'all' | 'tbd' | 'hallucination' | 'compliance' | 'vague'>('all');

  // Current issue index for floating navigation
  const [currentIssueIndex, setCurrentIssueIndex] = useState(0);

  // Collapsible sidebar state - allows users to hide/show sidebars for more editing space
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);

  // Compliance gate dialog state - shown before export
  const [showComplianceGate, setShowComplianceGate] = useState(false);
  const [pendingExportFormat, setPendingExportFormat] = useState<"pdf" | "docx">("pdf");

  // Ref to the editor container for DOM-based highlighting
  const editorContainerRef = useRef<HTMLDivElement>(null);

  // Document import state - for drag-and-drop PDF/DOCX import
  const { convertFile, converting, progress: importProgress, error: importError, clearError: clearImportError } = useDocumentImport();
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [showImportDialog, setShowImportDialog] = useState(false);
  // Imported documents list - tracks all imported files, persisted in localStorage
  // Use lazy initialization to load from localStorage synchronously on first render
  const [importedDocuments, setImportedDocuments] = useState<ImportedDocument[]>(() => {
    const stored = localStorage.getItem('importedDocuments');
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch (e) {
        console.error('Failed to parse stored imports:', e);
        return [];
      }
    }
    return [];
  });
  const [deleteConfirmDoc, setDeleteConfirmDoc] = useState<ImportedDocument | null>(null);

  // Save imported documents to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('importedDocuments', JSON.stringify(importedDocuments));
  }, [importedDocuments]);

  // Restore section content from imported documents on mount
  useEffect(() => {
    const stored = localStorage.getItem('importedDocuments');
    if (stored) {
      try {
        const docs: ImportedDocument[] = JSON.parse(stored);
        const restoredSections = { ...sections };
        let hasChanges = false;
        docs.forEach(doc => {
          if (doc.content && doc.placement === 'new_section' && !sections[doc.sectionName]) {
            restoredSections[doc.sectionName] = doc.content;
            hasChanges = true;
          }
        });
        if (hasChanges) {
          setSections(restoredSections);
        }
      } catch (e) {
        console.error('Failed to restore sections from imports:', e);
      }
    }
  }, []); // Run once on mount

  // Load version history from backend on mount
  useEffect(() => {
    if (!documentId) return;

    const loadVersionsFromBackend = async () => {
      setIsLoadingVersions(true);
      try {
        const response = await versionApi.list(documentId);
        if (response.versions.length > 0) {
          // Convert backend versions to frontend format
          const backendVersions = response.versions.map((v: DocumentVersion) => ({
            id: v.id,
            timestamp: v.created_at,
            message: v.message || `Version ${v.version_number}`,
            sections: v.sections_json ? JSON.parse(v.sections_json) : { [documentName]: v.content },
            author: v.author || 'Unknown',
          }));
          // Merge with initial version, keeping backend versions first (they're sorted desc by version_number)
          setVersionHistory(backendVersions.reverse());
        }
      } catch (error) {
        console.error('Failed to load version history:', error);
        // Keep the default initial version on error
      } finally {
        setIsLoadingVersions(false);
      }
    };

    loadVersionsFromBackend();
  }, [documentId, documentName]);

  const currentText = sections[activeSection] || "";
  // Local quality score (fast, client-side fallback)
  const quality = computeQualityScore(currentText, citations);
  // Local issues from text analysis (TBD placeholders, compliance, etc.)
  const localIssues = computeIssues(currentText);
  
  // Quality analysis is now MANUAL - user must click "Re-analyze" button after editing
  // Initial scores come from precomputed initialQualityScores passed as props
  // When user edits, section is marked "stale" but no API call is made automatically
  
  /**
   * Manual handler to trigger quality re-analysis
   * Called when user clicks the "Re-analyze" button after completing their edits
   * 
   * Dependencies:
   * - qualityApi.analyze: Backend QualityAgent for AI-powered 5-category analysis
   * - apiQualityBySection: Cache of quality scores by section name
   * - staleSections: Set of sections that have been edited since last analysis
   */
  const handleReanalyzeQuality = async () => {
    // Don't analyze very short content
    if (currentText.replace(/<[^>]*>/g, '').trim().length < 50) {
      setQualityError('Content too short to analyze (minimum 50 characters)');
      return;
    }
    
    setIsLoadingQuality(true);
    setQualityError(null);
    
    try {
      // Call backend QualityAgent for comprehensive 5-category analysis
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
  };
  
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

    // Add vague language issues from API if available
    // These are non-specific terms that should be replaced with measurable language
    if (apiQuality?.breakdown?.vague_language) {
      const vagueData = apiQuality.breakdown.vague_language;

      // Common vague words to detect in DoD documents
      const vagueWords = [
        'several', 'many', 'some', 'various', 'numerous', 'appropriate', 'adequate',
        'may', 'might', 'could', 'possibly', 'generally', 'typically', 'usually',
        'often', 'sometimes', 'reasonable', 'significant', 'substantial', 'considerable',
        'as needed', 'as required', 'as appropriate', 'sufficient', 'properly'
      ];

      // Only process if vague language was detected (score < 100 or count > 0)
      if (vagueData.count > 0 || vagueData.score < 100) {
        // Strip HTML and get plain text for pattern matching
        const plainText = currentText.replace(/<[^>]*>/g, '');
        const plainTextLower = plainText.toLowerCase();

        // Track which vague words were found to avoid duplicates
        const foundVagueWords = new Set<string>();

        // Scan for each vague word in the document
        vagueWords.forEach((vagueWord) => {
          // Case-insensitive search for the vague word
          const regex = new RegExp(`\\b${vagueWord}\\b`, 'gi');
          const matches = plainText.match(regex);

          if (matches && matches.length > 0 && !foundVagueWords.has(vagueWord.toLowerCase())) {
            foundVagueWords.add(vagueWord.toLowerCase());

            // Find context around the first occurrence
            const wordIndex = plainTextLower.indexOf(vagueWord.toLowerCase());
            const contextStart = Math.max(0, wordIndex - 50);
            const contextEnd = Math.min(plainText.length, wordIndex + vagueWord.length + 50);
            const context = plainText.substring(contextStart, contextEnd);

            // Create individual issue for each unique vague word found
            allIssues.push({
              id: `vague-${vagueWord.replace(/\s+/g, '-')}`,
              kind: 'warning',
              label: `Vague language: "${vagueWord}" - Consider using specific, measurable terms`,
              pattern: vagueWord,
              context: `...${context}...`,
              fix: {
                label: 'Make specific with AI',
                requiresAI: true,
                pattern: vagueWord,
                occurrenceIndex: 0, // Target the first occurrence
              },
            });
          }
        });

        // Also add issues from the API response if they contain actionable information
        const vagueIssues: string[] = vagueData.issues || [];
        vagueIssues.forEach((issue: string, index: number) => {
          // Extract vague word from issue message if possible (e.g., "Contains 'several'")
          const wordMatch = issue.match(/'([^']+)'/);
          const extractedWord = wordMatch ? wordMatch[1].toLowerCase() : null;

          // Only add if we haven't already added an issue for this word
          if (extractedWord && !foundVagueWords.has(extractedWord)) {
            foundVagueWords.add(extractedWord);

            allIssues.push({
              id: `vague-api-${index}`,
              kind: 'warning',
              label: issue,
              pattern: extractedWord,
              context: issue,
              fix: {
                label: 'Make specific with AI',
                requiresAI: true,
                pattern: extractedWord,
                occurrenceIndex: 0,
              },
            });
          }
        });
      }
    }

    return allIssues;
  }, [localIssues, apiQuality, currentText]);

  // Filter out dismissed issues
  const visibleIssues = useMemo(() => {
    return issues.filter(i => !dismissedIssueIds.has(i.id));
  }, [issues, dismissedIssueIds]);

  // Apply type filter to visible issues
  const filteredIssues = useMemo(() => {
    if (issueFilter === 'all') return visibleIssues;
    if (issueFilter === 'tbd') {
      return visibleIssues.filter(i => i.pattern?.toLowerCase().includes('tbd'));
    }
    if (issueFilter === 'vague') {
      return visibleIssues.filter(i => i.id.startsWith('vague'));
    }
    return visibleIssues.filter(i => i.kind === issueFilter);
  }, [visibleIssues, issueFilter]);

  // Count issues by type for filter dropdown
  const issueCountsByType = useMemo(() => ({
    all: visibleIssues.length,
    tbd: visibleIssues.filter(i => i.pattern?.toLowerCase().includes('tbd')).length,
    hallucination: visibleIssues.filter(i => i.kind === 'hallucination').length,
    compliance: visibleIssues.filter(i => i.kind === 'compliance').length,
    vague: visibleIssues.filter(i => i.id.startsWith('vague')).length,
  }), [visibleIssues]);

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

  // Handle file selection from drop zone
  const handleFileSelect = async (file: File) => {
    clearImportError();
    const result = await convertFile(file);
    if (result) {
      setImportResult(result);
      setShowImportDialog(true);
    } else if (importError) {
      toast.error(importError);
    }
  };

  // Handle import dialog confirmation
  const handleImportConfirm = (placement: ImportPlacement, sectionName?: string) => {
    if (!importResult) return;

    const html = importResult.html;
    let targetSectionName = activeSection;

    if (placement === 'new_section') {
      const name = sectionName || importResult.filename.replace(/\.(pdf|docx)$/i, '');
      targetSectionName = name;
      // Add new section
      setSections({ ...sections, [name]: html });
      setActiveSection(name);
      toast.success(`Created new section: ${name}`);
    } else if (placement === 'replace_current') {
      // Replace current section content
      setSections({ ...sections, [activeSection]: html });
      toast.success(`Replaced content in "${activeSection}"`);
    } else if (placement === 'append_current') {
      // Append to current section
      const currentContent = sections[activeSection] || '';
      setSections({ ...sections, [activeSection]: currentContent + html });
      toast.success(`Appended content to "${activeSection}"`);
    }

    // Mark section as stale for quality re-analysis
    setStaleSections(prev => new Set(prev).add(placement === 'new_section' ? (sectionName || '') : activeSection));

    // Track the imported document with content for persistence
    const newImport: ImportedDocument = {
      id: crypto.randomUUID(),
      filename: importResult.filename,
      fileType: importResult.fileType,
      importedAt: new Date().toISOString(),
      placement,
      sectionName: targetSectionName,
      content: html,
    };
    setImportedDocuments(prev => [...prev, newImport]);

    // Clear import state
    setImportResult(null);
    setShowImportDialog(false);
  };

  // Handle delete imported document - opens confirmation dialog
  const handleDeleteImport = (id: string) => {
    const doc = importedDocuments.find(d => d.id === id);
    if (doc) {
      setDeleteConfirmDoc(doc);
    }
  };

  // Confirm delete - optionally removes section content
  const confirmDeleteImport = (deleteSectionContent: boolean) => {
    if (!deleteConfirmDoc) return;

    if (deleteSectionContent) {
      const newSections = { ...sections };
      if (deleteConfirmDoc.placement === 'new_section') {
        // Remove the section entirely
        delete newSections[deleteConfirmDoc.sectionName];
        // Switch to another section if we deleted the active one
        if (activeSection === deleteConfirmDoc.sectionName) {
          const remainingSections = Object.keys(newSections);
          setActiveSection(remainingSections[0] || '');
        }
      } else {
        // For replace/append, clear the section content
        newSections[deleteConfirmDoc.sectionName] = '<p></p>';
      }
      setSections(newSections);
      toast.success(`Removed "${deleteConfirmDoc.filename}" and its content`);
    } else {
      toast.success(`Removed "${deleteConfirmDoc.filename}" from imports list`);
    }

    // Remove from imported documents list
    setImportedDocuments(prev => prev.filter(d => d.id !== deleteConfirmDoc.id));
    setDeleteConfirmDoc(null);
  };

  const commitVersion = async () => {
    const message = prompt("Version commit message:", "Manual edit");
    if (!message) return;

    // Combine all sections into content for backend
    const content = Object.values(sections).join('\n\n');

    // If we have a documentId, save to backend
    if (documentId) {
      setVersionSaveInProgress(true);
      try {
        const savedVersion = await versionApi.create(documentId, {
          content,
          sections,
          message,
          author: "User",
        });

        // Add the backend version to local state
        const newVersion = {
          id: savedVersion.id,
          timestamp: savedVersion.created_at,
          message: savedVersion.message || message,
          sections: { ...sections },
          author: savedVersion.author || "User",
        };
        setVersionHistory([...versionHistory, newVersion]);
        toast.success('Version saved');
      } catch (error) {
        console.error('Failed to save version:', error);
        toast.error('Failed to save version to server');
        // Still save locally as fallback
        const newVersion = {
          id: `v${versionHistory.length}`,
          timestamp: new Date().toISOString(),
          message,
          sections: { ...sections },
          author: "User",
        };
        setVersionHistory([...versionHistory, newVersion]);
      } finally {
        setVersionSaveInProgress(false);
      }
    } else {
      // No documentId - save locally only
      const newVersion = {
        id: `v${versionHistory.length}`,
        timestamp: new Date().toISOString(),
        message,
        sections: { ...sections },
        author: "User",
      };
      setVersionHistory([...versionHistory, newVersion]);
    }
  };

  const restoreVersion = async (version: typeof versionHistory[0]) => {
    if (!confirm(`Restore version "${version.message}"? This will create a new version with the restored content.`)) {
      return;
    }

    // Check if this is a backend version (UUID format) or local version (v0, v1, etc.)
    const isBackendVersion = documentId && version.id && !version.id.startsWith('v');

    if (isBackendVersion) {
      // Use backend API to restore
      setVersionSaveInProgress(true);
      try {
        const restored = await versionApi.restore(documentId, version.id);
        // Update local sections with restored content
        const restoredSections = restored.sections_json
          ? JSON.parse(restored.sections_json)
          : { [documentName]: restored.content };
        setSections(restoredSections);

        // Add the restored version to history
        const newVersion = {
          id: restored.id,
          timestamp: restored.created_at,
          message: restored.message || `Restored from version`,
          sections: restoredSections,
          author: restored.author || "User",
        };
        setVersionHistory([...versionHistory, newVersion]);
        toast.success('Version restored');
      } catch (error) {
        console.error('Failed to restore version:', error);
        toast.error('Failed to restore version');
      } finally {
        setVersionSaveInProgress(false);
      }
    } else {
      // Local version - restore directly
      setSections({ ...version.sections });
    }

    setViewMode("edit");
    setCompareVersion(null);
  };

  const generateAutoImprove = () => {
    const improvements = {
      before: currentText,
      after: autoImproveText(currentText, quality, filteredIssues),
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

  /**
   * Dismiss an issue (mark as false positive for this session)
   */
  const handleDismissIssue = useCallback((issueId: string) => {
    setDismissedIssueIds(prev => new Set([...prev, issueId]));
    // Clear highlight if this was the selected issue
    if (selectedIssue?.id === issueId) {
      handleClearHighlights();
    }
  }, [selectedIssue, handleClearHighlights]);

  /**
   * Restore all dismissed issues
   */
  const handleRestoreDismissed = useCallback(() => {
    setDismissedIssueIds(new Set());
  }, []);

  /**
   * Navigate to previous issue
   */
  const handlePrevIssue = useCallback(() => {
    if (filteredIssues.length === 0) return;
    const newIndex = Math.max(0, currentIssueIndex - 1);
    setCurrentIssueIndex(newIndex);
    handleIssueClick(filteredIssues[newIndex]);
  }, [currentIssueIndex, filteredIssues, handleIssueClick]);

  /**
   * Navigate to next issue
   */
  const handleNextIssue = useCallback(() => {
    if (filteredIssues.length === 0) return;
    const newIndex = Math.min(filteredIssues.length - 1, currentIssueIndex + 1);
    setCurrentIssueIndex(newIndex);
    handleIssueClick(filteredIssues[newIndex]);
  }, [currentIssueIndex, filteredIssues, handleIssueClick]);

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
        target.closest('mark') ||  // TipTap's native highlight uses <mark> element
        target.closest('[data-inline-popover]')  // Inline issue popover
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

  // Keyboard navigation for issues (Ctrl+[ for previous, Ctrl+] for next)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!issueFinderEnabled || filteredIssues.length === 0) return;

      if (e.metaKey || e.ctrlKey) {
        if (e.key === '[') {
          e.preventDefault();
          handlePrevIssue();
        } else if (e.key === ']') {
          e.preventDefault();
          handleNextIssue();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [issueFinderEnabled, filteredIssues.length, handlePrevIssue, handleNextIssue]);

  // Reset issue index when filtered issues change
  useEffect(() => {
    setCurrentIssueIndex(0);
  }, [filteredIssues.length]);

  // Click handler for highlighted text in editor - shows inline popover
  // Detects clicks on .quality-issue spans or <mark> elements (TipTap highlight)
  useEffect(() => {
    const handleEditorClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;

      // Check if clicked on a quality issue mark or highlight
      const issueElement = target.closest('.quality-issue') || target.closest('mark');

      if (issueElement) {
        // Extract issue data from data attributes
        const issueId = issueElement.getAttribute('data-issue-id');
        const issueKind = issueElement.getAttribute('data-issue-kind');
        const issueLabel = issueElement.getAttribute('data-issue-label') || issueElement.getAttribute('title');

        // Find the full issue from our issues array, or create a minimal one from attributes
        const matchedIssue = issues.find(i => i.id === issueId) || {
          id: issueId || `inline-${Date.now()}`,
          kind: (issueKind as InlinePopoverIssue['kind']) || 'warning',
          label: issueLabel || 'Issue detected',
          pattern: issueElement.textContent || '',
        };

        // Set the inline popover state with issue and click position
        setInlinePopover({
          issue: {
            id: matchedIssue.id,
            kind: matchedIssue.kind as InlinePopoverIssue['kind'],
            label: matchedIssue.label,
            pattern: matchedIssue.pattern,
          },
          position: { x: e.clientX, y: e.clientY },
        });

        e.stopPropagation(); // Prevent triggering click-away handlers
      }
    };

    const editorElement = editorContainerRef.current?.querySelector('.ProseMirror');
    editorElement?.addEventListener('click', handleEditorClick);

    return () => {
      editorElement?.removeEventListener('click', handleEditorClick);
    };
  }, [issues]);

  /**
   * Handle fixing all issues with AI sequentially
   * 
   * Processes each fixable issue one by one, using AI to generate
   * contextual replacements. Updates the document incrementally.
   * Each fix is applied before the next to ensure proper context.
   */
  const handleFixAllIssues = async () => {
    // Get only filtered issues that have AI fixes (requiresAI flag set)
    const fixableIssues = filteredIssues.filter(i => i.fix?.requiresAI);
    
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
      {/* Header toolbar - compact 48px with three zones */}
      <div className="border-b border-border bg-card/95 backdrop-blur-sm px-4 py-2 flex items-center h-12">
        {/* LEFT ZONE: Navigation + Document Context */}
        <div className="flex items-center gap-3 min-w-0">
          <TooltipProvider delayDuration={100}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onBack}>
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Back to documents</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <Separator orientation="vertical" className="h-5" />

          {/* Document context */}
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="h-4 w-4 text-primary flex-shrink-0" />
            <span className="font-medium text-sm truncate max-w-[180px]">
              {documentName || "Untitled Document"}
            </span>
            <span className="text-xs text-muted-foreground hidden sm:inline">
              • {activeSection}
            </span>
          </div>
        </div>

        {/* CENTER ZONE: View Mode Tabs */}
        <div className="flex-1 flex justify-center px-4">
          <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as "edit" | "compare" | "history" | "dependencies")}>
            <TabsList className="h-8">
              <TabsTrigger value="edit" className="gap-1.5 text-sm px-3 py-1">
                <FileText className="h-3.5 w-3.5" />
                <span className="hidden md:inline">Edit</span>
              </TabsTrigger>
              <TabsTrigger value="compare" className="gap-1.5 text-sm px-3 py-1">
                <GitCompare className="h-3.5 w-3.5" />
                <span className="hidden md:inline">Compare</span>
              </TabsTrigger>
              <TabsTrigger value="history" className="gap-1.5 text-sm px-3 py-1">
                <Clock className="h-3.5 w-3.5" />
                <span className="hidden md:inline">History</span>
              </TabsTrigger>
              {collaborationMetadata?.enabled && (
                <TabsTrigger value="dependencies" className="gap-1.5 text-sm px-3 py-1">
                  <GitBranch className="h-3.5 w-3.5" />
                  <span className="hidden lg:inline">Dependencies</span>
                </TabsTrigger>
              )}
            </TabsList>
          </Tabs>
        </div>

        {/* RIGHT ZONE: Actions */}
        <div className="flex items-center gap-1">
          {/* Secondary actions - icon only with tooltips */}
          <TooltipProvider delayDuration={100}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={commitVersion} disabled={versionSaveInProgress}>
                  {versionSaveInProgress ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">{versionSaveInProgress ? 'Saving...' : 'Commit version'}</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider delayDuration={100}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setShowAgentSelector(true)}
                >
                  <Layers className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Compare Agents</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* Field Navigator - only show when fields detected */}
          {fillableFields.length > 0 && (
            <FieldNavigatorButton
              fieldCount={fillableFields.length}
              onClick={() => setShowFieldNavigator(true)}
            />
          )}

          {/* Agent stats badge - compact */}
          {agentMetadata && Object.keys(agentMetadata).length > 0 && (
            <AgentStats agentMetadata={agentMetadata} />
          )}

          <Separator orientation="vertical" className="h-5 mx-1" />

          {/* Primary action - Export */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm" className="h-8 gap-2">
                <Download className="h-4 w-4" />
                <span className="hidden sm:inline">Export</span>
                <ChevronDown className="h-3.5 w-3.5 opacity-70" />
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

      {/* Main content area - overflow removed to allow sticky toolbar in RichTextEditor */}
      <div className="flex-1 flex">
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
                  {/* File import drop zone */}
                  <div className="mt-3 pt-3 border-t border-slate-100">
                    <FileDropZone
                      onFileSelect={handleFileSelect}
                      converting={converting}
                      progress={importProgress}
                      compact
                    />
                  </div>
                  {/* Imported documents list */}
                  <ImportedDocumentsList
                    documents={importedDocuments}
                    onDelete={handleDeleteImport}
                    onNavigate={(sectionName) => setActiveSection(sectionName)}
                  />
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

        {/* Main content - scroll container for sticky toolbar support */}
        <main className="flex-1 overflow-y-auto">
          {viewMode === "edit" && (
            <div ref={editorContainerRef} className="h-full">
              <EditView
                sectionName={activeSection}
                text={currentText}
                onTextChange={handleTextChange}
                issues={issueFinderEnabled ? filteredIssues : []}
                citations={citations}
                onEditorReady={setCurrentEditor}
                documentId={documentId}
                agentMetadata={agentMetadata}
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
              isLoading={isLoadingVersions}
              isSaving={versionSaveInProgress}
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
                    {/* Re-analyze button - only enabled when section has been edited (stale) */}
                    {/* User must click this after finishing edits to get updated quality score */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleReanalyzeQuality}
                      disabled={isLoadingQuality || !staleSections.has(activeSection)}
                      className="mt-2 h-7 text-xs"
                    >
                      <RefreshCw className={`h-3 w-3 mr-1.5 ${isLoadingQuality ? 'animate-spin' : ''}`} />
                      {isLoadingQuality ? 'Analyzing...' : 'Re-analyze'}
                    </Button>
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

            {/* Enhanced Issues Card with Toggle, Filter, and Grouped Issues */}
            <Card className="border-red-100 overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${issueFinderEnabled && filteredIssues.length > 0 ? 'bg-red-500 animate-pulse' : 'bg-slate-300'}`} />
                    Issues
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    {/* Issue finder toggle */}
                    <div className="flex items-center gap-1.5">
                      <Label htmlFor="issue-finder" className="text-[10px] text-muted-foreground">
                        {issueFinderEnabled ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
                      </Label>
                      <Switch
                        id="issue-finder"
                        checked={issueFinderEnabled}
                        onCheckedChange={(checked) => {
                          setIssueFinderEnabled(checked);
                          if (!checked) {
                            handleClearHighlights();
                          }
                        }}
                        className="scale-75"
                      />
                    </div>
                    <Badge variant={filteredIssues.length > 0 ? "destructive" : "secondary"} className="text-xs px-2">
                      {filteredIssues.length}
                    </Badge>
                  </div>
                </div>

                {/* Filter and controls row */}
                {issueFinderEnabled && visibleIssues.length > 0 && (
                  <div className="flex items-center gap-2 mt-2">
                    <Select value={issueFilter} onValueChange={(v) => setIssueFilter(v as typeof issueFilter)}>
                      <SelectTrigger className="h-7 text-[10px] flex-1">
                        <Filter className="h-3 w-3 mr-1" />
                        <SelectValue placeholder="Filter issues" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Issues ({issueCountsByType.all})</SelectItem>
                        <SelectItem value="tbd">TBD Placeholders ({issueCountsByType.tbd})</SelectItem>
                        <SelectItem value="hallucination">Hallucinations ({issueCountsByType.hallucination})</SelectItem>
                        <SelectItem value="compliance">Compliance ({issueCountsByType.compliance})</SelectItem>
                        <SelectItem value="vague">Vague Language ({issueCountsByType.vague})</SelectItem>
                      </SelectContent>
                    </Select>
                    {dismissedIssueIds.size > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-[10px] px-2"
                        onClick={handleRestoreDismissed}
                      >
                        +{dismissedIssueIds.size} hidden
                      </Button>
                    )}
                  </div>
                )}
              </CardHeader>

              {issueFinderEnabled && (
                <CardContent className="space-y-2 relative">
                  {/* Sticky Action Bar */}
                  {filteredIssues.filter(i => i.fix?.requiresAI).length > 1 && (
                    <div className="sticky top-0 z-10 -mx-6 px-6 py-2 bg-white/95 backdrop-blur-sm border-b mb-2">
                      <Button
                        className="w-full gap-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg"
                        size="sm"
                        onClick={() => setShowBatchFixPreview(true)}
                        disabled={isFixingAll}
                      >
                        {isFixingAll ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Fixing {fixProgress?.current || 1} of {fixProgress?.total}...
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4" />
                            Fix All with AI ({filteredIssues.filter(i => i.fix?.requiresAI).length})
                          </>
                        )}
                      </Button>
                    </div>
                  )}

                  {/* Floating Navigation Bar */}
                  {selectedIssue && filteredIssues.length > 1 && (
                    <div className="sticky top-12 z-10 -mx-6 px-4 py-1.5 bg-slate-50/95 backdrop-blur-sm border-y flex items-center justify-between text-xs">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={handlePrevIssue}
                        disabled={currentIssueIndex === 0}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span className="text-muted-foreground">
                        Issue {currentIssueIndex + 1} of {filteredIssues.length}
                        <span className="hidden sm:inline ml-1 text-slate-400">
                          (⌘[ / ⌘])
                        </span>
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={handleNextIssue}
                        disabled={currentIssueIndex === filteredIssues.length - 1}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  )}

                  {/* Issue Cards */}
                  {filteredIssues.map((issue, index) => {
                    const colors = getIssueColors(issue.kind);
                    const isSelected = selectedIssue?.id === issue.id;

                    return (
                      <div
                        key={issue.id}
                        data-issue-card
                        onClick={() => {
                          setCurrentIssueIndex(index);
                          handleIssueClick(issue);
                        }}
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

                        {/* Dismiss button */}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="absolute top-1 right-1 h-5 w-5 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-slate-200"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDismissIssue(issue.id);
                          }}
                          title="Dismiss this issue"
                        >
                          <X className="h-3 w-3 text-slate-400" />
                        </Button>

                        <div className="ml-4 pr-4">
                          <p className="text-xs text-slate-700 line-clamp-2 mb-2 leading-relaxed">
                            {issue.label}
                          </p>

                          {/* Fix button with AI styling */}
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

                  {/* Empty filtered state */}
                  {filteredIssues.length === 0 && visibleIssues.length > 0 && (
                    <div className="text-center py-4 text-xs text-muted-foreground">
                      No {issueFilter !== 'all' ? issueFilter : ''} issues found.
                      <Button
                        variant="link"
                        size="sm"
                        className="text-xs p-0 h-auto ml-1"
                        onClick={() => setIssueFilter('all')}
                      >
                        Show all
                      </Button>
                    </div>
                  )}
                </CardContent>
              )}

              {/* Issue finder disabled state */}
              {!issueFinderEnabled && (
                <CardContent>
                  <div className="text-center py-4 text-xs text-muted-foreground">
                    <EyeOff className="h-4 w-4 mx-auto mb-1 opacity-50" />
                    Issue detection is paused
                  </div>
                </CardContent>
              )}
            </Card>

            {/* No issues state - only show when enabled and no issues */}
            {issueFinderEnabled && visibleIssues.length === 0 && (
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

      {/* Inline Issue Popover - shows when clicking highlighted text in the editor */}
      <IssueInlinePopover
        isOpen={inlinePopover !== null}
        onClose={() => setInlinePopover(null)}
        issue={inlinePopover?.issue || null}
        position={inlinePopover?.position || { x: 0, y: 0 }}
        onFixWithAI={() => {
          if (inlinePopover?.issue) {
            // Find the full issue with fix details from the issues array
            const fullIssue = issues.find(i => i.id === inlinePopover.issue.id);
            if (fullIssue) {
              setFixPreviewIssue(fullIssue as any);
            } else {
              // Create a minimal issue with AI fix for patterns not in the issues array
              setFixPreviewIssue({
                id: inlinePopover.issue.id,
                kind: inlinePopover.issue.kind as 'error' | 'warning' | 'info' | 'compliance',
                label: inlinePopover.issue.label,
                pattern: inlinePopover.issue.pattern,
                fix: {
                  label: 'Fix with AI',
                  requiresAI: true,
                  pattern: inlinePopover.issue.pattern,
                },
              });
            }
            setInlinePopover(null);
          }
        }}
        onDismiss={() => setInlinePopover(null)}
      />

      {/* Batch Fix Preview Modal - shows all fixable issues with preview before applying */}
      <BatchFixPreviewModal
        isOpen={showBatchFixPreview}
        onClose={() => setShowBatchFixPreview(false)}
        issues={filteredIssues.filter(i => i.fix?.requiresAI)}
        documentText={currentText}
        sectionName={activeSection}
        onApplyFixes={(selectedIds, fixedText) => {
          // Save current state to version history before applying fixes (enables undo)
          const newVersion = {
            id: `v${versionHistory.length}`,
            timestamp: new Date().toISOString(),
            message: `Before batch fix: ${selectedIds.length} issues`,
            sections: { ...sections },
            author: "User",
          };
          setVersionHistory([...versionHistory, newVersion]);

          // Apply the fixes
          handleTextChange(fixedText);
          setShowBatchFixPreview(false);
        }}
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

      {/* Document Import Dialog - shown after file drop/selection */}
      <ImportOptionsDialog
        open={showImportDialog}
        onOpenChange={setShowImportDialog}
        importResult={importResult}
        currentSectionName={activeSection}
        existingSections={sectionNames}
        onConfirm={handleImportConfirm}
      />

      {/* Delete Import Confirmation Dialog */}
      <AlertDialog open={!!deleteConfirmDoc} onOpenChange={() => setDeleteConfirmDoc(null)}>
        <AlertDialogContent className="sm:max-w-[500px]">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-lg">Remove imported document?</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-2 p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                  <FileText className="h-4 w-4 text-slate-500 flex-shrink-0" />
                  <span className="text-sm font-medium text-slate-700 truncate">
                    {deleteConfirmDoc?.filename}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Imported into section: <span className="font-medium text-slate-700">"{deleteConfirmDoc?.sectionName}"</span>
                </p>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex flex-col gap-2 pt-4">
            <Button
              variant="outline"
              className="w-full justify-start h-auto py-3 px-4"
              onClick={() => confirmDeleteImport(false)}
            >
              <div className="text-left">
                <div className="font-medium">Keep content</div>
                <div className="text-xs text-muted-foreground font-normal">Only remove from imports list</div>
              </div>
            </Button>
            <Button
              variant="destructive"
              className="w-full justify-start h-auto py-3 px-4"
              onClick={() => confirmDeleteImport(true)}
            >
              <div className="text-left">
                <div className="font-medium">Delete everything</div>
                <div className="text-xs opacity-80 font-normal">Remove from list and delete section content</div>
              </div>
            </Button>
          </div>
          <AlertDialogFooter className="pt-2">
            <AlertDialogCancel className="w-full">Cancel</AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function EditView({ sectionName, text, onTextChange, issues, citations, onEditorReady, documentId, agentMetadata }: any) {
  // Don't try to highlight specific text positions - TipTap will handle this
  // Just pass issue metadata for display purposes
  const qualityIssues: QualityIssue[] = [];

  // Get agent info for this section (if available)
  const sectionAgentInfo = agentMetadata?.[sectionName];

  return (
    // No overflow-hidden - allows sticky toolbar to work with parent scroll container
    <div className="h-full flex flex-col">
      {/* Section Header - title and stats */}
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

      {/* Editor Content - no ScrollArea, parent main element handles scroll for sticky toolbar */}
      <div className="flex-1 p-6">
        <div className="max-w-5xl mx-auto space-y-4">
          {/* Rich Text Editor - toolbar is sticky within parent scroll container */}
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

          {/* Feedback Buttons - show only if this section was AI-generated */}
          {documentId && sectionAgentInfo?.agent && (
            <Card>
              <CardContent className="py-3 px-4">
                <FeedbackButtons
                  documentId={documentId}
                  sectionName={sectionName}
                  agentName={sectionAgentInfo.agent}
                />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
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

function HistoryView({ versionHistory, onRestore, onCompare, isLoading, isSaving }: any) {
  return (
    <ScrollArea className="h-full">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-3xl font-bold">Version History</h2>
          {(isLoading || isSaving) && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {isLoading ? 'Loading versions...' : 'Saving...'}
            </div>
          )}
        </div>

        {isLoading && versionHistory.length === 0 ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            Loading version history...
          </div>
        ) : versionHistory.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No versions yet. Click the save button to create a version snapshot.
          </div>
        ) : (
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
                        <Button variant="outline" size="sm" onClick={() => onCompare(version)} disabled={isSaving}>
                          Compare
                        </Button>
                        {idx > 0 && (
                          <Button size="sm" onClick={() => onRestore(version)} disabled={isSaving}>
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
        )}
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
