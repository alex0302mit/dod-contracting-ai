/**
 * EditorScreen Component
 * 
 * Wraps the existing LiveEditor with ConsoleRail integration.
 * Opens ConsoleRail by default and syncs quality data.
 * 
 * This is the flagship editor screen for document editing.
 * 
 * Dependencies:
 * - LiveEditor for the editor functionality
 * - useConsoleRail for rail state management
 * - useNavigation for content and navigation
 */

import { useEffect, useState, useCallback } from 'react';
import { LiveEditor } from '@/components/LiveEditor';
import { useConsoleRail } from '@/contexts/ConsoleRailContext';
import { useNavigation } from '@/contexts/NavigationContext';
import { FileText } from 'lucide-react';

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
 * EditorScreen wraps LiveEditor with ACES layout
 */
export function EditorScreen() {
  // Note: ConsoleRail is NOT shown for Editor - LiveEditor has its own quality panel
  const { closeRail } = useConsoleRail();
  const { editorContent, navigate, goBack } = useNavigation();
  
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
  
  // Update sections when editorContent changes
  useEffect(() => {
    if (editorContent && Object.keys(editorContent).length > 0) {
      setSections(editorContent);
    }
  }, [editorContent]);
  
  
  // Handle export navigation
  const handleExport = useCallback(() => {
    navigate('EXPORT');
  }, [navigate]);
  
  // Handle back navigation
  const handleBack = useCallback(() => {
    goBack();
  }, [goBack]);
  
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
        onExport={handleExport}
        onBack={handleBack}
      />
    </div>
  );
}

export default EditorScreen;
