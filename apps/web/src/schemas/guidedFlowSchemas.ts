/**
 * Zod Validation Schemas for Guided Flow
 *
 * Runtime validation schemas for Section K fields.
 * Integrated with React Hook Form via zodResolver.
 */

import { z } from 'zod';
import type { GuidedField, ConditionalOperator } from '@/types/guidedFlow';

// ============================================================================
// K.2 SAM.GOV REGISTRATION SCHEMA
// ============================================================================

export const k2SamGovSchema = z.object({
  k2: z.object({
    // Field 1: UEI Number
    uei: z
      .string()
      .min(1, "UEI is required")
      .regex(/^[A-Z0-9]{12}$/, "UEI must be exactly 12 alphanumeric characters")
      .transform(val => val.toUpperCase()),

    // Field 2: CAGE Code
    cage: z
      .string()
      .min(1, "CAGE Code is required")
      .regex(/^[A-Z0-9]{5}$/, "CAGE Code must be exactly 5 alphanumeric characters")
      .transform(val => val.toUpperCase()),

    // Field 3: SAM Expiration Date
    samExpirationDate: z
      .string()
      .min(1, "SAM expiration date is required")
      .refine(
        (dateStr) => {
          const date = new Date(dateStr);
          const now = new Date();
          return date > now;
        },
        { message: "SAM expiration must be in the future" }
      ),

    // Field 4: Certification Checkbox
    certifyAccurate: z
      .boolean()
      .refine(val => val === true, {
        message: "You must certify accuracy to proceed"
      }),

    // Field 5: Renewal Commitment (optional, conditional)
    certifyRenewal: z.boolean().optional()
  })
});

// ============================================================================
// K.9 CERTIFICATION SCHEMA
// ============================================================================

export const k9CertificationSchema = z.object({
  k9: z.object({
    // Field 1: Master Certification Checkbox
    certifyAll: z
      .boolean()
      .refine(val => val === true, {
        message: "Final certification is required to submit proposal"
      }),

    // Field 2: Authorized Representative Name (conditional)
    signature: z.object({
      name: z
        .string()
        .min(2, "Full legal name is required")
        .optional()
        .or(z.literal('')),

      // Field 3: Title (conditional)
      title: z
        .string()
        .min(2, "Official title is required")
        .optional()
        .or(z.literal('')),

      // Field 4: Signature Date (conditional)
      date: z
        .string()
        .optional()
        .or(z.literal(''))
        .refine(
          (dateStr) => {
            if (!dateStr) return true; // Allow empty for conditional
            const date = new Date(dateStr);
            const now = new Date();
            return date <= now;
          },
          { message: "Signature date cannot be in the future" }
        )
    }).optional()
  })
});

// ============================================================================
// COMBINED SECTION K SCHEMA
// ============================================================================

export const sectionKSchema = z.intersection(
  k2SamGovSchema,
  k9CertificationSchema
);

// Type inference for React Hook Form
export type SectionKFormData = z.infer<typeof sectionKSchema>;

// ============================================================================
// DYNAMIC SCHEMA GENERATION
// ============================================================================

/**
 * Generate Zod schema dynamically from GuidedField definitions
 *
 * This allows backend to define validation rules in the JSON structure
 * and frontend to generate matching Zod schemas at runtime.
 *
 * @param fields - Array of guided fields
 * @returns Zod schema object
 */
export function generateDynamicSchema(fields: GuidedField[]): z.ZodObject<z.ZodRawShape> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const schemaShape: Record<string, any> = {};

  fields.forEach((field) => {
    // Split nested path (e.g., "k2.uei" → ["k2", "uei"])
    const pathParts = field.rfhName.split('.');

    // Build nested schema structure
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let currentLevel: Record<string, any> = schemaShape;
    pathParts.forEach((part, index) => {
      const isLast = index === pathParts.length - 1;

      if (isLast) {
        // Create leaf schema based on field type and validation
        currentLevel[part] = createFieldSchema(field);
      } else {
        // Create intermediate object if needed
        if (!currentLevel[part]) {
          currentLevel[part] = {};
        }
        currentLevel = currentLevel[part];
      }
    });
  });

  // Convert nested object to Zod schema
  return objectToZodSchema(schemaShape);
}

/**
 * Create Zod schema for a single field based on its type and validation
 */
