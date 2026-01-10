/**
 * ParagraphStylesSelect Component
 * 
 * Dropdown for applying predefined paragraph styles (Normal, Heading 1-3, Quote).
 * Each style applies multiple formatting attributes at once.
 * 
 * Dependencies:
 *   - TipTap editor with Heading, FontSize, TextAlign extensions
 *   - Shadcn Select component
 */

import { Editor } from '@tiptap/react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// Props interface for ParagraphStylesSelect component
interface ParagraphStylesSelectProps {
  editor: Editor;
}

/**
 * Paragraph style definition
 * Each style can apply heading level, font size, alignment, and font weight
 */
interface ParagraphStyle {
  id: string;
  name: string;
  description: string;
  // Properties to apply
  heading?: 1 | 2 | 3;
  fontSize?: string;
  fontWeight?: string;
  textAlign?: 'left' | 'center' | 'right' | 'justify';
  isBlockquote?: boolean;
}

/**
 * Predefined paragraph styles
 * Based on common document formatting conventions
 */
export const PARAGRAPH_STYLES: ParagraphStyle[] = [
  {
    id: 'normal',
    name: 'Normal Text',
    description: '12pt, regular',
    fontSize: '12pt',
    textAlign: 'left',
  },
  {
    id: 'heading1',
    name: 'Heading 1',
    description: '16pt, bold, centered',
    heading: 1,
    fontSize: '16pt',
    fontWeight: 'bold',
    textAlign: 'center',
  },
  {
    id: 'heading2',
    name: 'Heading 2',
    description: '14pt, bold',
    heading: 2,
    fontSize: '14pt',
    fontWeight: 'bold',
    textAlign: 'left',
  },
  {
    id: 'heading3',
    name: 'Heading 3',
    description: '12pt, bold',
    heading: 3,
    fontSize: '12pt',
    fontWeight: 'bold',
    textAlign: 'left',
  },
  {
    id: 'quote',
    name: 'Quote',
    description: '12pt, italic, indented',
    fontSize: '12pt',
    isBlockquote: true,
  },
];

/**
 * Determine the current style based on editor state
 * @param editor - TipTap editor instance
 * @returns The ID of the matching style or 'normal'
 */
function getCurrentStyle(editor: Editor): string {
  // Check for headings first
  if (editor.isActive('heading', { level: 1 })) return 'heading1';
  if (editor.isActive('heading', { level: 2 })) return 'heading2';
  if (editor.isActive('heading', { level: 3 })) return 'heading3';
  if (editor.isActive('blockquote')) return 'quote';
  
  return 'normal';
}

/**
 * ParagraphStylesSelect - Dropdown for paragraph styles
 * 
 * Features:
 * - Shows current style name in trigger
 * - Each option shows name and description
 * - Applies multiple formatting attributes at once
 * - Resets conflicting formatting when changing styles
 */
export function ParagraphStylesSelect({ editor }: ParagraphStylesSelectProps) {
  // Get current style from editor state
  const currentStyleId = getCurrentStyle(editor);
  const currentStyle = PARAGRAPH_STYLES.find((s) => s.id === currentStyleId) || PARAGRAPH_STYLES[0];

  // Handle style selection
  const handleStyleChange = (styleId: string) => {
    const style = PARAGRAPH_STYLES.find((s) => s.id === styleId);
    if (!style) return;

    // Start a chain of commands
    let chain = editor.chain().focus();

    // First, clear existing block-level formatting
    // Remove heading if applying non-heading style
    if (!style.heading) {
      chain = chain.setParagraph();
    }
    
    // Remove blockquote if not applying quote style
    if (!style.isBlockquote && editor.isActive('blockquote')) {
      chain = chain.lift('blockquote');
    }

    // Apply the new style properties
    if (style.heading) {
      chain = chain.toggleHeading({ level: style.heading });
    }

    if (style.isBlockquote) {
      chain = chain.toggleBlockquote();
    }

    // Apply font size if specified
    if (style.fontSize) {
      // @ts-expect-error - setFontSize is from custom extension
      chain = chain.setFontSize(style.fontSize);
    }

    // Apply text alignment if specified
    if (style.textAlign) {
      // @ts-expect-error - setTextAlign is from TextAlign extension
      chain = chain.setTextAlign(style.textAlign);
    }

    // Execute the chain
    chain.run();
  };

  return (
    <Select value={currentStyleId} onValueChange={handleStyleChange}>
      <SelectTrigger 
        className="w-[130px] h-8 text-sm font-normal"
        title="Paragraph Style"
      >
        <SelectValue>
          <span>{currentStyle.name}</span>
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {PARAGRAPH_STYLES.map((style) => (
          <SelectItem 
            key={style.id} 
            value={style.id}
            className="flex flex-col items-start py-2"
          >
            <div className="flex flex-col">
              <span 
                className="font-medium"
                style={{
                  fontSize: style.id === 'heading1' ? '14px' : 
                           style.id === 'heading2' ? '13px' : '12px',
                  fontWeight: style.heading ? 'bold' : 'normal',
                  fontStyle: style.isBlockquote ? 'italic' : 'normal',
                }}
              >
                {style.name}
              </span>
              <span className="text-xs text-muted-foreground">
                {style.description}
              </span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export default ParagraphStylesSelect;
