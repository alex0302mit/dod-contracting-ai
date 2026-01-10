/**
 * Guided Flow Navigation Utilities
 *
 * Handles DOM scrolling, highlighting, and field navigation
 * for DocuSign-style guided completion.
 */

import type { GuidedField, AnimationConfig } from '@/types/guidedFlow';

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_SCROLL_DURATION = 300; // ms
const DEFAULT_HIGHLIGHT_DURATION = 200; // ms
const SCROLL_OFFSET = 100; // Pixels from top when scrolling to field
const HIGHLIGHT_CLASS = 'guided-flow-highlight';
const HIGHLIGHT_PULSE_CLASS = 'guided-flow-pulse';

// ============================================================================
// Scroll Utilities
// ============================================================================

/**
 * Smooth scroll to a field element
 *
 * @param selector - CSS selector for the field (e.g., "[data-field-id='k2-uei']")
 * @param duration - Animation duration in ms (default from animation config)
 * @param offset - Offset from top in pixels
 */
export function scrollToField(
  selector: string,
  duration: number = DEFAULT_SCROLL_DURATION,
  offset: number = SCROLL_OFFSET
): Promise<void> {
  return new Promise((resolve) => {
    const element = document.querySelector(selector);

    if (!element) {
      console.warn(`Field element not found: ${selector}`);
      resolve();
      return;
    }

    const rect = element.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const targetPosition = rect.top + scrollTop - offset;

    // Use smooth scroll if supported
    if ('scrollBehavior' in document.documentElement.style) {
      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });

      // Estimate when scroll completes
      setTimeout(() => resolve(), duration);
    } else {
      // Fallback: animated scroll
      animatedScroll(targetPosition, duration).then(resolve);
    }
  });
}

/**
 * Animated scroll polyfill for browsers without smooth scroll
 */
function animatedScroll(targetY: number, duration: number): Promise<void> {
  return new Promise((resolve) => {
    const startY = window.pageYOffset || document.documentElement.scrollTop;
    const distance = targetY - startY;
    const startTime = performance.now();

    function scroll() {
      const currentTime = performance.now();
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function (ease-in-out)
      const easeProgress = progress < 0.5
        ? 2 * progress * progress
        : -1 + (4 - 2 * progress) * progress;

      window.scrollTo(0, startY + distance * easeProgress);

      if (progress < 1) {
        requestAnimationFrame(scroll);
      } else {
        resolve();
      }
    }

    requestAnimationFrame(scroll);
  });
}

/**
 * Scroll element into view within a scrollable container
 *
 * Useful for fields inside modals or scrollable panels
 */
export function scrollIntoViewWithinContainer(
  element: HTMLElement,
  container: HTMLElement,
  offset: number = 20
): void {
  const elementRect = element.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();

  // Check if element is above viewport
  if (elementRect.top < containerRect.top) {
    container.scrollTop -= (containerRect.top - elementRect.top) + offset;
  }
  // Check if element is below viewport
  else if (elementRect.bottom > containerRect.bottom) {
    container.scrollTop += (elementRect.bottom - containerRect.bottom) + offset;
  }
}

// ============================================================================
// Highlight Utilities
// ============================================================================

/**
 * Highlight a field with outline/glow effect
 *
 * @param selector - CSS selector for the field
 * @param duration - How long to keep the highlight (ms)
 * @param pulse - Whether to add pulse animation
 * @returns Cleanup function to remove highlight
 */
export function highlightField(
  selector: string,
  duration: number = DEFAULT_HIGHLIGHT_DURATION,
  pulse: boolean = true
): () => void {
  const element = document.querySelector(selector);

  if (!element) {
    console.warn(`Field element not found for highlight: ${selector}`);
    return () => {};
  }

  // Add highlight classes
  element.classList.add(HIGHLIGHT_CLASS);
  if (pulse) {
    element.classList.add(HIGHLIGHT_PULSE_CLASS);
  }

  // Auto-remove after duration
  const timeoutId = setTimeout(() => {
    element.classList.remove(HIGHLIGHT_CLASS);
    element.classList.remove(HIGHLIGHT_PULSE_CLASS);
  }, duration);

  // Return cleanup function
  return () => {
    clearTimeout(timeoutId);
    element.classList.remove(HIGHLIGHT_CLASS);
    element.classList.remove(HIGHLIGHT_PULSE_CLASS);
  };
}

/**
 * Remove highlight from a field
 */
