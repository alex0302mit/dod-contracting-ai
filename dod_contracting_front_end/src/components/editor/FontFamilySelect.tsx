/**
 * FontFamilySelect Component
 * 
 * Dropdown selector for choosing font families in the editor.
 * Displays font options with preview in their actual font.
 * 
 * Dependencies:
 *   - TipTap editor with FontFamily extension
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

// Props interface for the FontFamilySelect component
interface FontFamilySelectProps {
  editor: Editor;
}

/**
 * Available font families with display names and CSS values
 * Each font includes a fallback stack for cross-platform compatibility
 */
export const FONT_FAMILIES = [
  { name: 'Times New Roman', value: '"Times New Roman", Times, serif' },
  { name: 'Arial', value: 'Arial, Helvetica, sans-serif' },
  { name: 'Calibri', value: 'Calibri, "Segoe UI", sans-serif' },
  { name: 'Georgia', value: 'Georgia, "Times New Roman", serif' },
  { name: 'Verdana', value: 'Verdana, Geneva, sans-serif' },
  { name: 'Courier New', value: '"Courier New", Courier, monospace' },
  { name: 'Trebuchet MS', value: '"Trebuchet MS", Helvetica, sans-serif' },
  { name: 'Garamond', value: 'Garamond, "Times New Roman", serif' },
];

/**
 * Get the current font family from the editor
 * @param editor - TipTap editor instance
 * @returns Current font family value or default
 */
function getCurrentFontFamily(editor: Editor): string {
  // Get the fontFamily attribute from textStyle mark
  const attrs = editor.getAttributes('textStyle');
  return attrs.fontFamily || FONT_FAMILIES[0].value;
}

/**
 * Get display name for a font family value
 * @param value - CSS font-family value
 * @returns Display name or the value itself if not found
 */
function getFontFamilyName(value: string): string {
  const font = FONT_FAMILIES.find((f) => f.value === value);
  if (font) return font.name;
  
  // Try to extract first font name from the value
  const match = value.match(/^["']?([^"',]+)/);
  return match ? match[1] : value;
}

/**
 * FontFamilySelect - Dropdown for selecting font family
 * 
 * Features:
 * - Shows current font in the trigger
 * - Font options displayed in their actual font
 * - Updates editor on selection change
 */
export function FontFamilySelect({ editor }: FontFamilySelectProps) {
  // Get current font family from editor state
  const currentValue = getCurrentFontFamily(editor);
  const currentName = getFontFamilyName(currentValue);

  // Handle font family selection
  const handleFontChange = (value: string) => {
    if (value) {
      // @ts-expect-error - setFontFamily is provided by FontFamily extension
      editor.chain().focus().setFontFamily(value).run();
    }
  };

  return (
    <Select value={currentValue} onValueChange={handleFontChange}>
      <SelectTrigger
        className="w-[140px] h-8 text-sm font-normal rounded-lg border-border shadow-sm transition-all duration-150 hover:border-muted-foreground focus:ring-2 focus:ring-primary/20"
        title="Font Family"
      >
        <SelectValue>
          <span style={{ fontFamily: currentValue }}>{currentName}</span>
        </SelectValue>
      </SelectTrigger>
      <SelectContent className="shadow-lg rounded-lg">
        {FONT_FAMILIES.map((font) => (
          <SelectItem
            key={font.value}
            value={font.value}
            className="text-sm transition-colors"
          >
            <span style={{ fontFamily: font.value }}>{font.name}</span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export default FontFamilySelect;
