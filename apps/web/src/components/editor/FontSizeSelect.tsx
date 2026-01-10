/**
 * FontSizeSelect Component
 * 
 * Dropdown selector with increment/decrement buttons for font size.
 * Displays current size and allows quick adjustments.
 * 
 * Dependencies:
 *   - TipTap editor with custom FontSize extension
 *   - Shadcn Select component
 *   - Lucide icons
 */

import { Editor } from '@tiptap/react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Minus, Plus } from 'lucide-react';
import { 
  FONT_SIZES, 
  getCurrentFontSize, 
  incrementFontSize, 
  decrementFontSize,
  parseFontSize 
} from './FontSizeExtension';

// Props interface for FontSizeSelect component
interface FontSizeSelectProps {
  editor: Editor;
}

// Default font size when none is set
const DEFAULT_FONT_SIZE = '12pt';

/**
 * Get display value for font size (strip unit for cleaner display)
 * @param size - Font size with unit (e.g., '12pt')
 * @returns Numeric display value (e.g., '12')
 */
function getDisplaySize(size: string): string {
  const num = parseFontSize(size);
  return num !== null ? String(num) : '12';
}

/**
 * FontSizeSelect - Dropdown with increment/decrement for font size
 * 
 * Features:
 * - Dropdown with standard font sizes
 * - Plus/minus buttons for quick adjustment
 * - Shows current size in the trigger
 * - Updates editor on selection change
 */
export function FontSizeSelect({ editor }: FontSizeSelectProps) {
  // Get current font size from editor or use default
  const currentSize = getCurrentFontSize(editor) || DEFAULT_FONT_SIZE;
  const displaySize = getDisplaySize(currentSize);

  // Handle size selection from dropdown
  const handleSizeChange = (value: string) => {
    if (value) {
      // @ts-expect-error - setFontSize is provided by custom FontSize extension
      editor.chain().focus().setFontSize(value).run();
    }
  };

  // Handle increment button click
  const handleIncrement = () => {
    const newSize = incrementFontSize(currentSize);
    // @ts-expect-error - setFontSize is provided by custom FontSize extension
    editor.chain().focus().setFontSize(newSize).run();
  };

  // Handle decrement button click
  const handleDecrement = () => {
    const newSize = decrementFontSize(currentSize);
    // @ts-expect-error - setFontSize is provided by custom FontSize extension
    editor.chain().focus().setFontSize(newSize).run();
  };

  // Check if at size limits
  const isAtMin = currentSize === FONT_SIZES[0];
  const isAtMax = currentSize === FONT_SIZES[FONT_SIZES.length - 1];

  return (
    <div className="flex items-center gap-0.5">
      {/* Decrement button */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-8 w-7 p-0 rounded-md transition-all duration-150 text-muted-foreground hover:bg-muted hover:text-foreground"
        onClick={handleDecrement}
        disabled={isAtMin}
        title="Decrease font size"
      >
        <Minus className="h-3.5 w-3.5" />
      </Button>

      {/* Font size dropdown */}
      <Select value={currentSize} onValueChange={handleSizeChange}>
        <SelectTrigger
          className="w-[60px] h-8 text-sm font-normal px-2 rounded-lg border-border shadow-sm transition-all duration-150 hover:border-muted-foreground focus:ring-2 focus:ring-primary/20"
          title="Font Size"
        >
          <SelectValue>
            <span>{displaySize}</span>
          </SelectValue>
        </SelectTrigger>
        <SelectContent className="shadow-lg rounded-lg">
          {FONT_SIZES.map((size) => (
            <SelectItem
              key={size}
              value={size}
              className="text-sm transition-colors"
            >
              {getDisplaySize(size)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Increment button */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-8 w-7 p-0 rounded-md transition-all duration-150 text-muted-foreground hover:bg-muted hover:text-foreground"
        onClick={handleIncrement}
        disabled={isAtMax}
        title="Increase font size"
      >
        <Plus className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}

export default FontSizeSelect;
