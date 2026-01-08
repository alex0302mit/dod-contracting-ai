/**
 * QuickAccessToolbar Component
 * 
 * Microsoft Word-style quick access toolbar positioned above the ribbon.
 * Contains frequently used actions: Save, Undo, Redo.
 * 
 * Features:
 * - Compact height (28px) matching Word's QAT
 * - Icon-only buttons for space efficiency
 * - Subtle styling that doesn't compete with ribbon
 * 
 * Dependencies:
 *   - TipTap editor for undo/redo state
 *   - Lucide icons
 */

import { Editor } from '@tiptap/react';
import { Button } from '@/components/ui/button';
import { 
  Save, 
  Undo2, 
  Redo2,
  ChevronDown,
} from 'lucide-react';

// Props interface for QuickAccessToolbar
interface QuickAccessToolbarProps {
  editor: Editor | null;
  onSave?: () => void;
  isSaving?: boolean;
}

/**
 * QuickAccessToolbar - Compact toolbar above the ribbon
 * 
 * Provides quick access to common actions without navigating ribbon tabs.
 * Styled to be subtle and compact like Microsoft Word's QAT.
 */
export function QuickAccessToolbar({ 
  editor, 
  onSave,
  isSaving = false 
}: QuickAccessToolbarProps) {
  // Check if undo/redo are available
  const canUndo = editor?.can().undo() ?? false;
  const canRedo = editor?.can().redo() ?? false;

  // Handle undo action
  const handleUndo = () => {
    editor?.chain().focus().undo().run();
  };

  // Handle redo action
  const handleRedo = () => {
    editor?.chain().focus().redo().run();
  };

  return (
    <div className="quick-access-toolbar flex items-center h-7 px-2 bg-slate-100 border-b border-slate-200">
      {/* Save button */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={onSave}
        disabled={isSaving}
        className="h-5 w-5 p-0 hover:bg-slate-200"
        title="Save (Ctrl+S)"
      >
        <Save className="h-3.5 w-3.5 text-slate-600" />
      </Button>

      {/* Separator */}
      <div className="w-px h-4 bg-slate-300 mx-1" />

      {/* Undo button */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={handleUndo}
        disabled={!canUndo}
        className="h-5 w-5 p-0 hover:bg-slate-200 disabled:opacity-40"
        title="Undo (Ctrl+Z)"
      >
        <Undo2 className="h-3.5 w-3.5 text-slate-600" />
      </Button>

      {/* Redo button */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={handleRedo}
        disabled={!canRedo}
        className="h-5 w-5 p-0 hover:bg-slate-200 disabled:opacity-40"
        title="Redo (Ctrl+Y)"
      >
        <Redo2 className="h-3.5 w-3.5 text-slate-600" />
      </Button>

      {/* Customize dropdown (placeholder for future) */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-5 w-5 p-0 hover:bg-slate-200 ml-0.5"
        title="Customize Quick Access Toolbar"
      >
        <ChevronDown className="h-3 w-3 text-slate-500" />
      </Button>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Optional: App title or branding could go here */}
      <span className="text-xs text-slate-500 font-medium">
        ACES Document Editor
      </span>
    </div>
  );
}

export default QuickAccessToolbar;
