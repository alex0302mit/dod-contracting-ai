/**
 * Guided Form Panel Component
 *
 * Interactive form UI for filling smart fields with validation
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  CheckCircle2,
  AlertCircle,
  FileText,
  Calendar,
  DollarSign,
  Percent,
  Clock,
  Mail,
  Phone,
} from 'lucide-react';
import { SmartField, FieldTemplate, SmartFieldEngine } from '@/lib/SmartFieldEngine';
import { fieldTemplates } from '@/lib/fieldTemplates';

interface GuidedFormPanelProps {
  templates: FieldTemplate[];
  onInsertField?: (templateId: string, values: Record<string, string>) => void;
}

const FIELD_TYPE_ICONS: Record<string, any> = {
  text: FileText,
  number: FileText,
  date: Calendar,
  currency: DollarSign,
  percentage: Percent,
  duration: Clock,
  email: Mail,
  phone: Phone,
  textarea: FileText,
  select: FileText,
  multiselect: FileText,
};

export function GuidedFormPanel({ templates, onInsertField }: GuidedFormPanelProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<FieldTemplate | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [engine] = useState(() => {
    const eng = new SmartFieldEngine();
    eng.registerTemplates(fieldTemplates);
    return eng;
  });

  const handleFieldChange = (fieldId: string, value: string) => {
    setFormValues((prev) => ({ ...prev, [fieldId]: value }));

    // Clear validation error for this field
    if (validationErrors[fieldId]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[fieldId];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    if (!selectedTemplate) return false;

    const errors: Record<string, string> = {};
    let isValid = true;

    selectedTemplate.fields.forEach((field) => {
      const value = formValues[field.id] || '';
      const validationResult = engine.validateField(field, value);

      if (typeof validationResult === 'string') {
        errors[field.id] = validationResult;
        isValid = false;
      }
    });

    setValidationErrors(errors);
    return isValid;
  };

  const handleInsert = () => {
    if (!selectedTemplate || !validateForm()) {
      return;
    }

    onInsertField?.(selectedTemplate.id, formValues);

    // Reset form
    setFormValues({});
    setSelectedTemplate(null);
    setValidationErrors({});
  };

  const handleCancel = () => {
    setSelectedTemplate(null);
    setFormValues({});
    setValidationErrors({});
  };

  // Group templates by category
  const templatesByCategory = templates.reduce((acc, template) => {
    const category = template.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(template);
    return acc;
  }, {} as Record<string, FieldTemplate[]>);

  const categories = Object.keys(templatesByCategory).sort();

  return (
    <div className="space-y-4">
      {!selectedTemplate ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Smart Field Templates</CardTitle>
            <CardDescription className="text-xs">
              Select a template to insert structured content
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              <div className="space-y-4">
                {categories.map((category) => (
                  <div key={category} className="space-y-2">
                    <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                      {category}
                    </h4>
                    <div className="space-y-1">
                      {templatesByCategory[category].map((template) => (
                        <Button
                          key={template.id}
                          variant="outline"
                          className="w-full h-auto py-3 px-3 text-left justify-start"
                          onClick={() => setSelectedTemplate(template)}
                        >
                          <div className="w-full">
                            <div className="font-medium text-sm mb-1">{template.name}</div>
                            <div className="text-xs text-muted-foreground">
                              {template.description}
                            </div>
                            <div className="mt-2 flex items-center gap-1">
                              <Badge variant="secondary" className="text-[9px] h-4">
                                {template.fields.length} fields
                              </Badge>
                            </div>
                          </div>
                        </Button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-sm">{selectedTemplate.name}</CardTitle>
                <CardDescription className="text-xs mt-1">
                  {selectedTemplate.description}
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={handleCancel} className="h-7 text-xs">
                Cancel
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              <div className="space-y-4 pr-4">
                {selectedTemplate.fields.map((field) => (
                  <FieldInput
                    key={field.id}
                    field={field}
                    value={formValues[field.id] || ''}
                    error={validationErrors[field.id]}
                    onChange={(value) => handleFieldChange(field.id, value)}
                  />
                ))}

                <div className="flex gap-2 pt-4">
                  <Button className="flex-1 gap-2" onClick={handleInsert}>
                    <CheckCircle2 className="h-4 w-4" />
                    Insert Field
                  </Button>
                </div>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function FieldInput({
  field,
  value,
  error,
  onChange,
}: {
  field: SmartField;
  value: string;
  error?: string;
  onChange: (value: string) => void;
}) {
  const Icon = FIELD_TYPE_ICONS[field.fieldType] || FileText;
  const isRequired = field.validation?.required || false;

  return (
    <div className="space-y-2">
      <Label htmlFor={field.id} className="text-xs font-medium flex items-center gap-2">
        <Icon className="h-3 w-3 text-muted-foreground" />
        {field.label}
        {isRequired && <span className="text-red-500">*</span>}
      </Label>

      {field.description && (
        <p className="text-[10px] text-muted-foreground">{field.description}</p>
      )}

      {/* Text input */}
      {(field.fieldType === 'text' || field.fieldType === 'email' || field.fieldType === 'phone') && (
        <Input
          id={field.id}
          type={field.fieldType === 'email' ? 'email' : field.fieldType === 'phone' ? 'tel' : 'text'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          className={`h-8 text-xs ${error ? 'border-red-500' : ''}`}
        />
      )}

      {/* Number/Currency/Percentage */}
      {(field.fieldType === 'number' || field.fieldType === 'currency' || field.fieldType === 'percentage') && (
        <div className="relative">
          {field.fieldType === 'currency' && (
            <DollarSign className="absolute left-2 top-2 h-4 w-4 text-muted-foreground" />
          )}
          <Input
            id={field.id}
            type="number"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            className={`h-8 text-xs ${field.fieldType === 'currency' ? 'pl-7' : ''} ${error ? 'border-red-500' : ''}`}
            min={field.validation?.min}
            max={field.validation?.max}
          />
          {field.fieldType === 'percentage' && (
            <Percent className="absolute right-2 top-2 h-4 w-4 text-muted-foreground" />
          )}
        </div>
      )}

      {/* Date */}
      {field.fieldType === 'date' && (
        <Input
          id={field.id}
          type="date"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={`h-8 text-xs ${error ? 'border-red-500' : ''}`}
        />
      )}

      {/* Duration */}
      {field.fieldType === 'duration' && (
        <Input
          id={field.id}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder || 'e.g., 30 days, 6 months'}
          className={`h-8 text-xs ${error ? 'border-red-500' : ''}`}
        />
      )}

      {/* Textarea */}
      {field.fieldType === 'textarea' && (
        <Textarea
          id={field.id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          className={`text-xs resize-none ${error ? 'border-red-500' : ''}`}
          rows={4}
        />
      )}

      {/* Select */}
      {field.fieldType === 'select' && field.options && (
        <Select value={value} onValueChange={onChange}>
          <SelectTrigger className={`h-8 text-xs ${error ? 'border-red-500' : ''}`}>
            <SelectValue placeholder="Select an option..." />
          </SelectTrigger>
          <SelectContent>
            {field.options.map((option) => (
              <SelectItem key={option.value} value={option.value} className="text-xs">
                <div>
                  <div>{option.label}</div>
                  {option.description && (
                    <div className="text-[10px] text-muted-foreground">{option.description}</div>
                  )}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {/* Multi-select */}
      {field.fieldType === 'multiselect' && field.options && (
        <div className="space-y-1">
          {field.options.map((option) => (
            <label
              key={option.value}
              className="flex items-center gap-2 p-2 rounded border hover:bg-muted/50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={value.split(',').includes(option.value)}
                onChange={(e) => {
                  const currentValues = value ? value.split(',') : [];
                  const newValues = e.target.checked
                    ? [...currentValues, option.value]
                    : currentValues.filter((v) => v !== option.value);
                  onChange(newValues.join(','));
                }}
                className="h-3 w-3"
              />
              <span className="text-xs">{option.label}</span>
            </label>
          ))}
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-1 text-xs text-red-600">
          <AlertCircle className="h-3 w-3" />
          {error}
        </div>
      )}
    </div>
  );
}
