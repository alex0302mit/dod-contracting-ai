/**
 * QuickReviewStep Component
 * 
 * Final step of the Quick Generate wizard - review and export generated documents.
 * Features:
 * - Document navigator sidebar
 * - Preview panel with section content
 * - Quality score badges
 * - Export actions (Download ZIP, Open in Editor)
 * - Regenerate option
 * 
 * Dependencies:
 * - Shadcn UI components for styling
 * - Types from ./types.ts
 */

import { useState } from "react";
import {
  FileText,
  Download,
  ExternalLink,
  RefreshCw,
  ArrowLeft,
  CheckCircle2,
  Award,
  Copy,
  Check,
  ChevronRight,
  Sparkles,
  FileStack,
  AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { QuickReviewStepProps } from "./types";

/**
 * QuickReviewStep displays the final generated documents for review.
 * Users can preview content, export, or open in the full editor.
 */
export function QuickReviewStep({
  sections,
  qualityAnalysis,
  onOpenEditor,
  onDownload,
  onBack,
  onRegenerate
}: QuickReviewStepProps) {
  // Currently selected section for preview
  const [selectedSection, setSelectedSection] = useState<string | null>(
    Object.keys(sections)[0] || null
  );
  
  // Track if content was copied
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  // Get section names sorted by UCF section order
  const sectionNames = Object.keys(sections).sort((a, b) => {
    // Extract section letters for sorting (e.g., "Section A" -> "A")
    const getSection = (name: string) => {
      const match = name.match(/Section\s+([A-Z])/i);
      return match ? match[1] : name;
    };
    return getSection(a).localeCompare(getSection(b));
  });

  // Calculate overall quality score
  const overallQuality = qualityAnalysis?.overall_score || 
    Math.round(Object.values(qualityAnalysis || {}).reduce((sum: number, q: any) => {
      return sum + (typeof q === 'number' ? q : q?.score || 85);
    }, 0) / Math.max(Object.keys(qualityAnalysis || {}).length, 1)) || 85;

  /**
   * Get quality score for a specific section
   */
  const getSectionQuality = (sectionName: string): number => {
    if (!qualityAnalysis) return 85;
    const sectionData = qualityAnalysis[sectionName];
    if (typeof sectionData === 'number') return sectionData;
    if (sectionData?.score) return sectionData.score;
    return 85;
  };

  /**
   * Get quality badge color based on score
   */
  const getQualityColor = (score: number): string => {
    if (score >= 90) return 'bg-emerald-500';
    if (score >= 75) return 'bg-blue-500';
    if (score >= 60) return 'bg-amber-500';
    return 'bg-red-500';
  };

  /**
   * Copy section content to clipboard
   */
  const handleCopySection = async (sectionName: string) => {
    const content = sections[sectionName];
    // Strip HTML tags for clipboard
    const textContent = content.replace(/<[^>]*>/g, '');
    
    try {
      await navigator.clipboard.writeText(textContent);
      setCopiedSection(sectionName);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopiedSection(null), 2000);
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  };

  /**
   * Categorize sections into groups
   */
  const categorizedSections = {
    solicitation: sectionNames.filter(name => name.includes('Section')),
    supporting: sectionNames.filter(name => !name.includes('Section'))
  };

  return (
    <div className="space-y-6">
      {/* Header with Summary */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-emerald-500" />
            Package Ready!
          </h2>
          <p className="text-muted-foreground">
            Your contracting package has been generated. Review the content below.
          </p>
        </div>

        {/* Quality Badge */}
        <Card className="bg-gradient-to-br from-emerald-50 to-white border-emerald-200">
          <CardContent className="py-4 px-6">
            <div className="flex items-center gap-3">
              <div className={`h-12 w-12 rounded-full ${getQualityColor(overallQuality)} flex items-center justify-center`}>
                <Award className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-2xl font-bold text-emerald-700">{overallQuality}%</p>
                <p className="text-sm text-muted-foreground">Quality Score</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{categorizedSections.solicitation.length}</p>
                <p className="text-sm text-muted-foreground">Solicitation Sections</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <FileStack className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{categorizedSections.supporting.length}</p>
                <p className="text-sm text-muted-foreground">Supporting Documents</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{sectionNames.length}</p>
                <p className="text-sm text-muted-foreground">Total Documents</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-12 gap-6 min-h-[500px]">
        {/* Document Navigator Sidebar */}
        <Card className="col-span-4">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Document Navigator</CardTitle>
            <CardDescription>Click to preview content</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[450px]">
              {/* Solicitation Sections */}
              {categorizedSections.solicitation.length > 0 && (
                <div className="px-4 py-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                    Solicitation Sections
                  </p>
                  <div className="space-y-1">
                    {categorizedSections.solicitation.map((name) => {
                      const quality = getSectionQuality(name);
                      const isSelected = selectedSection === name;
                      
                      return (
                        <button
                          key={name}
                          onClick={() => setSelectedSection(name)}
                          className={`
                            w-full flex items-center justify-between p-2 rounded-lg text-left text-sm
                            transition-all duration-150
                            ${isSelected 
                              ? 'bg-blue-100 text-blue-900 font-medium' 
                              : 'hover:bg-slate-100 text-slate-700'}
                          `}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <CheckCircle2 className={`h-4 w-4 shrink-0 ${isSelected ? 'text-blue-600' : 'text-emerald-500'}`} />
                            <span className="truncate">{name}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className={`text-xs ${getQualityColor(quality)} text-white border-0`}>
                              {quality}%
                            </Badge>
                            {isSelected && <ChevronRight className="h-4 w-4" />}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Supporting Documents */}
              {categorizedSections.supporting.length > 0 && (
                <div className="px-4 py-2">
                  <Separator className="my-2" />
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                    Supporting Documents
                  </p>
                  <div className="space-y-1">
                    {categorizedSections.supporting.map((name) => {
                      const quality = getSectionQuality(name);
                      const isSelected = selectedSection === name;
                      
                      return (
                        <button
                          key={name}
                          onClick={() => setSelectedSection(name)}
                          className={`
                            w-full flex items-center justify-between p-2 rounded-lg text-left text-sm
                            transition-all duration-150
                            ${isSelected 
                              ? 'bg-blue-100 text-blue-900 font-medium' 
                              : 'hover:bg-slate-100 text-slate-700'}
                          `}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <CheckCircle2 className={`h-4 w-4 shrink-0 ${isSelected ? 'text-blue-600' : 'text-emerald-500'}`} />
                            <span className="truncate">{name}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className={`text-xs ${getQualityColor(quality)} text-white border-0`}>
                              {quality}%
                            </Badge>
                            {isSelected && <ChevronRight className="h-4 w-4" />}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Preview Panel */}
        <Card className="col-span-8">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg">
                {selectedSection || 'Select a document'}
              </CardTitle>
              {selectedSection && (
                <CardDescription>
                  Quality: {getSectionQuality(selectedSection)}% • Generated content preview
                </CardDescription>
              )}
            </div>
            {selectedSection && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopySection(selectedSection)}
                className="gap-2"
              >
                {copiedSection === selectedSection ? (
                  <>
                    <Check className="h-4 w-4 text-emerald-500" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Copy
                  </>
                )}
              </Button>
            )}
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              {selectedSection ? (
                <div 
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: sections[selectedSection] }}
                />
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Select a document from the navigator to preview</p>
                  </div>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <Card className="bg-gradient-to-r from-slate-50 to-white">
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={onBack} className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Selection
              </Button>
              <Button variant="outline" onClick={onRegenerate} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Regenerate
              </Button>
            </div>

            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={onDownload} className="gap-2">
                <Download className="h-4 w-4" />
                Download ZIP
              </Button>
              <Button 
                onClick={onOpenEditor}
                className="gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
              >
                <ExternalLink className="h-4 w-4" />
                Open in Full Editor
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tips */}
      <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5 shrink-0" />
        <div>
          <p className="font-medium text-blue-800 text-sm">Next Steps</p>
          <ul className="text-sm text-blue-700 mt-1 space-y-1 list-disc list-inside">
            <li>Open in the full editor for detailed editing and formatting</li>
            <li>Use compliance check before final export</li>
            <li>Download as ZIP to get individual DOCX files</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
