/**
 * DocumentTypeSelector - Step 1 of the Generate Document wizard.
 * Displays document types grouped by procurement phase for multi-select.
 */

import { useState, useEffect } from 'react';
import { Check, Clock, BarChart3, Loader2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { standaloneApi } from '@/services/api';
import type { DocumentTypeSchema, DocumentTypeSchemas } from './types';

const PHASE_LABELS: Record<string, string> = {
  pre_solicitation: 'Pre-Solicitation',
  solicitation: 'Solicitation',
  post_solicitation: 'Post-Solicitation',
};

const PHASE_ORDER = ['pre_solicitation', 'solicitation', 'post_solicitation'];

const COMPLEXITY_COLORS: Record<string, string> = {
  low: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  high: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400',
};

interface DocumentTypeSelectorProps {
  onNext: (selected: Array<{ docType: string; schema: DocumentTypeSchema }>) => void;
}

export function DocumentTypeSelector({ onNext }: DocumentTypeSelectorProps) {
  const [schemas, setSchemas] = useState<DocumentTypeSchemas>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    async function loadSchemas() {
      try {
        const response = await standaloneApi.getFormSchemas();
        setSchemas(response.schemas);
      } catch (err: any) {
        setError(err.message || 'Failed to load document types');
      } finally {
        setLoading(false);
      }
    }
    loadSchemas();
  }, []);

  const toggleSelection = (docType: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(docType)) {
        next.delete(docType);
      } else {
        next.add(docType);
      }
      return next;
    });
  };

  const handleNext = () => {
    const docs = Array.from(selected).map(docType => ({
      docType,
      schema: schemas[docType],
    }));
    onNext(docs);
  };

  // Group by phase
  const grouped: Record<string, Array<{ key: string; schema: DocumentTypeSchema }>> = {};
  for (const [key, schema] of Object.entries(schemas)) {
    const phase = schema.phase || 'other';
    if (!grouped[phase]) grouped[phase] = [];
    grouped[phase].push({ key, schema });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-3 text-muted-foreground">Loading document types...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <p className="text-destructive">{error}</p>
        <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold">Select Document Types</h2>
        <p className="text-muted-foreground mt-1">
          Choose one or more document types to generate. You'll provide context details in the next step.
        </p>
      </div>

      {PHASE_ORDER.map(phase => {
        const docs = grouped[phase];
        if (!docs?.length) return null;

        return (
          <div key={phase}>
            <h3 className="text-lg font-semibold mb-3 text-foreground">
              {PHASE_LABELS[phase] || phase}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {docs.map(({ key, schema }) => {
                const isSelected = selected.has(key);
                return (
                  <Card
                    key={key}
                    onClick={() => toggleSelection(key)}
                    className={`p-4 cursor-pointer transition-all border-2 hover:shadow-md ${
                      isSelected
                        ? 'border-primary bg-primary/5 shadow-sm'
                        : 'border-transparent hover:border-muted-foreground/20'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-sm truncate">{schema.name}</h4>
                          {isSelected && (
                            <div className="flex-shrink-0 h-5 w-5 rounded-full bg-primary flex items-center justify-center">
                              <Check className="h-3 w-3 text-primary-foreground" />
                            </div>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {schema.description}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <Badge variant="outline" className={`text-xs ${COMPLEXITY_COLORS[schema.complexity]}`}>
                        <BarChart3 className="h-3 w-3 mr-1" />
                        {schema.complexity}
                      </Badge>
                      <span className="text-xs text-muted-foreground flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        ~{schema.estimated_minutes} min
                      </span>
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        );
      })}

      <div className="flex justify-end pt-4 border-t">
        <Button
          onClick={handleNext}
          disabled={selected.size === 0}
          size="lg"
        >
          Continue with {selected.size} document{selected.size !== 1 ? 's' : ''}
        </Button>
      </div>
    </div>
  );
}
