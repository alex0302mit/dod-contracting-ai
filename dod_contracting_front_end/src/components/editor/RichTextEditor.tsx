/**
 * Rich Text Editor Component
 *
 * Notion-like editor with inline markdown rendering, quality feedback,
 * citation management, and AI Copilot integration.
 * 
 * Features:
 * - TipTap-based rich text editing
 * - Custom extensions for citations, smart tags, etc.
 * - AI Copilot popup on text selection
 * - Quality issue highlighting
 * 
 * Dependencies:
 * - @tiptap/react: Core editor
 * - EditorCopilot: AI assistant popup
 */

import { useEditor, EditorContent, Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import Placeholder from '@tiptap/extension-placeholder';
import Highlight from '@tiptap/extension-highlight';
// New extensions for enhanced toolbar features
import TextAlign from '@tiptap/extension-text-align';
import { Color } from '@tiptap/extension-color';
import { TextStyle } from '@tiptap/extension-text-style';
// NOTE: Link extension removed due to keyed plugin conflict with React StrictMode
// Links still work via basic HTML anchor tags in the editor
// TipTap Table Extensions for interactive table support
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableHeader } from '@tiptap/extension-table-header';
import { TableCell } from '@tiptap/extension-table-cell';
import { QualityIssueMark, QualityIssue } from './QualityIssueExtension';
import { CitationMark } from './CitationExtension';
import { SmartTag } from './SmartTagExtension';
import { Tooltip } from './TooltipExtension';
import { SmartField } from './SmartFieldExtension';
import { Callout } from './CalloutExtension';
import { CommentMark } from './CommentExtension';
import { EditorToolbar } from './EditorToolbar';
import { EditorCopilot } from './EditorCopilot';
import { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import './editor-styles.css';
// Import content sanitizer to remove empty list items before display
import { sanitizeListContent } from '@/lib/contentSanitizer';

// Citation interface for document references
interface Citation {
  id: number;
  source: string;
  page: number;
  text: string;
  bbox?: { x: number; y: number; w: number; h: number };
}

// Props for the RichTextEditor component
interface RichTextEditorProps {
  content: string;
  onChange: (content: string) => void;
  citations: Citation[];
  qualityIssues: QualityIssue[];
  placeholder?: string;
  onEditorReady?: (editor: Editor) => void;
  sectionName?: string;  // Added for Copilot context
}

// Copilot visibility state interface
interface CopilotState {
  isVisible: boolean;
  position: { top: number; left: number };
  selectedText: string;
  // Store the exact selection positions to ensure we replace the correct text
  selectionRange: { from: number; to: number } | null;
}

export function RichTextEditor({
  content,
  onChange,
  citations,
  qualityIssues,
  placeholder = "Start writing...",
  onEditorReady,
  sectionName = "Document",
}: RichTextEditorProps) {
  // State for citation modal
  const [showCitationModal, setShowCitationModal] = useState(false);
  
  // State for Copilot popup
  const [copilotState, setCopilotState] = useState<CopilotState>({
    isVisible: false,
    position: { top: 0, left: 0 },
    selectedText: "",
    selectionRange: null
  });
  
  // Ref for the editor container to calculate positions
  const editorContainerRef = useRef<HTMLDivElement>(null);
  
  // Debounce timer for selection handling
  const selectionTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Sanitize content to remove empty list items before passing to TipTap
  // This prevents empty bullets from appearing in the editor
  const sanitizedContent = useMemo(() => {
    return sanitizeListContent(content);
  }, [content]);

  // Create the TipTap editor instance
  // @ts-expect-error - TipTap table extensions have version compatibility issues between local and global node_modules
  const editor = useEditor(
    {
      extensions: [
        StarterKit.configure({
          heading: {
            levels: [1, 2, 3],
          },
        }),
        // Underline extension (not included in StarterKit)
        Underline,
        // Highlight extension for issue highlighting and text highlighting
        Highlight.configure({
          multicolor: true,
        }),
        Placeholder.configure({
          placeholder,
        }),
        // Text alignment extension for left, center, right, justify
        TextAlign.configure({
          types: ['heading', 'paragraph'],
          alignments: ['left', 'center', 'right', 'justify'],
        }),
        // TextStyle is required for Color extension
        TextStyle,
        // Color extension for text color support
        Color,
        // NOTE: Link extension removed - caused keyed plugin conflicts
        // Links still work via basic HTML anchor tags
        // Table extensions for interactive table editing
        Table.configure({
          resizable: true,  // Allow column resizing
          HTMLAttributes: {
            class: 'tiptap-table',  // Custom class for styling
          },
        }),
        TableRow,
        TableHeader,
        TableCell,
        // Custom extensions for DoD document editing
        QualityIssueMark,
        CitationMark,
        SmartTag,
        Tooltip,
        SmartField,
        Callout,
        CommentMark,
      ],
      // Use sanitized content to prevent empty list items from appearing
      content: sanitizedContent,
      editorProps: {
        attributes: {
          class: 'prose prose-sm max-w-none focus:outline-none min-h-[300px] px-4 py-3',
          // Disable browser extensions (Grammarly, etc.) from interfering
          'data-gramm': 'false',
          'data-gramm_editor': 'false',
          'data-enable-grammarly': 'false',
          'spellcheck': 'false',
        },
      },
      onUpdate: ({ editor }) => {
        // Use getHTML() to preserve formatting
        onChange(editor.getHTML());
      },
      // Handle selection changes for Copilot
      onSelectionUpdate: ({ editor }) => {
        handleSelectionChange(editor);
      },
    },
    [] // Empty dependency array - editor should only be created once
  );

  // Handle text selection to show/hide Copilot
  const handleSelectionChange = useCallback((editorInstance: Editor) => {
    // Clear any pending timer
    if (selectionTimerRef.current) {
      clearTimeout(selectionTimerRef.current);
    }

    // Debounce selection handling to avoid flicker
    selectionTimerRef.current = setTimeout(() => {
      const { from, to } = editorInstance.state.selection;
      const selectedText = editorInstance.state.doc.textBetween(from, to, ' ');
      
      // Only show Copilot if there's meaningful text selected (at least 3 chars)
      if (selectedText && selectedText.trim().length >= 3) {
        // Get the DOM selection to calculate position
        const domSelection = window.getSelection();
        if (domSelection && domSelection.rangeCount > 0) {
          const range = domSelection.getRangeAt(0);
          const rect = range.getBoundingClientRect();

          // Calculate position relative to viewport
          // Position the popup below the selection
          const top = rect.bottom + window.scrollY + 10;
          const left = rect.left + (rect.width / 2);

          setCopilotState({
            isVisible: true,
            position: { top, left },
            selectedText: selectedText.trim(),
            // Store exact positions so we replace the correct text even if selection changes
            selectionRange: { from, to }
          });
        }
      } else {
        // Hide Copilot when no text is selected
        setCopilotState(prev => ({
          ...prev,
          isVisible: false
        }));
      }
    }, 300); // 300ms debounce
  }, []);

  // Close Copilot popup
  const handleCloseCopilot = useCallback(() => {
    setCopilotState(prev => ({
      ...prev,
      isVisible: false
    }));
  }, []);

  // Convert markdown formatting to HTML for Tiptap compatibility
  const markdownToHtml = (text: string): string => {
    return text
      // Bold: **text** or __text__
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/__(.+?)__/g, '<strong>$1</strong>')
      // Italic: *text* or _text_ (not within words)
      .replace(/(?<![*\w])\*([^*]+)\*(?![*\w])/g, '<em>$1</em>')
      .replace(/(?<![_\w])_([^_]+)_(?![_\w])/g, '<em>$1</em>')
      // Line breaks
      .replace(/\n/g, '<br>');
  };

  // Apply text from Copilot to replace selection
  const handleApplyText = useCallback((newText: string) => {
    if (!editor) return;

    // Convert markdown to HTML for proper Tiptap rendering
    const htmlContent = markdownToHtml(newText);

    // Use the stored selection range to ensure we replace exactly what the user highlighted
    // This prevents issues if the user clicked elsewhere before applying
    const range = copilotState.selectionRange;
    if (!range) {
      console.warn("No stored selection range, using current selection");
      const { from, to } = editor.state.selection;
      editor.chain().focus().deleteRange({ from, to }).insertContent(htmlContent).run();
    } else {
      // Verify the stored range is still valid (document hasn't changed significantly)
      const docSize = editor.state.doc.content.size;
      if (range.from >= 0 && range.to <= docSize && range.from < range.to) {
        editor.chain().focus().deleteRange(range).insertContent(htmlContent).run();
      } else {
        console.warn("Stored range invalid, using current selection");
        const { from, to } = editor.state.selection;
        editor.chain().focus().deleteRange({ from, to }).insertContent(htmlContent).run();
      }
    }

    // Close the Copilot
    handleCloseCopilot();
  }, [editor, handleCloseCopilot, copilotState.selectionRange]);

  // Update editor content when the content prop changes
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content);
    }
  }, [content, editor]);

  // Notify parent when editor is ready
  useEffect(() => {
    if (editor && onEditorReady) {
      onEditorReady(editor);
    }
  }, [editor, onEditorReady]);

  // Apply quality issues when they change
  useEffect(() => {
    if (!editor) return;

    const transaction = editor.state.tr;
    let modified = false;

    // First, clear all existing quality issue marks
    editor.state.doc.descendants((node, pos) => {
      if (node.marks.some((mark) => mark.type.name === 'qualityIssue')) {
        transaction.removeMark(
          pos,
          pos + node.nodeSize,
          editor.schema.marks.qualityIssue
        );
        modified = true;
      }
    });

    // Then apply new quality issue marks
    qualityIssues.forEach((issue) => {
      if (issue.from < editor.state.doc.content.size && issue.to <= editor.state.doc.content.size) {
        transaction.addMark(
          issue.from,
          issue.to,
          editor.schema.marks.qualityIssue.create({
            issueId: issue.id,
            issueKind: issue.kind,
            issueLabel: issue.label,
          })
        );
        modified = true;
      }
    });

    if (modified) {
      editor.view.dispatch(transaction);
    }
  }, [qualityIssues, editor]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (selectionTimerRef.current) {
        clearTimeout(selectionTimerRef.current);
      }
    };
  }, []);

  // Handle citation insertion
  const handleInsertCitation = (citation: Citation) => {
    if (editor) {
      // @ts-expect-error - Custom command from CitationExtension
      editor.chain().focus().insertCitation(citation.id, citation.source).run();
    }
  };

  // Loading state while editor initializes
  if (!editor) {
    return <div className="animate-pulse bg-slate-100 h-64 rounded-lg" />;
  }

  return (
    <div
      ref={editorContainerRef}
      className="border rounded-lg bg-white shadow-sm relative"
      data-gramm="false"
      data-gramm_editor="false"
      data-enable-grammarly="false"
    >
      {/* Toolbar */}
      <EditorToolbar
        editor={editor}
        onInsertCitation={() => setShowCitationModal(true)}
      />

      {/* Editor Content */}
      <div
        className="border-t"
        data-gramm="false"
        data-gramm_editor="false"
        data-enable-grammarly="false"
      >
        <EditorContent editor={editor} />
      </div>

      {/* AI Copilot Popup - appears when text is selected */}
      <EditorCopilot
        editor={editor}
        sectionName={sectionName}
        isVisible={copilotState.isVisible}
        position={copilotState.position}
        selectedText={copilotState.selectedText}
        onClose={handleCloseCopilot}
        onApplyText={handleApplyText}
      />

      {/* Citation Modal */}
      {showCitationModal && (
        <div className="fixed inset-0 z-50">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setShowCitationModal(false)}
          />
          <div className="fixed inset-0 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-hidden">
              {/* Citation Modal Content */}
              <CitationModalContent
                citations={citations}
                onInsert={handleInsertCitation}
                onClose={() => setShowCitationModal(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Inline Citation Modal Content component
function CitationModalContent({
  citations,
  onInsert,
  onClose,
}: {
  citations: Citation[];
  onInsert: (citation: Citation) => void;
  onClose: () => void;
}) {
  const [search, setSearch] = useState('');

  // Filter citations based on search query
  const filtered = citations.filter(
    (c) =>
      c.source.toLowerCase().includes(search.toLowerCase()) ||
      c.text.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 space-y-4">
      <h3 className="text-lg font-semibold">Insert Citation</h3>

      <input
        type="text"
        placeholder="Search citations..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full border rounded px-3 py-2"
        autoFocus
      />

      <div className="max-h-96 overflow-y-auto space-y-2">
        {filtered.map((citation) => (
          <button
            key={citation.id}
            onClick={() => {
              onInsert(citation);
              onClose();
            }}
            className="w-full text-left p-3 border rounded hover:bg-blue-50 transition"
          >
            <div className="font-semibold text-sm">
              [{citation.id}] {citation.source}
            </div>
            <div className="text-xs text-gray-600 mt-1 line-clamp-2">
              {citation.text}
            </div>
          </button>
        ))}
      </div>

      <button
        onClick={onClose}
        className="w-full px-4 py-2 border rounded hover:bg-gray-100"
      >
        Cancel
      </button>
    </div>
  );
}
