/**
 * EditorStatusBar Component
 * 
 * Microsoft Word-style status bar at the bottom of the editor.
 * Displays document statistics and zoom controls.
 * 
 * Features:
 * - Page count (Page X of Y)
 * - Word count
 * - Character count
 * - Zoom slider
 * - View mode icons (future)
 * 
 * Dependencies:
 *   - TipTap editor for content stats
 *   - ZoomControl component
 */

import { Editor } from '@tiptap/react';
import { ZoomControl } from './ZoomControl';
import { FileText, Layout, Columns } from 'lucide-react';
import { Button } from '@/components/ui/button';

// Props interface for EditorStatusBar
interface EditorStatusBarProps {
  editor: Editor | null;
  zoomLevel: number;
  onZoomChange: (zoom: number) => void;
  pageHeight?: number; // in pixels, for page count estimation
}

/**
 * Calculate word count from text content
 * @param text - The text content
 * @returns Number of words
 */
function countWords(text: string): number {
  if (!text || text.trim().length === 0) return 0;
  return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

/**
 * Estimate page count based on content height
 * @param contentLength - Character count
 * @param pageHeight - Height of one page in pixels
 * @returns Estimated page count
 */
function estimatePageCount(contentLength: number, pageHeight: number): number {
  // Rough estimate: ~3000 characters per page (varies with font/formatting)
  const charsPerPage = 3000;
  return Math.max(1, Math.ceil(contentLength / charsPerPage));
}

/**
 * EditorStatusBar - Document info and zoom controls
 * 
 * Provides at-a-glance document statistics and zoom control,
 * similar to Microsoft Word's status bar.
 */
export function EditorStatusBar({
  editor,
  zoomLevel,
  onZoomChange,
  pageHeight = 1056, // Default: 11 inches at 96 DPI
}: EditorStatusBarProps) {
  // Get document content for stats
  const textContent = editor?.state.doc.textContent || '';
  const characterCount = textContent.length;
  const wordCount = countWords(textContent);
  const pageCount = estimatePageCount(characterCount, pageHeight);
  const currentPage = 1; // TODO: Calculate based on cursor position

  return (
    <div className="editor-status-bar flex items-center justify-between h-6 px-3 bg-gray-100 border-t border-gray-300 text-xs text-slate-600">
      {/* Left section: Page and word info */}
      <div className="flex items-center gap-4">
        {/* Page count */}
        <div className="flex items-center gap-1" title={`${pageCount} page(s) total`}>
          <FileText className="h-3 w-3" />
          <span>Page {currentPage} of {pageCount}</span>
        </div>

        {/* Separator */}
        <div className="w-px h-3 bg-gray-300" />

        {/* Word count */}
        <div title={`${wordCount} words`}>
          <span>{wordCount.toLocaleString()} Words</span>
        </div>

        {/* Separator */}
        <div className="w-px h-3 bg-gray-300" />

        {/* Character count */}
        <div title={`${characterCount} characters`}>
          <span>{characterCount.toLocaleString()} Characters</span>
        </div>
      </div>

      {/* Center section: Status messages (optional) */}
      <div className="flex-1 text-center">
        {/* Could show "Saving...", "Saved", etc. */}
      </div>

      {/* Right section: View modes and zoom */}
      <div className="flex items-center gap-2">
        {/* View mode buttons (visual only for now) */}
        <div className="flex items-center gap-0.5">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-5 w-5 p-0 hover:bg-gray-200"
            title="Print Layout"
          >
            <FileText className="h-3 w-3" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-5 w-5 p-0 hover:bg-gray-200"
            title="Web Layout"
          >
            <Layout className="h-3 w-3" />
          </Button>
        </div>

        {/* Separator */}
        <div className="w-px h-3 bg-gray-300" />

        {/* Zoom control */}
        <ZoomControl
          zoomLevel={zoomLevel}
          onZoomChange={onZoomChange}
        />
      </div>
    </div>
  );
}

/**
 * EditorStatusBarMinimal - Compact status bar for smaller screens
 * 
 * Shows only essential info: word count and zoom percentage.
 */
export function EditorStatusBarMinimal({
  editor,
  zoomLevel,
  onZoomChange,
}: Omit<EditorStatusBarProps, 'pageHeight'>) {
  const textContent = editor?.state.doc.textContent || '';
  const wordCount = countWords(textContent);

  return (
    <div className="editor-status-bar-minimal flex items-center justify-between h-5 px-2 bg-gray-100 border-t border-gray-200 text-xs text-slate-500">
      <span>{wordCount} words</span>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => onZoomChange(Math.max(50, zoomLevel - 10))}
          className="hover:text-slate-700"
        >
          −
        </button>
        <span className="min-w-[36px] text-center">{zoomLevel}%</span>
        <button
          type="button"
          onClick={() => onZoomChange(Math.min(200, zoomLevel + 10))}
          className="hover:text-slate-700"
        >
          +
        </button>
      </div>
    </div>
  );
}

export default EditorStatusBar;
