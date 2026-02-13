/**
 * EditorScreen Component
 *
 * Wraps the existing LiveEditor with ConsoleRail integration.
 * Opens ConsoleRail by default and syncs quality data.
 *
 * Project-aware mode: When navigating from a project document, this screen
 * fetches ALL generated documents for that project and loads them as sections
 * in the editor sidebar. Each section is backed by its own documentId so that
 * lineage, reasoning, quality, and version panels update when switching sections.
 *
 * This is the flagship editor screen for document editing.
 *
 * Dependencies:
 * - LiveEditor for the editor functionality
 * - useConsoleRail for rail state management
 * - useNavigation for content and navigation
 * - useEditorNavigation for document ID + project ID tracking
 * - projectsApi for fetching project documents in project-aware mode
 * - convertMarkdownToHtml for converting markdown content to editor-ready HTML
 */

import { useEffect, useState, useCallback, useMemo } from 'react';
import { LiveEditor } from '@/components/LiveEditor';
import { useConsoleRail } from '@/contexts/ConsoleRailContext';
import { useNavigation } from '@/contexts/NavigationContext';
import { useEditorNavigation } from '@/contexts/EditorNavigationContext';
import { projectsApi } from '@/services/api';
import { convertMarkdownToHtml } from '@/lib/markdownToHtml';
import { FileText, Loader2 } from 'lucide-react';

// Default sections for when editor opens without content
const DEFAULT_SECTIONS: Record<string, string> = {
  'Overview': '<p>Start writing your document here, or generate content using Quick Generate.</p>',
};

// Default citations (empty)
const DEFAULT_CITATIONS: Array<{
  id: number;
  source: string;
  page: number;
  text: string;
  bbox: { x: number; y: number; w: number; h: number };
}> = [];

// Default assumptions (empty)
const DEFAULT_ASSUMPTIONS: Array<{
  id: string;
  text: string;
  source: string;
}> = [];

/**
 * EditorScreen wraps LiveEditor with ACES layout.
 * Supports two modes:
 * 1. Single-document mode (Quick Generate / no projectId) -- loads one section
 * 2. Project-aware mode (projectId present) -- fetches all generated docs as sections
 */
