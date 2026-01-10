/**
 * Enhanced Editor Formatting Toolbar
 *
 * Complete toolbar with all essential editing features organized in groups:
 * - History: Undo/Redo
 * - Text Formatting: Bold, Italic, Underline, Strikethrough, Clear Formatting
 * - Colors: Text Color Picker, Highlight Color Picker
 * - Headings: H1, H2, H3
 * - Alignment: Left, Center, Right, Justify
 * - Lists: Bullet, Ordered, Indent, Outdent
 * - Insert: Table, Link, Horizontal Rule, Code Block, Block Quote
 * - Special: Citation, Smart Tag, Tooltip, Callout
 * - Find & Replace: Collapsible search bar with replace functionality
 * 
 * Dependencies:
 * - TipTap editor with extensions: StarterKit, TextAlign, Color, TextStyle, Link
 * - Shadcn UI components: Button, Popover, Input, Separator
 * - Lucide icons for visual indicators
 */

import { Editor } from '@tiptap/react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  // History icons
  Undo2,
  Redo2,
  // Text formatting icons
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  RemoveFormatting,
  // Color icons
  Palette,
  Highlighter,
  // Heading icons
  Heading1,
  Heading2,
  Heading3,
  // Alignment icons
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  // List icons
  List,
  ListOrdered,
  IndentIncrease,
  IndentDecrease,
  // Insert icons
  Table,
  // Link2 removed - Link extension caused plugin conflicts
  Minus as HorizontalRule,
  Code2,
  Quote,
  Plus,
  Minus,
  // Special feature icons
  FileText,
  Tag,
  HelpCircle,
  MessageSquare,
  // Search icons
  Search,
  X,
  ChevronUp,
  ChevronDown,
} from 'lucide-react';
import { SmartTagPopover } from './SmartTagPopover';
import { CalloutPopover } from './CalloutPopover';
import { useState, useCallback } from 'react';

// ============================================================================
// Types & Interfaces
// ============================================================================

interface EditorToolbarProps {
  editor: Editor;
  onInsertCitation: () => void;
}

// Color palette for text and highlight colors
const TEXT_COLORS = [
  { name: 'Default', value: 'inherit' },
  { name: 'Red', value: '#dc2626' },
  { name: 'Orange', value: '#ea580c' },
  { name: 'Green', value: '#16a34a' },
  { name: 'Blue', value: '#2563eb' },
  { name: 'Purple', value: '#9333ea' },
  { name: 'Gray', value: '#6b7280' },
  { name: 'Black', value: '#000000' },
];

const HIGHLIGHT_COLORS = [
  { name: 'None', value: '' },
  { name: 'Yellow', value: '#fef08a' },
  { name: 'Green', value: '#bbf7d0' },
  { name: 'Blue', value: '#bfdbfe' },
  { name: 'Pink', value: '#fbcfe8' },
  { name: 'Orange', value: '#fed7aa' },
];

// ============================================================================
// Main Component
// ============================================================================

