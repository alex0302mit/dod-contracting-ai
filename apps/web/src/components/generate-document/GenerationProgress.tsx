/**
 * GenerationProgress - Step 3 of the Generate Document wizard.
 * Polls generation status and auto-navigates to editor on completion.
 */

import { useState, useEffect, useRef } from 'react';
import { Loader2, CheckCircle2, XCircle, FileText, Sparkles, Shield } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { standaloneApi } from '@/services/api';
import { useNavigation } from '@/contexts/NavigationContext';
import { convertSectionsToHtml } from '@/lib/markdownToHtml';
import { toast } from 'sonner';

interface GenerationProgressProps {
  taskId: string;
  documentNames: string[];
}

export function GenerationProgress({ taskId, documentNames }: GenerationProgressProps) {
  const { navigateToEditor } = useNavigation();
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('Initializing...');
  const [status, setStatus] = useState<'pending' | 'in_progress' | 'completed' | 'failed'>('pending');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    pollRef.current = setInterval(async () => {
      try {
        const statusData = await standaloneApi.getGenerationStatus(taskId);
        setProgress(statusData.progress);
        setMessage(statusData.message || '');
        setStatus(statusData.status);

        if (statusData.status === 'completed' && statusData.result) {
          if (pollRef.current) clearInterval(pollRef.current);

          const htmlSections = convertSectionsToHtml(statusData.result.sections);
          toast.success('Documents generated successfully!');
          navigateToEditor(htmlSections);
        } else if (statusData.status === 'failed') {
          if (pollRef.current) clearInterval(pollRef.current);
          toast.error(statusData.message || 'Generation failed');
        }
      } catch (err: any) {
        console.error('Poll error:', err);
        // Don't stop polling on transient errors
      }
    }, 2000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [taskId, navigateToEditor]);

  const dots = '.'.repeat(((Date.now() / 500) | 0) % 4);

  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center space-y-8 max-w-lg px-4">
        {status === 'failed' ? (
          <>
            <XCircle className="h-16 w-16 text-destructive mx-auto" />
            <h2 className="text-2xl font-bold">Generation Failed</h2>
            <p className="text-muted-foreground">{message}</p>
          </>
        ) : (
          <>
            <div className="relative">
              <Loader2 className="h-16 w-16 animate-spin text-primary mx-auto" />
              {status === 'completed' && (
                <CheckCircle2 className="h-16 w-16 text-emerald-500 mx-auto absolute inset-0" />
              )}
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Generating Documents</h2>
              <p className="text-muted-foreground">
                {message}{dots}
              </p>
            </div>

            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-muted-foreground">{progress}% complete</p>
            </div>

            <div className="space-y-2">
              {documentNames.map(name => (
                <div key={name} className="flex items-center gap-2 text-sm text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  <span>{name}</span>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-3 mt-6">
              <div className="p-3 rounded-lg border bg-card">
                <FileText className="h-6 w-6 text-blue-500 mx-auto mb-1" />
                <div className="text-xs font-medium">Context</div>
              </div>
              <div className="p-3 rounded-lg border bg-card">
                <Sparkles className="h-6 w-6 text-violet-500 mx-auto mb-1" />
                <div className="text-xs font-medium">Generating</div>
              </div>
              <div className="p-3 rounded-lg border bg-card">
                <Shield className="h-6 w-6 text-emerald-500 mx-auto mb-1" />
                <div className="text-xs font-medium">Validating</div>
              </div>
            </div>

            <p className="text-xs text-muted-foreground">
              This usually takes 30-90 seconds per document
            </p>
          </>
        )}
      </div>
    </div>
  );
}
