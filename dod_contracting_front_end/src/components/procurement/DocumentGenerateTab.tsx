import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { toast } from 'sonner';
import {
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  Loader2,
  ExternalLink,
  Save,
  XCircle,
  Info,
} from 'lucide-react';
import { ProjectDocument } from '@/hooks/useProjectDocuments';
import {
  documentGenerationApi,
  type GenerationTaskInfo,
  type DependencyCheckResult,
} from '@/services/api';

interface DocumentGenerateTabProps {
  document: ProjectDocument;
  projectId: string;
  onGenerated: (content: string, openInEditor: boolean) => void;
  onUpdate: () => void;
}

type OutputOption = 'editor' | 'save';

export function DocumentGenerateTab({
  document,
  projectId,
  onGenerated,
  onUpdate,
}: DocumentGenerateTabProps) {
  const [additionalContext, setAdditionalContext] = useState('');
  const [outputOption, setOutputOption] = useState<OutputOption>('save');
  const [isGenerating, setIsGenerating] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskInfo, setTaskInfo] = useState<GenerationTaskInfo | null>(null);
  const [dependencyCheck, setDependencyCheck] = useState<DependencyCheckResult | null>(null);
  const [loadingDeps, setLoadingDeps] = useState(true);

  // Check dependencies on mount
  useEffect(() => {
    checkDependencies();
  }, [document.id]);

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

          if (status.result?.content) {
            if (outputOption === 'editor') {
              onGenerated(status.result.content, true);
              toast.success('Document generated! Opening in editor...');
            } else {
              // Save to document
              await documentGenerationApi.saveContent(
                document.id,
                status.result.content,
                status.result.quality_score
              );
              toast.success('Document generated and saved!');
              onUpdate();
            }
          }
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
  }, [taskId, isGenerating, outputOption, document.id, onGenerated, onUpdate]);

  const checkDependencies = async () => {
    setLoadingDeps(true);
    try {
      const result = await documentGenerationApi.checkDependencies(document.id);
      setDependencyCheck(result);
    } catch (error) {
      console.error('Error checking dependencies:', error);
      toast.error('Failed to check dependencies');
    } finally {
      setLoadingDeps(false);
    }
  };

  const handleGenerate = async () => {
    if (!dependencyCheck?.can_generate) {
      toast.error('Cannot generate - dependencies not met');
      return;
    }

    setIsGenerating(true);
    setTaskInfo(null);

    try {
      // Build assumptions from project context
      const assumptions = [
        {
          id: 'doc_type',
          text: `Document Type: ${document.document_name}`,
          source: 'Document Checklist',
        },
        {
          id: 'category',
          text: `Category: ${document.category}`,
          source: 'Document Template',
        },
      ];

      if (document.description) {
        assumptions.push({
          id: 'description',
          text: document.description,
          source: 'Document Template',
        });
      }

      const response = await documentGenerationApi.generate(
        document.id,
        assumptions,
        additionalContext || undefined
      );

      setTaskId(response.task_id);
      toast.info(`Generating ${document.document_name}...`);
    } catch (error: any) {
      setIsGenerating(false);
      toast.error(`Failed to start generation: ${error.message}`);
    }
  };

  const getStatusIcon = () => {
    if (loadingDeps) return <Loader2 className="h-5 w-5 animate-spin text-slate-400" />;
    if (!dependencyCheck) return <AlertTriangle className="h-5 w-5 text-amber-500" />;
    if (dependencyCheck.can_generate) return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    return <XCircle className="h-5 w-5 text-red-500" />;
  };

  const hasGeneratedContent = document.generation_status === 'generated' && document.generated_content;

  return (
    <div className="space-y-6">
      {/* Status Banner */}
      {hasGeneratedContent && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertTitle className="text-green-800">Content Already Generated</AlertTitle>
          <AlertDescription className="text-green-700">
            This document has AI-generated content
            {document.ai_quality_score && ` (Quality Score: ${document.ai_quality_score}/100)`}.
            Generating again will replace the existing content.
          </AlertDescription>
        </Alert>
      )}

      {/* Dependency Check Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <CardTitle className="text-lg">Generation Prerequisites</CardTitle>
            </div>
            {dependencyCheck && (
              <Badge
                variant="outline"
                className={
                  dependencyCheck.can_generate
                    ? 'bg-green-50 text-green-700 border-green-200'
                    : 'bg-red-50 text-red-700 border-red-200'
                }
              >
                {dependencyCheck.can_generate ? 'Ready to Generate' : 'Dependencies Required'}
              </Badge>
            )}
          </div>
          <CardDescription>
            Check that all required documents are available before generating
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingDeps ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
              <span className="ml-2 text-slate-600">Checking dependencies...</span>
            </div>
          ) : dependencyCheck ? (
            <div className="space-y-4">
              {dependencyCheck.missing_dependencies.length > 0 && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Missing Dependencies</AlertTitle>
                  <AlertDescription>
                    <p className="mb-2">
                      The following documents must be generated or uploaded first:
                    </p>
                    <ul className="list-disc list-inside">
                      {dependencyCheck.missing_dependencies.map((dep) => (
                        <li key={dep}>{dep}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {dependencyCheck.available_dependencies.length > 0 && (
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-slate-700">Available Dependencies:</p>
                    <p className="text-sm text-slate-600">
                      {dependencyCheck.available_dependencies.join(', ')}
                    </p>
                  </div>
                </div>
              )}

              {dependencyCheck.missing_dependencies.length === 0 &&
                dependencyCheck.available_dependencies.length === 0 && (
                  <div className="flex items-center gap-2 text-slate-600">
                    <Info className="h-4 w-4" />
                    <span className="text-sm">
                      This document has no dependencies - it can be generated immediately.
                    </span>
                  </div>
                )}

              <div className="flex items-center gap-2 pt-2 border-t">
                <Clock className="h-4 w-4 text-slate-400" />
                <span className="text-sm text-slate-600">
                  Estimated generation time: ~{dependencyCheck.estimated_minutes} minutes
                </span>
              </div>
            </div>
          ) : (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                Failed to check dependencies. Please try again.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Context Input */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Additional Context
          </CardTitle>
          <CardDescription>
            Provide any additional context or specific requirements for this document
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder={`Enter any specific requirements, constraints, or context for the ${document.document_name}...`}
            value={additionalContext}
            onChange={(e) => setAdditionalContext(e.target.value)}
            rows={4}
            disabled={isGenerating}
          />
          <p className="text-xs text-slate-500 mt-2">
            The AI will use your project information, existing documents, and this context to
            generate content.
          </p>
        </CardContent>
      </Card>

      {/* Output Options */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Output Options</CardTitle>
          <CardDescription>Choose where to send the generated content</CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup
            value={outputOption}
            onValueChange={(value) => setOutputOption(value as OutputOption)}
            disabled={isGenerating}
            className="space-y-2"
          >
            {/* Save as Draft option - entire row is clickable */}
            <div 
              className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                outputOption === 'save' ? 'bg-blue-50 border-blue-300' : 'hover:bg-slate-50'
              } ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
              onClick={() => !isGenerating && setOutputOption('save')}
            >
              <RadioGroupItem value="save" id="save" className="mt-1" />
              <Label htmlFor="save" className="flex-1 cursor-pointer">
                <div className="font-medium">Save as Draft</div>
                <div className="text-sm text-slate-500">
                  Save the generated content to this document. You can review and edit it later.
                </div>
              </Label>
              <Save className="h-5 w-5 text-slate-400" />
            </div>
            {/* Open in Live Editor option - entire row is clickable */}
            <div 
              className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                outputOption === 'editor' ? 'bg-blue-50 border-blue-300' : 'hover:bg-slate-50'
              } ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
              onClick={() => !isGenerating && setOutputOption('editor')}
            >
              <RadioGroupItem value="editor" id="editor" className="mt-1" />
              <Label htmlFor="editor" className="flex-1 cursor-pointer">
                <div className="font-medium">Open in Live Editor</div>
                <div className="text-sm text-slate-500">
                  Open the generated content in the Live Editor for immediate review and editing.
                </div>
              </Label>
              <ExternalLink className="h-5 w-5 text-slate-400" />
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Generation Progress */}
      {isGenerating && taskInfo && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                  <span className="font-medium text-blue-900">Generating...</span>
                </div>
                <span className="text-sm text-blue-700">{taskInfo.progress}%</span>
              </div>
              <Progress value={taskInfo.progress} className="h-2" />
              <p className="text-sm text-blue-700">{taskInfo.message}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generate Button */}
      <div className="flex justify-end gap-3">
        <Button
          onClick={handleGenerate}
          disabled={!dependencyCheck?.can_generate || isGenerating || loadingDeps}
          className="gap-2"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Generate {document.document_name}
            </>
          )}
        </Button>
      </div>

      {/* Existing Content Preview */}
      {hasGeneratedContent && !isGenerating && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Previously Generated Content</CardTitle>
            <CardDescription>
              Generated on {document.generated_at ? new Date(document.generated_at).toLocaleString() : 'Unknown'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-h-64 overflow-y-auto rounded-lg bg-slate-50 p-4">
              <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans">
                {document.generated_content?.substring(0, 1000)}
                {(document.generated_content?.length || 0) > 1000 && '...'}
              </pre>
            </div>
            <div className="flex justify-end mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onGenerated(document.generated_content || '', true)}
                className="gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                Open Full Content in Editor
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