export function unhighlightField(selector: string): void {
  const element = document.querySelector(selector);
  if (element) {
    element.classList.remove(HIGHLIGHT_CLASS);
    element.classList.remove(HIGHLIGHT_PULSE_CLASS);
  }
}

/**
 * Remove all highlights from the page
 */
export function clearAllHighlights(): void {
  const highlightedElements = document.querySelectorAll(`.${HIGHLIGHT_CLASS}`);
  highlightedElements.forEach(el => {
    el.classList.remove(HIGHLIGHT_CLASS);
    el.classList.remove(HIGHLIGHT_PULSE_CLASS);
  });
}

// ============================================================================
// Combined Navigation
// ============================================================================

/**
 * Navigate to a field with scroll + highlight
 *
 * This is the main navigation function used by the guided flow
 *
 * @param field - Field to navigate to
 * @param animationConfig - Animation configuration from document
 * @returns Promise that resolves when navigation completes
 */
export async function navigateToField(
  field: GuidedField,
  animationConfig?: AnimationConfig
): Promise<void> {
  if (!field.selector) {
    console.warn(`Field ${field.id} has no selector defined`);
    return;
  }

  // Get animation durations
  const scrollDuration = animationConfig?.scrollDuration || DEFAULT_SCROLL_DURATION;
  const highlightDuration = animationConfig?.highlightDuration || DEFAULT_HIGHLIGHT_DURATION;

  // Clear any existing highlights
  clearAllHighlights();

  // Scroll to field (async)
  await scrollToField(field.selector, scrollDuration);

  // Highlight field (after scroll completes)
  highlightField(field.selector, highlightDuration * 5); // Keep highlight longer
}

/**
 * Focus on a field input element
 *
 * Useful for immediately placing cursor in text fields
 */
export function focusField(selector: string): void {
  const element = document.querySelector(selector);

  if (element instanceof HTMLInputElement ||
      element instanceof HTMLTextAreaElement ||
      element instanceof HTMLSelectElement) {
    element.focus();
  } else if (element) {
    // Try to find focusable child
    const focusable = element.querySelector<HTMLElement>(
      'input, textarea, select, button, [contenteditable="true"]'
    );
    if (focusable) {
      focusable.focus();
    }
  }
}

/**
 * Navigate to field with scroll, highlight, and focus
 */
export async function navigateAndFocusField(
  field: GuidedField,
  animationConfig?: AnimationConfig
): Promise<void> {
  await navigateToField(field, animationConfig);

  // Focus after navigation completes
  if (field.selector) {
    setTimeout(() => {
      focusField(field.selector!);
    }, 100); // Small delay to ensure scroll completes
  }
}

// ============================================================================
// Progress Indicator Utilities
// ============================================================================

/**
 * Get visual progress bar data
 *
 * @param current - Current field index (0-based)
 * @param total - Total number of fields
 * @returns Progress data for rendering
 */
export function getProgressData(current: number, total: number) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  const remaining = Math.max(0, total - current);

  return {
    current,
    total,
    percentage,
    remaining,
    isComplete: current >= total
  };
}

/**
 * Format progress text
 *
 * @example "3 of 9 fields completed (33%)"
 */
export function formatProgressText(current: number, total: number): string {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  return `${current} of ${total} fields completed (${percentage}%)`;
}

// ============================================================================
// Field Ordering Utilities
// ============================================================================

/**
 * Sort fields by their order property
 */
export function sortFieldsByOrder(fields: GuidedField[]): GuidedField[] {
  return [...fields].sort((a, b) => a.order - b.order);
}

/**
 * Get field index in ordered list
 */
export function getFieldIndex(field: GuidedField, allFields: GuidedField[]): number {
  const sorted = sortFieldsByOrder(allFields);
  return sorted.findIndex(f => f.id === field.id);
}

/**
 * Get next field in order
 */
export function getNextFieldInOrder(
  currentField: GuidedField,
  allFields: GuidedField[]
): GuidedField | null {
  const sorted = sortFieldsByOrder(allFields);
  const currentIndex = sorted.findIndex(f => f.id === currentField.id);

  if (currentIndex === -1 || currentIndex >= sorted.length - 1) {
    return null;
  }

  return sorted[currentIndex + 1];
}

/**
 * Get previous field in order
 */
export function getPreviousFieldInOrder(
  currentField: GuidedField,
  allFields: GuidedField[]
): GuidedField | null {
  const sorted = sortFieldsByOrder(allFields);
  const currentIndex = sorted.findIndex(f => f.id === currentField.id);

  if (currentIndex <= 0) {
    return null;
  }

  return sorted[currentIndex - 1];
}

