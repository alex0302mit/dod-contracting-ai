/**
 * ExtractionProgress Component
 * 
 * Step 2 of the Quick Generate wizard - shows AI extraction progress.
 * Features:
 * - Animated progress bar
 * - Step checklist with completion status
 * - Real-time assumption count preview
 * - Cancel functionality
 * 
 * Dependencies:
 * - Shadcn UI components for styling
 * - Types from ./types.ts
 */

import { useEffect, useState } from "react";
import {
  Loader2,
  CheckCircle2,
  Circle,
  FileSearch,
  Sparkles,
  GitBranch,
  AlertCircle,
  X
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ExtractionProgressProps } from "./types";

/**
 * Configuration for extraction steps shown in the checklist
 */
interface ExtractionStep {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const EXTRACTION_STEPS: ExtractionStep[] = [
  {
    id: 'upload',
    label: 'Uploading documents',
    description: 'Transferring files to processing server',
    icon: <FileSearch className="h-4 w-4" />
  },
  {
    id: 'chunking',
    label: 'Chunking and indexing',
    description: 'Breaking documents into searchable segments',
    icon: <GitBranch className="h-4 w-4" />
  },
  {
    id: 'extracting',
    label: 'Extracting assumptions',
    description: 'AI analyzing content for key information',
    icon: <Sparkles className="h-4 w-4" />
  },
  {
    id: 'mapping',
    label: 'Mapping to requirements',
    description: 'Linking to FAR/DFARS requirements',
    icon: <GitBranch className="h-4 w-4" />
  }
];

/**
 * ExtractionProgress displays the progress of AI document analysis.
 * Shows a visual checklist of steps and real-time progress.
 */
export function ExtractionProgress({
  progress,
  statusMessage,
  assumptionsFound,
  onCancel
}: ExtractionProgressProps) {
  // Determine which step is currently active based on progress
  const getCurrentStep = (): number => {
    if (progress < 25) return 0;
    if (progress < 50) return 1;
    if (progress < 75) return 2;
    if (progress < 100) return 3;
    return 4; // All complete
  };

  const currentStep = getCurrentStep();

  // Animated dots for loading indicator
  const [dots, setDots] = useState('');
  
  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8 py-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Analyzing Documents</h2>
        <p className="text-muted-foreground">
          Our AI is extracting key information from your uploaded documents.
        </p>
      </div>

      {/* Main Progress Card */}
      <Card className="max-w-xl mx-auto">
        <CardContent className="py-8">
          {/* Animated Icon */}
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="h-20 w-20 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center">
                <Loader2 className="h-10 w-10 text-blue-600 animate-spin" />
              </div>
              {/* Pulse effect */}
              <div className="absolute inset-0 h-20 w-20 rounded-full bg-blue-400 animate-ping opacity-20" />
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2 mb-6">
            <Progress value={progress} className="h-2" />
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">{statusMessage || 'Processing...'}</span>
              <span className="font-medium">{progress}%</span>
            </div>
          </div>

          {/* Assumptions Found Preview */}
          {assumptionsFound > 0 && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-emerald-100 flex items-center justify-center">
                  <Sparkles className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <p className="font-medium text-emerald-800">
                    {assumptionsFound} assumptions identified
                  </p>
                  <p className="text-sm text-emerald-600">
                    More may be found as analysis continues{dots}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Step Checklist */}
          <div className="space-y-3">
            {EXTRACTION_STEPS.map((step, index) => {
              const isComplete = index < currentStep;
              const isActive = index === currentStep;
              const isPending = index > currentStep;

              return (
                <div
                  key={step.id}
                  className={`
                    flex items-center gap-3 p-3 rounded-lg transition-all
                    ${isActive ? 'bg-blue-50 border border-blue-200' : ''}
                    ${isComplete ? 'bg-green-50' : ''}
                    ${isPending ? 'opacity-50' : ''}
                  `}
                >
                  {/* Status Icon */}
                  <div className={`
                    h-8 w-8 rounded-full flex items-center justify-center
                    ${isComplete ? 'bg-green-500 text-white' : ''}
                    ${isActive ? 'bg-blue-500 text-white' : ''}
                    ${isPending ? 'bg-slate-200 text-slate-400' : ''}
                  `}>
                    {isComplete ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : isActive ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Circle className="h-4 w-4" />
                    )}
                  </div>

                  {/* Step Info */}
                  <div className="flex-1">
                    <p className={`font-medium text-sm ${
                      isComplete ? 'text-green-700' : 
                      isActive ? 'text-blue-700' : 
                      'text-slate-500'
                    }`}>
                      {step.label}
                      {isActive && dots}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {step.description}
                    </p>
                  </div>

                  {/* Step Icon */}
                  <div className={`
                    ${isComplete ? 'text-green-500' : ''}
                    ${isActive ? 'text-blue-500' : ''}
                    ${isPending ? 'text-slate-300' : ''}
                  `}>
                    {step.icon}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Cancel Button */}
      <div className="flex justify-center">
        <Button
          variant="outline"
          onClick={onCancel}
          className="gap-2 text-slate-600"
        >
          <X className="h-4 w-4" />
          Cancel Processing
        </Button>
      </div>

      {/* Helpful Tips */}
      <div className="max-w-xl mx-auto">
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 shrink-0" />
          <div>
            <p className="font-medium text-amber-800 text-sm">Processing Tips</p>
            <ul className="text-sm text-amber-700 mt-1 space-y-1 list-disc list-inside">
              <li>Larger documents take longer to analyze</li>
              <li>PDFs with text extraction issues may have fewer assumptions</li>
              <li>You can edit and add assumptions in the next step</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * GenerationProgress Component
 * 
 * Variant of ExtractionProgress for the document generation phase.
 * Shows progress of AI document generation with section-by-section updates.
 */
export interface GenerationProgressProps {
  progress: number;
  currentDocument: string;
  completedDocuments: string[];
  totalDocuments: number;
  onCancel: () => void;
}

export function GenerationProgress({
  progress,
  currentDocument,
  completedDocuments,
  totalDocuments,
  onCancel
}: GenerationProgressProps) {
  // Animated dots for loading indicator
  const [dots, setDots] = useState('');
  
  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8 py-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Generating Documents</h2>
        <p className="text-muted-foreground">
          AI agents are creating your contracting package based on your assumptions and selections.
        </p>
      </div>

      {/* Main Progress Card */}
      <Card className="max-w-2xl mx-auto">
        <CardContent className="py-8">
          {/* Animated Icon */}
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="h-20 w-20 rounded-full bg-gradient-to-br from-emerald-100 to-emerald-200 flex items-center justify-center">
                <Sparkles className="h-10 w-10 text-emerald-600 animate-pulse" />
              </div>
              {/* Pulse effect */}
              <div className="absolute inset-0 h-20 w-20 rounded-full bg-emerald-400 animate-ping opacity-20" />
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2 mb-6">
            <Progress value={progress} className="h-3" />
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">
                Generating: {currentDocument}{dots}
              </span>
              <span className="font-medium">{progress}%</span>
            </div>
          </div>

          {/* Document Progress */}
          <div className="bg-slate-50 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <p className="font-medium text-sm">Document Progress</p>
              <p className="text-sm text-muted-foreground">
                {completedDocuments.length} of {totalDocuments} complete
              </p>
            </div>

            {/* Completed Documents List */}
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {completedDocuments.map((doc) => (
                <div
                  key={doc}
                  className="flex items-center gap-2 p-2 bg-green-50 rounded-md"
                >
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span className="text-sm text-green-700">{doc}</span>
                </div>
              ))}
              
              {/* Current Document */}
              {currentDocument && (
                <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-md">
                  <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
                  <span className="text-sm text-blue-700">{currentDocument}</span>
                </div>
              )}
            </div>
          </div>

          {/* Estimated Time */}
          <div className="text-center text-sm text-muted-foreground">
            Estimated time remaining: {Math.max(1, Math.ceil((100 - progress) / 10))} min
          </div>
        </CardContent>
      </Card>

      {/* Cancel Button */}
      <div className="flex justify-center">
        <Button
          variant="outline"
          onClick={onCancel}
          className="gap-2 text-slate-600"
        >
          <X className="h-4 w-4" />
          Cancel Generation
        </Button>
      </div>
    </div>
  );
}
