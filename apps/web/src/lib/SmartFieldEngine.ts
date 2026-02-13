/**
 * Smart Field Engine
 *
 * Manages structured data entry fields with validation and auto-population
 */

export type FieldType =
  | 'text'
  | 'number'
  | 'date'
  | 'select'
  | 'multiselect'
  | 'textarea'
  | 'currency'
  | 'percentage'
  | 'duration'
  | 'phone'
  | 'email';

export interface FieldOption {
  value: string;
  label: string;
  description?: string;
}

export interface FieldValidation {
  required?: boolean;
  min?: number;
  max?: number;
  pattern?: RegExp;
  custom?: (value: string) => boolean | string;
}

export interface SmartField {
  id: string;
  fieldType: FieldType;
  label: string;
  description?: string;
  placeholder?: string;
  value?: string;
  options?: FieldOption[]; // For select/multiselect
  validation?: FieldValidation;
  autoFill?: 'company-name' | 'poc-name' | 'poc-email' | 'poc-phone' | 'date-today' | 'contract-number';
  category?: 'technical' | 'management' | 'pricing' | 'administrative' | 'compliance';
}

export interface FieldTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  appliesTo?: string[]; // Section names
  fields: SmartField[];
  outputFormat?: (values: Record<string, string>) => string; // Custom output formatter
}

export interface FieldInstance {
  fieldId: string;
  templateId: string;
  position: number;
  values: Record<string, string>;
  isComplete: boolean;
}

/**
 * Smart Field Engine - manages field templates and instances
 */
export class SmartFieldEngine {
  private templates: Map<string, FieldTemplate> = new Map();
  private instances: Map<string, FieldInstance> = new Map();

  /**
   * Register a field template
   */
  registerTemplate(template: FieldTemplate): void {
    this.templates.set(template.id, template);
  }

  /**
   * Register multiple templates
   */
  registerTemplates(templates: FieldTemplate[]): void {
    templates.forEach((template) => this.registerTemplate(template));
  }

  /**
   * Get all templates
   */
  getTemplates(): FieldTemplate[] {
    return Array.from(this.templates.values());
  }

  /**
   * Get template by ID
   */
  getTemplate(id: string): FieldTemplate | undefined {
    return this.templates.get(id);
  }

  /**
   * Get templates for a specific section
   */
  getTemplatesForSection(sectionName: string): FieldTemplate[] {
    return this.getTemplates().filter(
      (template) => !template.appliesTo || template.appliesTo.length === 0 || template.appliesTo.includes(sectionName)
    );
  }

  /**
   * Get templates by category
   */
  getTemplatesByCategory(category: string): FieldTemplate[] {
    return this.getTemplates().filter((template) => template.category === category);
  }

  /**
   * Create a field instance from a template
   */
  createFieldInstance(templateId: string, position: number): FieldInstance | null {
    const template = this.getTemplate(templateId);
    if (!template) return null;

    const instance: FieldInstance = {
      fieldId: `field-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      templateId,
      position,
      values: {},
      isComplete: false,
    };

    // Auto-fill values if specified
    template.fields.forEach((field) => {
      if (field.autoFill) {
        instance.values[field.id] = this.getAutoFillValue(field.autoFill);
      }
    });

    this.instances.set(instance.fieldId, instance);
    return instance;
  }

  /**
   * Update field instance values
   */
  updateFieldInstance(fieldId: string, values: Record<string, string>): void {
    const instance = this.instances.get(fieldId);
    if (!instance) return;

    instance.values = { ...instance.values, ...values };
    instance.isComplete = this.isInstanceComplete(instance);
  }

  /**
   * Check if field instance is complete
   */
  private isInstanceComplete(instance: FieldInstance): boolean {
    const template = this.getTemplate(instance.templateId);
    if (!template) return false;

    return template.fields.every((field) => {
      const value = instance.values[field.id];

      // Required field must have value
      if (field.validation?.required && !value) {
        return false;
      }

      // Validate value if present
      if (value && field.validation) {
        return this.validateField(field, value) === true;
      }

      return true;
    });
  }

  /**
   * Validate a field value
   */
  validateField(field: SmartField, value: string): boolean | string {
    if (!field.validation) return true;

    const { required, min, max, pattern, custom } = field.validation;

    // Required check
    if (required && !value) {
      return `${field.label} is required`;
    }

    if (!value) return true; // Empty optional field is valid

    // Min/max for numbers
    if (field.fieldType === 'number' || field.fieldType === 'currency' || field.fieldType === 'percentage') {
      const num = parseFloat(value);
      if (isNaN(num)) {
        return `${field.label} must be a valid number`;
      }
      if (min !== undefined && num < min) {
        return `${field.label} must be at least ${min}`;
      }
      if (max !== undefined && num > max) {
        return `${field.label} must be at most ${max}`;
      }
    }

    // Min/max for text (length)
    if (field.fieldType === 'text' || field.fieldType === 'textarea') {
      if (min !== undefined && value.length < min) {
        return `${field.label} must be at least ${min} characters`;
      }
      if (max !== undefined && value.length > max) {
        return `${field.label} must be at most ${max} characters`;
      }
    }

    // Pattern validation
    if (pattern && !pattern.test(value)) {
      return `${field.label} format is invalid`;
    }

    // Custom validation
    if (custom) {
      return custom(value);
    }

    return true;
  }

  /**
   * Get auto-fill value based on type
   */
  private getAutoFillValue(autoFillType: SmartField['autoFill']): string {
    switch (autoFillType) {
      case 'date-today':
        return new Date().toISOString().split('T')[0];
      case 'company-name':
        return ''; // Would be populated from user profile
      case 'poc-name':
        return ''; // Would be populated from user profile
      case 'poc-email':
        return ''; // Would be populated from user profile
      case 'poc-phone':
        return ''; // Would be populated from user profile
      case 'contract-number':
        return ''; // Would be populated from context
      default:
        return '';
    }
  }

  /**
   * Generate output text from field instance
   */
  generateOutput(fieldId: string): string {
    const instance = this.instances.get(fieldId);
    if (!instance) return '';

    const template = this.getTemplate(instance.templateId);
    if (!template) return '';

    // Use custom output format if provided
    if (template.outputFormat) {
      return template.outputFormat(instance.values);
    }

    // Default output format
    return template.fields
      .map((field) => {
        const value = instance.values[field.id];
        if (!value) return '';
        return `**${field.label}:** ${value}`;
      })
      .filter(Boolean)
      .join('\n\n');
  }

  /**
   * Get field instance by ID
   */
  getFieldInstance(fieldId: string): FieldInstance | undefined {
    return this.instances.get(fieldId);
  }

  /**
   * Delete field instance
   */
  deleteFieldInstance(fieldId: string): void {
    this.instances.delete(fieldId);
  }
}
