import { ArrowLeft, CheckCircle2, AlertCircle, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface Assumption {
  id: string;
  text: string;
  source: string;
  status?: 'approved' | 'needs_review';
}

interface TraceMatrixProps {
  assumptions: Assumption[];
  onBack: () => void;
  onPlan: () => void;
}

interface TraceMapping {
  assumption: Assumption;
  requirement: string;
  status: 'traced' | 'inferred' | 'needs_mapping';
  confidence: 'high' | 'medium' | 'low';
}

export function TraceMatrix({ assumptions, onBack, onPlan }: TraceMatrixProps) {
  // Intelligent requirement mapping based on keywords and patterns
  const mapAssumptionToRequirement = (assumption: Assumption): TraceMapping => {
    const text = assumption.text.toLowerCase();
    const source = assumption.source.toLowerCase();

    // Pattern matching for common DoD acquisition requirements
    const patterns = [
      // Evaluation criteria patterns
      {
        keywords: ['evaluation', 'eval', 'bvto', 'best value', 'tradeoff', 'lpta', 'lowest price'],
        requirement: 'FAR 15.304 - Evaluation Factors',
        confidence: 'high' as const
      },
      // Contract type patterns
      {
        keywords: ['idiq', 'indefinite delivery', 'contract type', 'firm fixed price', 'ffp', 'cpff'],
        requirement: 'FAR 16 - Contract Types',
        confidence: 'high' as const
      },
      // Security and compliance patterns
      {
        keywords: ['cui', 'cmmc', 'security', 'dfars', 'classified', 'clearance', 'nist', '800-171'],
        requirement: 'DFARS 252.204-7012 - Safeguarding CUI',
        confidence: 'high' as const
      },
      // Timeline patterns
      {
        keywords: ['schedule', 'timeline', 'delivery', 'award', 'milestone', 'period of performance'],
        requirement: 'Section F - Performance Schedule',
        confidence: 'medium' as const
      },
      // Budget patterns
      {
        keywords: ['budget', 'cost', 'price', 'ceiling', 'funding', 'igce'],
        requirement: 'Section B - Cost/Price Schedule',
        confidence: 'medium' as const
      },
      // Performance requirements
      {
        keywords: ['performance', 'kpp', 'ksa', 'technical', 'specification', 'requirement'],
        requirement: 'Section C - Performance Requirements',
        confidence: 'medium' as const
      },
      // Small business patterns
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
  };

  // Map all assumptions to requirements
  const traceData: TraceMapping[] = assumptions.map(mapAssumptionToRequirement);

  // Calculate statistics
  const tracedCount = traceData.filter(t => t.status === 'traced').length;
  const inferredCount = traceData.filter(t => t.status === 'inferred').length;
  const needsMappingCount = traceData.filter(t => t.status === 'needs_mapping').length;
  const approvedCount = assumptions.filter(a => a.status === 'approved').length;

  return (
    <div className="container mx-auto p-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-3">
          Traceability Matrix
        </h1>
        <p className="text-lg text-muted-foreground">
          Verify all assumptions are properly traced to requirements
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{assumptions.length}</div>
              <div className="text-sm text-muted-foreground mt-1">Total Assumptions</div>
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

      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Requirement Traceability</CardTitle>
              <CardDescription>
                Assumptions mapped to source requirements using intelligent pattern matching
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {approvedCount > 0 && (
                <Badge variant="default" className="bg-green-600">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  {approvedCount} approved
                </Badge>
              )}
            </div>
          </div>
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
                    <TableRow key={trace.assumption.id} className={
                      trace.assumption.status === 'approved' ? 'bg-green-50/50' : ''
                    }>
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
                      <p className="text-sm mt-1">Go back and extract assumptions from your documents</p>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Assumptions
        </Button>
        <Button onClick={onPlan} className="ml-auto" disabled={assumptions.length === 0}>
          Continue to Generation Plan
        </Button>
      </div>
    </div>
  );
}