// ============================================================================
// Keyboard Navigation
// ============================================================================

/**
 * Handle keyboard shortcuts for guided flow navigation
 *
 * @param event - Keyboard event
 * @param handlers - Navigation handlers
 */
export function handleKeyboardNavigation(
  event: KeyboardEvent,
  handlers: {
    onNext?: () => void;
    onPrevious?: () => void;
    onEscape?: () => void;
  }
): void {
  // Don't interfere with typing in inputs
  const target = event.target as HTMLElement;
  if (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.isContentEditable
  ) {
    // Allow Enter in single-line inputs to advance
    if (event.key === 'Enter' && target.tagName === 'INPUT') {
      event.preventDefault();
      handlers.onNext?.();
    }
    return;
  }

  switch (event.key) {
    case 'ArrowRight':
    case 'Enter':
      event.preventDefault();
      handlers.onNext?.();
      break;

    case 'ArrowLeft':
      event.preventDefault();
      handlers.onPrevious?.();
      break;

    case 'Escape':
      event.preventDefault();
      handlers.onEscape?.();
      break;
  }
}

// ============================================================================
// Animation Class Helpers
// ============================================================================

/**
 * Get Tailwind transition classes based on animation speed
 */
export function getTransitionClasses(speed: 'instant' | 'fast' | 'medium' | 'slow'): string {
  switch (speed) {
    case 'instant':
      return 'transition-none';
    case 'fast':
      return 'transition-all duration-200 ease-out';
    case 'medium':
      return 'transition-all duration-300 ease-out';
    case 'slow':
      return 'transition-all duration-500 ease-out';
    default:
      return 'transition-all duration-200 ease-out';
  }
}

/**
 * Get scroll behavior CSS property value
 */
export function getScrollBehavior(speed: 'instant' | 'fast' | 'medium' | 'slow'): 'auto' | 'smooth' {
  return speed === 'instant' ? 'auto' : 'smooth';
}

// ============================================================================
// Field Validation Visual Feedback
// ============================================================================

/**
 * Add shake animation to field on validation error
 */
export function shakeField(selector: string): void {
  const element = document.querySelector(selector);
  if (!element) return;

  element.classList.add('animate-shake');

  setTimeout(() => {
    element.classList.remove('animate-shake');
  }, 500);
}

/**
 * Add success animation to field on completion
 */
export function celebrateField(selector: string): void {
  const element = document.querySelector(selector);
  if (!element) return;

  element.classList.add('animate-success-pulse');

  setTimeout(() => {
    element.classList.remove('animate-success-pulse');
  }, 1000);
}

// ============================================================================
// Intersection Observer for Auto-Highlight
// ============================================================================

/**
 * Create intersection observer to auto-highlight fields in viewport
 *
 * Useful for showing which field is currently "active" as user scrolls
 */
export function createFieldIntersectionObserver(
  fields: GuidedField[],
  onFieldInView: (field: GuidedField) => void
): IntersectionObserver {
  const options = {
    root: null, // viewport
    rootMargin: '-40% 0px -40% 0px', // Middle 20% of viewport
    threshold: 0
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        // Find which field this element belongs to
        const fieldId = entry.target.getAttribute('data-field-id');
        const field = fields.find(f => f.id === fieldId);

        if (field) {
          onFieldInView(field);
        }
      }
    });
  }, options);

  // Observe all field elements
  fields.forEach((field) => {
    if (field.selector) {
      const element = document.querySelector(field.selector);
      if (element) {
        observer.observe(element);
      }
    }
  });

  return observer;
}

// ============================================================================
// Export All
// ============================================================================

export default {
  // Scroll
  scrollToField,
  scrollIntoViewWithinContainer,

  // Highlight
  highlightField,
  unhighlightField,
  clearAllHighlights,

  // Combined
  navigateToField,
  navigateAndFocusField,
  focusField,

  // Progress
  getProgressData,
  formatProgressText,

  // Ordering
  sortFieldsByOrder,
  getFieldIndex,
  getNextFieldInOrder,
  getPreviousFieldInOrder,

  // Keyboard
  handleKeyboardNavigation,

  // Animation
  getTransitionClasses,
  getScrollBehavior,
  shakeField,
  celebrateField,

  // Intersection
  createFieldIntersectionObserver
};