export function EditorScreen() {
  // Note: ConsoleRail is NOT shown for Editor - LiveEditor has its own quality panel
  const { closeRail } = useConsoleRail();
  // Include setEditorContent to sync content before export navigation
  const { editorContent, navigate, goBack, setEditorContent } = useNavigation();
  // Get pending content with documentId and projectId for project-aware mode
  const { pendingEditorContent, clearPendingContent } = useEditorNavigation();

  // Track document ID, name, and project ID for reasoning/lineage features
  const [documentId, setDocumentId] = useState<string | undefined>(undefined);
  const [documentName, setDocumentName] = useState<string | undefined>(undefined);
  const [projectId, setProjectId] = useState<string | undefined>(undefined);

  // documentIdMap: maps section name -> database document ID
  // Used in project-aware mode so LiveEditor can resolve the active documentId per section
  const [documentIdMap, setDocumentIdMap] = useState<Record<string, string>>({});

  // Loading state for project document fetch
  const [isLoadingProjectDocs, setIsLoadingProjectDocs] = useState(false);

  // Editor state
  const [sections, setSections] = useState<Record<string, string>>(
    editorContent || DEFAULT_SECTIONS
  );
  const [citations] = useState(DEFAULT_CITATIONS);
  const [assumptions] = useState(DEFAULT_ASSUMPTIONS);
  const [agentMetadata] = useState<Record<string, any>>({});
  const [collaborationMetadata] = useState<any>(null);
  const [qualityAnalysis] = useState<Record<string, any>>({});

  // Close ConsoleRail when entering Editor (LiveEditor has its own quality panel)
  useEffect(() => {
    closeRail();
  }, [closeRail]);

  // Load content from EditorNavigationContext when navigating from a project document.
  // If projectId is present, fetch ALL generated docs for the project and build sections.
  // Otherwise, fall back to single-document mode (same as before).
  useEffect(() => {
    if (!pendingEditorContent) return;

    const { content, documentName: docName, documentId: docId, projectId: projId } = pendingEditorContent;

    // Always set the clicked document's ID and name for initial display
    setDocumentId(docId);
    setDocumentName(docName);
    setProjectId(projId);

    if (projId) {
      // Project-aware mode: fetch all generated documents for this project
      setIsLoadingProjectDocs(true);

      // Start with the clicked document immediately so the editor isn't blank
      setSections({ [docName]: content });
      setDocumentIdMap(docId ? { [docName]: docId } : {});

      // Fetch remaining project docs in background
      projectsApi.getDocuments(projId)
        .then((response) => {
          const allDocs = response.documents || [];
          // Filter to only generated documents (have AI content)
          const generatedDocs = allDocs.filter(
            (doc: any) => doc.generation_status === 'generated' && doc.generated_content
          );

          // Build sections and ID map from all generated docs
          const newSections: Record<string, string> = {};
          const newIdMap: Record<string, string> = {};

          for (const doc of generatedDocs) {
            // Convert markdown content to HTML for the editor
            newSections[doc.document_name] = convertMarkdownToHtml(doc.generated_content);
            newIdMap[doc.document_name] = doc.id;
          }

          // Only update if we actually found generated docs
          if (Object.keys(newSections).length > 0) {
            setSections(newSections);
            setDocumentIdMap(newIdMap);
          }
        })
        .catch((error) => {
          console.error('Failed to fetch project documents for editor:', error);
          // Keep the single document that was already loaded
        })
        .finally(() => {
          setIsLoadingProjectDocs(false);
        });
    } else {
      // Single-document mode (Quick Generate, no project context)
      setSections({ [docName]: content });
      setDocumentIdMap(docId ? { [docName]: docId } : {});
    }

    // Clear pending content after loading to prevent re-triggering
    clearPendingContent();
  }, [pendingEditorContent, clearPendingContent]);

  // Update sections when editorContent changes (fallback for other navigation paths)
  useEffect(() => {
    if (editorContent && Object.keys(editorContent).length > 0) {
      setSections(editorContent);
    }
  }, [editorContent]);
  
  
  // Handle export navigation
  // Sync current sections to context before navigating to export
  // This ensures the export view receives the latest edited content, not stale data
  const handleExport = useCallback(() => {
    setEditorContent(sections);
    navigate('EXPORT');
  }, [navigate, sections, setEditorContent]);
  
  // Handle back navigation
  const handleBack = useCallback(() => {
    goBack();
  }, [goBack]);

  // Loading state while fetching project documents
  if (isLoadingProjectDocs && Object.keys(sections).length <= 1) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <h2 className="text-lg font-medium mb-2">Loading project documents...</h2>
          <p className="text-muted-foreground">
            Fetching all generated documents for this project
          </p>
        </div>
      </div>
    );
  }
  
  // Empty state
  if (Object.keys(sections).length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <FileText className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
          <h2 className="text-lg font-medium mb-2">No content to edit</h2>
          <p className="text-muted-foreground mb-4">
            Generate documents using Quick Generate or the Tracker
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full overflow-hidden">
      <LiveEditor
        lockedAssumptions={assumptions}
        sections={sections}
        setSections={setSections}
        citations={citations}
        agentMetadata={agentMetadata}
        collaborationMetadata={collaborationMetadata}
        initialQualityScores={qualityAnalysis}
        documentId={documentId}
        documentName={documentName}
        // Project-aware: map of section name -> document ID for full context switching
        documentIdMap={Object.keys(documentIdMap).length > 0 ? documentIdMap : undefined}
        onExport={handleExport}
        onBack={handleBack}
      />
    </div>
  );
}

export default EditorScreen;
