/**
 * Enhanced Compliance Component
 *
 * Dynamic compliance verification with FAR/DFARS analysis,
 * section-by-section breakdown, and drill-down capabilities
 */

import { useState } from "react";
import { ArrowLeft, CheckCircle2, AlertCircle, XCircle, FileText, Shield, ChevronDown, ChevronRight, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { AgentBadge } from "@/components/AgentBadge";
import {
  performComplianceAnalysis,
  type ComplianceAnalysis,
  type SectionCompliance,
  type ComplianceIssue,
} from "@/lib/complianceUtils";

interface Citation {
  id: number;
  source: string;
  page: number;
  text: string;
  bbox?: { x: number; y: number; w: number; h: number };
}

interface ComplianceProps {
  sections: Record<string, string>;
  citations: Citation[];
  agentMetadata?: Record<string, any>;
  collaborationMetadata?: any;
  onBack: () => void;
  onExport: () => void;
}

export function Compliance({
  sections,
  citations,
  agentMetadata,
  collaborationMetadata,
  onBack,
  onExport,
}: ComplianceProps) {
  // Perform compliance analysis
  const analysis: ComplianceAnalysis = performComplianceAnalysis(sections, citations);

  // State for drill-down
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [showLowScoreWarning, setShowLowScoreWarning] = useState(false);

  // Sort sections by score (lowest first to highlight problems)
  const sortedSections = [...analysis.sectionCompliance].sort((a, b) => a.score - b.score);

  // Handle export with warning if score is low
  const handleExport = () => {
    if (analysis.overallScore < 70) {
      setShowLowScoreWarning(true);
    } else {
      onExport();
    }
  };

  return (
    <div className="container mx-auto p-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-3">
          Compliance Gate
        </h1>
        <p className="text-lg text-muted-foreground">
          Comprehensive verification of FAR, DFARS, and policy compliance
        </p>
      </div>

      {/* Overall Compliance Summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Overall Compliance Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Overall Score */}
            <div className="text-center">
              <div className="text-5xl font-bold mb-2">
                {analysis.overallScore}
              </div>
              <Badge
                variant={
                  analysis.overallStatus === 'pass'
                    ? 'default'
                    : analysis.overallStatus === 'review'
                    ? 'secondary'
                    : 'destructive'
                }
                className={`text-sm ${
                  analysis.overallStatus === 'pass'
                    ? 'bg-green-600'
                    : analysis.overallStatus === 'review'
                    ? 'bg-amber-500'
                    : 'bg-red-600'
                }`}
              >
                {analysis.overallStatus.toUpperCase()}
              </Badge>
              <div className="text-xs text-muted-foreground mt-2">Overall Score</div>
            </div>

            {/* Sections Analyzed */}
            <div className="text-center">
              <div className="text-5xl font-bold mb-2">{analysis.sectionsAnalyzed}</div>
              <div className="text-sm text-muted-foreground">Sections Analyzed</div>
            </div>

            {/* Status Breakdown */}
            <div className="text-center">
              <div className="space-y-1">
                <div className="flex items-center justify-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="font-semibold">
                    {analysis.sectionCompliance.filter((s) => s.status === 'pass').length}
                  </span>
                  <span className="text-sm text-muted-foreground">Pass</span>
                </div>
                <div className="flex items-center justify-center gap-2">
                  <AlertCircle className="h-4 w-4 text-amber-500" />
                  <span className="font-semibold">
                    {analysis.sectionCompliance.filter((s) => s.status === 'review').length}
                  </span>
                  <span className="text-sm text-muted-foreground">Review</span>
                </div>
                <div className="flex items-center justify-center gap-2">
                  <XCircle className="h-4 w-4 text-red-600" />
                  <span className="font-semibold">
                    {analysis.sectionCompliance.filter((s) => s.status === 'fail').length}
                  </span>
                  <span className="text-sm text-muted-foreground">Fail</span>
                </div>
              </div>
            </div>

            {/* Critical Issues */}
            <div className="text-center">
              <div className="text-5xl font-bold mb-2 text-red-600">
                {analysis.criticalIssues.length}
              </div>
              <div className="text-sm text-muted-foreground">Critical Issues</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Critical Issues Alert */}
      {analysis.criticalIssues.length > 0 && (
        <Card className="mb-6 border-red-300 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-700 flex items-center gap-2">
              <XCircle className="h-5 w-5" />
              Critical Issues Requiring Attention
            </CardTitle>
            <CardDescription className="text-red-600">
              These issues must be addressed before export
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analysis.criticalIssues.slice(0, 5).map((issue) => (
                <div
                  key={issue.id}
                  className="flex items-start justify-between gap-4 p-3 bg-white rounded-lg border border-red-200"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge
                        variant="destructive"
                        className={`text-xs ${
                          issue.kind === 'compliance' ? 'bg-purple-600' : 'bg-red-600'
                        }`}
                      >
                        {issue.kind.toUpperCase()}
                      </Badge>
                      <span className="text-sm font-medium text-slate-700">{issue.sectionName}</span>
                    </div>
                    <p className="text-sm text-slate-600">{issue.label}</p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setExpandedSection(issue.sectionName);
                      // Scroll to section table
                      document.getElementById('section-table')?.scrollIntoView({ behavior: 'smooth' });
                    }}
                  >
                    <FileText className="h-3 w-3 mr-1" />
                    View
                  </Button>
                </div>
              ))}
              {analysis.criticalIssues.length > 5 && (
                <p className="text-sm text-muted-foreground text-center">
                  ...and {analysis.criticalIssues.length - 5} more critical issues
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* FAR/DFARS Coverage */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* FAR Coverage */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">FAR Coverage</CardTitle>
            <CardDescription>Federal Acquisition Regulation references</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-2">
                {/* Found FAR references */}
                {analysis.farCoverage.map((far, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-medium">{far.clause}</div>
                      <div className="text-xs text-muted-foreground">
                        Used in: {far.sections.join(', ')}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Missing FAR references */}
                {analysis.missingFAR.map((far, idx) => (
                  <div key={`missing-${idx}`} className="flex items-start gap-2 text-sm">
                    <XCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-medium text-red-700">{far}</div>
                      <div className="text-xs text-red-600">Missing - may be required</div>
                    </div>
                  </div>
                ))}

                {analysis.farCoverage.length === 0 && analysis.missingFAR.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No FAR references detected
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* DFARS Coverage */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">DFARS Coverage</CardTitle>
            <CardDescription>Defense Federal Acquisition Regulation Supplement</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-2">
                {/* Found DFARS references */}
                {analysis.dfarsCoverage.map((dfars, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-medium">{dfars.clause}</div>
                      <div className="text-xs text-muted-foreground">
                        Used in: {dfars.sections.join(', ')}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Missing DFARS references */}
                {analysis.missingDFARS.map((dfars, idx) => (
                  <div key={`missing-${idx}`} className="flex items-start gap-2 text-sm">
                    <XCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-medium text-red-700">{dfars}</div>
                      <div className="text-xs text-red-600">Missing - required for CUI handling</div>
                    </div>
                  </div>
                ))}

                {analysis.dfarsCoverage.length === 0 && analysis.missingDFARS.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No DFARS references detected (may not be required)
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Section-by-Section Compliance */}
      <Card className="mb-8" id="section-table">
        <CardHeader>
          <CardTitle>Section-by-Section Compliance</CardTitle>
          <CardDescription>Detailed breakdown of compliance status per section</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[30%]">Section Name</TableHead>
                  <TableHead className="w-[15%]">Words</TableHead>
                  <TableHead className="w-[15%]">Score</TableHead>
                  <TableHead className="w-[20%]">Issues</TableHead>
                  <TableHead className="w-[15%]">Status</TableHead>
                  <TableHead className="w-[5%]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedSections.map((section) => (
                  <SectionRow
                    key={section.sectionName}
                    section={section}
                    agentMetadata={agentMetadata?.[section.sectionName]}
                    isExpanded={expandedSection === section.sectionName}
                    onToggle={() =>
                      setExpandedSection(
                        expandedSection === section.sectionName ? null : section.sectionName
                      )
                    }
                  />
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Editor
        </Button>
        <Button variant="outline" className="ml-auto">
          <Download className="h-4 w-4 mr-2" />
          Export Compliance Report
        </Button>
        <Button onClick={handleExport}>Continue to Export</Button>
      </div>

      {/* Low Score Warning Dialog */}
      <Dialog open={showLowScoreWarning} onOpenChange={setShowLowScoreWarning}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-600">
              <AlertCircle className="h-5 w-5" />
              Low Compliance Score Warning
            </DialogTitle>
            <DialogDescription>
              The overall compliance score is {analysis.overallScore}/100, which is below the recommended
              threshold of 70. You have {analysis.criticalIssues.length} critical issue
              {analysis.criticalIssues.length !== 1 ? 's' : ''} that should be addressed.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm font-semibold mb-2">Critical Issues:</p>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {analysis.criticalIssues.slice(0, 3).map((issue) => (
                <li key={issue.id}>
                  {issue.sectionName}: {issue.label}
                </li>
              ))}
              {analysis.criticalIssues.length > 3 && (
                <li>...and {analysis.criticalIssues.length - 3} more</li>
              )}
            </ul>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLowScoreWarning(false)}>
              Return to Review
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                setShowLowScoreWarning(false);
                onExport();
              }}
            >
              Proceed Anyway
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/**
 * Section Row Component with Expandable Details
 */
function SectionRow({
  section,
  agentMetadata,
  isExpanded,
  onToggle,
}: {
  section: SectionCompliance;
  agentMetadata?: any;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const errorCount = section.issues.filter((i) => i.kind === 'error').length;
  const warningCount = section.issues.filter((i) => i.kind === 'warning').length;
  const complianceCount = section.issues.filter((i) => i.kind === 'compliance').length;

  return (
    <>
      <TableRow
        className={`cursor-pointer ${
          section.status === 'fail'
            ? 'bg-red-50 hover:bg-red-100'
            : section.status === 'review'
            ? 'bg-amber-50 hover:bg-amber-100'
            : 'hover:bg-slate-50'
        }`}
        onClick={onToggle}
      >
        <TableCell>
          <div className="flex items-center gap-2">
            <span className="font-medium">{section.sectionName}</span>
            {agentMetadata && <AgentBadge metadata={agentMetadata} compact />}
          </div>
        </TableCell>
        <TableCell className="text-sm text-muted-foreground">{section.wordCount}</TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <span className="font-bold">{section.score}</span>
            <Progress value={section.score} className="h-2 w-16" />
          </div>
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-1 flex-wrap">
            {errorCount > 0 && (
              <Badge variant="destructive" className="text-xs">
                {errorCount} errors
              </Badge>
            )}
            {complianceCount > 0 && (
              <Badge className="text-xs bg-purple-600">
                {complianceCount} compliance
              </Badge>
            )}
            {warningCount > 0 && (
              <Badge variant="secondary" className="text-xs bg-amber-500">
                {warningCount} warnings
              </Badge>
            )}
            {section.issues.length === 0 && (
              <span className="text-xs text-muted-foreground">No issues</span>
            )}
          </div>
        </TableCell>
        <TableCell>
          <Badge
            variant={
              section.status === 'pass'
                ? 'default'
                : section.status === 'review'
                ? 'secondary'
                : 'destructive'
            }
            className={`${
              section.status === 'pass'
                ? 'bg-green-600'
                : section.status === 'review'
                ? 'bg-amber-500'
                : 'bg-red-600'
            }`}
          >
            {section.status.toUpperCase()}
          </Badge>
        </TableCell>
        <TableCell>
          {isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </TableCell>
      </TableRow>

      {/* Expanded Details */}
      {isExpanded && (
        <TableRow>
          <TableCell colSpan={6} className="bg-slate-50">
            <div className="p-4 space-y-4">
              {/* Quality Breakdown */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Quality Breakdown</h4>
                <div className="grid grid-cols-4 gap-3">
                  <QualityMetric
                    label="Readability"
                    value={section.qualityBreakdown.readability}
                  />
                  <QualityMetric label="Citations" value={section.qualityBreakdown.citations} />
                  <QualityMetric label="Compliance" value={section.qualityBreakdown.compliance} />
                  <QualityMetric label="Length" value={section.qualityBreakdown.length} />
                </div>
              </div>

              <Separator />

              {/* Issues */}
              {section.issues.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">Issues Found</h4>
                  <div className="space-y-2">
                    {section.issues.map((issue) => (
                      <div
                        key={issue.id}
                        className="flex items-start gap-2 p-2 bg-white rounded border"
                      >
                        <Badge
                          variant={issue.kind === 'error' ? 'destructive' : 'secondary'}
                          className={`text-xs mt-0.5 ${
                            issue.kind === 'compliance'
                              ? 'bg-purple-600'
                              : issue.kind === 'warning'
                              ? 'bg-amber-500'
                              : ''
                          }`}
                        >
                          {issue.kind}
                        </Badge>
                        <div className="flex-1">
                          <p className="text-sm">{issue.label}</p>
                          {issue.fix && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Fix available: {issue.fix.label}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

/**
 * Quality Metric Display
 */
function QualityMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-xs font-medium">{label}</span>
        <span className="text-xs font-bold">{value}</span>
      </div>
      <Progress value={value} className="h-2" />
    </div>
  );
}
