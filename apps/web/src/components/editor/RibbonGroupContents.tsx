/**
 * RibbonGroupContents - Reusable toolbar group content components
 * 
 * These components contain the actual controls for each toolbar group.
 * They are extracted to be reusable in both expanded (RibbonGroup) and
 * collapsed (CollapsedGroup dropdown) states.
 * 
 * Dependencies:
 * - TipTap Editor
 * - shadcn/ui components
 * - lucide-react icons
 */

import { Editor } from '@tiptap/react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  RemoveFormatting,
  Palette,
  Highlighter,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  List,
  ListOrdered,
  IndentIncrease,
  IndentDecrease,
  Undo2,
  Redo2,
  Search,
  Type,
  Hash,
  ZoomIn,
  ZoomOut,
  Maximize,
  Save,
  Download,
  Printer,
} from 'lucide-react';
import { FontFamilySelect } from './FontFamilySelect';
import { FontSizeSelect } from './FontSizeSelect';
import { ParagraphStylesSelect } from './ParagraphStylesSelect';

// ============================================================================
// Shared Types
// ============================================================================

interface GroupContentProps {
  editor: Editor;
  compact?: boolean; // When true, use vertical layout for collapsed state
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
// Toolbar Button Component (shared)
// ============================================================================

interface ToolbarButtonProps {
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  className?: string;
}

function ToolbarButton({ onClick, active, disabled, icon: Icon, label, className = '' }: ToolbarButtonProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={onClick}
      disabled={disabled}
      className={`h-8 w-8 p-0 rounded-md transition-all duration-150 ${
        active
          ? 'bg-primary/10 text-primary ring-1 ring-primary/20 shadow-sm'
          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      } ${className}`}
      title={label}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );
}

// ============================================================================
// Color Swatch Component (shared)
// ============================================================================

interface ColorSwatchProps {
  color: string;
  name: string;
  onClick: () => void;
  isActive?: boolean;
}

