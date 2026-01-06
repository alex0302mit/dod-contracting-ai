/**
 * Guided Field Form
 *
 * Dynamically renders form inputs based on field type.
 * Integrates with React Hook Form for validation.
 */

import { useGuidedFlow } from '@/contexts/GuidedFlowContext';
import { Controller } from 'react-hook-form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { Card } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';
import type { GuidedField } from '@/types/guidedFlow';

interface GuidedFieldFormProps {
  field: GuidedField;
}

export function GuidedFieldForm({ field }: GuidedFieldFormProps) {
  const { form, getFieldPermission } = useGuidedFlow();
  const { control, formState: { errors } } = form;

  // Get permission level for this field
  const permission = getFieldPermission(field);
  const isReadOnly = permission === 'view' || permission === 'none';

  // Get error message for this field
  const fieldPath = field.rfhName.split('.');
  let errorObj: any = errors;
  for (const part of fieldPath) {
    if (errorObj && errorObj[part]) {
      errorObj = errorObj[part];
    } else {
      errorObj = null;
      break;
    }
  }
  const errorMessage = errorObj && typeof errorObj === 'object' && 'message' in errorObj
    ? String(errorObj.message)
    : null;

  // ========================================================================
  // Render Different Field Types
  // ========================================================================

  return (
    <div className="space-y-2">
      <Label htmlFor={field.id} className="text-sm font-medium">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </Label>

      <Controller
        name={field.rfhName}
        control={control}
        render={({ field: controllerField }) => {
          switch (field.type) {
            // ============================================================
            // CHECKBOX
            // ============================================================
            case 'checkbox':
              return (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id={field.id}
                    checked={controllerField.value || false}
                    onCheckedChange={controllerField.onChange}
                    disabled={isReadOnly}
                    data-field-id={field.id}
                  />
                  <Label
                    htmlFor={field.id}
                    className="text-sm font-normal cursor-pointer"
                  >
                    {field.label}
                  </Label>
                </div>
              );

            // ============================================================
            // TEXT INPUT
            // ============================================================
            case 'text':
              return (
                <Input
                  id={field.id}
                  type="text"
                  {...controllerField}
                  value={controllerField.value || ''}
                  disabled={isReadOnly}
                  placeholder={field.helperText}
                  data-field-id={field.id}
                  className={errorMessage ? 'border-red-500' : ''}
                />
              );

            // ============================================================
            // TEXTAREA
            // ============================================================
            case 'textarea':
              return (
                <Textarea
                  id={field.id}
                  {...controllerField}
                  value={controllerField.value || ''}
                  disabled={isReadOnly}
                  placeholder={field.helperText}
                  rows={6}
                  data-field-id={field.id}
                  className={errorMessage ? 'border-red-500' : ''}
                />
              );

            // ============================================================
            // DATE PICKER
            // ============================================================
            case 'date':
              return (
                <Input
                  id={field.id}
                  type="date"
                  {...controllerField}
                  value={controllerField.value || ''}
                  disabled={isReadOnly}
                  data-field-id={field.id}
                  className={errorMessage ? 'border-red-500' : ''}
                />
              );

            // ============================================================
            // SELECT DROPDOWN
            // ============================================================
            case 'select':
              return (
                <Select
                  value={controllerField.value || ''}
                  onValueChange={controllerField.onChange}
                  disabled={isReadOnly}
                >
                  <SelectTrigger
                    id={field.id}
                    data-field-id={field.id}
                    className={errorMessage ? 'border-red-500' : ''}
                  >
                    <SelectValue placeholder="Select an option..." />
                  </SelectTrigger>
                  <SelectContent>
                    {field.options?.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              );

            // ============================================================
            // SIGNATURE BLOCK
            // ============================================================
            case 'signature':
              return (
                <Card className="p-4 space-y-4" data-field-id={field.id}>
                  {/* Name */}
                  <div className="space-y-2">
                    <Label htmlFor={`${field.id}-name`} className="text-sm">
                      Full Name <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id={`${field.id}-name`}
                      type="text"
                      value={controllerField.value?.name || ''}
                      onChange={(e) => {
                        controllerField.onChange({
                          ...controllerField.value,
                          name: e.target.value
                        });
                      }}
                      disabled={isReadOnly}
                      placeholder="John Doe"
                    />
                  </div>

                  {/* Title */}
                  <div className="space-y-2">
                    <Label htmlFor={`${field.id}-title`} className="text-sm">
                      Title <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id={`${field.id}-title`}
                      type="text"
                      value={controllerField.value?.title || ''}
                      onChange={(e) => {
                        controllerField.onChange({
                          ...controllerField.value,
                          title: e.target.value
                        });
                      }}
                      disabled={isReadOnly}
                      placeholder="CEO, President, etc."
                    />
                  </div>

                  {/* Date */}
                  <div className="space-y-2">
                    <Label htmlFor={`${field.id}-date`} className="text-sm">
                      Date <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id={`${field.id}-date`}
                      type="date"
                      value={controllerField.value?.date || ''}
                      onChange={(e) => {
                        controllerField.onChange({
                          ...controllerField.value,
                          date: e.target.value
                        });
                      }}
                      disabled={isReadOnly}
                    />
                  </div>

                  {/* Signature Line */}
                  <div className="pt-4 border-t">
                    <div className="border-b-2 border-slate-300 pb-2 mb-2">
                      <p className="text-sm italic text-slate-500">Electronic Signature</p>
                      {controllerField.value?.name && (
                        <p className="text-base font-signature text-slate-900">
                          {controllerField.value.name}
                        </p>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">
                      By typing your name above, you agree this constitutes a legal electronic signature
                    </p>
                  </div>
                </Card>
              );

            // ============================================================
            // DEFAULT/UNKNOWN
            // ============================================================
            default:
              return (
                <div className="p-4 bg-slate-100 rounded text-sm text-slate-600">
                  Unsupported field type: {field.type}
                </div>
              );
          }
        }}
      />

      {/* Error Message */}
      {errorMessage && (
        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg mt-2">
          <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-red-900">{errorMessage}</p>
        </div>
      )}

      {/* Read-Only Notice */}
      {isReadOnly && (
        <p className="text-xs text-slate-500 italic">
          You have {permission} permission for this field
        </p>
      )}
    </div>
  );
}
