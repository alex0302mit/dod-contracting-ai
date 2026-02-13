/**
 * Callout Presets
 *
 * Pre-defined callout configurations for common use cases
 */

import { CalloutType } from '@/components/editor/CalloutExtension';

export interface CalloutPreset {
  type: CalloutType;
  title: string;
  icon: string;
  description: string;
  example: string;
}

export const calloutPresets: CalloutPreset[] = [
  {
    type: 'info',
    title: 'Information',
    icon: 'ℹ️',
    description: 'General information or context',
    example: 'This section requires special attention to FAR 52.204-7 compliance.',
  },
  {
    type: 'warning',
    title: 'Warning',
    icon: '⚠️',
    description: 'Important warnings or cautions',
    example: 'Price information must not appear in the technical volume per RFP Section L.',
  },
  {
    type: 'danger',
    title: 'Critical',
    icon: '🚨',
    description: 'Critical issues or blockers',
    example: 'Missing required security clearance documentation will result in proposal rejection.',
  },
  {
    type: 'success',
    title: 'Success',
    icon: '✅',
    description: 'Successful completion or best practices',
    example: 'All compliance requirements have been met for this section.',
  },
  {
    type: 'tip',
    title: 'Pro Tip',
    icon: '💡',
    description: 'Helpful tips and recommendations',
    example: 'Include quantitative metrics to strengthen your past performance narrative.',
  },
  {
    type: 'note',
    title: 'Note',
    icon: '📝',
    description: 'Additional notes or comments',
    example: 'This requirement may be updated in Amendment 003 - monitor SAM.gov.',
  },
  {
    type: 'important',
    title: 'Important',
    icon: '❗',
    description: 'Key points to emphasize',
    example: 'The evaluation will heavily weight technical approach (60% of total score).',
  },
  {
    type: 'caution',
    title: 'Caution',
    icon: '⚡',
    description: 'Proceed with caution',
    example: 'Ensure all team members have active security clearances before proposal submission.',
  },
];

/**
 * Get preset by type
 */
export function getPresetByType(type: CalloutType): CalloutPreset | undefined {
  return calloutPresets.find((preset) => preset.type === type);
}

/**
 * Get preset title
 */
export function getPresetTitle(type: CalloutType): string {
  const preset = getPresetByType(type);
  return preset?.title || type.charAt(0).toUpperCase() + type.slice(1);
}

/**
 * Get preset icon
 */
export function getPresetIcon(type: CalloutType): string {
  const preset = getPresetByType(type);
  return preset?.icon || '📌';
}