export function EditorToolbar({ editor, onInsertCitation }: EditorToolbarProps) {
  // ---------------------------
  // State Management
  // ---------------------------
  
  // Tooltip popover state
  const [showTooltipPopover, setShowTooltipPopover] = useState(false);
  const [tooltipText, setTooltipText] = useState('');
  
  // Table insertion state
  const [showTablePopover, setShowTablePopover] = useState(false);
  const [tableRows, setTableRows] = useState(3);
  const [tableCols, setTableCols] = useState(3);

  // NOTE: Link insertion state removed - Link extension caused plugin conflicts
  
  // Color picker states
  const [showTextColorPopover, setShowTextColorPopover] = useState(false);
  const [showHighlightPopover, setShowHighlightPopover] = useState(false);
  
  // Find & Replace state
  const [showFindReplace, setShowFindReplace] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [replaceTerm, setReplaceTerm] = useState('');
  const [matchCount, setMatchCount] = useState(0);
  const [currentMatch, setCurrentMatch] = useState(0);

  // Early return if editor not ready
  if (!editor) {
    return null;
  }
  
  // ---------------------------
  // Handler Functions
  // ---------------------------
  
  // Insert a new table with specified dimensions
  const handleInsertTable = () => {
    // @ts-expect-error - insertTable is provided by @tiptap/extension-table
    editor
      .chain()
      .focus()
      .insertTable({ rows: tableRows, cols: tableCols, withHeaderRow: true })
      .run();
    
    setTableRows(3);
    setTableCols(3);
    setShowTablePopover(false);
  };

  // Add tooltip to selected text
  const handleAddTooltip = () => {
    if (!tooltipText.trim()) return;

    const { from, to } = editor.state.selection;
    if (from === to) return; // No selection

    // @ts-expect-error - addTooltip is provided by custom TooltipExtension
    editor
      .chain()
      .focus()
      .addTooltip({
        tooltipId: `tooltip-${Date.now()}`,
        tooltipText: tooltipText.trim(),
        tooltipType: 'help',
      })
      .run();

    setTooltipText('');
    setShowTooltipPopover(false);
  };

  // NOTE: handleInsertLink removed - Link extension caused plugin conflicts

  // Set text color
  // @ts-expect-error - setColor/unsetColor are provided by @tiptap/extension-color
  const handleSetTextColor = (color: string) => {
    if (color === 'inherit') {
      editor.chain().focus().unsetColor().run();
    } else {
      editor.chain().focus().setColor(color).run();
    }
    setShowTextColorPopover(false);
  };

  // Set highlight color
  // @ts-expect-error - setHighlight/unsetHighlight are provided by @tiptap/extension-highlight
  const handleSetHighlight = (color: string) => {
    if (!color) {
      editor.chain().focus().unsetHighlight().run();
    } else {
      editor.chain().focus().setHighlight({ color }).run();
    }
    setShowHighlightPopover(false);
  };

  // Clear all formatting from selection
  const handleClearFormatting = () => {
    editor.chain().focus().unsetAllMarks().clearNodes().run();
  };

  // Set text alignment - handlers for alignment buttons
  // @ts-expect-error - setTextAlign is provided by @tiptap/extension-text-align
  const handleAlignLeft = () => editor.chain().focus().setTextAlign('left').run();
  // @ts-expect-error - setTextAlign is provided by @tiptap/extension-text-align
  const handleAlignCenter = () => editor.chain().focus().setTextAlign('center').run();
  // @ts-expect-error - setTextAlign is provided by @tiptap/extension-text-align
  const handleAlignRight = () => editor.chain().focus().setTextAlign('right').run();
  // @ts-expect-error - setTextAlign is provided by @tiptap/extension-text-align
  const handleAlignJustify = () => editor.chain().focus().setTextAlign('justify').run();

  // Find & Replace functions
  const handleFind = useCallback(() => {
    if (!searchTerm) {
      setMatchCount(0);
      setCurrentMatch(0);
      return;
    }

    const { doc } = editor.state;
    let count = 0;
    const positions: number[] = [];

    // Search through document content
    doc.descendants((node, pos) => {
      if (node.isText && node.text) {
        const text = node.text.toLowerCase();
        const term = searchTerm.toLowerCase();
        let index = text.indexOf(term);
        
        while (index !== -1) {
          positions.push(pos + index);
          count++;
          index = text.indexOf(term, index + 1);
        }
      }
    });

    setMatchCount(count);
    
    if (count > 0 && positions.length > 0) {
      setCurrentMatch(1);
      // Scroll to first match
      const from = positions[0];
      const to = from + searchTerm.length;
      editor.chain().focus().setTextSelection({ from, to }).run();
    } else {
      setCurrentMatch(0);
    }
  }, [searchTerm, editor]);

  const handleGoToNextMatch = () => {
    if (matchCount === 0) return;
    
    const newMatch = currentMatch < matchCount ? currentMatch + 1 : 1;
    setCurrentMatch(newMatch);
    
    // Find and navigate to the next match
    const { doc } = editor.state;
    const { from: selFrom } = editor.state.selection;
    let count = 0;
    let targetPos = -1;

    doc.descendants((node, pos) => {
      if (node.isText && node.text) {
        const text = node.text.toLowerCase();
        const term = searchTerm.toLowerCase();
        let index = text.indexOf(term);
        
        while (index !== -1) {
          count++;
          if (count === newMatch || (targetPos === -1 && pos + index > selFrom)) {
            targetPos = pos + index;
            if (count === newMatch) return false; // Stop searching
          }
          index = text.indexOf(term, index + 1);
        }
      }
    });

    if (targetPos !== -1) {
      const to = targetPos + searchTerm.length;
      editor.chain().focus().setTextSelection({ from: targetPos, to }).run();
    }
  };

  const handleGoToPrevMatch = () => {
    if (matchCount === 0) return;
    
    const newMatch = currentMatch > 1 ? currentMatch - 1 : matchCount;
    setCurrentMatch(newMatch);
    
    // Find and navigate to the previous match
    const { doc } = editor.state;
    const positions: number[] = [];

    doc.descendants((node, pos) => {
      if (node.isText && node.text) {
        const text = node.text.toLowerCase();
        const term = searchTerm.toLowerCase();
        let index = text.indexOf(term);
        
        while (index !== -1) {
          positions.push(pos + index);
          index = text.indexOf(term, index + 1);
        }
      }
    });

    if (positions.length > 0 && newMatch > 0) {
      const targetPos = positions[newMatch - 1];
      const to = targetPos + searchTerm.length;
      editor.chain().focus().setTextSelection({ from: targetPos, to }).run();
    }
  };

  const handleReplace = () => {
    if (!searchTerm || matchCount === 0) return;

    const { from, to } = editor.state.selection;
    const selectedText = editor.state.doc.textBetween(from, to);

    if (selectedText.toLowerCase() === searchTerm.toLowerCase()) {
      editor.chain().focus().deleteSelection().insertContent(replaceTerm).run();
      setMatchCount(prev => Math.max(0, prev - 1));
      if (matchCount > 1) {
        handleFind(); // Re-run search to update positions
      }
    }
  };

  const handleReplaceAll = () => {
    if (!searchTerm) return;

    const { doc, tr } = editor.state;
    const positions: { from: number; to: number }[] = [];

    // Collect all positions (in reverse order for safe replacement)
    doc.descendants((node, pos) => {
      if (node.isText && node.text) {
        const text = node.text.toLowerCase();
        const term = searchTerm.toLowerCase();
        let index = text.indexOf(term);
        
        while (index !== -1) {
          positions.push({
            from: pos + index,
            to: pos + index + searchTerm.length,
          });
          index = text.indexOf(term, index + 1);
        }
      }
    });

    // Replace from end to start to preserve positions
    positions.reverse().forEach(({ from, to }) => {
      tr.replaceWith(from, to, editor.schema.text(replaceTerm));
    });

    editor.view.dispatch(tr);
    setMatchCount(0);
    setCurrentMatch(0);
  };

  // ---------------------------
  // Reusable Components
  // ---------------------------

  // Standard toolbar button component
  const ToolbarButton = ({
    onClick,
    active,
    disabled,
    icon: Icon,
    label,
    className = '',
  }: {
    onClick: () => void;
    active?: boolean;
    disabled?: boolean;
    icon: React.ElementType;
    label: string;
    className?: string;
  }) => (
    <Button
      type="button"
      variant={active ? 'default' : 'ghost'}
      size="sm"
      onClick={onClick}
      disabled={disabled}
      className={`h-8 w-8 p-0 ${active ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' : ''} ${className}`}
      title={label}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );

  // Color swatch button for color pickers
  const ColorSwatch = ({
    color,
    name,
    onClick,
    isActive,
  }: {
    color: string;
    name: string;
    onClick: () => void;
    isActive: boolean;
  }) => (
    <button
      type="button"
      onClick={onClick}
      className={`w-6 h-6 rounded border-2 transition-all ${
        isActive ? 'border-blue-500 scale-110' : 'border-gray-200 hover:border-gray-400'
      }`}
      style={{ backgroundColor: color || 'transparent' }}
      title={name}
    >
      {!color && <X className="h-4 w-4 text-gray-400 mx-auto" />}
    </button>
  );

  // ---------------------------
  // Render
  // ---------------------------

  return (
    <div className="border-b bg-slate-50 sticky top-0 z-20">
      {/* Main Toolbar Row */}
      <div className="flex items-center gap-1 p-2 flex-wrap">
        
        {/* ==================== HISTORY GROUP ==================== */}
        <ToolbarButton
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
          icon={Undo2}
          label="Undo (Ctrl+Z)"
        />
        <ToolbarButton
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
          icon={Redo2}
          label="Redo (Ctrl+Y)"
        />

        <Separator orientation="vertical" className="h-6 mx-1" />

        {/* ==================== TEXT FORMATTING GROUP ==================== */}
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBold().run()}
        active={editor.isActive('bold')}
        icon={Bold}
        label="Bold (Ctrl+B)"
      />
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleItalic().run()}
        active={editor.isActive('italic')}
        icon={Italic}
        label="Italic (Ctrl+I)"
      />
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleUnderline().run()}
        active={editor.isActive('underline')}
        icon={UnderlineIcon}
        label="Underline (Ctrl+U)"
      />
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleStrike().run()}
          active={editor.isActive('strike')}
          icon={Strikethrough}
          label="Strikethrough (Ctrl+Shift+S)"
        />
        <ToolbarButton
          onClick={handleClearFormatting}
          icon={RemoveFormatting}
          label="Clear Formatting (Ctrl+\\)"
        />

        <Separator orientation="vertical" className="h-6 mx-1" />

        {/* ==================== COLORS GROUP ==================== */}
        {/* Text Color Picker */}
        <Popover open={showTextColorPopover} onOpenChange={setShowTextColorPopover}>
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Text Color"
            >
              <Palette className="h-4 w-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-2" align="start">
            <div className="space-y-2">
              <Label className="text-xs font-medium">Text Color</Label>
              <div className="flex gap-1 flex-wrap max-w-[180px]">
                {TEXT_COLORS.map((c) => (
                  <ColorSwatch
                    key={c.value}
                    color={c.value === 'inherit' ? '#ffffff' : c.value}
                    name={c.name}
                    onClick={() => handleSetTextColor(c.value)}
                    isActive={
                      c.value === 'inherit'
                        ? !editor.getAttributes('textStyle').color
                        : editor.getAttributes('textStyle').color === c.value
                    }
                  />
                ))}
              </div>
            </div>
          </PopoverContent>
        </Popover>

        {/* Highlight Color Picker */}
        <Popover open={showHighlightPopover} onOpenChange={setShowHighlightPopover}>
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Highlight Color"
            >
              <Highlighter className="h-4 w-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-2" align="start">
            <div className="space-y-2">
              <Label className="text-xs font-medium">Highlight Color</Label>
              <div className="flex gap-1 flex-wrap max-w-[160px]">
                {HIGHLIGHT_COLORS.map((c) => (
                  <ColorSwatch
                    key={c.name}
                    color={c.value}
                    name={c.name}
                    onClick={() => handleSetHighlight(c.value)}
                    isActive={
                      !c.value
                        ? !editor.isActive('highlight')
                        : editor.isActive('highlight', { color: c.value })
                    }
                  />
                ))}
              </div>
            </div>
          </PopoverContent>
        </Popover>

      <Separator orientation="vertical" className="h-6 mx-1" />

        {/* ==================== HEADINGS GROUP ==================== */}
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        active={editor.isActive('heading', { level: 1 })}
        icon={Heading1}
        label="Heading 1"
      />
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        active={editor.isActive('heading', { level: 2 })}
        icon={Heading2}
        label="Heading 2"
      />
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        active={editor.isActive('heading', { level: 3 })}
        icon={Heading3}
        label="Heading 3"
      />

      <Separator orientation="vertical" className="h-6 mx-1" />

        {/* ==================== ALIGNMENT GROUP ==================== */}
        <ToolbarButton
          onClick={handleAlignLeft}
          active={editor.isActive({ textAlign: 'left' })}
          icon={AlignLeft}
          label="Align Left (Ctrl+Shift+L)"
        />
        <ToolbarButton
          onClick={handleAlignCenter}
          active={editor.isActive({ textAlign: 'center' })}
          icon={AlignCenter}
          label="Align Center (Ctrl+Shift+E)"
        />
        <ToolbarButton
          onClick={handleAlignRight}
          active={editor.isActive({ textAlign: 'right' })}
          icon={AlignRight}
          label="Align Right (Ctrl+Shift+R)"
        />
        <ToolbarButton
          onClick={handleAlignJustify}
          active={editor.isActive({ textAlign: 'justify' })}
          icon={AlignJustify}
          label="Justify (Ctrl+Shift+J)"
        />

        <Separator orientation="vertical" className="h-6 mx-1" />

        {/* ==================== LISTS GROUP ==================== */}
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        active={editor.isActive('bulletList')}
        icon={List}
        label="Bullet List"
      />
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        active={editor.isActive('orderedList')}
        icon={ListOrdered}
        label="Numbered List"
      />
        <ToolbarButton
          onClick={() => editor.chain().focus().sinkListItem('listItem').run()}
          disabled={!editor.can().sinkListItem('listItem')}
          icon={IndentIncrease}
          label="Indent (Tab)"
        />
      <ToolbarButton
          onClick={() => editor.chain().focus().liftListItem('listItem').run()}
          disabled={!editor.can().liftListItem('listItem')}
          icon={IndentDecrease}
          label="Outdent (Shift+Tab)"
      />

      <Separator orientation="vertical" className="h-6 mx-1" />

        {/* ==================== INSERT ELEMENTS GROUP ==================== */}
      {/* Table Insertion */}
      <Popover open={showTablePopover} onOpenChange={setShowTablePopover}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            title="Insert Table"
          >
            <Table className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-64" align="start">
          <div className="space-y-4">
            <div className="space-y-1">
              <Label className="text-sm font-medium">Insert Table</Label>
              <p className="text-xs text-muted-foreground">
                Specify the number of rows and columns
              </p>
            </div>
            
            {/* Row selector */}
            <div className="flex items-center justify-between">
                <Label className="text-sm">Rows</Label>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setTableRows(Math.max(1, tableRows - 1))}
                  disabled={tableRows <= 1}
                >
                  <Minus className="h-3 w-3" />
                </Button>
                <span className="w-8 text-center text-sm font-medium">{tableRows}</span>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setTableRows(Math.min(20, tableRows + 1))}
                  disabled={tableRows >= 20}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
            
            {/* Column selector */}
            <div className="flex items-center justify-between">
                <Label className="text-sm">Columns</Label>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setTableCols(Math.max(1, tableCols - 1))}
                  disabled={tableCols <= 1}
                >
                  <Minus className="h-3 w-3" />
                </Button>
                <span className="w-8 text-center text-sm font-medium">{tableCols}</span>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setTableCols(Math.min(10, tableCols + 1))}
                  disabled={tableCols >= 10}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
            
            {/* Preview indicator */}
            <div className="text-xs text-muted-foreground text-center py-1 bg-slate-50 rounded">
              {tableRows} × {tableCols} table (first row is header)
            </div>
            
            {/* Action buttons */}
            <div className="flex gap-2">
                <Button size="sm" onClick={handleInsertTable} className="flex-1">
                Insert Table
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setTableRows(3);
                  setTableCols(3);
                  setShowTablePopover(false);
                }}
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>

        {/* NOTE: Link button removed - Link extension caused plugin conflicts */}

        {/* Horizontal Rule */}
        <ToolbarButton
          onClick={() => editor.chain().focus().setHorizontalRule().run()}
          icon={HorizontalRule}
          label="Insert Divider (---)"
        />

        {/* Code Block */}
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          active={editor.isActive('codeBlock')}
          icon={Code2}
          label="Code Block (Ctrl+Alt+C)"
        />

        {/* Block Quote */}
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          active={editor.isActive('blockquote')}
          icon={Quote}
          label="Block Quote"
        />

      <Separator orientation="vertical" className="h-6 mx-1" />

        {/* ==================== SPECIAL FEATURES GROUP ==================== */}
      {/* Citation */}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={onInsertCitation}
        className="h-8 px-3 gap-2 bg-blue-50 border-blue-200 hover:bg-blue-100 hover:border-blue-300"
        title="Insert Citation"
      >
        <FileText className="h-4 w-4" />
          <span className="text-xs font-medium hidden sm:inline">Citation</span>
      </Button>

      {/* Smart Tag */}
      <SmartTagPopover editor={editor}>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          title="Insert Smart Tag (Ctrl+Shift+T)"
        >
          <Tag className="h-4 w-4" />
        </Button>
      </SmartTagPopover>

      {/* Tooltip */}
      <Popover open={showTooltipPopover} onOpenChange={setShowTooltipPopover}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            title="Add Tooltip (Ctrl+Shift+H)"
          >
            <HelpCircle className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="start">
          <div className="space-y-3">
            <div className="space-y-2">
                <Label className="text-sm font-medium">Add Tooltip to Selection</Label>
              <p className="text-xs text-muted-foreground">
                Select text first, then add helpful information
              </p>
            </div>
              <Input
                placeholder="Enter tooltip text..."
                value={tooltipText}
                onChange={(e) => setTooltipText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && tooltipText.trim()) {
                    e.preventDefault();
                    handleAddTooltip();
                  }
                }}
                autoFocus
              />
            <div className="flex gap-2">
              <Button size="sm" onClick={handleAddTooltip} disabled={!tooltipText.trim()} className="flex-1">
                Add Tooltip
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setTooltipText('');
                  setShowTooltipPopover(false);
                }}
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Callout */}
      <CalloutPopover editor={editor}>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          title="Insert Callout (Ctrl+Shift+C)"
        >
          <MessageSquare className="h-4 w-4" />
        </Button>
      </CalloutPopover>

        <Separator orientation="vertical" className="h-6 mx-1" />

        {/* ==================== FIND & REPLACE TOGGLE ==================== */}
        <ToolbarButton
          onClick={() => setShowFindReplace(!showFindReplace)}
          active={showFindReplace}
          icon={Search}
          label="Find & Replace (Ctrl+F)"
        />

      {/* Spacer */}
      <div className="flex-1" />

        {/* Character Count */}
        <div className="text-xs text-muted-foreground px-2 hidden sm:block">
          {editor.storage.characterCount?.characters?.() || 
           editor.state.doc.textContent.length || 0} chars
        </div>
      </div>

      {/* ==================== FIND & REPLACE BAR ==================== */}
      {showFindReplace && (
        <div className="flex items-center gap-2 px-2 py-2 border-t bg-white flex-wrap">
          {/* Find Section */}
          <div className="flex items-center gap-2">
            <Label className="text-xs font-medium whitespace-nowrap">Find:</Label>
            <Input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleFind();
                }
              }}
              className="h-7 w-32 sm:w-40 text-sm"
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleGoToPrevMatch}
              disabled={matchCount === 0}
              className="h-7 w-7 p-0"
              title="Previous Match"
            >
              <ChevronUp className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleGoToNextMatch}
              disabled={matchCount === 0}
              className="h-7 w-7 p-0"
              title="Next Match"
            >
              <ChevronDown className="h-4 w-4" />
            </Button>
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {matchCount > 0 ? `${currentMatch}/${matchCount}` : 'No results'}
            </span>
          </div>

          <Separator orientation="vertical" className="h-5 mx-1" />

          {/* Replace Section */}
          <div className="flex items-center gap-2">
            <Label className="text-xs font-medium whitespace-nowrap">Replace:</Label>
            <Input
              type="text"
              placeholder="Replace with..."
              value={replaceTerm}
              onChange={(e) => setReplaceTerm(e.target.value)}
              className="h-7 w-32 sm:w-40 text-sm"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleReplace}
              disabled={matchCount === 0}
              className="h-7 px-2 text-xs"
            >
              Replace
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleReplaceAll}
              disabled={matchCount === 0}
              className="h-7 px-2 text-xs"
            >
              All
            </Button>
          </div>

          {/* Close button */}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              setShowFindReplace(false);
              setSearchTerm('');
              setReplaceTerm('');
              setMatchCount(0);
              setCurrentMatch(0);
            }}
            className="h-7 w-7 p-0 ml-auto"
            title="Close Find & Replace"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
