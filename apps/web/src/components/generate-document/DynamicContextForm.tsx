/**
 * DynamicContextForm - Step 2 of the Generate Document wizard.
 * Renders per-document-type form fields based on schema definitions.
 * Uses tabbed interface when multiple documents are selected.
 */

import { useState } from 'react';
import { ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import type { DocumentTypeSchema, FormField, SelectedDocument } from './types';

interface DynamicContextFormProps {
  selectedDocs: Array<{ docType: string; schema: DocumentTypeSchema }>;
  onBack: () => void;
  onGenerate: (documents: SelectedDocument[]) => void;
}

export function DynamicContextForm({ selectedDocs, onBack, onGenerate }: DynamicContextFormProps) {
  // State: context per doc type
  const [contexts, setContexts] = useState<Record<string, Record<string, string>>>(() => {
    const initial: Record<string, Record<string, string>> = {};
    for (const { docType } of selectedDocs) {
      initial[docType] = {};
    }
    return initial;
  });

  const [activeTab, setActiveTab] = useState(selectedDocs[0]?.docType || '');
  const [validationErrors, setValidationErrors] = useState<Record<string, string[]>>({});

  const updateField = (docType: string, key: string, value: string) => {
    setContexts(prev => ({
      ...prev,
      [docType]: { ...prev[docType], [key]: value },
    }));
    // Clear validation errors for this doc type on change
    setValidationErrors(prev => ({ ...prev, [docType]: [] }));
  };

  const validate = (): boolean => {
    const errors: Record<string, string[]> = {};
    let valid = true;

    for (const { docType, schema } of selectedDocs) {
      const docErrors: string[] = [];
      for (const field of schema.fields) {
        if (field.required && !contexts[docType]?.[field.key]) {
          docErrors.push(field.label);
          valid = false;
        }
      }
      if (docErrors.length > 0) {
        errors[docType] = docErrors;
      }
    }

    setValidationErrors(errors);
    if (!valid) {
      // Switch to first tab with errors
      const firstErrorTab = Object.keys(errors)[0];
      if (firstErrorTab) setActiveTab(firstErrorTab);
    }
    return valid;
  };

  const handleGenerate = () => {
    if (!validate()) return;

    const documents: SelectedDocument[] = selectedDocs.map(({ docType, schema }) => ({
      docType,
      schema,
      context: contexts[docType] || {},
    }));

    onGenerate(documents);
  };

  const renderField = (docType: string, field: FormField) => {
    const value = contexts[docType]?.[field.key] || '';
    const hasError = validationErrors[docType]?.includes(field.label);

    return (
      <div key={field.key} className="space-y-2">
        <Label htmlFor={`${docType}-${field.key}`} className={hasError ? 'text-destructive' : ''}>
          {field.label}
          {field.required && <span className="text-destructive ml-1">*</span>}
        </Label>

        {field.type === 'text' && (
          <Input
            id={`${docType}-${field.key}`}
            value={value}
            onChange={e => updateField(docType, field.key, e.target.value)}
            placeholder={field.placeholder}
            className={hasError ? 'border-destructive' : ''}
          />
        )}

        {field.type === 'textarea' && (
          <Textarea
            id={`${docType}-${field.key}`}
            value={value}
            onChange={e => updateField(docType, field.key, e.target.value)}
            placeholder={field.placeholder}
            rows={4}
            className={hasError ? 'border-destructive' : ''}
          />
        )}

        {field.type === 'number' && (
          <Input
            id={`${docType}-${field.key}`}
            type="number"
            value={value}
            onChange={e => updateField(docType, field.key, e.target.value)}
            placeholder={field.placeholder}
            className={hasError ? 'border-destructive' : ''}
          />
        )}

        {field.type === 'select' && field.options && (
          <Select
            value={value}
            onValueChange={v => updateField(docType, field.key, v)}
          >
            <SelectTrigger className={hasError ? 'border-destructive' : ''}>
              <SelectValue placeholder="Select..." />
            </SelectTrigger>
            <SelectContent>
              {field.options.map(opt => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {field.type === 'date' && (
          <Input
            id={`${docType}-${field.key}`}
            type="date"
            value={value}
            onChange={e => updateField(docType, field.key, e.target.value)}
            className={hasError ? 'border-destructive' : ''}
          />
        )}
      </div>
    );
  };

  const renderDocForm = (docType: string, schema: DocumentTypeSchema) => (
    <div className="space-y-4">
      {validationErrors[docType]?.length > 0 && (
        <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20">
          <p className="text-sm text-destructive font-medium">
            Please fill in required fields: {validationErrors[docType].join(', ')}
          </p>
        </div>
      )}
      {schema.fields.map(field => renderField(docType, field))}
    </div>
  );

  // Single document: no tabs
  if (selectedDocs.length === 1) {
    const { docType, schema } = selectedDocs[0];
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Provide Context</h2>
          <p className="text-muted-foreground mt-1">
            Fill in the details for <strong>{schema.name}</strong>.
          </p>
        </div>

        <Card className="p-6">
          {renderDocForm(docType, schema)}
        </Card>

        <div className="flex justify-between pt-4 border-t">
          <Button variant="outline" onClick={onBack}>
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <Button onClick={handleGenerate} size="lg">
            Generate Document
          </Button>
        </div>
      </div>
    );
  }

  // Multiple documents: tabbed interface
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Provide Context</h2>
        <p className="text-muted-foreground mt-1">
          Fill in context for each document type. Fields marked with * are required.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full justify-start flex-wrap h-auto gap-1 bg-muted/50 p-1">
          {selectedDocs.map(({ docType, schema }) => (
            <TabsTrigger
              key={docType}
              value={docType}
              className={`text-xs ${validationErrors[docType]?.length ? 'text-destructive' : ''}`}
            >
              {schema.name}
            </TabsTrigger>
          ))}
        </TabsList>

        {selectedDocs.map(({ docType, schema }) => (
          <TabsContent key={docType} value={docType}>
            <Card className="p-6">
              <p className="text-sm text-muted-foreground mb-4">{schema.description}</p>
              {renderDocForm(docType, schema)}
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      <div className="flex justify-between pt-4 border-t">
        <Button variant="outline" onClick={onBack}>
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back
        </Button>
        <Button onClick={handleGenerate} size="lg">
          Generate {selectedDocs.length} Document{selectedDocs.length > 1 ? 's' : ''}
        </Button>
      </div>
    </div>
  );
}