function ColorSwatch({ color, name, onClick, isActive }: ColorSwatchProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-6 h-6 rounded-md border-2 transition-all duration-150 ${
        isActive ? 'border-primary ring-2 ring-primary/20 scale-110' : 'border-slate-200 hover:border-slate-400 hover:scale-105'
      }`}
      style={{ backgroundColor: color || '#ffffff' }}
      title={name}
    />
  );
}

// ============================================================================
// FONT GROUP CONTENT
// ============================================================================

interface FontGroupContentProps extends GroupContentProps {
  showTextColorPopover: boolean;
  setShowTextColorPopover: (show: boolean) => void;
  showHighlightPopover: boolean;
  setShowHighlightPopover: (show: boolean) => void;
}

export function FontGroupContent({
  editor,
  compact = false,
  showTextColorPopover,
  setShowTextColorPopover,
  showHighlightPopover,
  setShowHighlightPopover,
}: FontGroupContentProps) {
  // Handlers
  const handleSetTextColor = (color: string) => {
    if (color === 'inherit') {
      editor.chain().focus().unsetColor().run();
    } else {
      editor.chain().focus().setColor(color).run();
    }
    setShowTextColorPopover(false);
  };

  const handleSetHighlight = (color: string) => {
    if (!color) {
      editor.chain().focus().unsetHighlight().run();
    } else {
      editor.chain().focus().setHighlight({ color }).run();
    }
    setShowHighlightPopover(false);
  };

  const handleClearFormatting = () => {
    editor.chain().focus().clearNodes().unsetAllMarks().run();
  };

  return (
    <div className={`flex ${compact ? 'flex-col' : 'flex-col'} gap-1`}>
      {/* Row 1: Font family and size */}
      <div className="flex items-center gap-1">
        <FontFamilySelect editor={editor} />
        <FontSizeSelect editor={editor} />
      </div>
      
      {/* Row 2: Text formatting */}
      <div className="flex items-center gap-0.5 flex-wrap">
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
          label="Strikethrough"
        />
        
        {/* Text Color */}
        <Popover open={showTextColorPopover} onOpenChange={setShowTextColorPopover}>
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 rounded-md transition-all duration-150 text-muted-foreground hover:bg-muted hover:text-foreground"
              title="Text Color"
            >
              <Palette className="h-4 w-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-3 shadow-lg rounded-xl" align="start">
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
        
        {/* Highlight Color */}
        <Popover open={showHighlightPopover} onOpenChange={setShowHighlightPopover}>
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 rounded-md transition-all duration-150 text-muted-foreground hover:bg-muted hover:text-foreground"
              title="Highlight"
            >
              <Highlighter className="h-4 w-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-3 shadow-lg rounded-xl" align="start">
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
        
        <ToolbarButton
          onClick={handleClearFormatting}
          icon={RemoveFormatting}
          label="Clear Formatting"
        />
      </div>
    </div>
  );
}

// ============================================================================
// PARAGRAPH GROUP CONTENT
// ============================================================================

export function ParagraphGroupContent({ editor, compact = false }: GroupContentProps) {
  return (
    <div className={`flex ${compact ? 'flex-col' : 'flex-col'} gap-1`}>
      {/* Row 1: Alignment */}
      <div className="flex items-center gap-0.5">
        <ToolbarButton
          onClick={() => editor.chain().focus().setTextAlign('left').run()}
          active={editor.isActive({ textAlign: 'left' })}
          icon={AlignLeft}
          label="Align Left"
        />
        <ToolbarButton
          onClick={() => editor.chain().focus().setTextAlign('center').run()}
          active={editor.isActive({ textAlign: 'center' })}
          icon={AlignCenter}
          label="Align Center"
        />
        <ToolbarButton
          onClick={() => editor.chain().focus().setTextAlign('right').run()}
          active={editor.isActive({ textAlign: 'right' })}
          icon={AlignRight}
          label="Align Right"
        />
        <ToolbarButton
          onClick={() => editor.chain().focus().setTextAlign('justify').run()}
          active={editor.isActive({ textAlign: 'justify' })}
          icon={AlignJustify}
          label="Justify"
        />
      </div>
      
      {/* Row 2: Lists and indent */}
      <div className="flex items-center gap-0.5">
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
          onClick={() => editor.chain().focus().liftListItem('listItem').run()}
          disabled={!editor.can().liftListItem('listItem')}
          icon={IndentDecrease}
          label="Outdent"
        />
        <ToolbarButton
          onClick={() => editor.chain().focus().sinkListItem('listItem').run()}
          disabled={!editor.can().sinkListItem('listItem')}
          icon={IndentIncrease}
          label="Indent"
        />
      </div>
    </div>
  );
}

// ============================================================================
// STYLES GROUP CONTENT
// ============================================================================

export function StylesGroupContent({ editor }: GroupContentProps) {
  return (
    <div className="flex items-center">
      <ParagraphStylesSelect editor={editor} />
    </div>
  );
}

// ============================================================================
// EDITING GROUP CONTENT
// ============================================================================

interface EditingGroupContentProps extends GroupContentProps {
  showFindReplace: boolean;
  setShowFindReplace: (show: boolean) => void;
}

export function EditingGroupContent({ 
  editor, 
  showFindReplace, 
  setShowFindReplace 
}: EditingGroupContentProps) {
  return (
    <div className="flex items-center gap-0.5">
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
      <Button
        type="button"
        variant={showFindReplace ? 'default' : 'ghost'}
        size="sm"
        className={`h-8 w-8 p-0 rounded-md transition-all duration-150 ${
          showFindReplace
            ? 'bg-primary/10 text-primary ring-1 ring-primary/20 shadow-sm'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        }`}
        onClick={() => setShowFindReplace(!showFindReplace)}
        title="Find & Replace"
      >
        <Search className="h-4 w-4" />
      </Button>
    </div>
  );
}

// ============================================================================
// DOCUMENT GROUP CONTENT
// ============================================================================

export function DocumentGroupContent({ editor }: GroupContentProps) {
  const wordCount = editor.state.doc.textContent.trim().split(/\s+/).filter(w => w.length > 0).length;
  const charCount = editor.state.doc.textContent.length;
  
  return (
    <div className="flex flex-col gap-1 min-w-[100px]">
      {/* Word count */}
      <div className="flex items-center gap-1.5 text-xs text-slate-600">
        <Type className="h-3 w-3" />
        <span>{wordCount.toLocaleString()} words</span>
      </div>
      {/* Character count */}
      <div className="flex items-center gap-1.5 text-xs text-slate-600">
        <Hash className="h-3 w-3" />
        <span>{charCount.toLocaleString()} chars</span>
      </div>
    </div>
  );
}

// ============================================================================
// VIEW GROUP CONTENT
// ============================================================================

export function ViewGroupContent({ editor }: GroupContentProps) {
  return (
    <div className="flex items-center gap-0.5">
      <ToolbarButton
        onClick={() => {/* Zoom out - handled by parent */}}
        icon={ZoomOut}
        label="Zoom Out"
      />
      <span className="text-xs text-slate-600 min-w-[40px] text-center">100%</span>
      <ToolbarButton
        onClick={() => {/* Zoom in - handled by parent */}}
        icon={ZoomIn}
        label="Zoom In"
      />
      <ToolbarButton
        onClick={() => {
          if (document.fullscreenElement) {
            document.exitFullscreen();
          } else {
            document.documentElement.requestFullscreen();
          }
        }}
        icon={Maximize}
        label="Toggle Fullscreen"
      />
    </div>
  );
}

// ============================================================================
// ACTIONS GROUP CONTENT
// ============================================================================

export function ActionsGroupContent({ editor }: GroupContentProps) {
  return (
    <div className="flex items-center gap-0.5">
      <ToolbarButton
        onClick={() => {
          console.log('Save document');
        }}
        icon={Save}
        label="Save (Ctrl+S)"
      />
      <ToolbarButton
        onClick={() => {
          console.log('Export document');
        }}
        icon={Download}
        label="Export"
      />
      <ToolbarButton
        onClick={() => window.print()}
        icon={Printer}
        label="Print (Ctrl+P)"
      />
    </div>
  );
}
