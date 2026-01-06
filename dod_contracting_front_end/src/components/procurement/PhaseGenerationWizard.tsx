import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  Loader2,
  XCircle,
  Info,
} from 'lucide-react';
import { ProjectDocument } from '@/hooks/useProjectDocuments';
import {
  projectsApi,
  documentGenerationApi,
  type GenerationTaskInfo,
} from '@/services/api';

interface PhaseGenerationWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  documents: ProjectDocument[];
  onComplete: () => void;
}

type WizardStep = 'select' | 'context' | 'generate';

interface DocumentSelection {
  id: string;
  name: string;
  selected: boolean;
  canGenerate: boolean;
  missingDeps: string[];
  estimatedMinutes: number;
}

export function PhaseGenerationWizard({
  open,
  onOpenChange,
  projectId,
  documents,
  onComplete,
}: PhaseGenerationWizardProps) {
  const [step, setStep] = useState<WizardStep>('select');
  const [selections, setSelections] = useState<DocumentSelection[]>([]);
  const [additionalContext, setAdditionalContext] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskInfo, setTaskInfo] = useState<GenerationTaskInfo | null>(null);
  const [loadingDeps, setLoadingDeps] = useState(false);

  // Initialize selections when dialog opens
  useEffect(() => {
    if (open) {
      initializeSelections();
      setStep('select');
      setAdditionalContext('');
      setIsGenerating(false);
      setTaskId(null);
      setTaskInfo(null);
    }
  }, [open, documents]);

  // Poll for task status when generating
  useEffect(() => {
    if (!taskId || !isGenerating) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await documentGenerationApi.getTaskStatus(taskId);
        setTaskInfo(status);

        if (status.status === 'completed') {
          setIsGenerating(false);
          clearInterval(pollInterval);
          
          const completed = status.completed_documents?.length || 0;
          const failed = status.failed_documents?.length || 0;
          
          if (failed > 0) {
            toast.warning(`Generation complete: ${completed} succeeded, ${failed} failed`);
          } else {
            toast.success(`Successfully generated ${completed} documents!`);
          }
          
          onComplete();
          onOpenChange(false);
        } else if (status.status === 'failed') {
          setIsGenerating(false);
          clearInterval(pollInterval);
          toast.error(`Generation failed: ${status.error || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error polling task status:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [taskId, isGenerating, onComplete, onOpenChange]);

  const initializeSelections = async () => {
    setLoadingDeps(true);
    
    // Filter to pending documents that can be generated
    const pendingDocs = documents.filter(
      (d) => d.status === 'pending' && d.generation_status !== 'generating'
    );

    const newSelections: DocumentSelection[] = [];

    for (const doc of pendingDocs) {
      try {
        const depCheck = await documentGenerationApi.checkDependencies(doc.id);
        newSelections.push({
          id: doc.id,
          name: doc.document_name,
          selected: depCheck.can_generate, // Auto-select if can generate
          canGenerate: depCheck.can_generate,
          missingDeps: depCheck.missing_dependencies,
          estimatedMinutes: depCheck.estimated_minutes,
        });
      } catch (error) {
        newSelections.push({
          id: doc.id,
          name: doc.document_name,
          selected: false,
          canGenerate: false,
          missingDeps: ['Error checking dependencies'],
          estimatedMinutes: 2,
        });
      }
    }

    setSelections(newSelections);
    setLoadingDeps(false);
  };

  const toggleSelection = (id: string) => {
    setSelections((prev) =>
      prev.map((s) =>
        s.id === id && s.canGenerate ? { ...s, selected: !s.selected } : s
      )
    );
  };

  const selectAll = () => {
    setSelections((prev) =>
      prev.map((s) => (s.canGenerate ? { ...s, selected: true } : s))
    );
  };

  const selectNone = () => {
    setSelections((prev) => prev.map((s) => ({ ...s, selected: false })));
  };

  const selectedCount = selections.filter((s) => s.selected).length;
  const totalEstimate = selections
    .filter((s) => s.selected)
    .reduce((sum, s) => sum + s.estimatedMinutes, 0);

  const handleStartGeneration = async () => {
    const selectedIds = selections.filter((s) => s.selected).map((s) => s.id);
    
    if (selectedIds.length === 0) {
      toast.error('Please select at least one document');
      return;
    }

    setIsGenerating(true);
    setStep('generate');

    try {
      // Build assumptions
      const assumptions = additionalContext
        ? [{ id: 'user_context', text: additionalContext, source: 'User Input' }]
        : [];

      const response = await projectsApi.generateBatch(
        projectId,
        selectedIds,
        assumptions
      );

      setTaskId(response.task_id);
      toast.info(`Starting batch generation of ${response.document_count} documents...`);
    } catch (error: any) {
      setIsGenerating(false);
      toast.error(`Failed to start generation: ${error.message}`);
      setStep('select');
    }
  };

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center gap-2 mb-6">
      {['select', 'context', 'generate'].map((s, i) => (
        <div key={s} className="flex items-center">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step === s
                ? 'bg-blue-600 text-white'
                : i < ['select', 'context', 'generate'].indexOf(step)
                ? 'bg-green-100 text-green-700'
                : 'bg-slate-100 text-slate-500'
            }`}
          >
            {i < ['select', 'context', 'generate'].indexOf(step) ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              i + 1
            )}
          </div>
          {i < 2 && <div className="w-12 h-0.5 bg-slate-200 mx-2" />}
        </div>
      ))}
    </div>
  );

  const renderSelectStep = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Select Documents to Generate</h3>
          <p className="text-sm text-slate-600">
            Choose which documents you want to generate with AI
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={selectAll}>
            Select All
          </Button>
          <Button variant="outline" size="sm" onClick={selectNone}>
            Clear
          </Button>
        </div>
      </div>

      {loadingDeps ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
          <span className="ml-2 text-slate-600">Checking dependencies...</span>
        </div>
      ) : selections.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-slate-400 mx-auto mb-4" />
          <p className="text-slate-600">No pending documents available for generation</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {selections.map((selection, index) => (
            <Card
              key={selection.id}
              className={`cursor-pointer transition-all ${
                selection.selected
                  ? 'border-blue-300 bg-blue-50'
                  : selection.canGenerate
                  ? 'hover:border-slate-300'
                  : 'opacity-60 cursor-not-allowed'
              }`}
              onClick={() => toggleSelection(selection.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={selection.selected}
                    disabled={!selection.canGenerate}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-500">
                          {index + 1}.
                        </span>
                        <span className="font-medium">{selection.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {selection.canGenerate ? (
                          <Badge variant="outline" className="text-green-700 bg-green-50 border-green-200">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Ready
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-amber-700 bg-amber-50 border-amber-200">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Blocked
                          </Badge>
                        )}
                        <span className="text-xs text-slate-500">
                          ~{selection.estimatedMinutes} min
                        </span>
                      </div>
                    </div>
                    {!selection.canGenerate && selection.missingDeps.length > 0 && (
                      <p className="text-xs text-amber-600 mt-1">
                        Requires: {selection.missingDeps.join(', ')}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {selectedCount > 0 && (
        <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">
              {selectedCount} document{selectedCount > 1 ? 's' : ''} selected
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-500" />
            <span className="text-sm text-blue-700">
              ~{totalEstimate} minutes estimated
            </span>
          </div>
        </div>
      )}
    </div>
  );

  const renderContextStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Provide Additional Context</h3>
        <p className="text-sm text-slate-600">
          Add any specific requirements or context for the document generation
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Selected Documents</CardTitle>
          <CardDescription>
            The following documents will be generated in dependency order
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {selections
              .filter((s) => s.selected)
              .map((s, i) => (
                <Badge key={s.id} variant="secondary">
                  {i + 1}. {s.name}
                </Badge>
              ))}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-2">
        <Label htmlFor="context">Additional Context (Optional)</Label>
        <Textarea
          id="context"
          placeholder="Enter any specific requirements, constraints, or additional context that should be considered when generating these documents..."
          value={additionalContext}
          onChange={(e) => setAdditionalContext(e.target.value)}
          rows={5}
        />
        <p className="text-xs text-slate-500">
          This context will be applied to all selected documents. The AI will also
          use your project information and any previously generated documents as
          context.
        </p>
      </div>

      <div className="flex items-start gap-2 p-3 bg-amber-50 rounded-lg">
        <Info className="h-4 w-4 text-amber-600 mt-0.5" />
        <div className="text-sm text-amber-800">
          <p className="font-medium">Note:</p>
          <p>
            Documents with dependencies will be generated in order. Each subsequent
            document will use content from previously generated documents as context.
          </p>
        </div>
      </div>
    </div>
  );

  const renderGenerateStep = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
          {isGenerating ? (
            <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
          ) : taskInfo?.status === 'completed' ? (
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          ) : (
            <XCircle className="h-8 w-8 text-red-600" />
          )}
        </div>
        <h3 className="text-lg font-semibold">
          {isGenerating
            ? 'Generating Documents...'
            : taskInfo?.status === 'completed'
            ? 'Generation Complete!'
            : 'Generation Failed'}
        </h3>
        <p className="text-sm text-slate-600 mt-1">
          {taskInfo?.message || 'Starting generation...'}
        </p>
      </div>

      {taskInfo && (
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Progress</span>
              <span className="font-medium">{taskInfo.progress}%</span>
            </div>
            <Progress value={taskInfo.progress} className="h-2" />
          </div>

          {taskInfo.current_document && (
            <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              <span className="text-sm text-blue-800">
                Generating: {taskInfo.current_document}
              </span>
            </div>
          )}

          {taskInfo.completed_documents && taskInfo.completed_documents.length > 0 && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  Completed ({taskInfo.completed_documents.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <div className="space-y-1">
                  {taskInfo.completed_documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between text-sm"
                    >
                      <span>{doc.name}</span>
                      {doc.quality_score && (
                        <Badge variant="outline" className="text-xs">
                          Quality: {doc.quality_score}%
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {taskInfo.failed_documents && taskInfo.failed_documents.length > 0 && (
            <Card className="border-red-200">
              <CardHeader className="py-3">
                <CardTitle className="text-sm flex items-center gap-2 text-red-700">
                  <XCircle className="h-4 w-4" />
                  Failed ({taskInfo.failed_documents.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <div className="space-y-1">
                  {taskInfo.failed_documents.map((doc) => (
                    <div key={doc.id} className="text-sm">
                      <span className="font-medium">{doc.name}</span>
                      <p className="text-xs text-red-600">{doc.error}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            Generate Documents with AI
          </DialogTitle>
          <DialogDescription>
            Generate multiple documents in batch using AI. Documents will be
            generated in dependency order.
          </DialogDescription>
        </DialogHeader>

        <Separator />

        {renderStepIndicator()}

        {step === 'select' && renderSelectStep()}
        {step === 'context' && renderContextStep()}
        {step === 'generate' && renderGenerateStep()}

        <Separator />

        <DialogFooter>
          {step === 'select' && (
            <>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => setStep('context')}
                disabled={selectedCount === 0}
                className="gap-2"
              >
                Next: Add Context
                <ArrowRight className="h-4 w-4" />
              </Button>
            </>
          )}

          {step === 'context' && (
            <>
              <Button
                variant="outline"
                onClick={() => setStep('select')}
                className="gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleStartGeneration} className="gap-2">
                <Sparkles className="h-4 w-4" />
                Generate {selectedCount} Document{selectedCount > 1 ? 's' : ''}
              </Button>
            </>
          )}

          {step === 'generate' && !isGenerating && (
            <Button onClick={() => onOpenChange(false)}>Close</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
