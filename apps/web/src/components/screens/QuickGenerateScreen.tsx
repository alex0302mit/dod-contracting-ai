/**
 * QuickGenerateScreen Component
 * 
 * Wraps the existing QuickGenerateTab with ACES styling.
 * No ConsoleRail on this screen.
 * 
 * Dependencies:
 * - QuickGenerateTab for the wizard flow
 * - useNavigation for editor navigation
 */

import { QuickGenerateTab } from '@/components/quick-generate/QuickGenerateTab';
import { useNavigation } from '@/contexts/NavigationContext';

/**
 * QuickGenerateScreen wraps QuickGenerateTab
 */
export function QuickGenerateScreen() {
  const { navigateToEditor, setEditorContent } = useNavigation();
  
  // Handle opening generated content in editor
  const handleOpenEditor = (sections: Record<string, string>) => {
    setEditorContent(sections);
    navigateToEditor(sections);
  };
  
  // Handle completion (optional analytics, etc.)
  const handleComplete = (sections: Record<string, string>) => {
    setEditorContent(sections);
    navigateToEditor(sections);
  };
  
  return (
    <div className="h-full overflow-auto">
      <QuickGenerateTab
        onOpenEditor={handleOpenEditor}
        onComplete={handleComplete}
      />
    </div>
  );
}

export default QuickGenerateScreen;
