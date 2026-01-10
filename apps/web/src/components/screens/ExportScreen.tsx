/**
 * ExportScreen Component
 * 
 * Wraps the existing ExportView component.
 * Provides document export functionality.
 * 
 * Dependencies:
 * - ExportView for export functionality
 * - useNavigation for content and navigation
 */

import { ExportView } from '@/components/ExportView';
import { useNavigation } from '@/contexts/NavigationContext';

/**
 * ExportScreen wraps ExportView
 */
export function ExportScreen() {
  const { editorContent, goBack } = useNavigation();
  
  // Default empty state if no content
  const sections = editorContent || {};
  const citations: any[] = [];
  const metadata = {
    project_name: 'ACES Export',
    assumptions: [],
  };
  
  return (
    <div className="h-full overflow-auto">
      <ExportView
        sections={sections}
        citations={citations}
        metadata={metadata}
        onBack={goBack}
      />
    </div>
  );
}

export default ExportScreen;
