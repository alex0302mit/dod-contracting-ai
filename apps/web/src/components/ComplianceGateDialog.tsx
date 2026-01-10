/**
 * Compliance Gate Dialog
 *
 * Modal shown before export to display compliance status and issues.
 * Users can either return to edit or acknowledge issues and proceed with export.
 */

import { useState } from "react";
import { CheckCircle2, AlertCircle, XCircle, Shield, FileText, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  performComplianceAnalysis,
  type ComplianceAnalysis,
} from "@/lib/complianceUtils";

interface Citation {
  id: number;
  source: string;
  page: number;
  text: string;
}

interface ComplianceGateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sections: Record<string, string>;
  citations: Citation[];
  onProceed: () => void;
  onDownloadReport: () => void;
  exportFormat: "pdf" | "docx";
}

export function ComplianceGateDialog({
  open,
  onOpenChange,
  sections,
  citations,
  onProceed,
  onDownloadReport,
  exportFormat,
}: ComplianceGateDialogProps) {
  const [acknowledged, setAcknowledged] = useState(false);

  // Perform compliance analysis
  const analysis: ComplianceAnalysis = performComplianceAnalysis(sections, citations);

  const hasIssues = analysis.overallScore < 85;
  const hasCriticalIssues = analysis.criticalIssues.length > 0;
  const errorCount = analysis.criticalIssues.filter(i => i.kind === 'error').length;
  const warningCount = analysis.sectionCompliance.reduce(
    (acc, s) => acc + s.issues.filter(i => i.kind === 'warning').length,
    0
  );
  const complianceCount = analysis.sectionCompliance.reduce(
    (acc, s) => acc + s.issues.filter(i => i.kind === 'compliance').length,
    0
  );

  const canProceed = !hasCriticalIssues || acknowledged;

  const handleProceed = () => {
    setAcknowledged(false);
    onProceed();
  };

  const handleClose = () => {
    setAcknowledged(false);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Compliance Check
          </DialogTitle>
          <DialogDescription>
            Review compliance status before exporting to {exportFormat.toUpperCase()}
          </DialogDescription>
        </DialogHeader>

        {/* Compliance Score */}
        <div className="flex items-center justify-between py-4">
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="text-4xl font-bold">{analysis.overallScore}</div>
              <div className="text-xs text-muted-foreground">Score</div>
            </div>
            <Badge
              variant={
                analysis.overallStatus === 'pass'
                  ? 'default'
                  : analysis.overallStatus === 'review'
                  ? 'secondary'
                  : 'destructive'
              }
              className={`text-sm px-3 py-1 ${
                analysis.overallStatus === 'pass'
                  ? 'bg-green-600'
                  : analysis.overallStatus === 'review'
                  ? 'bg-amber-500'
                  : 'bg-red-600'
              }`}
            >
              {analysis.overallStatus === 'pass' && <CheckCircle2 className="h-3 w-3 mr-1" />}
              {analysis.overallStatus === 'review' && <AlertCircle className="h-3 w-3 mr-1" />}
              {analysis.overallStatus === 'fail' && <XCircle className="h-3 w-3 mr-1" />}
              {analysis.overallStatus.toUpperCase()}
            </Badge>
          </div>
          <div className="text-right text-sm text-muted-foreground">
            {analysis.sectionsAnalyzed} sections analyzed
          </div>
        </div>

        <Separator />

        {/* Issue Summary */}
        <div className="py-4">
          <div className="text-sm font-medium mb-3">Issue Summary</div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className={`p-3 rounded-lg ${errorCount > 0 ? 'bg-red-50' : 'bg-slate-50'}`}>
              <div className={`text-2xl font-bold ${errorCount > 0 ? 'text-red-600' : 'text-slate-400'}`}>
                {errorCount}
              </div>
              <div className="text-xs text-muted-foreground">Errors</div>
            </div>
            <div className={`p-3 rounded-lg ${complianceCount > 0 ? 'bg-purple-50' : 'bg-slate-50'}`}>
              <div className={`text-2xl font-bold ${complianceCount > 0 ? 'text-purple-600' : 'text-slate-400'}`}>
                {complianceCount}
              </div>
              <div className="text-xs text-muted-foreground">Compliance</div>
            </div>
            <div className={`p-3 rounded-lg ${warningCount > 0 ? 'bg-amber-50' : 'bg-slate-50'}`}>
              <div className={`text-2xl font-bold ${warningCount > 0 ? 'text-amber-600' : 'text-slate-400'}`}>
                {warningCount}
              </div>
              <div className="text-xs text-muted-foreground">Warnings</div>
            </div>
          </div>
        </div>

        {/* Critical Issues List */}
        {hasCriticalIssues && (
          <>
            <Separator />
            <div className="py-4">
              <div className="text-sm font-medium mb-2 text-red-600">
                Critical Issues ({analysis.criticalIssues.length})
              </div>
              <ScrollArea className="h-32">
                <ul className="space-y-2 text-sm">
                  {analysis.criticalIssues.slice(0, 5).map((issue) => (
                    <li key={issue.id} className="flex items-start gap-2">
                      <XCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                      <span>
                        <span className="font-medium">{issue.sectionName}:</span>{" "}
                        {issue.label}
                      </span>
                    </li>
                  ))}
                  {analysis.criticalIssues.length > 5 && (
                    <li className="text-muted-foreground pl-6">
                      ...and {analysis.criticalIssues.length - 5} more issues
                    </li>
                  )}
                </ul>
              </ScrollArea>
            </div>
          </>
        )}

        {/* Acknowledgment Checkbox */}
        {hasCriticalIssues && (
          <>
            <Separator />
            <div className="flex items-start gap-3 py-4">
              <Checkbox
                id="acknowledge"
                checked={acknowledged}
                onCheckedChange={(checked) => setAcknowledged(checked === true)}
              />
              <label
                htmlFor="acknowledge"
                className="text-sm text-muted-foreground cursor-pointer leading-tight"
              >
                I acknowledge there are compliance issues and wish to proceed with the export anyway.
              </label>
            </div>
          </>
        )}

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={onDownloadReport}
            className="sm:mr-auto"
          >
            <FileText className="h-4 w-4 mr-2" />
            Download Report
          </Button>
          <Button variant="outline" onClick={handleClose}>
            Return to Edit
          </Button>
          <Button
            onClick={handleProceed}
            disabled={!canProceed}
            variant={hasCriticalIssues ? "destructive" : "default"}
          >
            <Download className="h-4 w-4 mr-2" />
            Export {exportFormat.toUpperCase()}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
