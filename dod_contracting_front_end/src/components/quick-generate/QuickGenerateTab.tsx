/**
 * QuickGenerateTab Component
 * 
 * Main container for the Quick Generate wizard that orchestrates:
 * - Step 1: Upload source documents
 * - Step 2: AI extraction (processing state)
 * - Steps 3-5: DocumentWorkflow (Assumptions, Traceability, Selection)
 * - Step 6: Generation and Review
 * 
 * Features:
 * - Visual progress stepper showing current position
 * - State persistence across steps
 * - Integration with existing DocumentWorkflow component
 * - Generation progress with real-time updates
 * 
 * Dependencies:
 * - QuickUploadStep, ExtractionProgress, QuickReviewStep components
 * - DocumentWorkflow for steps 3-5
 * - ragApi for backend communication
 * - Shadcn UI components
 */

import { useState, useCallback, useEffect } from "react";
import {
  Upload,
  FileSearch,
  GitBranch,
  FileText,
  Sparkles,
  Check,
  ArrowLeft
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { ragApi } from "@/services/api";
import { convertSectionsToHtml } from "@/lib/markdownToHtml";

// Import sub-components
import { QuickUploadStep } from "./QuickUploadStep";
import { ExtractionProgress, GenerationProgress } from "./ExtractionProgress";
import { QuickReviewStep } from "./QuickReviewStep";

// Import types
import {
  QuickGenerateStep,
  QuickGenerateTabProps,
  UploadedFile,
  Assumption,
  GeneratedDocument,
  WIZARD_STEPS
} from "./types";

// Import the existing DocumentWorkflow component
import { DocumentWorkflow } from "@/components/DocumentWorkflow";

/**
 * Step configuration for the progress stepper
 */
interface StepperConfig {
  step: QuickGenerateStep;
  number: number;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const STEPPER_CONFIG: StepperConfig[] = [
  { step: 'UPLOAD', number: 1, title: 'Upload', description: 'Add source documents', icon: <Upload className="h-5 w-5" /> },
  { step: 'ASSUMPTIONS', number: 2, title: 'Assumptions', description: 'Review extracted data', icon: <FileSearch className="h-5 w-5" /> },
  { step: 'TRACEABILITY', number: 3, title: 'Traceability', description: 'Map to requirements', icon: <GitBranch className="h-5 w-5" /> },
  { step: 'SELECTION', number: 4, title: 'Documents', description: 'Select output types', icon: <FileText className="h-5 w-5" /> },
  { step: 'REVIEW', number: 5, title: 'Generate', description: 'Review & export', icon: <Sparkles className="h-5 w-5" /> },
];

/**
 * Map QuickGenerateStep to DocumentWorkflow step number
 */
const stepToWorkflowStep = (step: QuickGenerateStep): 1 | 2 | 3 | null => {
  switch (step) {
    case 'ASSUMPTIONS': return 1;
    case 'TRACEABILITY': return 2;
    case 'SELECTION': return 3;
    default: return null;
  }
};

/**
 * QuickGenerateTab orchestrates the complete Quick Generate wizard flow.
 */
export function QuickGenerateTab({ onOpenEditor, onComplete }: QuickGenerateTabProps) {
  // ============================================
  // State Management
  // ============================================
  
  // Current wizard step
  const [currentStep, setCurrentStep] = useState<QuickGenerateStep>('UPLOAD');
  
  // Step 1: Upload state
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [userContext, setUserContext] = useState('');
  
  // Step 2: Extraction state
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionProgress, setExtractionProgress] = useState(0);
  const [extractionStatus, setExtractionStatus] = useState('');
  
  // Steps 3-5: DocumentWorkflow state
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [planLocked, setPlanLocked] = useState(false);
  
  // Step 6: Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [currentGeneratingDoc, setCurrentGeneratingDoc] = useState('');
  const [completedDocs, setCompletedDocs] = useState<string[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<GeneratedDocument[]>([]);
  
  // Final results
  const [generatedSections, setGeneratedSections] = useState<Record<string, string>>({});
  const [qualityAnalysis, setQualityAnalysis] = useState<Record<string, any>>({});

  // ============================================
  // Step Navigation Helpers
  // ============================================
  
  /**
   * Get the numeric index of a step for progress calculation
   */
  const getStepIndex = (step: QuickGenerateStep): number => {
    const index = STEPPER_CONFIG.findIndex(s => s.step === step);
    // Handle intermediate states
    if (step === 'EXTRACTING') return 0.5;
    if (step === 'GENERATING') return 4.5;
    return index;
  };

  /**
   * Check if a step is complete
   */
  const isStepComplete = (step: QuickGenerateStep): boolean => {
    const currentIndex = getStepIndex(currentStep);
    const targetIndex = getStepIndex(step);
    return targetIndex < currentIndex;
  };

  /**
   * Check if a step is the current step
   */
  const isCurrentStep = (step: QuickGenerateStep): boolean => {
    // Handle intermediate states
    if (currentStep === 'EXTRACTING' && step === 'UPLOAD') return true;
    if (currentStep === 'GENERATING' && step === 'REVIEW') return true;
    return currentStep === step;
  };

  // ============================================
  // Upload Handlers (Step 1)
  // ============================================
  
  /**
   * Handle files being added (either new or updated)
   */
  const handleFilesAdded = useCallback((newFiles: UploadedFile[]) => {
    setUploadedFiles(prev => {
      const updated = [...prev];
      newFiles.forEach(newFile => {
        const existingIndex = updated.findIndex(f => f.id === newFile.id);
        if (existingIndex >= 0) {
          updated[existingIndex] = newFile;
        } else {
          updated.push(newFile);
        }
      });
      return updated;
    });
  }, []);

  /**
   * Handle file removal
   */
  const handleFileRemoved = useCallback((fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  }, []);

  // ============================================
  // Extraction Handlers (Step 2)
  // ============================================
  
  /**
   * Start the extraction process
   */
  const handleStartExtraction = async () => {
    setIsExtracting(true);
    setCurrentStep('EXTRACTING');
    setExtractionProgress(0);
    setExtractionStatus('Starting extraction...');

    try {
      // Simulate progress updates (actual progress comes from backend polling)
      const progressInterval = setInterval(() => {
        setExtractionProgress(prev => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 15;
        });
      }, 500);

      setExtractionStatus('Analyzing documents...');
      setExtractionProgress(30);

      // Call the extraction API
      const result = await ragApi.extractAssumptions();
      
      clearInterval(progressInterval);
      setExtractionProgress(100);
      setExtractionStatus('Complete!');

      // Set extracted assumptions
      const extractedAssumptions: Assumption[] = result.assumptions.map((a: any, idx: number) => ({
        id: a.id || `a${idx + 1}`,
        text: a.text,
        source: a.source || 'Extracted from documents',
        status: 'needs_review' as const
      }));

      setAssumptions(extractedAssumptions);
      
      toast.success(`Extracted ${extractedAssumptions.length} assumptions from ${result.documents_analyzed} documents`);
      
      // Move to assumptions step
      setTimeout(() => {
        setCurrentStep('ASSUMPTIONS');
        setIsExtracting(false);
      }, 500);

    } catch (error: any) {
      console.error('Extraction error:', error);
      toast.error(`Extraction failed: ${error.message}`);
      setCurrentStep('UPLOAD');
      setIsExtracting(false);
    }
  };

  /**
   * Cancel extraction
   */
  const handleCancelExtraction = () => {
    setIsExtracting(false);
    setCurrentStep('UPLOAD');
    setExtractionProgress(0);
    toast.info('Extraction cancelled');
  };

  // ============================================
  // DocumentWorkflow Integration (Steps 3-5)
  // ============================================
  
  /**
   * Handle back navigation from DocumentWorkflow
   */
  const handleWorkflowBack = () => {
    // If in assumptions step, go back to upload
    if (currentStep === 'ASSUMPTIONS') {
      setCurrentStep('UPLOAD');
    }
  };

  /**
   * Handle plan lock
   */
  const handleLockPlan = () => {
    setPlanLocked(true);
  };

  /**
   * Handle plan unlock
   */
  const handleUnlockPlan = () => {
    setPlanLocked(false);
  };

  /**
   * Handle document generation trigger from DocumentWorkflow
   */
  const handleGenerate = async (docs: GeneratedDocument[]) => {
    setSelectedDocuments(docs);
    setCurrentStep('GENERATING');
    setIsGenerating(true);
    setGenerationProgress(0);
    setCompletedDocs([]);

    try {
      // Start generation
      const response = await ragApi.generateDocuments({
        assumptions: assumptions.map(a => ({
          id: a.id,
          text: a.text,
          source: a.source
        })),
        documents: docs.map(doc => ({
          name: doc.name,
          section: doc.section,
          category: doc.category,
          linkedAssumptions: doc.linkedAssumptions,
        })),
      });

      toast.success(`Generating ${response.documents_requested} documents...`);

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const status = await ragApi.getGenerationStatus(response.task_id);
          setGenerationProgress(status.progress);

          // Update current document being generated
          if (status.current_document) {
            setCurrentGeneratingDoc(status.current_document);
          }

          // Track completed documents
          if (status.completed_documents) {
            setCompletedDocs(status.completed_documents);
          }

          if (status.status === 'completed' && status.result) {
            clearInterval(pollInterval);
            
            // Convert markdown sections to HTML for display
            const htmlSections = convertSectionsToHtml(status.result.sections);
            setGeneratedSections(htmlSections);

            // Store quality analysis if available
            if (status.result.quality_analysis) {
              setQualityAnalysis(status.result.quality_analysis);
            }

            setIsGenerating(false);
            setCurrentStep('REVIEW');
            toast.success("Documents generated successfully!");
            
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setIsGenerating(false);
            setCurrentStep('SELECTION');
            toast.error(status.message || "Document generation failed");
          }
        } catch (error: any) {
          clearInterval(pollInterval);
          setIsGenerating(false);
          setCurrentStep('SELECTION');
          toast.error(`Generation error: ${error.message}`);
        }
      }, 2000);

    } catch (error: any) {
      console.error('Generation error:', error);
      toast.error(`Failed to start generation: ${error.message}`);
      setIsGenerating(false);
      setCurrentStep('SELECTION');
    }
  };

  /**
   * Cancel generation
   */
  const handleCancelGeneration = () => {
    setIsGenerating(false);
    setCurrentStep('SELECTION');
    toast.info('Generation cancelled');
  };

  // ============================================
  // Review Handlers (Step 6)
  // ============================================
  
  /**
   * Open generated content in full editor
   */
  const handleOpenInEditor = () => {
    onOpenEditor(generatedSections);
    if (onComplete) {
      onComplete(generatedSections);
    }
  };

  /**
   * Download generated package
   */
  const handleDownload = async () => {
    // For now, just show a toast - actual download would use export API
    toast.info('Download feature coming soon - use "Open in Editor" then Export');
  };

  /**
   * Go back from review to selection
   */
  const handleBackFromReview = () => {
    setCurrentStep('SELECTION');
  };

  /**
   * Regenerate documents
   */
  const handleRegenerate = () => {
    if (selectedDocuments.length > 0) {
      handleGenerate(selectedDocuments);
    }
  };

  // ============================================
  // Render: Progress Stepper
  // ============================================
  
  const renderStepper = () => (
    <div className="mb-8 p-6 rounded-2xl bg-gradient-to-br from-slate-100/80 to-white/60 backdrop-blur-sm border border-white/40 shadow-lg">
      <div className="flex items-center justify-between relative px-4">
        {/* Connector line background */}
        <div className="absolute top-1/2 left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-slate-200 via-slate-300 to-slate-200 -translate-y-1/2 -z-10" />
        
        {/* Progress line fill */}
        <div 
          className="absolute top-1/2 left-[10%] h-0.5 bg-gradient-to-r from-blue-400 via-blue-500 to-emerald-400 -translate-y-1/2 -z-10 transition-all duration-700 ease-out"
          style={{ 
            width: `${Math.min(getStepIndex(currentStep) / (STEPPER_CONFIG.length - 1) * 80, 80)}%`,
            boxShadow: '0 0 12px rgba(59, 130, 246, 0.5), 0 0 4px rgba(59, 130, 246, 0.3)'
          }}
        />

        {STEPPER_CONFIG.map((config) => {
          const isActive = isCurrentStep(config.step);
          const isCompleted = isStepComplete(config.step);

          return (
            <div
              key={config.step}
              className={`
                relative flex flex-col items-center p-3 rounded-xl transition-all duration-300 min-w-[100px]
                ${isActive 
                  ? 'bg-white/90 shadow-xl shadow-blue-500/20 scale-105 border border-blue-200/60 -translate-y-1' 
                  : isCompleted
                  ? 'bg-white/70 border border-emerald-200/40'
                  : 'bg-white/30 border border-transparent opacity-60'}
              `}
            >
              {/* Step Icon */}
              <div className={`
                w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300
                ${isActive
                  ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/40'
                  : isCompleted
                  ? 'bg-gradient-to-br from-emerald-400 to-emerald-500 text-white shadow-md shadow-emerald-500/30'
                  : 'bg-slate-100 text-slate-400'}
              `}>
                {isCompleted ? <Check className="h-5 w-5" /> : config.icon}
              </div>

              {/* Step Label */}
              <p className={`mt-2 font-semibold text-xs transition-colors ${
                isActive ? 'text-blue-600' : isCompleted ? 'text-emerald-600' : 'text-slate-500'
              }`}>
                {config.title}
              </p>
              <p className="text-[10px] text-muted-foreground text-center">
                {config.description}
              </p>

              {/* Active indicator */}
              {isActive && (
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  // ============================================
  // Render: Main Content
  // ============================================
  
  const renderContent = () => {
    // Step 1: Upload
    if (currentStep === 'UPLOAD') {
      return (
        <QuickUploadStep
          uploadedFiles={uploadedFiles}
          onFilesAdded={handleFilesAdded}
          onFileRemoved={handleFileRemoved}
          userContext={userContext}
          onContextChange={setUserContext}
          onContinue={handleStartExtraction}
          isExtracting={isExtracting}
        />
      );
    }

    // Step 2: Extracting (processing state)
    if (currentStep === 'EXTRACTING') {
      return (
        <ExtractionProgress
          progress={extractionProgress}
          statusMessage={extractionStatus}
          assumptionsFound={assumptions.length}
          onCancel={handleCancelExtraction}
        />
      );
    }

    // Steps 3-5: DocumentWorkflow (Assumptions, Traceability, Selection)
    if (currentStep === 'ASSUMPTIONS' || currentStep === 'TRACEABILITY' || currentStep === 'SELECTION') {
      return (
        <DocumentWorkflow
          assumptions={assumptions}
          setAssumptions={setAssumptions}
          locked={planLocked}
          onLock={handleLockPlan}
          onUnlock={handleUnlockPlan}
          onGenerate={handleGenerate}
          onBack={handleWorkflowBack}
        />
      );
    }

    // Step 6a: Generating (processing state)
    if (currentStep === 'GENERATING') {
      return (
        <GenerationProgress
          progress={generationProgress}
          currentDocument={currentGeneratingDoc}
          completedDocuments={completedDocs}
          totalDocuments={selectedDocuments.length}
          onCancel={handleCancelGeneration}
        />
      );
    }

    // Step 6b: Review
    if (currentStep === 'REVIEW') {
      return (
        <QuickReviewStep
          sections={generatedSections}
          qualityAnalysis={qualityAnalysis}
          onOpenEditor={handleOpenInEditor}
          onDownload={handleDownload}
          onBack={handleBackFromReview}
          onRegenerate={handleRegenerate}
        />
      );
    }

    return null;
  };

  // ============================================
  // Main Render
  // ============================================
  
  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
          Quick Package Generator
        </h1>
        <p className="text-muted-foreground mt-1">
          Generate a complete contracting package from your documents in minutes
        </p>
      </div>

      {/* Progress Stepper - hide during workflow steps as it has its own */}
      {!['ASSUMPTIONS', 'TRACEABILITY', 'SELECTION'].includes(currentStep) && renderStepper()}

      {/* Main Content */}
      <div className="min-h-[500px]">
        {renderContent()}
      </div>
    </div>
  );
}
