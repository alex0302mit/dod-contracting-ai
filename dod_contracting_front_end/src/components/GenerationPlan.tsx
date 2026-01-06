import { useState, useEffect } from "react";
import { ArrowLeft, Lock, Unlock, CheckCircle2, Circle, Sparkles, FileText, Info, Plus, Minus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PhaseInfo } from "@/components/PhaseInfo";
import { ragApi } from "@/services/api";

interface Assumption {
  id: string;
  text: string;
  source: string;
  status?: 'approved' | 'needs_review';
}

interface GenerationPlanProps {
  assumptions: Assumption[];
  locked: boolean;
  onLock: () => void;
  onEdit: () => void;
  onGenerate: (selectedDocs: GeneratedDocument[]) => void;
  onBack: () => void;
}

interface GeneratedDocument {
  name: string;
  category: 'required' | 'recommended' | 'optional';
  description: string;
  justification: string;
  linkedAssumptions: string[]; // assumption IDs
  section?: string;
}

export function GenerationPlan({ assumptions, locked, onLock, onEdit, onGenerate, onBack }: GenerationPlanProps) {
  // Comprehensive document generation - shows ALL possible documents
  const generateDocumentList = (): GeneratedDocument[] => {
    const assumptionTexts = assumptions.map(a => ({
      id: a.id,
      text: a.text.toLowerCase(),
      source: a.source.toLowerCase()
    }));

    // Helper to check if any assumption matches keywords
    const hasKeywords = (keywords: string[]): string[] => {
      return assumptionTexts
        .filter(a => keywords.some(kw => a.text.includes(kw) || a.source.includes(kw)))
        .map(a => a.id);
    };

    // Get linked assumptions for each document type
    const evalAssumptions = hasKeywords(['evaluation', 'eval', 'bvto', 'best value', 'tradeoff', 'lpta']);
    const idiqAssumptions = hasKeywords(['idiq', 'indefinite delivery', 'task order', 'delivery order']);
    const securityAssumptions = hasKeywords(['cui', 'cmmc', 'dfars', 'security', 'classified', 'nist', '800-171']);
    const perfAssumptions = hasKeywords(['performance', 'kpp', 'ksa', 'technical', 'specification', 'pws', 'sow']);
    const costAssumptions = hasKeywords(['cost', 'price', 'budget', 'ceiling', 'igce', 'funding']);
    const sbAssumptions = hasKeywords(['small business', 'set-aside', 'sdvosb', '8(a)', 'hubzone']);

    // ALL standard DoD acquisition documents (always show all options)
    const docs: GeneratedDocument[] = [
      // Solicitation Sections (Uniform Contract Format)
      {
        name: 'Section A - Solicitation/Contract Form',
        category: 'required',
        description: 'SF 1449, 33, or 26 - Basic contract information',
        justification: 'Required header for all solicitations',
        linkedAssumptions: [],
        section: 'A'
      },
      {
        name: 'Section B - Supplies/Services and Prices',
        category: 'required',
        description: 'CLIN structure, pricing, and payment terms',
        justification: 'Every contract requires pricing information',
        linkedAssumptions: costAssumptions,
        section: 'B'
      },
      {
        name: 'Section C - Performance Work Statement',
        category: 'required',
        description: 'Detailed technical requirements, deliverables, and performance standards',
        justification: 'Defines what the contractor must accomplish',
        linkedAssumptions: perfAssumptions,
        section: 'C'
      },
      {
        name: 'Section D - Packaging and Marking',
        category: 'optional',
        description: 'Packaging, labeling, and marking requirements',
        justification: 'Required for product deliveries',
        linkedAssumptions: [],
        section: 'D'
      },
      {
        name: 'Section E - Inspection and Acceptance',
        category: 'recommended',
        description: 'Quality assurance and acceptance procedures',
        justification: 'Defines how deliverables will be inspected',
        linkedAssumptions: perfAssumptions,
        section: 'E'
      },
      {
        name: 'Section F - Delivery/Performance Schedule',
        category: 'required',
        description: 'Period of performance, ordering procedures, and delivery timelines',
        justification: 'Required for all contracts',
        linkedAssumptions: idiqAssumptions,
        section: 'F'
      },
      {
        name: 'Section G - Contract Administration',
        category: 'required',
        description: 'COR designation, reporting requirements, and administration details',
        justification: 'Defines contract management procedures',
        linkedAssumptions: idiqAssumptions,
        section: 'G'
      },
      {
        name: 'Section H - Special Contract Requirements',
        category: 'required',
        description: 'DFARS clauses, CUI handling, CMMC requirements, and security provisions',
        justification: 'Contains special terms and conditions',
        linkedAssumptions: securityAssumptions,
        section: 'H'
      },
      {
        name: 'Section I - Contract Clauses',
        category: 'required',
        description: 'FAR and DFARS clauses incorporated by reference',
        justification: 'Standard clauses required for all contracts',
        linkedAssumptions: [],
        section: 'I'
      },
      {
        name: 'Section J - List of Attachments',
        category: 'optional',
        description: 'Index of exhibits and attachments',
        justification: 'Required if attachments are included',
        linkedAssumptions: [],
        section: 'J'
      },
      {
        name: 'Section K - Representations and Certifications',
        category: 'required',
        description: 'Required contractor certifications and representations',
        justification: 'FAR requires contractor certifications',
        linkedAssumptions: [],
        section: 'K'
      },
      {
        name: 'Section L - Instructions to Offerors',
        category: 'required',
        description: 'Proposal preparation instructions and submission requirements',
        justification: 'Required for competitive procurements',
        linkedAssumptions: evalAssumptions,
        section: 'L'
      },
      {
        name: 'Section M - Evaluation Factors',
        category: 'required',
        description: 'Evaluation criteria, weights, and award decision approach',
        justification: 'FAR 15.304 requires stating evaluation factors',
        linkedAssumptions: evalAssumptions,
        section: 'M'
      },

      // Supporting Documents
      {
        name: 'Independent Government Cost Estimate (IGCE)',
        category: 'recommended',
        description: 'Government estimate of fair and reasonable pricing',
        justification: 'Required for price reasonableness determination',
        linkedAssumptions: costAssumptions
      },
      {
        name: 'Quality Assurance Surveillance Plan (QASP)',
        category: 'recommended',
        description: 'Performance monitoring methods and acceptance criteria',
        justification: 'Best practice for performance-based acquisitions',
        linkedAssumptions: perfAssumptions
      },
      {
        name: 'Market Research Report',
        category: 'recommended',
        description: 'Analysis of commercial capabilities and pricing',
        justification: 'FAR Part 10 requires market research',
        linkedAssumptions: []
      },
      {
        name: 'Acquisition Plan',
        category: 'recommended',
        description: 'Overall acquisition strategy and approach',
        justification: 'Required for acquisitions over SAT',
        linkedAssumptions: []
      },
      {
        name: 'Source Selection Plan',
        category: 'recommended',
        description: 'Evaluation team structure and procedures',
        justification: 'Required for competitive acquisitions',
        linkedAssumptions: evalAssumptions
      },
      {
        name: 'Small Business Subcontracting Plan',
        category: 'recommended',
        description: 'Small business utilization requirements and goals',
        justification: 'Required for contracts over $750K (non-small business)',
        linkedAssumptions: sbAssumptions
      },

      // Pre-Solicitation Documents
      {
        name: 'Presolicitation Notice',
        category: 'optional',
        description: 'Initial market notification to gauge industry interest',
        justification: 'Best practice for complex acquisitions',
        linkedAssumptions: []
      },
      {
        name: 'Sources Sought Notice',
        category: 'optional',
        description: 'Request for capability statements from potential vendors',
        justification: 'Helps identify qualified sources',
        linkedAssumptions: []
      },
      {
        name: 'Draft RFP',
        category: 'optional',
        description: 'Preliminary solicitation for industry feedback',
        justification: 'Allows industry to comment before final RFP',
        linkedAssumptions: []
      },
    ];

    return docs;
  };

  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [phaseAnalysis, setPhaseAnalysis] = useState<any>(null);
  const [analyzingPhase, setAnalyzingPhase] = useState(false);
  const documentList = generateDocumentList();

  // Initialize selected documents with all required and recommended
  useState(() => {
    const initialSelection = new Set(
      documentList
        .filter(d => d.category === 'required' || d.category === 'recommended')
        .map(d => d.name)
    );
    setSelectedDocuments(initialSelection);
  });

  // Analyze phase whenever selection changes
  useEffect(() => {
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

    // Debounce the analysis call
    const timeoutId = setTimeout(analyzePhase, 500);
    return () => clearTimeout(timeoutId);
  }, [selectedDocuments]);

  const toggleDocument = (docName: string, category: 'required' | 'recommended' | 'optional') => {
    if (locked) return; // Can't toggle if locked

    const newSelection = new Set(selectedDocuments);
    if (newSelection.has(docName)) {
      newSelection.delete(docName);
    } else {
      newSelection.add(docName);
    }
    setSelectedDocuments(newSelection);
  };

  const requiredCount = documentList.filter(d => d.category === 'required').length;
  const recommendedCount = documentList.filter(d => d.category === 'recommended' && selectedDocuments.has(d.name)).length;
  const optionalCount = documentList.filter(d => d.category === 'optional' && selectedDocuments.has(d.name)).length;

  return (
    <div className="container mx-auto p-8 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-3">
          Generation Plan
        </h1>
        <p className="text-lg text-muted-foreground">
          Configure which documents to generate for Day-One artifacts
        </p>
      </div>

      {/* Phase Analysis */}
      {selectedDocuments.size > 0 && (
        <div className="mb-8">
          <PhaseInfo analysis={phaseAnalysis} loading={analyzingPhase} />
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
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
              <div className="text-3xl font-bold text-blue-600">{recommendedCount}</div>
              <div className="text-sm text-muted-foreground mt-1">Recommended Selected</div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-200 bg-slate-50/50">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-slate-600">{optionalCount}</div>
              <div className="text-sm text-muted-foreground mt-1">Optional Selected</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-8">
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
          <div className="space-y-4">
            {documentList.map((doc) => {
              const isSelected = selectedDocuments.has(doc.name);
              const isRequired = doc.category === 'required';

              return (
                <Card
                  key={doc.name}
                  className={`border-2 transition-all ${
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
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      {/* Selection Indicator */}
                      <div className="flex-shrink-0 mt-1">
                        {isSelected ? (
                          <CheckCircle2 className={`h-5 w-5 ${
                            isRequired
                              ? 'text-green-600'
                              : doc.category === 'recommended'
                              ? 'text-blue-600'
                              : 'text-slate-600'
                          }`} />
                        ) : (
                          <Circle className="h-5 w-5 text-muted-foreground" />
                        )}
                      </div>

                      {/* Document Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="font-semibold text-lg">{doc.name}</div>
                          {doc.section && (
                            <Badge variant="outline" className="text-xs">
                              Section {doc.section}
                            </Badge>
                          )}
                          <Badge
                            variant={
                              isRequired
                                ? 'default'
                                : doc.category === 'recommended'
                                ? 'secondary'
                                : 'outline'
                            }
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

                        <p className="text-sm text-muted-foreground mb-2">
                          {doc.description}
                        </p>

                        <div className="flex items-start gap-2 mb-3">
                          <Info className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
                          <p className="text-xs text-slate-600 italic">
                            {doc.justification}
                          </p>
                        </div>

                        {/* Linked Assumptions */}
                        {doc.linkedAssumptions.length > 0 && (
                          <div className="flex items-center gap-2 flex-wrap">
                            <FileText className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                              Traced to assumptions:
                            </span>
                            {doc.linkedAssumptions.map((aId) => (
                              <Badge
                                key={aId}
                                variant="outline"
                                className="text-xs bg-blue-50 border-blue-200"
                              >
                                {aId}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Toggle Button */}
                      {!locked && (
                        <Button
                          size="sm"
                          variant={isSelected ? 'default' : 'outline'}
                          onClick={() => toggleDocument(doc.name, doc.category)}
                          className={
                            isSelected && doc.category === 'recommended'
                              ? 'bg-blue-600 hover:bg-blue-700'
                              : isSelected && isRequired
                              ? 'bg-green-600 hover:bg-green-700'
                              : ''
                          }
                        >
                          {isSelected ? (
                            <>
                              <Minus className="h-4 w-4 mr-1" />
                              Remove
                            </>
                          ) : (
                            <>
                              <Plus className="h-4 w-4 mr-1" />
                              Add
                            </>
                          )}
                        </Button>
                      )}
                      {locked && isRequired && (
                        <Badge variant="outline" className="bg-green-50 border-green-200 text-green-700">
                          Required
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        {!locked ? (
          <Button onClick={onLock} className="ml-auto bg-amber-600 hover:bg-amber-700">
            <Lock className="h-4 w-4 mr-2" />
            Lock Plan
          </Button>
        ) : (
          <>
            <Button variant="outline" onClick={onEdit} className="ml-auto">
              Edit Plan
            </Button>
            <Button
              onClick={() => {
                const docsToGenerate = documentList.filter(d => selectedDocuments.has(d.name));
                onGenerate(docsToGenerate);
              }}
              className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              Generate Documents ({selectedDocuments.size})
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
