/**
 * PasswordRequirements Component
 *
 * Real-time password validation checklist showing which requirements are met.
 * Displays checkmarks for met requirements and X marks for unmet ones.
 *
 * Requirements match backend validation:
 * - Minimum 12 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one digit
 * - At least one special character
 */

import { Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PasswordRequirementsProps {
  password: string;
  className?: string;
}

interface Requirement {
  label: string;
  test: (password: string) => boolean;
}

const requirements: Requirement[] = [
  {
    label: 'At least 12 characters',
    test: (password) => password.length >= 12,
  },
  {
    label: 'At least one uppercase letter',
    test: (password) => /[A-Z]/.test(password),
  },
  {
    label: 'At least one lowercase letter',
    test: (password) => /[a-z]/.test(password),
  },
  {
    label: 'At least one digit',
    test: (password) => /[0-9]/.test(password),
  },
  {
    label: 'At least one special character (!@#$%^&*(),.?":{}|<>)',
    test: (password) => /[!@#$%^&*(),.?":{}|<>]/.test(password),
  },
];

/**
 * Validate password against all requirements.
 * Returns true if all requirements are met.
 *
 * @param password - The password string to validate
 * @returns true if password meets all requirements, false otherwise
 */
export function validatePassword(password: string): boolean {
  return requirements.every((req) => req.test(password));
}

/**
 * Get detailed validation results for each requirement.
 * Useful for showing which specific requirements are not met.
 *
 * @param password - The password string to validate
 * @returns Array of objects with requirement label and whether it passed
 */
export function getPasswordValidationDetails(password: string): Array<{ label: string; passed: boolean }> {
  return requirements.map((req) => ({
    label: req.label,
    passed: req.test(password),
  }));
}

/**
 * PasswordRequirements - Visual checklist for password validation
 */
export function PasswordRequirements({ password, className }: PasswordRequirementsProps) {
  return (
    <div className={cn('space-y-1', className)}>
      <p className="text-xs font-medium text-slate-600 mb-2">Password Requirements:</p>
      <ul className="space-y-1">
        {requirements.map((req, index) => {
          const passed = req.test(password);
          return (
            <li
              key={index}
              className={cn(
                'flex items-center gap-2 text-xs',
                passed ? 'text-green-600' : 'text-slate-500'
              )}
            >
              {passed ? (
                <Check className="h-3.5 w-3.5 text-green-500" />
              ) : (
                <X className="h-3.5 w-3.5 text-slate-400" />
              )}
              <span className={passed ? 'line-through opacity-70' : ''}>
                {req.label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default PasswordRequirements;
