/**
 * DocumentWorkflow Component
 * 
 * A unified wizard-style workflow that combines:
 * - Step 1: Assumptions - Review and edit extracted assumptions
 * - Step 2: Traceability - Map assumptions to FAR/DFARS requirements
 * - Step 3: Generation Plan - Select documents to generate
 * 
 * Features:
 * - Visual progress stepper at the top
 * - Contextual previews of adjacent steps
 * - Smooth transitions between steps
 * - Persistent state across steps
 * 
 * Dependencies:
 * - Shadcn UI components
 * - Lucide icons
 * - ragApi for backend communication
 */

import { useState, useEffect, useMemo } from "react";
import {
  ArrowLeft, ArrowRight, Check, FileSearch, Plus, Trash2, Edit2,
  X, CheckCircle2, AlertCircle, Lock, Unlock, Sparkles, FileText,
  Minus, Circle, ChevronDown, ChevronUp, GitBranch
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { PhaseInfo } from "@/components/PhaseInfo";
import { ragApi } from "@/services/api";

// ============================================
// Type Definitions
// ============================================

interface Assumption {
  id: string;
  text: string;
  source: string;
  status?: 'approved' | 'needs_review';
}

interface GeneratedDocument {
  name: string;
  category: 'required' | 'recommended' | 'optional';
  description: string;
  justification: string;
  linkedAssumptions: string[];
  section?: string;
}

interface TraceMapping {
  assumption: Assumption;
  requirement: string;
  status: 'traced' | 'inferred' | 'needs_mapping';
  confidence: 'high' | 'medium' | 'low';
}

interface DocumentWorkflowProps {
  assumptions: Assumption[];
  setAssumptions: (assumptions: Assumption[]) => void;
  locked: boolean;
  onLock: () => void;
  onUnlock: () => void;
  onGenerate: (selectedDocs: GeneratedDocument[]) => void;
  onBack: () => void;
}

// Workflow step configuration
type WorkflowStep = 1 | 2 | 3;

const STEPS = [
  { number: 1, title: "Assumptions", description: "Review & edit extracted assumptions", icon: FileSearch },
  { number: 2, title: "Traceability", description: "Map to requirements", icon: GitBranch },
  { number: 3, title: "Generation Plan", description: "Select documents", icon: Sparkles },
] as const;

// ============================================
// Main Component
// ============================================

export function DocumentWorkflow({
  assumptions,
  setAssumptions,
  locked,
  onLock,
  onUnlock,
  onGenerate,
  onBack
}: DocumentWorkflowProps) {
  // Current step in the workflow
  const [currentStep, setCurrentStep] = useState<WorkflowStep>(1);
  
  // Step 1: Assumption editing state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [editSource, setEditSource] = useState("");
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [newText, setNewText] = useState("");
  const [newSource, setNewSource] = useState("");
  
  // Step 3: Document selection state
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [phaseAnalysis, setPhaseAnalysis] = useState<any>(null);
  const [analyzingPhase, setAnalyzingPhase] = useState(false);
  
  // Collapsed state for step previews
  const [showStepPreview, setShowStepPreview] = useState(true);

  // Generate document list based on assumptions - memoized to prevent unnecessary recalculations
  // Only recomputes when assumptions array changes
  const documentList = useMemo(() => generateDocumentList(assumptions), [assumptions]);
  
  // Initialize selected documents when documentList changes
  // Uses memoized documentList as dependency to ensure selection reflects
  // documents linked to current assumptions without causing infinite loops
  useEffect(() => {
    const initialSelection = new Set(
      documentList
        .filter(d => d.category === 'required' || d.category === 'recommended')
        .map(d => d.name)
    );
    setSelectedDocuments(initialSelection);
  }, [documentList]);

  // Analyze phase when selection changes (Step 3)
  useEffect(() => {
    if (currentStep !== 3) return;
    
    const analyzePhase = async () => {
      if (selectedDocuments.size === 0) {
        setPhaseAnalysis(null);
        return;
      }

      setAnalyzingPhase(true);
      try {
        const documentNames = Array.from(selectedDocuments);
        const response = await ragApi.analyzeGenerationPlan(documentNames);
        setPhaseAnalysis(response.analysis);
      } catch (error) {
        console.error('Error analyzing phase:', error);
        setPhaseAnalysis(null);
      } finally {
        setAnalyzingPhase(false);
      }
    };

    const timeoutId = setTimeout(analyzePhase, 500);
    return () => clearTimeout(timeoutId);
  }, [selectedDocuments, currentStep]);

  // Compute traceability data
  const traceData = assumptions.map(a => mapAssumptionToRequirement(a));

  // Navigate between steps
  const goToStep = (step: WorkflowStep) => {
    if (step < 1 || step > 3) return;
    setCurrentStep(step);
  };

  const nextStep = () => {
    if (currentStep < 3) {
      setCurrentStep((currentStep + 1) as WorkflowStep);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep((currentStep - 1) as WorkflowStep);
    }
  };

  // Check if step is completed
  const isStepCompleted = (step: number): boolean => {
    if (step === 1) return assumptions.length > 0;
    if (step === 2) return assumptions.length > 0;
    if (step === 3) return locked;
    return false;
  };

  // ============================================
  // Step 1: Assumptions Handlers
  // ============================================

  const startEdit = (assumption: Assumption) => {
    setEditingId(assumption.id);
    setEditText(assumption.text);
    setEditSource(assumption.source);
  };

  const saveEdit = () => {
    if (!editText.trim()) {
      toast.error("Assumption text cannot be empty");
      return;
    }
    setAssumptions(
      assumptions.map((a) =>
        a.id === editingId
          ? { ...a, text: editText.trim(), source: editSource.trim() }
          : a
      )
    );
    setEditingId(null);
    setEditText("");
    setEditSource("");
    toast.success("Assumption updated");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditText("");
    setEditSource("");
  };

  const deleteAssumption = (id: string) => {
    setAssumptions(assumptions.filter((a) => a.id !== id));
    toast.success("Assumption removed");
  };

  const toggleStatus = (id: string) => {
    setAssumptions(
      assumptions.map((a) => {
        if (a.id === id) {
          const newStatus = a.status === 'approved' ? 'needs_review' : 'approved';
          return { ...a, status: newStatus };
        }
        return a;
      })
    );
  };

  const addNewAssumption = () => {
    if (!newText.trim()) {
      toast.error("Assumption text cannot be empty");
      return;
    }
    const maxId = assumptions.reduce((max, a) => {
      const num = parseInt(a.id.replace('a', ''));
      return num > max ? num : max;
    }, 0);

    const newAssumption: Assumption = {
      id: `a${maxId + 1}`,
      text: newText.trim(),
      source: newSource.trim() || "User Added",
      status: 'needs_review'
    };

    setAssumptions([...assumptions, newAssumption]);
    setIsAddingNew(false);
    setNewText("");
    setNewSource("");
    toast.success("New assumption added");
  };

  const cancelAdd = () => {
    setIsAddingNew(false);
    setNewText("");
    setNewSource("");
  };

  // ============================================
  // Step 3: Document Selection Handlers
  // ============================================

  const toggleDocument = (docName: string) => {
    if (locked) return;
    const newSelection = new Set(selectedDocuments);
    if (newSelection.has(docName)) {
      newSelection.delete(docName);
    } else {
      newSelection.add(docName);
    }
    setSelectedDocuments(newSelection);
  };

  // ============================================
  // Statistics
  // ============================================

  const approvedCount = assumptions.filter(a => a.status === 'approved').length;
  const reviewCount = assumptions.filter(a => a.status === 'needs_review').length;
  const tracedCount = traceData.filter(t => t.status === 'traced').length;
  const inferredCount = traceData.filter(t => t.status === 'inferred').length;
  const needsMappingCount = traceData.filter(t => t.status === 'needs_mapping').length;
  const requiredCount = documentList.filter(d => d.category === 'required').length;
  const recommendedSelectedCount = documentList.filter(d => d.category === 'recommended' && selectedDocuments.has(d.name)).length;
  const optionalSelectedCount = documentList.filter(d => d.category === 'optional' && selectedDocuments.has(d.name)).length;

  // ============================================
  // Render
  // ============================================

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Editor
        </Button>
      </div>

      {/* Glass Morphism Progress Stepper */}
      <div className="mb-8 p-6 rounded-2xl bg-gradient-to-br from-slate-100/80 to-white/60 backdrop-blur-sm border border-white/40 shadow-lg">
        <div className="flex items-center justify-between relative px-4">
          {/* Connector line background - positioned behind step cards */}
          <div className="absolute top-1/2 left-[15%] right-[15%] h-0.5 bg-gradient-to-r from-slate-200 via-slate-300 to-slate-200 -translate-y-1/2 -z-10" />
          
          {/* Animated progress line fill with glow effect */}
          <div 
            className="absolute top-1/2 left-[15%] h-0.5 bg-gradient-to-r from-blue-400 via-blue-500 to-emerald-400 -translate-y-1/2 -z-10 transition-all duration-700 ease-out"
            style={{ 
              width: `${((currentStep - 1) / 2) * 70}%`,
              boxShadow: '0 0 12px rgba(59, 130, 246, 0.5), 0 0 4px rgba(59, 130, 246, 0.3)'
            }}
          />

          {STEPS.map((step) => {
            const Icon = step.icon;
            const isActive = currentStep === step.number;
            const isCompleted = currentStep > step.number || isStepCompleted(step.number);
            const isClickable = step.number <= currentStep || isStepCompleted(step.number - 1);

            return (
              <button
                key={step.number}
                onClick={() => isClickable && goToStep(step.number as WorkflowStep)}
                disabled={!isClickable}
                className={`relative flex flex-col items-center p-4 rounded-xl transition-all duration-300 min-w-[140px] ${
                  isActive 
                    ? 'bg-white/90 shadow-xl shadow-blue-500/20 scale-105 border border-blue-200/60 -translate-y-1' 
                    : isCompleted
                    ? 'bg-white/70 hover:bg-white/90 hover:shadow-lg border border-emerald-200/40'
                    : isClickable
                    ? 'bg-white/50 hover:bg-white/70 hover:shadow-md border border-transparent'
                    : 'bg-white/30 border border-transparent opacity-60 cursor-not-allowed'
                }`}
              >
                {/* Step Icon Container */}
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center transition-all duration-300 ${
                  isActive
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/40'
                    : isCompleted
                    ? 'bg-gradient-to-br from-emerald-400 to-emerald-500 text-white shadow-md shadow-emerald-500/30'
                    : 'bg-slate-100 text-slate-400'
                }`}>
                  {isCompleted && !isActive ? (
                    <Check className="h-6 w-6" />
                  ) : (
                    <Icon className="h-6 w-6" />
                  )}
                </div>

                {/* Step Label */}
                <p className={`mt-3 font-semibold text-sm transition-colors ${
                  isActive ? 'text-blue-600' : isCompleted ? 'text-emerald-600' : 'text-slate-500'
                }`}>
                  {step.title}
                </p>
                <p className="text-xs text-muted-foreground mt-1 text-center">
                  {step.description}
                </p>

                {/* Active indicator dot */}
                {isActive && (
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Glass Morphism Summary Bar */}
      <div className="mb-6 p-4 rounded-xl bg-white/70 backdrop-blur-sm border border-slate-200/60 shadow-sm">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-6">
            {/* Assumptions Summary */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-50/80 border border-blue-100">
              <FileSearch className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium text-blue-700">{assumptions.length} assumptions</span>
              {approvedCount > 0 && (
                <Badge variant="outline" className="text-emerald-600 border-emerald-300 bg-emerald-50 text-xs">
                  {approvedCount} approved
                </Badge>
              )}
            </div>

            {/* Trace Summary */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-50/80 border border-purple-100">
              <GitBranch className="h-4 w-4 text-purple-500" />
              <span className="text-sm font-medium text-purple-700">{tracedCount + inferredCount} traced</span>
              {needsMappingCount > 0 && (
                <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 text-xs">
                  {needsMappingCount} pending
                </Badge>
              )}
            </div>

            {/* Documents Summary */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50/80 border border-emerald-100">
              <Sparkles className="h-4 w-4 text-emerald-500" />
              <span className="text-sm font-medium text-emerald-700">{selectedDocuments.size} documents</span>
              {locked && (
                <Badge className="bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs shadow-sm">
                  Locked
                </Badge>
              )}
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowStepPreview(!showStepPreview)}
            className="text-xs hover:bg-slate-100/80"
          >
            {showStepPreview ? (
              <>
                <ChevronUp className="h-3 w-3 mr-1" />
                Hide Preview
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3 mr-1" />
                Show Preview
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="min-h-[500px]">
        {/* ============================================ */}
        {/* STEP 1: ASSUMPTIONS */}
        {/* ============================================ */}
        {currentStep === 1 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div>
              <h2 className="text-2xl font-bold mb-2">Review Assumptions</h2>
              <p className="text-muted-foreground">
                These assumptions were extracted from your uploaded documents. Review, edit, and approve them before proceeding.
              </p>
            </div>

            {/* Status Summary */}
            <div className="flex items-center gap-3">
              {approvedCount > 0 && (
                <Badge variant="default" className="bg-green-600">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  {approvedCount} approved
                </Badge>
              )}
              {reviewCount > 0 && (
                <Badge variant="secondary">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  {reviewCount} need review
                </Badge>
              )}
              <Badge variant="outline">{assumptions.length} total</Badge>
            </div>

            {/* Assumptions List */}
            <div className="space-y-3">
              {assumptions.map((assumption) => (
                <Card
                  key={assumption.id}
                  className={`border-2 transition-all ${
                    assumption.status === 'approved'
                      ? 'border-green-200 bg-green-50/50'
                      : 'border-amber-200 bg-amber-50/50 hover:shadow-md'
                  }`}
                >
                  <CardContent className="pt-6">
                    {editingId === assumption.id ? (
                      <div className="space-y-3">
                        <div className="flex items-start gap-4">
                          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                            {assumption.id.replace("a", "")}
                          </div>
                          <div className="flex-1 space-y-3">
                            <Textarea
                              value={editText}
                              onChange={(e) => setEditText(e.target.value)}
                              placeholder="Assumption text..."
                              className="min-h-[80px]"
                            />
                            <Input
                              value={editSource}
                              onChange={(e) => setEditSource(e.target.value)}
                              placeholder="Source reference..."
                            />
                          </div>
                        </div>
                        <div className="flex items-center gap-2 justify-end">
                          <Button size="sm" variant="outline" onClick={cancelEdit}>
                            <X className="h-4 w-4 mr-1" />
                            Cancel
                          </Button>
                          <Button size="sm" onClick={saveEdit}>
                            <Check className="h-4 w-4 mr-1" />
                            Save
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start gap-4">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                          {assumption.id.replace("a", "")}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium mb-2">{assumption.text}</p>
                          <div className="flex items-center gap-2">
                            <FileSearch className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">{assumption.source}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant={assumption.status === 'approved' ? 'default' : 'outline'}
                            onClick={() => toggleStatus(assumption.id)}
                            className={assumption.status === 'approved' ? 'bg-green-600 hover:bg-green-700' : ''}
                          >
                            {assumption.status === 'approved' ? (
                              <>
                                <CheckCircle2 className="h-4 w-4 mr-1" />
                                Approved
                              </>
                            ) : (
                              <>
                                <AlertCircle className="h-4 w-4 mr-1" />
                                Review
                              </>
                            )}
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => startEdit(assumption)}>
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => deleteAssumption(assumption.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}

              {/* Add New Assumption */}
              {isAddingNew ? (
                <Card className="border-2 border-dashed border-blue-300 bg-blue-50/50">
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="flex items-start gap-4">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                          <Plus className="h-4 w-4" />
                        </div>
                        <div className="flex-1 space-y-3">
                          <Textarea
                            value={newText}
                            onChange={(e) => setNewText(e.target.value)}
                            placeholder="Enter assumption text..."
                            className="min-h-[80px]"
                            autoFocus
                          />
                          <Input
                            value={newSource}
                            onChange={(e) => setNewSource(e.target.value)}
                            placeholder="Source reference (optional)..."
                          />
                        </div>
                      </div>
                      <div className="flex items-center gap-2 justify-end">
                        <Button size="sm" variant="outline" onClick={cancelAdd}>
                          <X className="h-4 w-4 mr-1" />
                          Cancel
                        </Button>
                        <Button size="sm" onClick={addNewAssumption}>
                          <Check className="h-4 w-4 mr-1" />
                          Add
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Button
                  variant="outline"
                  className="w-full border-2 border-dashed border-blue-300 bg-blue-50/50 hover:bg-blue-100/50 text-blue-700"
                  onClick={() => setIsAddingNew(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add New Assumption
                </Button>
              )}
            </div>

            {/* Next Step Preview */}
            {showStepPreview && assumptions.length > 0 && (
              <Card className="border-dashed border-slate-300 bg-slate-50/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2 text-slate-600">
                    <ArrowRight className="h-4 w-4" />
                    Next: Traceability Matrix
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm text-muted-foreground">
                    {tracedCount + inferredCount} of {assumptions.length} assumptions will be automatically mapped to FAR/DFARS requirements.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* ============================================ */}
        {/* STEP 2: TRACEABILITY */}
        {/* ============================================ */}
        {currentStep === 2 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div>
              <h2 className="text-2xl font-bold mb-2">Traceability Matrix</h2>
              <p className="text-muted-foreground">
                Verify how assumptions map to FAR/DFARS requirements using intelligent pattern matching.
              </p>
            </div>

            {/* Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">{assumptions.length}</div>
                    <div className="text-sm text-muted-foreground mt-1">Total</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-green-200 bg-green-50/50">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">{tracedCount}</div>
                    <div className="text-sm text-muted-foreground mt-1">Directly Traced</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-blue-200 bg-blue-50/50">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">{inferredCount}</div>
                    <div className="text-sm text-muted-foreground mt-1">Auto-Mapped</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-amber-200 bg-amber-50/50">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-amber-600">{needsMappingCount}</div>
                    <div className="text-sm text-muted-foreground mt-1">Needs Mapping</div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Trace Table */}
            <Card>
              <CardHeader>
                <CardTitle>Requirement Traceability</CardTitle>
                <CardDescription>
                  Assumptions mapped to source requirements using intelligent pattern matching
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[5%]">ID</TableHead>
                        <TableHead className="w-[40%]">Assumption</TableHead>
                        <TableHead className="w-[35%]">Traced Requirement</TableHead>
                        <TableHead className="w-[20%]">Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {traceData.length > 0 ? (
                        traceData.map((trace) => (
                          <TableRow
                            key={trace.assumption.id}
                            className={trace.assumption.status === 'approved' ? 'bg-green-50/50' : ''}
                          >
                            <TableCell className="font-mono text-sm text-muted-foreground">
                              {trace.assumption.id}
                            </TableCell>
                            <TableCell>
                              <div>
                                <div className="font-medium mb-1">{trace.assumption.text}</div>
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                  <FileText className="h-3 w-3" />
                                  <span>{trace.assumption.source}</span>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell className="text-sm">
                              {trace.requirement}
                            </TableCell>
                            <TableCell>
                              {trace.status === 'traced' && (
                                <Badge variant="default" className="gap-1 bg-green-600">
                                  <CheckCircle2 className="h-3 w-3" />
                                  Traced
                                </Badge>
                              )}
                              {trace.status === 'inferred' && (
                                <Badge variant="default" className="gap-1 bg-blue-600">
                                  <CheckCircle2 className="h-3 w-3" />
                                  Auto-Mapped
                                </Badge>
                              )}
                              {trace.status === 'needs_mapping' && (
                                <Badge variant="secondary" className="gap-1">
                                  <AlertCircle className="h-3 w-3" />
                                  Needs Review
                                </Badge>
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center py-12 text-muted-foreground">
                            <AlertCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                            <p className="font-medium">No assumptions to trace</p>
                            <p className="text-sm mt-1">Go back and add assumptions first</p>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            {/* Next Step Preview */}
            {showStepPreview && (
              <Card className="border-dashed border-slate-300 bg-slate-50/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2 text-slate-600">
                    <ArrowRight className="h-4 w-4" />
                    Next: Generation Plan
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm text-muted-foreground">
                    Select from {documentList.length} available documents including {requiredCount} required and{' '}
                    {documentList.filter(d => d.category === 'recommended').length} recommended.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* ============================================ */}
        {/* STEP 3: GENERATION PLAN */}
        {/* ============================================ */}
        {currentStep === 3 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2">Generation Plan</h2>
                <p className="text-muted-foreground">
                  Configure which documents to generate for Day-One artifacts
                </p>
              </div>
              {locked ? (
                <Badge className="bg-amber-500 gap-1">
                  <Lock className="h-3 w-3" />
                  Plan Locked
                </Badge>
              ) : (
                <Badge variant="outline" className="gap-1">
                  <Unlock className="h-3 w-3" />
                  Editing
                </Badge>
              )}
            </div>

            {/* Phase Analysis */}
            {selectedDocuments.size > 0 && (
              <PhaseInfo analysis={phaseAnalysis} loading={analyzingPhase} />
            )}

            {/* Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="border-green-200 bg-green-50/50">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">{requiredCount}</div>
                    <div className="text-sm text-muted-foreground mt-1">Required Documents</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-blue-200 bg-blue-50/50">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">{recommendedSelectedCount}</div>
                    <div className="text-sm text-muted-foreground mt-1">Recommended Selected</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-slate-200 bg-slate-50/50">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-slate-600">{optionalSelectedCount}</div>
                    <div className="text-sm text-muted-foreground mt-1">Optional Selected</div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Document Selection */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Documents to Generate</CardTitle>
                    <CardDescription>Intelligently mapped from your assumptions</CardDescription>
                  </div>
                  {locked ? (
                    <Lock className="h-5 w-5 text-amber-600" />
                  ) : (
                    <Unlock className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                  {documentList.map((doc) => {
                    const isSelected = selectedDocuments.has(doc.name);
                    const isRequired = doc.category === 'required';

                    return (
                      <Card
                        key={doc.name}
                        className={`border transition-all ${
                          isRequired
                            ? 'border-green-200 bg-green-50/50'
                            : doc.category === 'recommended'
                            ? isSelected
                              ? 'border-blue-200 bg-blue-50/50'
                              : 'border-slate-200 hover:border-blue-300'
                            : isSelected
                            ? 'border-slate-200 bg-slate-50/50'
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <CardContent className="py-4">
                          <div className="flex items-center gap-4">
                            {/* Selection Indicator */}
                            <div className="flex-shrink-0">
                              {isSelected ? (
                                <CheckCircle2
                                  className={`h-5 w-5 ${
                                    isRequired
                                      ? 'text-green-600'
                                      : doc.category === 'recommended'
                                      ? 'text-blue-600'
                                      : 'text-slate-600'
                                  }`}
                                />
                              ) : (
                                <Circle className="h-5 w-5 text-muted-foreground" />
                              )}
                            </div>

                            {/* Document Info */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1 flex-wrap">
                                <span className="font-medium truncate">{doc.name}</span>
                                {doc.section && (
                                  <Badge variant="outline" className="text-xs">
                                    Section {doc.section}
                                  </Badge>
                                )}
                                <Badge
                                  variant={isRequired ? 'default' : doc.category === 'recommended' ? 'secondary' : 'outline'}
                                  className={
                                    isRequired
                                      ? 'bg-green-600'
                                      : doc.category === 'recommended'
                                      ? 'bg-blue-600 text-white'
                                      : ''
                                  }
                                >
                                  {doc.category}
                                </Badge>
                              </div>
                              <p className="text-xs text-muted-foreground truncate">{doc.description}</p>
                            </div>

                            {/* Toggle Button */}
                            {!locked && (
                              <Button
                                size="sm"
                                variant={isSelected ? 'default' : 'outline'}
                                onClick={() => toggleDocument(doc.name)}
                                className={
                                  isSelected && doc.category === 'recommended'
                                    ? 'bg-blue-600 hover:bg-blue-700'
                                    : isSelected && isRequired
                                    ? 'bg-green-600 hover:bg-green-700'
                                    : ''
                                }
                              >
                                {isSelected ? (
                                  <Minus className="h-4 w-4" />
                                ) : (
                                  <Plus className="h-4 w-4" />
                                )}
                              </Button>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Navigation Footer */}
      <div className="mt-8 flex items-center justify-between border-t pt-6">
        <Button
          variant="outline"
          onClick={currentStep === 1 ? onBack : prevStep}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          {currentStep === 1 ? 'Back to Editor' : 'Previous'}
        </Button>

        <div className="flex items-center gap-3">
          {currentStep === 3 && !locked && (
            <Button onClick={onLock} className="bg-amber-600 hover:bg-amber-700 gap-2">
              <Lock className="h-4 w-4" />
              Lock Plan
            </Button>
          )}
          
          {currentStep === 3 && locked && (
            <>
              <Button variant="outline" onClick={onUnlock}>
                <Unlock className="h-4 w-4 mr-2" />
                Edit Plan
              </Button>
              <Button
                onClick={() => {
                  const docsToGenerate = documentList.filter(d => selectedDocuments.has(d.name));
                  onGenerate(docsToGenerate);
                }}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 gap-2"
              >
                <Sparkles className="h-4 w-4" />
                Generate Documents ({selectedDocuments.size})
              </Button>
            </>
          )}

          {currentStep < 3 && (
            <Button onClick={nextStep} className="gap-2" disabled={assumptions.length === 0}>
              Next
              <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================
// Helper Functions
// ============================================

/**
 * Maps an assumption to a FAR/DFARS requirement using pattern matching
 */
function mapAssumptionToRequirement(assumption: Assumption): TraceMapping {
  const text = assumption.text.toLowerCase();
  const source = assumption.source.toLowerCase();

  const patterns = [
    {
      keywords: ['evaluation', 'eval', 'bvto', 'best value', 'tradeoff', 'lpta', 'lowest price'],
      requirement: 'FAR 15.304 - Evaluation Factors',
      confidence: 'high' as const
    },
    {
      keywords: ['idiq', 'indefinite delivery', 'contract type', 'firm fixed price', 'ffp', 'cpff'],
      requirement: 'FAR 16 - Contract Types',
      confidence: 'high' as const
    },
    {
      keywords: ['cui', 'cmmc', 'security', 'dfars', 'classified', 'clearance', 'nist', '800-171'],
      requirement: 'DFARS 252.204-7012 - Safeguarding CUI',
      confidence: 'high' as const
    },
    {
      keywords: ['schedule', 'timeline', 'delivery', 'award', 'milestone', 'period of performance'],
      requirement: 'Section F - Performance Schedule',
      confidence: 'medium' as const
    },
    {
      keywords: ['budget', 'cost', 'price', 'ceiling', 'funding', 'igce'],
      requirement: 'Section B - Cost/Price Schedule',
      confidence: 'medium' as const
    },
    {
      keywords: ['performance', 'kpp', 'ksa', 'technical', 'specification', 'requirement'],
      requirement: 'Section C - Performance Requirements',
      confidence: 'medium' as const
    },
    {
      keywords: ['small business', 'set-aside', 'sdvosb', '8(a)', 'hubzone'],
      requirement: 'FAR 19 - Small Business Programs',
      confidence: 'high' as const
    }
  ];

  // Check if source already contains requirement reference
  if (source.includes('far') || source.includes('dfars') || source.includes('req') || source.includes('§')) {
    return {
      assumption,
      requirement: assumption.source,
      status: 'traced',
      confidence: 'high'
    };
  }

  // Try to match patterns
  for (const pattern of patterns) {
    if (pattern.keywords.some(keyword => text.includes(keyword) || source.includes(keyword))) {
      return {
        assumption,
        requirement: pattern.requirement,
        status: 'inferred',
        confidence: pattern.confidence
      };
    }
  }

  // No match found
  return {
    assumption,
    requirement: 'Pending Requirement Mapping',
    status: 'needs_mapping',
    confidence: 'low'
  };
}

/**
 * Generates the list of available documents based on assumptions
 */
function generateDocumentList(assumptions: Assumption[]): GeneratedDocument[] {
  const assumptionTexts = assumptions.map(a => ({
    id: a.id,
    text: a.text.toLowerCase(),
    source: a.source.toLowerCase()
  }));

  const hasKeywords = (keywords: string[]): string[] => {
    return assumptionTexts
      .filter(a => keywords.some(kw => a.text.includes(kw) || a.source.includes(kw)))
      .map(a => a.id);
  };

  const evalAssumptions = hasKeywords(['evaluation', 'eval', 'bvto', 'best value', 'tradeoff', 'lpta']);
  const idiqAssumptions = hasKeywords(['idiq', 'indefinite delivery', 'task order', 'delivery order']);
  const securityAssumptions = hasKeywords(['cui', 'cmmc', 'dfars', 'security', 'classified', 'nist', '800-171']);
  const perfAssumptions = hasKeywords(['performance', 'kpp', 'ksa', 'technical', 'specification', 'pws', 'sow']);
  const costAssumptions = hasKeywords(['cost', 'price', 'budget', 'ceiling', 'igce', 'funding']);
  const sbAssumptions = hasKeywords(['small business', 'set-aside', 'sdvosb', '8(a)', 'hubzone']);

  return [
    // Solicitation Sections (Uniform Contract Format)
    { name: 'Section A - Solicitation/Contract Form', category: 'required', description: 'SF 1449, 33, or 26 - Basic contract information', justification: 'Required header for all solicitations', linkedAssumptions: [], section: 'A' },
    { name: 'Section B - Supplies/Services and Prices', category: 'required', description: 'CLIN structure, pricing, and payment terms', justification: 'Every contract requires pricing information', linkedAssumptions: costAssumptions, section: 'B' },
    { name: 'Section C - Performance Work Statement', category: 'required', description: 'Detailed technical requirements, deliverables, and performance standards', justification: 'Defines what the contractor must accomplish', linkedAssumptions: perfAssumptions, section: 'C' },
    { name: 'Section D - Packaging and Marking', category: 'optional', description: 'Packaging, labeling, and marking requirements', justification: 'Required for product deliveries', linkedAssumptions: [], section: 'D' },
    { name: 'Section E - Inspection and Acceptance', category: 'recommended', description: 'Quality assurance and acceptance procedures', justification: 'Defines how deliverables will be inspected', linkedAssumptions: perfAssumptions, section: 'E' },
    { name: 'Section F - Delivery/Performance Schedule', category: 'required', description: 'Period of performance, ordering procedures, and delivery timelines', justification: 'Required for all contracts', linkedAssumptions: idiqAssumptions, section: 'F' },
    { name: 'Section G - Contract Administration', category: 'required', description: 'COR designation, reporting requirements, and administration details', justification: 'Defines contract management procedures', linkedAssumptions: idiqAssumptions, section: 'G' },
    { name: 'Section H - Special Contract Requirements', category: 'required', description: 'DFARS clauses, CUI handling, CMMC requirements, and security provisions', justification: 'Contains special terms and conditions', linkedAssumptions: securityAssumptions, section: 'H' },
    { name: 'Section I - Contract Clauses', category: 'required', description: 'FAR and DFARS clauses incorporated by reference', justification: 'Standard clauses required for all contracts', linkedAssumptions: [], section: 'I' },
    { name: 'Section J - List of Attachments', category: 'optional', description: 'Index of exhibits and attachments', justification: 'Required if attachments are included', linkedAssumptions: [], section: 'J' },
    { name: 'Section K - Representations and Certifications', category: 'required', description: 'Required contractor certifications and representations', justification: 'FAR requires contractor certifications', linkedAssumptions: [], section: 'K' },
    { name: 'Section L - Instructions to Offerors', category: 'required', description: 'Proposal preparation instructions and submission requirements', justification: 'Required for competitive procurements', linkedAssumptions: evalAssumptions, section: 'L' },
    { name: 'Section M - Evaluation Factors', category: 'required', description: 'Evaluation criteria, weights, and award decision approach', justification: 'FAR 15.304 requires stating evaluation factors', linkedAssumptions: evalAssumptions, section: 'M' },
    // Supporting Documents
    { name: 'Independent Government Cost Estimate (IGCE)', category: 'recommended', description: 'Government estimate of fair and reasonable pricing', justification: 'Required for price reasonableness determination', linkedAssumptions: costAssumptions },
    { name: 'Quality Assurance Surveillance Plan (QASP)', category: 'recommended', description: 'Performance monitoring methods and acceptance criteria', justification: 'Best practice for performance-based acquisitions', linkedAssumptions: perfAssumptions },
    { name: 'Market Research Report', category: 'recommended', description: 'Analysis of commercial capabilities and pricing', justification: 'FAR Part 10 requires market research', linkedAssumptions: [] },
    { name: 'Acquisition Plan', category: 'recommended', description: 'Overall acquisition strategy and approach', justification: 'Required for acquisitions over SAT', linkedAssumptions: [] },
    { name: 'Source Selection Plan', category: 'recommended', description: 'Evaluation team structure and procedures', justification: 'Required for competitive acquisitions', linkedAssumptions: evalAssumptions },
    { name: 'Small Business Subcontracting Plan', category: 'recommended', description: 'Small business utilization requirements and goals', justification: 'Required for contracts over $750K (non-small business)', linkedAssumptions: sbAssumptions },
    // Pre-Solicitation Documents
    { name: 'Presolicitation Notice', category: 'optional', description: 'Initial market notification to gauge industry interest', justification: 'Best practice for complex acquisitions', linkedAssumptions: [] },
    { name: 'Sources Sought Notice', category: 'optional', description: 'Request for capability statements from potential vendors', justification: 'Helps identify qualified sources', linkedAssumptions: [] },
    { name: 'Draft RFP', category: 'optional', description: 'Preliminary solicitation for industry feedback', justification: 'Allows industry to comment before final RFP', linkedAssumptions: [] },
  ];
}

