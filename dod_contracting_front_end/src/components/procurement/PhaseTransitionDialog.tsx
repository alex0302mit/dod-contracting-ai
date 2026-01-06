/**
 * PhaseTransitionDialog Component
 * 
 * A dialog for requesting phase transitions in procurement projects.
 * Shows validation status for required documents and allows users
 * to request approval from a gatekeeper (CO or Source Selection Authority).
 * 
 * Dependencies:
 * - phaseTransitionsApi from services/api.ts
 * - Shadcn UI components (Dialog, Button, Select, Badge, ScrollArea)
 * - Lucide icons for status indicators
 */

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  ArrowRight,
  FileText,
  UserCheck,
  Shield,
} from 'lucide-react';
import {
  phaseTransitionsApi,
  type TransitionValidation,
  type EligibleGatekeeper,
} from '@/services/api';

// Phase display name mapping
const phaseDisplayNames: Record<string, string> = {
  pre_solicitation: 'Pre-Solicitation',
  solicitation: 'Solicitation',
  post_solicitation: 'Post-Solicitation',
  award: 'Award',
};

interface PhaseTransitionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  phaseId: string;
  phaseName: string;
  projectName: string;
  onSuccess?: () => void;
}

export function PhaseTransitionDialog({
  open,
  onOpenChange,
  phaseId,
  phaseName,
  projectName,
  onSuccess,
}: PhaseTransitionDialogProps) {
  // State for validation results
  const [validation, setValidation] = useState<TransitionValidation | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedGatekeeper, setSelectedGatekeeper] = useState<string>('');

  // Load validation when dialog opens
  useEffect(() => {
    if (open && phaseId) {
      loadValidation();
    }
  }, [open, phaseId]);

  // Fetch validation from API
  const loadValidation = async () => {
    setLoading(true);
    try {
      const result = await phaseTransitionsApi.validateTransition(phaseId);
      setValidation(result);
      
      // Auto-select first eligible gatekeeper if available
      if (result.eligible_gatekeepers && result.eligible_gatekeepers.length > 0) {
        setSelectedGatekeeper(result.eligible_gatekeepers[0].id);
      }
    } catch (error) {
      console.error('Error loading transition validation:', error);
      toast.error('Failed to load transition validation');
    } finally {
      setLoading(false);
    }
  };

  // Submit transition request
  const handleSubmit = async () => {
    if (!validation?.can_transition) {
      toast.error('Cannot request transition - blocking issues exist');
      return;
    }

    setSubmitting(true);
    try {
      await phaseTransitionsApi.requestTransition(
        phaseId,
        selectedGatekeeper || undefined
      );
      toast.success('Phase transition request submitted');
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      console.error('Error requesting transition:', error);
      toast.error('Failed to submit transition request');
    } finally {
      setSubmitting(false);
    }
  };

  // Get status badge for a document
  const getDocumentStatusBadge = (status: { exists: boolean; approved: boolean; status: string | null }) => {
    if (!status.exists) {
      return <Badge variant="destructive" className="gap-1"><XCircle className="h-3 w-3" /> Missing</Badge>;
    }
    if (status.approved) {
      return <Badge className="bg-green-100 text-green-800 gap-1"><CheckCircle2 className="h-3 w-3" /> Approved</Badge>;
    }
    return (
      <Badge variant="outline" className="gap-1 text-amber-700 border-amber-300 bg-amber-50">
        <AlertTriangle className="h-3 w-3" /> {status.status || 'Pending'}
      </Badge>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-600" />
            Request Phase Transition
          </DialogTitle>
          <DialogDescription>
            Review document status and request approval to move to the next phase.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          // Loading state
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-3 text-slate-600">Validating transition requirements...</span>
          </div>
        ) : validation ? (
          <div className="space-y-6">
            {/* Transition Overview */}
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Project</p>
                  <p className="font-medium">{projectName}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-center">
                    <Badge variant="outline" className="text-base px-3 py-1">
                      {phaseDisplayNames[validation.from_phase] || validation.from_phase}
                    </Badge>
                  </div>
                  <ArrowRight className="h-5 w-5 text-slate-400" />
                  <div className="text-center">
                    <Badge className="bg-blue-100 text-blue-800 text-base px-3 py-1">
                      {validation.to_phase 
                        ? phaseDisplayNames[validation.to_phase] || validation.to_phase
                        : 'N/A'}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>

            {/* No next phase available */}
            {!validation.to_phase && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="flex items-center gap-2 text-amber-800">
                  <AlertTriangle className="h-5 w-5" />
                  <span className="font-medium">Final Phase</span>
                </div>
                <p className="mt-1 text-sm text-amber-700">
                  This is the final phase. No further transitions are available.
                </p>
              </div>
            )}

            {/* Document Status Checklist */}
            {validation.to_phase && (
              <>
                <div>
                  <h4 className="font-medium flex items-center gap-2 mb-3">
                    <FileText className="h-4 w-4" />
                    Required Documents
                  </h4>
                  <ScrollArea className="h-[200px] border rounded-lg">
                    <div className="p-3 space-y-2">
                      {Object.entries(validation.document_status).length > 0 ? (
                        Object.entries(validation.document_status).map(([docName, status]) => (
                          <div
                            key={docName}
                            className="flex items-center justify-between py-2 px-3 bg-white rounded border"
                          >
                            <span className="text-sm">{docName}</span>
                            {getDocumentStatusBadge(status)}
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-slate-500 text-center py-4">
                          No required documents defined for this phase
                        </p>
                      )}
                    </div>
                  </ScrollArea>
                </div>

                {/* Blocking Issues */}
                {validation.blocking_issues.length > 0 && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="font-medium text-red-800 flex items-center gap-2 mb-2">
                      <XCircle className="h-4 w-4" />
                      Blocking Issues
                    </h4>
                    <ul className="space-y-1">
                      {validation.blocking_issues.map((issue, i) => (
                        <li key={i} className="text-sm text-red-700">• {issue}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Warnings */}
                {validation.warnings.length > 0 && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <h4 className="font-medium text-amber-800 flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4" />
                      Warnings
                    </h4>
                    <ul className="space-y-1">
                      {validation.warnings.map((warning, i) => (
                        <li key={i} className="text-sm text-amber-700">• {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Gatekeeper Selection */}
                {validation.can_transition && validation.eligible_gatekeepers && validation.eligible_gatekeepers.length > 0 && (
                  <div>
                    <Label htmlFor="gatekeeper" className="flex items-center gap-2 mb-2">
                      <UserCheck className="h-4 w-4" />
                      Select Gatekeeper for Approval
                    </Label>
                    <Select value={selectedGatekeeper} onValueChange={setSelectedGatekeeper}>
                      <SelectTrigger id="gatekeeper">
                        <SelectValue placeholder="Select a gatekeeper" />
                      </SelectTrigger>
                      <SelectContent>
                        {validation.eligible_gatekeepers.map((gk: EligibleGatekeeper) => (
                          <SelectItem key={gk.id} value={gk.id}>
                            {gk.name} ({gk.role})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {validation.required_gatekeeper && (
                      <p className="mt-1 text-xs text-slate-500">
                        Required gatekeeper role: {validation.required_gatekeeper}
                      </p>
                    )}
                  </div>
                )}

                {/* Success state */}
                {validation.can_transition && validation.blocking_issues.length === 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-green-800">
                      <CheckCircle2 className="h-5 w-5" />
                      <span className="font-medium">Ready for Transition</span>
                    </div>
                    <p className="mt-1 text-sm text-green-700">
                      All requirements met. You can request approval to proceed.
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        ) : (
          // Error state
          <div className="text-center py-8 text-slate-500">
            Failed to load validation data
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={
              loading ||
              submitting ||
              !validation?.can_transition ||
              !validation?.to_phase ||
              !validation?.user_can_request
            }
            className="gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <ArrowRight className="h-4 w-4" />
                Request Transition
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

