/**
 * Guided Flow Panel
 *
 * Sidebar button/panel for launching guided completion flow.
 * Shows progress indicator and quick access to start guided mode.
 */

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Compass,
  Play,
  CheckCircle2,
  Clock,
  Sparkles
} from 'lucide-react';
import { GuidedFlowDialog } from './GuidedFlowDialog';
import type { GuidedDocument, User } from '@/types/guidedFlow';

interface GuidedFlowPanelProps {
  document: GuidedDocument;
  currentUser: User;
  initialValues?: Record<string, any>;
  onSave?: (values: Record<string, any>) => Promise<void>;
  onComplete?: (values: Record<string, any>) => void;
  documentPreview?: React.ReactNode;
  progress?: {
    completed: number;
    total: number;
    percentage: number;
  };
}

export function GuidedFlowPanel({
  document,
  currentUser,
  initialValues,
  onSave,
  onComplete,
  documentPreview,
  progress
}: GuidedFlowPanelProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Calculate progress (use provided or default)
  const completedFields = progress?.completed || 0;
  const totalFields = progress?.total || document.sections.flatMap(s => s.fields).filter(f => f.required).length;
  const percentage = progress?.percentage || (totalFields > 0 ? Math.round((completedFields / totalFields) * 100) : 0);

  const isComplete = percentage === 100;
  const isInProgress = completedFields > 0 && !isComplete;
  const isNotStarted = completedFields === 0;

  return (
    <>
      {/* Launcher Card */}
      <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-cyan-50">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                <Compass className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <CardTitle className="text-base">Guided Completion</CardTitle>
                <CardDescription className="text-xs">
                  Step-by-step field walkthrough
                </CardDescription>
              </div>
            </div>
            {isComplete && (
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Progress Indicator */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Progress</span>
              <span className="font-semibold text-slate-900">
                {completedFields} / {totalFields} fields
              </span>
            </div>
            <Progress value={percentage} className="h-2" />
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>{percentage}% complete</span>
              {!isComplete && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {totalFields - completedFields} remaining
                </span>
              )}
            </div>
          </div>

          {/* Status Badge */}
          <div className="flex items-center gap-2">
            {isComplete && (
              <Badge className="bg-green-100 text-green-800 border-green-300">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Complete
              </Badge>
            )}
            {isInProgress && (
              <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-300">
                <Play className="h-3 w-3 mr-1" />
                In Progress
              </Badge>
            )}
            {isNotStarted && (
              <Badge variant="outline" className="border-slate-300">
                Not Started
              </Badge>
            )}
          </div>

          {/* Features List */}
          <div className="space-y-1.5 pt-2 border-t">
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <Sparkles className="h-3 w-3 text-purple-600" />
              <span>AI-powered field suggestions</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <CheckCircle2 className="h-3 w-3 text-green-600" />
              <span>Real-time validation</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <Clock className="h-3 w-3 text-blue-600" />
              <span>Auto-save on completion</span>
            </div>
          </div>

          {/* Launch Button */}
          <Button
            onClick={() => setIsDialogOpen(true)}
            className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700"
            size="lg"
          >
            {isNotStarted && (
              <>
                <Play className="h-4 w-4 mr-2" />
                Start Guided Mode
              </>
            )}
            {isInProgress && (
              <>
                <Play className="h-4 w-4 mr-2" />
                Continue Guided Mode
              </>
            )}
            {isComplete && (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Review Completion
              </>
            )}
          </Button>

          {/* Help Text */}
          <p className="text-xs text-center text-slate-500">
            We'll guide you through each field with helpful tips and smart suggestions
          </p>
        </CardContent>
      </Card>

      {/* Guided Flow Dialog */}
      <GuidedFlowDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        document={document}
        currentUser={currentUser}
        initialValues={initialValues}
        onSave={onSave}
        onComplete={onComplete}
        documentPreview={documentPreview}
      />
    </>
  );
}
