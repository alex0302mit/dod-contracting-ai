/**
 * FontSize Extension for TipTap
 * 
 * Custom extension to support arbitrary font sizes in the editor.
 * Extends the TextStyle extension to add fontSize attribute support.
 * 
 * Usage:
 *   editor.chain().focus().setFontSize('14pt').run()
 *   editor.chain().focus().unsetFontSize().run()
 * 
 * Dependencies:
 *   - Requires @tiptap/extension-text-style to be registered
 */

import { Extension } from '@tiptap/core';

// Type declaration for the fontSize commands
declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    fontSize: {
      /**
       * Set the font size
       * @param fontSize - The font size value (e.g., '12pt', '14px', '1rem')
       */
      setFontSize: (fontSize: string) => ReturnType;
      /**
       * Unset the font size (revert to default)
       */
      unsetFontSize: () => ReturnType;
    };
  }
}

/**
 * FontSize Extension
 * 
 * Adds fontSize support to the editor via the style attribute.
 * Works in conjunction with TextStyle extension.
 */
export const FontSize = Extension.create({
  name: 'fontSize',

  // Options for configuring the extension
  addOptions() {
    return {
      // Available font sizes for the dropdown
      types: ['textStyle'],
    };
  },

  // Register the fontSize attribute on the textStyle mark
  addGlobalAttributes() {
    return [
      {
        types: this.options.types,
        attributes: {
          fontSize: {
            default: null,
            // Parse fontSize from existing HTML elements
            parseHTML: (element) => element.style.fontSize || null,
            // Render fontSize as inline style
            renderHTML: (attributes) => {
              if (!attributes.fontSize) {
                return {};
              }
              return {
                style: `font-size: ${attributes.fontSize}`,
              };
            },
          },
        },
      },
    ];
  },

  // Add editor commands for setting/unsetting font size
  addCommands() {
    return {
      setFontSize:
        (fontSize: string) =>
        ({ chain }) => {
          return chain().setMark('textStyle', { fontSize }).run();
        },
      unsetFontSize:
        () =>
        ({ chain }) => {
          return chain()
            .setMark('textStyle', { fontSize: null })
            .removeEmptyTextStyle()
            .run();
        },
    };
  },
});

/**
 * Helper function to get current font size from editor state
 * @param editor - The TipTap editor instance
 * @returns Current font size or null if not set
 */
export function getCurrentFontSize(editor: any): string | null {
  const attrs = editor.getAttributes('textStyle');
  return attrs.fontSize || null;
}

/**
 * Predefined font sizes for the dropdown selector
 * Common sizes used in document editing
 */
export const FONT_SIZES = [
  '8pt',
  '9pt',
  '10pt',
  '10.5pt',
  '11pt',
  '12pt',
  '14pt',
  '16pt',
  '18pt',
  '20pt',
  '24pt',
  '28pt',
  '36pt',
  '48pt',
  '72pt',
];

/**
 * Parse a font size string to get the numeric value
 * @param fontSize - Font size string (e.g., '12pt', '14px')
 * @returns Numeric value or null
 */
export function parseFontSize(fontSize: string): number | null {
  const match = fontSize.match(/^(\d+(?:\.\d+)?)/);
  return match ? parseFloat(match[1]) : null;
}

/**
 * Increment font size to the next standard size
 * @param currentSize - Current font size (e.g., '12pt')
 * @returns Next larger font size or same if at max
 */
export function incrementFontSize(currentSize: string): string {
  const current = parseFontSize(currentSize);
  if (current === null) return '12pt';
  
  const currentIndex = FONT_SIZES.findIndex((size) => {
    const sizeNum = parseFontSize(size);
    return sizeNum !== null && sizeNum >= current;
  });
  
  if (currentIndex === -1 || currentIndex >= FONT_SIZES.length - 1) {
    return FONT_SIZES[FONT_SIZES.length - 1];
  }
  
  return FONT_SIZES[currentIndex + 1];
}

/**
 * Decrement font size to the previous standard size
 * @param currentSize - Current font size (e.g., '12pt')
 * @returns Next smaller font size or same if at min
 */
export function decrementFontSize(currentSize: string): string {
  const current = parseFontSize(currentSize);
  if (current === null) return '12pt';
  
  const currentIndex = FONT_SIZES.findIndex((size) => {
    const sizeNum = parseFontSize(size);
    return sizeNum !== null && sizeNum >= current;
  });
  
  if (currentIndex <= 0) {
    return FONT_SIZES[0];
  }
  
  return FONT_SIZES[currentIndex - 1];
}

export default FontSize;
