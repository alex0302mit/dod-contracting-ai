/**
 * GenerateDocumentScreen - Standalone document generation wizard.
 * 3-step flow: Select Types -> Fill Context -> Generating
 */

import { useState } from 'react';
import { standaloneApi } from '@/services/api';
import { toast } from 'sonner';
import { DocumentTypeSelector } from '@/components/generate-document/DocumentTypeSelector';
import { DynamicContextForm } from '@/components/generate-document/DynamicContextForm';
import { GenerationProgress } from '@/components/generate-document/GenerationProgress';
import type { WizardStep, DocumentTypeSchema, SelectedDocument } from '@/components/generate-document/types';

export function GenerateDocumentScreen() {
  const [step, setStep] = useState<WizardStep>('SELECT_TYPES');
  const [selectedDocs, setSelectedDocs] = useState<Array<{ docType: string; schema: DocumentTypeSchema }>>([]);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [documentNames, setDocumentNames] = useState<string[]>([]);

  const handleTypeSelection = (docs: Array<{ docType: string; schema: DocumentTypeSchema }>) => {
    setSelectedDocs(docs);
    setStep('FILL_CONTEXT');
  };

  const handleGenerate = async (documents: SelectedDocument[]) => {
    try {
      const payload = documents.map(d => ({
        doc_type: d.docType,
        context: d.context,
      }));

      const response = await standaloneApi.generate(payload);
      setTaskId(response.task_id);
      setDocumentNames(documents.map(d => d.schema.name));
      setStep('GENERATING');
      toast.success(`Generating ${response.documents_requested} document(s)...`);
    } catch (err: any) {
      toast.error(`Failed to start generation: ${err.message}`);
    }
  };

  // Step indicator
  const steps = [
    { key: 'SELECT_TYPES', label: 'Select Types' },
    { key: 'FILL_CONTEXT', label: 'Provide Context' },
    { key: 'GENERATING', label: 'Generate' },
  ];
  const currentStepIndex = steps.findIndex(s => s.key === step);

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-4xl mx-auto py-8 px-6">
        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          {steps.map((s, i) => (
            <div key={s.key} className="flex items-center gap-2">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                  i <= currentStepIndex
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {i + 1}
              </div>
              <span
                className={`text-sm hidden sm:block ${
                  i <= currentStepIndex ? 'text-foreground font-medium' : 'text-muted-foreground'
                }`}
              >
                {s.label}
              </span>
              {i < steps.length - 1 && (
                <div className={`w-12 h-0.5 ${i < currentStepIndex ? 'bg-primary' : 'bg-muted'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Step content */}
        {step === 'SELECT_TYPES' && (
          <DocumentTypeSelector onNext={handleTypeSelection} />
        )}

        {step === 'FILL_CONTEXT' && (
          <DynamicContextForm
            selectedDocs={selectedDocs}
            onBack={() => setStep('SELECT_TYPES')}
            onGenerate={handleGenerate}
          />
        )}

        {step === 'GENERATING' && taskId && (
          <GenerationProgress taskId={taskId} documentNames={documentNames} />
        )}
      </div>
    </div>
  );
}

export default GenerateDocumentScreen;
