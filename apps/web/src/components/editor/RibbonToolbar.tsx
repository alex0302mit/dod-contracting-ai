/**
 * RibbonToolbar Component
 * 
 * Microsoft Word-style ribbon toolbar with tabbed interface.
 * Organizes editor controls into Home, Insert, and Layout tabs.
 * 
 * Features:
 * - File header with editable document name
 * - Mode selector (Editing/Viewing)
 * - Tabbed ribbon interface
 * - Find & Replace panel
 * 
 * Dependencies:
 * - TipTap editor with extensions
 * - Shadcn UI components (Tabs, Button, Input, Popover, Select)
 * - FontFamilySelect, FontSizeSelect, ParagraphStylesSelect
 * - SmartTagPopover, CalloutPopover
 */

import { useState, useCallback } from 'react';
import { Editor } from '@tiptap/react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
// Responsive toolbar hook and collapsed group component
import { useResponsiveToolbar } from './hooks/useResponsiveToolbar';
import { CollapsedGroup } from './CollapsedGroup';
// Reusable group content components
import {
  FontGroupContent,
  ParagraphGroupContent,
  StylesGroupContent,
  EditingGroupContent,
  DocumentGroupContent,
  ViewGroupContent,
  ActionsGroupContent,
} from './RibbonGroupContents';
import {
  // Text formatting icons
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  RemoveFormatting,
  // Color icons
  Palette,
  Highlighter,
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
  // History icons
  Undo2,
  Redo2,
  // Mode icons
  Edit3,
  Eye,
  // Document info icons
  Type,
  Hash,
  // View icons
  ZoomIn,
  ZoomOut,
  Ruler,
  Maximize,
  // Actions icons
  Save,
  Download,
  Printer,
} from 'lucide-react';

// Import custom components
import { FontFamilySelect } from './FontFamilySelect';
import { FontSizeSelect } from './FontSizeSelect';
import { ParagraphStylesSelect } from './ParagraphStylesSelect';
import { SmartTagPopover } from './SmartTagPopover';
import { CalloutPopover } from './CalloutPopover';
import { RibbonGroup, RibbonDivider } from './RibbonGroup';

// ============================================================================
// Types & Interfaces
// ============================================================================

