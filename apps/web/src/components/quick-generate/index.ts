/**
 * Quick Generate Module
 * 
 * Exports all components and types for the Quick Generate wizard feature.
 * This wizard allows users to generate contracting packages without creating a project.
 */

// Main container component
export { QuickGenerateTab } from './QuickGenerateTab';

// Sub-components
export { QuickUploadStep } from './QuickUploadStep';
export { ExtractionProgress, GenerationProgress } from './ExtractionProgress';
export { QuickReviewStep } from './QuickReviewStep';

// Types
export * from './types';