function createFieldSchema(field: GuidedField): z.ZodTypeAny {
  let schema: z.ZodTypeAny;

  // Base schema by field type
  switch (field.type) {
    case 'checkbox':
      schema = z.boolean();
      if (field.required) {
        schema = schema.refine(val => val === true, {
          message: field.validation?.message || `${field.label} is required`
        });
      }
      break;

    case 'text':
    case 'textarea':
      schema = z.string();

      // Apply validation rules
      if (field.validation) {
        if (field.validation.pattern) {
          schema = (schema as z.ZodString).regex(
            field.validation.pattern,
            field.validation.message || 'Invalid format'
          );
        }
        if (field.validation.min !== undefined) {
          schema = (schema as z.ZodString).min(
            field.validation.min,
            field.validation.message || `Minimum ${field.validation.min} characters`
          );
        }
        if (field.validation.max !== undefined) {
          schema = (schema as z.ZodString).max(
            field.validation.max,
            field.validation.message || `Maximum ${field.validation.max} characters`
          );
        }
      }

      // Required validation
      if (field.required) {
        schema = (schema as z.ZodString).min(1, `${field.label} is required`);
      }
      break;

    case 'date':
      schema = z.string();

      // Required validation MUST come before refine
      if (field.required) {
        schema = (schema as z.ZodString).min(1, `${field.label} is required`);
      }

      if (field.validation?.message) {
        // Custom date validation (after required check)
        schema = schema.refine(
          (dateStr) => {
            if (!dateStr) return true; // Allow empty for optional fields
            const date = new Date(dateStr);
            return !isNaN(date.getTime());
          },
          { message: field.validation.message }
        );
      }
      break;

    case 'select':
      // Validate against options if provided
      if (field.options && field.options.length > 0) {
        const validValues = field.options.map(opt => opt.value);
        schema = z.enum(validValues as [string, ...string[]]);
      } else {
        schema = z.string();
        if (field.required) {
          schema = (schema as z.ZodString).min(1, `${field.label} is required`);
        }
      }
      break;

    case 'signature':
      // Signature is a nested object with name, title, date
      schema = z.object({
        name: z.string().min(2, 'Full name required'),
        title: z.string().min(2, 'Title required'),
        date: z.string().min(1, 'Signature date required')
      });
      break;

    default:
      schema = z.any();
  }

  // Handle optional fields (not required or has conditionalOn)
  if (!field.required || field.conditionalOn) {
    schema = schema.optional();
  }

  return schema;
}

/**
 * Convert nested object structure to Zod schema recursively
 */
function objectToZodSchema(obj: Record<string, any>): z.ZodObject<z.ZodRawShape> {
  const shape: Record<string, z.ZodTypeAny> = {};

  Object.keys(obj).forEach((key) => {
    const value = obj[key];

    if (value instanceof z.ZodType) {
      // Already a Zod schema
      shape[key] = value;
    } else if (typeof value === 'object' && value !== null) {
      // Nested object - recurse
      shape[key] = objectToZodSchema(value);
    } else {
      // Fallback to any
      shape[key] = z.any();
    }
  });

  return z.object(shape);
}

// ============================================================================
// CONDITIONAL VALIDATION HELPERS
// ============================================================================

/**
 * Evaluate conditional rule against form values
 *
 * Used to determine if conditional fields should be validated
 *
 * @param rule - Conditional rule from field definition
 * @param formValues - Current form values
 * @returns Whether condition is met
 */
export function evaluateConditional(
  rule: { fieldId: string; operator: ConditionalOperator; value?: any },
  formValues: Record<string, any>
): boolean {
  // Find field value by traversing nested path
  const fieldValue = getNestedValue(formValues, rule.fieldId);

  switch (rule.operator) {
    case 'equals':
      return fieldValue === rule.value;

    case 'notEquals':
      return fieldValue !== rule.value;

    case 'contains':
      if (typeof fieldValue === 'string') {
        return fieldValue.includes(rule.value);
      }
      if (Array.isArray(fieldValue)) {
        return fieldValue.includes(rule.value);
      }
      return false;

    case 'isEmpty':
      return !fieldValue || fieldValue === '' || (Array.isArray(fieldValue) && fieldValue.length === 0);

    case 'isNotEmpty':
      return !!fieldValue && fieldValue !== '' && (!Array.isArray(fieldValue) || fieldValue.length > 0);

    default:
      return false;
  }
}

/**
 * Get nested value from object using dot notation or field ID
 */
