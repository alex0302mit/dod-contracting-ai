/**
 * Guided Field Highlighter
 *
 * Automatically highlights and scrolls to the current field in the document.
 * Uses Intersection Observer for performance.
 */

import { useEffect, useRef } from 'react';
import { useGuidedFlow } from '@/contexts/GuidedFlowContext';
import { navigateAndFocusField, clearAllHighlights } from '@/utils/guidedFlowNavigation';

export function GuidedFieldHighlighter() {
  const { currentField, state } = useGuidedFlow();
  const previousFieldRef = useRef<string | null>(null);
  const animationConfigRef = useRef(state.document.animations);

  // ========================================================================
  // Highlight Current Field
  // ========================================================================

  useEffect(() => {
    if (!currentField || !currentField.selector) {
      clearAllHighlights();
      return;
    }

    // Only navigate if field actually changed
    if (previousFieldRef.current !== currentField.id) {
      navigateAndFocusField(currentField, animationConfigRef.current);
      previousFieldRef.current = currentField.id;
    }

    // Cleanup on unmount
    return () => {
      clearAllHighlights();
    };
  }, [currentField]);

  // This component doesn't render anything - it's a side-effect component
  return null;
}
