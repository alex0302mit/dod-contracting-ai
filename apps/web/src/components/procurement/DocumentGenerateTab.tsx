import { useState, useEffect, useCallback, useRef } from 'react';
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
  Wifi,
  WifiOff,
} from 'lucide-react';
import { ProjectDocument } from '@/hooks/useProjectDocuments';
import {
  documentGenerationApi,
  createWebSocket,
  type GenerationTaskInfo,
  type DependencyCheckResult,
  type WebSocketMessage,
} from '@/services/api';
import { markdownToHtml } from '@/lib/markdownToHtml';

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
  const [wsConnected, setWsConnected] = useState(false);

  // WebSocket reference
  const wsRef = useRef<WebSocket | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Ref to store current taskId - avoids stale closure issues in callbacks
  // When WebSocket closes, the startPolling callback may have stale taskId from closure
  // Using a ref ensures we always have the current value
  const taskIdRef = useRef<string | null>(null);

  // Check dependencies on mount
  useEffect(() => {
    checkDependencies();
  }, [document.id]);

  // Setup WebSocket connection when generating starts AND we have a task ID
  // We need taskId before connecting so we can filter messages properly
  useEffect(() => {
    // #region agent log
    // [DEBUG] Log every useEffect run to track WebSocket setup timing
    fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:useEffect:wsSetup',message:'WebSocket useEffect triggered',data:{isGenerating,projectId:!!projectId,taskId,taskIdRef:taskIdRef.current,willConnect:isGenerating&&!!projectId&&!!taskId},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'useEffect'})}).catch(()=>{});
    // #endregion
    // Don't connect WebSocket until we have a taskId - prevents premature connection/closure
    if (!isGenerating || !projectId || !taskId) return;

    // Connect to WebSocket for real-time updates
    const ws = createWebSocket(projectId);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('📡 WebSocket connected for generation updates');
      // #region agent log
      // [DEBUG] Log WebSocket open
      fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:ws.onopen',message:'WebSocket connected',data:{taskIdRef:taskIdRef.current},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'ws-connect'})}).catch(()=>{});
      // #endregion
      setWsConnected(true);
      // Clear polling when WebSocket connects
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        // Get current taskId from ref to avoid stale closure
        const currentTaskId = taskIdRef.current;

        // #region agent log
        // [DEBUG] Log all incoming WebSocket messages to test hypotheses A, B, E
        fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:ws.onmessage',message:'WS message received',data:{msgType:data.type,msgTaskId:data.task_id,taskIdFromRef:currentTaskId,taskIdFromClosure:taskId,willFilter:data.task_id && data.task_id !== currentTaskId,hasContent:!!data.content,rawData:JSON.stringify(data).slice(0,500)},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'A,B,E'})}).catch(()=>{});
        // #endregion

        // Only process messages for our current task (use ref to avoid stale closure)
        if (data.task_id && data.task_id !== currentTaskId) return;

        switch (data.type) {
          case 'progress':
            setTaskInfo((prev) => ({
              ...(prev || { task_id: taskId || '', status: 'in_progress' }),
              progress: data.percentage || data.progress || 0,
              message: data.message || 'Processing...',
              status: 'in_progress',
            }));
            break;

          case 'generation_complete':
          case 'task_complete':
            // #region agent log
            // [DEBUG] Log when completion handler is called - tests hypothesis A
            fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:completion-case',message:'Calling handleGenerationComplete',data:{type:data.type,hasContent:!!data.content},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'A'})}).catch(()=>{});
            // #endregion
            handleGenerationComplete(data);
            break;

          case 'error':
            handleGenerationError(data.message || 'Unknown error');
            break;
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };

    ws.onerror = () => {
      console.warn('⚠️ WebSocket error, falling back to polling');
      setWsConnected(false);
      startPolling();
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      // Get current values from refs to avoid stale closures
      const currentTaskId = taskIdRef.current;
      // #region agent log
      // [DEBUG] Log WebSocket close - tests hypothesis C
      fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:ws.onclose',message:'WebSocket closed',data:{isGenerating,taskIdFromRef:currentTaskId,willStartPolling:isGenerating && !!currentTaskId},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'C'})}).catch(()=>{});
      // #endregion
      setWsConnected(false);
      // Start polling as fallback if still generating AND we have a taskId
      if (isGenerating && currentTaskId) {
        startPolling();
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      wsRef.current = null;
    };
  }, [isGenerating, projectId, taskId]);

  // Polling fallback (starts only if WebSocket disconnects)
  // Uses taskIdRef.current instead of taskId to avoid stale closure issues
  const startPolling = useCallback(() => {
    // Get current taskId from ref to avoid stale closure
    const currentTaskId = taskIdRef.current;
    
    // #region agent log
    // [DEBUG] Log startPolling entry - tests stale closure hypothesis
    fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:startPolling:entry',message:'startPolling called',data:{taskIdFromRef:currentTaskId,taskIdFromClosure:taskId,isGenerating,alreadyPolling:!!pollIntervalRef.current,willEarlyReturn:!!pollIntervalRef.current||!currentTaskId||!isGenerating},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'A-polling'})}).catch(()=>{});
    // #endregion
    if (pollIntervalRef.current) return; // Already polling
    if (!currentTaskId || !isGenerating) return;

    console.log('📊 Starting polling fallback');
    // #region agent log
    // [DEBUG] Log polling actually started
    fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:startPolling:started',message:'Polling interval started',data:{taskId:currentTaskId},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'A-polling'})}).catch(()=>{});
    // #endregion
    pollIntervalRef.current = setInterval(async () => {
      try {
        // Use ref for current taskId in interval callback as well
        const pollingTaskId = taskIdRef.current;
        if (!pollingTaskId) return;
        
        const status = await documentGenerationApi.getTaskStatus(pollingTaskId);
        // #region agent log
        // [DEBUG] Log polling response
        fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:polling:response',message:'Polling got status',data:{taskId:pollingTaskId,status:status.status,progress:status.progress,hasResult:!!status.result,error:status.error},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'polling'})}).catch(()=>{});
        // #endregion
        setTaskInfo(status);

        if (status.status === 'completed') {
          handleGenerationComplete(status.result);
        } else if (status.status === 'failed') {
          handleGenerationError(status.error || 'Unknown error');
        }
      } catch (error) {
        console.error('Error polling task status:', error);
        // #region agent log
        // [DEBUG] Log polling error
        fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:polling:error',message:'Polling failed',data:{error:String(error)},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'polling'})}).catch(()=>{});
        // #endregion
      }
    }, 2000);
  }, [isGenerating]); // Removed taskId from deps since we use ref now

  // Cleanup polling on unmount or when generation ends
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, []);

  const handleGenerationComplete = async (result: any) => {
    // #region agent log
    // [DEBUG] Log entry to handleGenerationComplete - tests hypothesis D
    fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:handleGenerationComplete:entry',message:'handleGenerationComplete called',data:{hasResult:!!result,hasContent:!!result?.content,outputOption,contentLength:result?.content?.length||0},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'D'})}).catch(()=>{});
    // #endregion
    setIsGenerating(false);

    // Clear polling
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    const content = result?.content;
    if (content) {
      // #region agent log
      // [DEBUG] Log content branch taken
      fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:handleGenerationComplete:hasContent',message:'Content found, outputOption branch',data:{outputOption,willOpenEditor:outputOption==='editor'},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
      if (outputOption === 'editor') {
        onGenerated(content, true);
        toast.success('Document generated! Opening in editor...');
      } else {
        // Save to document
        try {
          await documentGenerationApi.saveContent(
            document.id,
            content,
            result?.quality_score
          );
          toast.success('Document generated and saved!');
          onUpdate();
        } catch (error) {
          console.error('Error saving content:', error);
          toast.error('Document generated but failed to save');
        }
      }
    } else {
      // #region agent log
      // [DEBUG] Log fallback to API fetch - tests hypothesis D
      fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:handleGenerationComplete:noContent',message:'No content in result, fetching from API',data:{taskId},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
      // No content in WebSocket message, fetch from API
      try {
        const status = await documentGenerationApi.getTaskStatus(taskId!);
        if (status.result?.content) {
          await handleGenerationComplete(status.result);
        }
      } catch (error) {
        console.error('Error fetching final result:', error);
      }
    }
  };

  const handleGenerationError = (errorMessage: string) => {
    setIsGenerating(false);
    // Clear taskId ref to reset state
    taskIdRef.current = null;

    // Clear polling
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    toast.error(`Generation failed: ${errorMessage}`);
  };

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
    // #region agent log
    // [DEBUG] Log handleGenerate entry
    fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:handleGenerate:entry',message:'handleGenerate called',data:{canGenerate:dependencyCheck?.can_generate,documentId:document.id},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'flow'})}).catch(()=>{});
    // #endregion
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

      // #region agent log
      // [DEBUG] Log before API call
      fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:handleGenerate:beforeApi',message:'About to call generate API',data:{documentId:document.id,assumptionsCount:assumptions.length},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'flow'})}).catch(()=>{});
      // #endregion
      const response = await documentGenerationApi.generate(
        document.id,
        assumptions,
        additionalContext || undefined
      );

      // #region agent log
      // [DEBUG] Log when task ID is set - tests hypothesis A (stale closure timing)
      fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:handleGenerate:taskIdSet',message:'Task ID received from API',data:{newTaskId:response.task_id,previousTaskId:taskId},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
      // Update both state and ref - ref is used to avoid stale closure in startPolling
      taskIdRef.current = response.task_id;
      setTaskId(response.task_id);
      toast.info(`Generating ${document.document_name}...`);
    } catch (error: any) {
      // #region agent log
      // [DEBUG] Log API error
      fetch('http://127.0.0.1:7244/ingest/9015424d-319b-4106-b807-78d5a4f24cad',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'DocumentGenerateTab.tsx:handleGenerate:catch',message:'API call failed',data:{errorMessage:error?.message,errorName:error?.name},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'API-error'})}).catch(()=>{});
      // #endregion
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
                <div className="flex items-center gap-3">
                  <span className="text-sm text-blue-700">{taskInfo.progress}%</span>
                  {/* WebSocket status indicator */}
                  <div className="flex items-center gap-1" title={wsConnected ? 'Real-time updates' : 'Polling for updates'}>
                    {wsConnected ? (
                      <Wifi className="h-4 w-4 text-green-600" />
                    ) : (
                      <WifiOff className="h-4 w-4 text-slate-400" />
                    )}
                  </div>
                </div>
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
              <div
                className="text-sm text-slate-700 prose prose-sm prose-slate max-w-none [&>h1]:text-base [&>h1]:font-semibold [&>h2]:text-sm [&>h2]:font-semibold [&>h3]:text-sm [&>p]:my-1"
                dangerouslySetInnerHTML={{
                  __html: markdownToHtml(document.generated_content?.substring(0, 1000) || '')
                }}
              />
              {(document.generated_content?.length || 0) > 1000 && (
                <span className="text-slate-400 text-sm">...</span>
              )}
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