function getNestedValue(obj: Record<string, any>, path: string): any {
  // Try direct field ID lookup first
  if (obj[path] !== undefined) {
    return obj[path];
  }

  // Try dot notation path
  const parts = path.split('.');
  let current = obj;

  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = current[part];
    } else {
      return undefined;
    }
  }

  return current;
}

// ============================================================================
// SCHEMA REFINEMENTS FOR CONDITIONAL FIELDS
// ============================================================================

/**
 * Add conditional validation to schema
 *
 * Example: If K9 certification is checked, signature fields become required
 *
 * @param baseSchema - Base Zod schema
 * @param fields - Field definitions with conditional rules
 * @returns Refined schema with conditional validation
 */
export function addConditionalValidation(
  baseSchema: z.ZodObject<z.ZodRawShape>,
  fields: GuidedField[]
): z.ZodTypeAny {
  let refinedSchema: z.ZodTypeAny = baseSchema;

  // Group fields by their conditional dependencies
  const conditionalFields = fields.filter(f => f.conditionalOn);

  conditionalFields.forEach((field) => {
    if (!field.conditionalOn) return;

    const { fieldId, operator, value } = field.conditionalOn;

    // Add refinement that validates conditionally required fields
    refinedSchema = refinedSchema.refine(
      (data) => {
        // Check if condition is met
        const conditionMet = evaluateConditional(
          { fieldId, operator, value },
          data
        );

        // If condition is met and field is required, validate it
        if (conditionMet && field.required) {
          const fieldValue = getNestedValue(data, field.rfhName);

          // Basic validation based on field type
          switch (field.type) {
            case 'checkbox':
              return fieldValue === true;
            case 'text':
            case 'textarea':
            case 'date':
            case 'select':
              return !!fieldValue && fieldValue !== '';
            default:
              return !!fieldValue;
          }
        }

        return true; // Condition not met or field not required
      },
      {
        message: field.validation?.message || `${field.label} is required when conditions are met`,
        path: field.rfhName.split('.')
      }
    );
  });

  return refinedSchema;
}

// ============================================================================
// PRE-CONFIGURED SCHEMAS FOR COMMON PATTERNS
// ============================================================================

/**
 * Schema for UEI (Unique Entity Identifier)
 * Used in SAM.gov registration
 */
export const ueiSchema = z
  .string()
  .regex(/^[A-Z0-9]{12}$/, "UEI must be 12 alphanumeric characters")
  .transform(val => val.toUpperCase());

/**
 * Schema for CAGE Code
 * Commercial and Government Entity Code
 */
export const cageCodeSchema = z
  .string()
  .regex(/^[A-Z0-9]{5}$/, "CAGE Code must be 5 alphanumeric characters")
  .transform(val => val.toUpperCase());

/**
 * Schema for DUNS Number (legacy, still used in some contexts)
 */
export const dunsSchema = z
  .string()
  .regex(/^\d{9}$/, "DUNS must be exactly 9 digits");

/**
 * Schema for future dates (expirations, deadlines)
 */
export const futureDateSchema = z
  .string()
  .refine(
    (dateStr) => {
      const date = new Date(dateStr);
      const now = new Date();
      return date > now;
    },
    { message: "Date must be in the future" }
  );

/**
 * Schema for past/present dates (signatures, historical dates)
 */
export const pastDateSchema = z
  .string()
  .refine(
    (dateStr) => {
      const date = new Date(dateStr);
      const now = new Date();
      return date <= now;
    },
    { message: "Date cannot be in the future" }
  );

/**
 * Schema for email addresses
 */
export const emailSchema = z
  .string()
  .email("Invalid email address")
  .toLowerCase();

/**
 * Schema for phone numbers (US format)
 */
export const phoneSchema = z
  .string()
  .regex(/^[\d\s\-()]+$/, "Invalid phone number format")
  .transform(val => val.replace(/\D/g, '')) // Strip non-digits
  .refine(
    (digits) => digits.length === 10,
    { message: "Phone number must be 10 digits" }
  );

// ============================================================================
// EXPORT EVERYTHING
// ============================================================================

export default {
  // Section schemas
  k2SamGovSchema,
  k9CertificationSchema,
  sectionKSchema,

  // Dynamic generation
  generateDynamicSchema,
  addConditionalValidation,

  // Helpers
  evaluateConditional,

  // Common patterns
  ueiSchema,
  cageCodeSchema,
  dunsSchema,
  futureDateSchema,
  pastDateSchema,
  emailSchema,
  phoneSchema
};