interface RibbonToolbarProps {
  editor: Editor;
  documentName?: string;
  onDocumentNameChange?: (name: string) => void;
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

// Line spacing options
const LINE_SPACING_OPTIONS = [
  { label: '1.0', value: '1' },
  { label: '1.15', value: '1.15' },
  { label: '1.5', value: '1.5' },
  { label: '2.0', value: '2' },
  { label: '2.5', value: '2.5' },
  { label: '3.0', value: '3' },
];

// ============================================================================
// Main Component
// ============================================================================

export function RibbonToolbar({ 
  editor, 
  documentName = 'Untitled Document',
  onDocumentNameChange,
  onInsertCitation 
}: RibbonToolbarProps) {
  // ---------------------------
  // State Management
  // ---------------------------
  
  // Document name editing state
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState(documentName);
  
  // Mode state
  const [editorMode, setEditorMode] = useState<'editing' | 'viewing'>('editing');
  
  // Tooltip popover state
  const [showTooltipPopover, setShowTooltipPopover] = useState(false);
  const [tooltipText, setTooltipText] = useState('');
  
  // Table insertion state
  const [showTablePopover, setShowTablePopover] = useState(false);
  const [tableRows, setTableRows] = useState(3);
  const [tableCols, setTableCols] = useState(3);
  
  // Color picker states
  const [showTextColorPopover, setShowTextColorPopover] = useState(false);
  const [showHighlightPopover, setShowHighlightPopover] = useState(false);
  
  // Find & Replace state
  const [showFindReplace, setShowFindReplace] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [replaceTerm, setReplaceTerm] = useState('');
  const [matchCount, setMatchCount] = useState(0);
  const [currentMatch, setCurrentMatch] = useState(0);

  // Responsive toolbar - detects container width and determines which groups to collapse
  const { containerRef, isCollapsed } = useResponsiveToolbar();

  // Early return if editor not ready
  if (!editor) {
    return null;
  }

  // ---------------------------
  // Document Name Handlers
  // ---------------------------

  const handleNameSave = () => {
    setIsEditingName(false);
    if (onDocumentNameChange && editedName.trim()) {
      onDocumentNameChange(editedName.trim());
    }
  };

  const handleNameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleNameSave();
    } else if (e.key === 'Escape') {
      setEditedName(documentName);
      setIsEditingName(false);
    }
  };

  // ---------------------------
  // Handler Functions
  // ---------------------------
  
  // Insert a new table with specified dimensions
  // Using type assertion to handle TipTap extension methods
  const handleInsertTable = () => {
    (editor.chain().focus() as any)
      .insertTable({ rows: tableRows, cols: tableCols, withHeaderRow: true })
      .run();
    
    setTableRows(3);
    setTableCols(3);
    setShowTablePopover(false);
  };

  // Add tooltip to selected text
  // Using type assertion for custom TooltipExtension command
  const handleAddTooltip = () => {
    if (!tooltipText.trim()) return;

    const { from, to } = editor.state.selection;
    if (from === to) return;

    (editor.chain().focus() as any)
      .addTooltip({
        tooltipId: `tooltip-${Date.now()}`,
        tooltipText: tooltipText.trim(),
        tooltipType: 'help',
      })
      .run();

    setTooltipText('');
    setShowTooltipPopover(false);
  };

  // Set text color
  // Using type assertion for Color extension methods
  const handleSetTextColor = (color: string) => {
    if (color === 'inherit') {
      (editor.chain().focus() as any).unsetColor().run();
    } else {
      (editor.chain().focus() as any).setColor(color).run();
    }
    setShowTextColorPopover(false);
  };

  // Set highlight color
  // Using type assertion for Highlight extension methods
  const handleSetHighlight = (color: string) => {
    if (!color) {
      (editor.chain().focus() as any).unsetHighlight().run();
    } else {
      (editor.chain().focus() as any).setHighlight({ color }).run();
    }
    setShowHighlightPopover(false);
  };

  // Clear all formatting from selection
  const handleClearFormatting = () => {
    editor.chain().focus().unsetAllMarks().clearNodes().run();
  };

  // Set text alignment
  // Using type assertion for TextAlign extension methods
  const handleAlignLeft = () => (editor.chain().focus() as any).setTextAlign('left').run();
  const handleAlignCenter = () => (editor.chain().focus() as any).setTextAlign('center').run();
  const handleAlignRight = () => (editor.chain().focus() as any).setTextAlign('right').run();
  const handleAlignJustify = () => (editor.chain().focus() as any).setTextAlign('justify').run();

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
            if (count === newMatch) return false;
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
        handleFind();
      }
    }
  };

  const handleReplaceAll = () => {
    if (!searchTerm) return;

    const { doc, tr } = editor.state;
    const positions: { from: number; to: number }[] = [];

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

  // Compact toolbar button for ribbon interface
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
      className={`h-8 w-8 p-0 rounded-md transition-all duration-150 ${
        active
          ? 'bg-primary/10 text-primary ring-1 ring-primary/20 shadow-sm hover:bg-primary/15'
          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      } ${className}`}
      title={label}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );

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
      className={`w-7 h-7 rounded-md transition-all duration-150 hover:scale-105 ${
        isActive
          ? 'ring-2 ring-primary ring-offset-1 scale-105'
          : 'border border-border hover:border-muted-foreground'
      }`}
      style={{ backgroundColor: color || 'transparent' }}
      title={name}
    >
      {!color && <X className="h-4 w-4 text-muted-foreground mx-auto" />}
    </button>
  );

  // ---------------------------
  // Render
  // ---------------------------

  return (
    <div 
      ref={containerRef}
      className="ribbon-toolbar bg-gradient-to-b from-slate-50 to-slate-100 shadow-sm border-b border-slate-200/60"
    >
      {/* ==================== RIBBON TABS ==================== */}
      <Tabs defaultValue="home" className="w-full">
        {/* Tab navigation with Word-style underline */}
        <TabsList className="w-full justify-start h-9 bg-transparent border-b border-slate-200/60 rounded-none px-1 gap-0">
          <TabsTrigger
            value="home"
            className="text-xs font-medium px-4 h-8 rounded-none border-b-2 border-transparent transition-all duration-150 hover:text-foreground data-[state=active]:border-primary data-[state=active]:text-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"
          >
            Home
          </TabsTrigger>
          <TabsTrigger
            value="insert"
            className="text-xs font-medium px-4 h-8 rounded-none border-b-2 border-transparent transition-all duration-150 hover:text-foreground data-[state=active]:border-primary data-[state=active]:text-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"
          >
            Insert
          </TabsTrigger>
          <TabsTrigger
            value="layout"
            className="text-xs font-medium px-4 h-8 rounded-none border-b-2 border-transparent transition-all duration-150 hover:text-foreground data-[state=active]:border-primary data-[state=active]:text-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"
          >
            Layout
          </TabsTrigger>
        </TabsList>

        {/* ==================== HOME TAB ==================== */}
        {/* Responsive: Groups collapse into dropdowns when toolbar is narrow */}
        <TabsContent value="home" className="mt-0">
          <div className="flex items-stretch">
            {/* ===== FONT GROUP - Never collapses (most essential) ===== */}
            <RibbonGroup label="Font" showSeparator={false}>
              <FontGroupContent
                editor={editor}
                showTextColorPopover={showTextColorPopover}
                setShowTextColorPopover={setShowTextColorPopover}
                showHighlightPopover={showHighlightPopover}
                setShowHighlightPopover={setShowHighlightPopover}
              />
            </RibbonGroup>

            <RibbonDivider />

            {/* ===== PARAGRAPH GROUP - Collapses at narrow widths ===== */}
            {isCollapsed('PARAGRAPH') ? (
              <CollapsedGroup label="Para" icon={AlignLeft}>
                <ParagraphGroupContent editor={editor} compact />
              </CollapsedGroup>
            ) : (
              <RibbonGroup label="Paragraph" showSeparator={false}>
                <ParagraphGroupContent editor={editor} />
              </RibbonGroup>
            )}

            {!isCollapsed('PARAGRAPH') && <RibbonDivider />}

            {/* ===== STYLES GROUP - Collapses at medium widths ===== */}
            {isCollapsed('STYLES') ? (
              <CollapsedGroup label="Styles" icon={Type}>
                <StylesGroupContent editor={editor} />
              </CollapsedGroup>
            ) : (
              <RibbonGroup label="Styles" showSeparator={false}>
                <StylesGroupContent editor={editor} />
              </RibbonGroup>
            )}

            {!isCollapsed('STYLES') && <RibbonDivider />}

            {/* ===== EDITING GROUP - Collapses at medium widths ===== */}
            {isCollapsed('EDITING') ? (
              <CollapsedGroup label="Edit" icon={Undo2}>
                <EditingGroupContent 
                  editor={editor} 
                  showFindReplace={showFindReplace}
                  setShowFindReplace={setShowFindReplace}
                />
              </CollapsedGroup>
            ) : (
              <RibbonGroup label="Editing" showSeparator={false}>
                <EditingGroupContent 
                  editor={editor} 
                  showFindReplace={showFindReplace}
                  setShowFindReplace={setShowFindReplace}
                />
              </RibbonGroup>
            )}

            {/* ===== SPACER TO PUSH RIGHT GROUPS ===== */}
            <div className="flex-1" />

            {/* ===== DOCUMENT INFO GROUP - Collapses early ===== */}
            {isCollapsed('DOCUMENT') ? (
              <CollapsedGroup label="Doc" icon={FileText}>
                <DocumentGroupContent editor={editor} />
              </CollapsedGroup>
            ) : (
              <RibbonGroup label="Document" showSeparator={false}>
                <DocumentGroupContent editor={editor} />
              </RibbonGroup>
            )}

            {!isCollapsed('DOCUMENT') && <RibbonDivider />}

            {/* ===== VIEW GROUP - Collapses early ===== */}
            {isCollapsed('VIEW') ? (
              <CollapsedGroup label="View" icon={ZoomIn}>
                <ViewGroupContent editor={editor} />
              </CollapsedGroup>
            ) : (
              <RibbonGroup label="View" showSeparator={false}>
                <ViewGroupContent editor={editor} />
              </RibbonGroup>
            )}

            {!isCollapsed('VIEW') && <RibbonDivider />}

            {/* ===== ACTIONS GROUP - Collapses first (least used during editing) ===== */}
            {isCollapsed('ACTIONS') ? (
              <CollapsedGroup label="Actions" icon={Save}>
                <ActionsGroupContent editor={editor} />
              </CollapsedGroup>
            ) : (
              <RibbonGroup label="Actions" showSeparator={false}>
                <ActionsGroupContent editor={editor} />
              </RibbonGroup>
            )}
          </div>
        </TabsContent>

        {/* ==================== INSERT TAB ==================== */}
        <TabsContent value="insert" className="mt-0">
          <div className="flex items-stretch">
            {/* Table */}
            <Popover open={showTablePopover} onOpenChange={setShowTablePopover}>
              <PopoverTrigger asChild>
                <Button type="button" variant="ghost" size="sm" className="h-8 px-3 gap-2" title="Insert Table">
                  <Table className="h-4 w-4" />
                  <span className="text-xs">Table</span>
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

            <Separator orientation="vertical" className="h-6 mx-1" />

            {/* Horizontal Rule */}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 px-3 gap-2"
              onClick={() => editor.chain().focus().setHorizontalRule().run()}
              title="Insert Divider"
            >
              <HorizontalRule className="h-4 w-4" />
              <span className="text-xs">Divider</span>
            </Button>

            {/* Code Block */}
            <Button
              type="button"
              variant={editor.isActive('codeBlock') ? 'default' : 'ghost'}
              size="sm"
              className="h-8 px-3 gap-2"
              onClick={() => editor.chain().focus().toggleCodeBlock().run()}
              title="Code Block"
            >
              <Code2 className="h-4 w-4" />
              <span className="text-xs">Code</span>
            </Button>

            {/* Block Quote */}
            <Button
              type="button"
              variant={editor.isActive('blockquote') ? 'default' : 'ghost'}
              size="sm"
              className="h-8 px-3 gap-2"
              onClick={() => editor.chain().focus().toggleBlockquote().run()}
              title="Block Quote"
            >
              <Quote className="h-4 w-4" />
              <span className="text-xs">Quote</span>
            </Button>

            <Separator orientation="vertical" className="h-6 mx-1" />

            {/* Citation */}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onInsertCitation}
              className="h-8 px-3 gap-2 bg-primary/5 border-primary/20 text-primary hover:bg-primary/10 transition-all duration-150"
              title="Insert Citation"
            >
              <FileText className="h-4 w-4" />
              <span className="text-xs font-medium">Citation</span>
            </Button>

            {/* Smart Tag */}
            <SmartTagPopover editor={editor}>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-8 px-3 gap-2"
                title="Insert Smart Tag"
              >
                <Tag className="h-4 w-4" />
                <span className="text-xs">Smart Tag</span>
              </Button>
            </SmartTagPopover>

            {/* Tooltip */}
            <Popover open={showTooltipPopover} onOpenChange={setShowTooltipPopover}>
              <PopoverTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-8 px-3 gap-2"
                  title="Add Tooltip"
                >
                  <HelpCircle className="h-4 w-4" />
                  <span className="text-xs">Tooltip</span>
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
                className="h-8 px-3 gap-2"
                title="Insert Callout"
              >
                <MessageSquare className="h-4 w-4" />
                <span className="text-xs">Callout</span>
              </Button>
            </CalloutPopover>
          </div>
        </TabsContent>

        {/* ==================== LAYOUT TAB ==================== */}
        <TabsContent value="layout" className="mt-0 p-2">
          <div className="flex items-center gap-4 flex-wrap">
            {/* Line Spacing */}
            <div className="flex items-center gap-2">
              <Label className="text-xs font-medium whitespace-nowrap">Line Spacing:</Label>
              <Select defaultValue="1.5">
                <SelectTrigger className="w-[70px] h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LINE_SPACING_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Separator orientation="vertical" className="h-6" />

            {/* Paragraph spacing info */}
            <div className="text-xs text-muted-foreground">
              Paragraph spacing: 12pt after
            </div>

            <div className="flex-1" />

            {/* Character count */}
            <div className="text-xs text-muted-foreground">
              {editor.state.doc.textContent.length} characters
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* ==================== FIND & REPLACE BAR ==================== */}
      {showFindReplace && (
        <div className="flex items-center gap-2 px-4 py-2 border-t border-slate-200/60 bg-white/80 backdrop-blur-sm flex-wrap">
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

export default RibbonToolbar;
