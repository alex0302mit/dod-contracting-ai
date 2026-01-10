import { useState, useEffect, useMemo, useCallback } from "react";
import { ArrowLeft, Download, FileText, FileArchive, AlertCircle, CheckCircle, Loader2, Clock, List, CheckSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import {
  prepareExport,
  downloadPDF,
  downloadDOCX,
  downloadJSON,
  downloadComplianceReport,
  downloadAllFormats,
  getExportHistory,
  validateExportData,
  type ExportPrepareResponse,
  type ExportHistoryItem
} from "@/lib/exportUtils";
import { performComplianceAnalysis } from "@/lib/complianceUtils";

interface ExportViewProps {
  sections: Record<string, string>;
  citations: any[];
  metadata: any;
  agentMetadata?: any;
  collaborationMetadata?: any;
  onBack: () => void;
}

export function ExportView({
  sections,
  citations,
  metadata,
  agentMetadata,
  collaborationMetadata,
  onBack
}: ExportViewProps) {
  const [exportData, setExportData] = useState<ExportPrepareResponse | null>(null);
  const [isPreparingExport, setIsPreparingExport] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);
  const [exportHistory, setExportHistory] = useState<ExportHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  
  // NEW: State for export mode and section selection
  // exportMode: 'all' exports everything, 'selected' exports only checked sections
  const [exportMode, setExportMode] = useState<'all' | 'selected'>('all');
  // selectedSections: Set of section names that are selected for export
  const [selectedSections, setSelectedSections] = useState<Set<string>>(
    new Set(Object.keys(sections))
  );

  // Prepare export metadata
  const fullMetadata = {
    ...metadata,
    agent_metadata: agentMetadata,
    collaboration_metadata: collaborationMetadata,
    project_name: metadata?.project_name || 'DoD Procurement Document',
    date: new Date().toISOString(),
  };

  // Validate export data
  const validation = validateExportData(sections, citations, fullMetadata);
  
  // Compute sections to export based on mode
  // If 'all' mode, export all sections; if 'selected' mode, export only selected ones
  const sectionsToExport = useMemo(() => {
    if (exportMode === 'all') {
      return Object.keys(sections);
    }
    return Array.from(selectedSections);
  }, [exportMode, selectedSections, sections]);
  
  // Handler to toggle a section's selection
  const toggleSection = useCallback((sectionName: string) => {
    setSelectedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionName)) {
        newSet.delete(sectionName);
      } else {
        newSet.add(sectionName);
      }
      return newSet;
    });
  }, []);
  
  // Handler to select all sections
  const selectAllSections = useCallback(() => {
    setSelectedSections(new Set(Object.keys(sections)));
  }, [sections]);
  
  // Handler to clear all section selections
  const clearAllSections = useCallback(() => {
    setSelectedSections(new Set());
  }, []);

  // Prepare export when mode or selection changes
  useEffect(() => {
    async function prepare() {
      // Don't prepare if validation failed
      if (!validation.valid) {
        setExportError(validation.errors.join('; '));
        return;
      }
      
      // Don't prepare if in 'selected' mode with no selections
      if (exportMode === 'selected' && sectionsToExport.length === 0) {
        setExportData(null);
        return;
      }

      setIsPreparingExport(true);
      setExportError(null);

      try {
        // Pass selected sections to backend for filtering
        // If exportMode is 'all', pass undefined to export everything
        const selectedForBackend = exportMode === 'selected' ? sectionsToExport : undefined;
        
        const result = await prepareExport(
          sections,
          citations,
          fullMetadata,
          Object.keys(sections),
          selectedForBackend
        );
        setExportData(result);
      } catch (error) {
        console.error('Export preparation error:', error);
        setExportError(error instanceof Error ? error.message : 'Failed to prepare export');
      } finally {
        setIsPreparingExport(false);
      }
    }

    prepare();
  }, [exportMode, sectionsToExport.length]); // Re-prepare when mode or selection count changes

  // Load export history
  async function loadHistory() {
    try {
      const history = await getExportHistory(10);
      setExportHistory(history.exports);
      setShowHistory(true);
    } catch (error) {
      console.error('Failed to load export history:', error);
    }
  }

  // Download handlers
  async function handleDownloadPDF() {
    if (!exportData) return;

    setDownloadingFormat('pdf');
    try {
      await downloadPDF(exportData.export_id);
    } catch (error) {
      console.error('PDF download error:', error);
      setExportError(error instanceof Error ? error.message : 'Failed to download PDF');
    } finally {
      setDownloadingFormat(null);
    }
  }

  async function handleDownloadDOCX() {
    if (!exportData) return;

    setDownloadingFormat('docx');
    try {
      await downloadDOCX(exportData.export_id, fullMetadata.project_name);
    } catch (error) {
      console.error('DOCX download error:', error);
      setExportError(error instanceof Error ? error.message : 'Failed to download DOCX');
    } finally {
      setDownloadingFormat(null);
    }
  }

  async function handleDownloadJSON() {
    if (!exportData) return;

    setDownloadingFormat('json');
    try {
      await downloadJSON(exportData.export_id);
    } catch (error) {
      console.error('JSON download error:', error);
      setExportError(error instanceof Error ? error.message : 'Failed to download JSON');
    } finally {
      setDownloadingFormat(null);
    }
  }

  async function handleDownloadComplianceReport() {
    setDownloadingFormat('compliance');
    try {
      // Generate compliance analysis
      const complianceAnalysis = performComplianceAnalysis(sections, citations);
      await downloadComplianceReport(complianceAnalysis);
    } catch (error) {
      console.error('Compliance report download error:', error);
      setExportError(error instanceof Error ? error.message : 'Failed to download compliance report');
    } finally {
      setDownloadingFormat(null);
    }
  }

  async function handleDownloadAll() {
    if (!exportData) return;

    setDownloadingFormat('all');
    try {
      await downloadAllFormats(exportData.export_id, fullMetadata.project_name);
    } catch (error) {
      console.error('Batch download error:', error);
      setExportError(error instanceof Error ? error.message : 'Failed to download all formats');
    } finally {
      setDownloadingFormat(null);
    }
  }

  const exportFormats = [
    {
      id: 'pdf',
      name: "PDF with citations",
      icon: FileText,
      description: "Complete document with embedded citations and references",
      size: exportData?.file_sizes.pdf || "Calculating...",
      handler: handleDownloadPDF
    },
    {
      id: 'docx',
      name: "DOCX editable",
      icon: FileText,
      description: "Microsoft Word format for further editing",
      size: exportData?.file_sizes.docx || "Calculating...",
      handler: handleDownloadDOCX
    },
    {
      id: 'json',
      name: "JSON metadata",
      icon: FileArchive,
      description: "Structured data including assumptions and traceability",
      size: exportData?.file_sizes.json || "Calculating...",
      handler: handleDownloadJSON
    },
  ];

  return (
    <div className="container mx-auto p-8 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-3">
          Export Documents
        </h1>
        <p className="text-lg text-muted-foreground">
          Download your generated acquisition documents in multiple formats
        </p>
      </div>

      {/* Validation Errors */}
      {!validation.valid && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Cannot export document:</strong>
            <ul className="list-disc list-inside mt-2">
              {validation.errors.map((error, idx) => (
                <li key={idx}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Export Error */}
      {exportError && validation.valid && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {exportError}
          </AlertDescription>
        </Alert>
      )}

      {/* Preparing Export */}
      {isPreparingExport && (
        <Alert className="mb-6">
          <Loader2 className="h-4 w-4 animate-spin" />
          <AlertDescription>
            Preparing export files...
          </AlertDescription>
        </Alert>
      )}

      {/* Export Ready */}
      {exportData && (
        <Alert className="mb-6 border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Export prepared successfully! Your documents are ready to download.
          </AlertDescription>
        </Alert>
      )}

      {/* Document Preview & Section Selection */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Select Sections to Export</CardTitle>
          <CardDescription>
            Choose which sections to include in your export
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Export Mode Toggle - Switch between exporting all or selected sections */}
          <div className="flex items-center gap-2 mb-4">
            <Button
              variant={exportMode === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setExportMode('all')}
              className={exportMode === 'all' ? 'bg-blue-600 hover:bg-blue-700' : ''}
            >
              <List className="h-4 w-4 mr-2" />
              Export All
            </Button>
            <Button
              variant={exportMode === 'selected' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setExportMode('selected')}
              className={exportMode === 'selected' ? 'bg-blue-600 hover:bg-blue-700' : ''}
            >
              <CheckSquare className="h-4 w-4 mr-2" />
              Export Selected
            </Button>
          </div>
          
          {/* Quick Actions - Only visible in 'selected' mode */}
          {exportMode === 'selected' && (
            <div className="flex items-center gap-2 mb-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAllSections}
                className="text-xs"
              >
                Select All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllSections}
                className="text-xs"
              >
                Clear All
              </Button>
              <span className="ml-auto text-xs text-muted-foreground">
                {selectedSections.size} of {Object.keys(sections).length} sections selected
              </span>
            </div>
          )}
          
          {/* Document Metadata Summary */}
          <div className="space-y-2 mb-4 pb-4 border-b">
            <div className="flex justify-between text-sm">
              <span className="font-medium">Project Name:</span>
              <span>{fullMetadata.project_name}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="font-medium">Sections to Export:</span>
              <span>{sectionsToExport.length} of {Object.keys(sections).length}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="font-medium">Citations:</span>
              <span>{citations.length}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="font-medium">Export Date:</span>
              <span>{new Date().toLocaleDateString()}</span>
            </div>
          </div>

          {/* Section List with Checkboxes */}
          <div className="mt-4">
            <h4 className="font-medium text-sm mb-3">
              {exportMode === 'all' ? 'All Sections:' : 'Select Sections:'}
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {Object.entries(sections).map(([name, content]) => {
                const plainText = content.replace(/<[^>]*>/g, '');
                const wordCount = plainText.split(/\s+/).filter(Boolean).length;
                const isSelected = selectedSections.has(name);
                const isIncluded = exportMode === 'all' || isSelected;
                
                return (
                  <div
                    key={name}
                    className={`flex items-center gap-3 p-3 rounded-lg border transition-colors cursor-pointer ${
                      isIncluded
                        ? 'bg-blue-50 border-blue-200'
                        : 'bg-slate-50 border-slate-200 opacity-60'
                    } ${exportMode === 'selected' ? 'hover:border-blue-400' : ''}`}
                    onClick={() => exportMode === 'selected' && toggleSection(name)}
                  >
                    {/* Show checkbox only in 'selected' mode */}
                    {exportMode === 'selected' && (
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => toggleSection(name)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{name}</div>
                      <div className="text-xs text-muted-foreground">{wordCount} words</div>
                    </div>
                    {isIncluded && (
                      <CheckCircle className="h-4 w-4 text-blue-500 flex-shrink-0" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          
          {/* Warning if no sections selected */}
          {exportMode === 'selected' && selectedSections.size === 0 && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Please select at least one section to export.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Export Formats */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Export Formats</CardTitle>
          <CardDescription>Select format and download your documents</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {exportFormats.map((format) => (
              <div
                key={format.id}
                className="flex items-center gap-4 p-4 rounded-lg border-2 hover:border-primary transition-colors"
              >
                <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white flex-shrink-0">
                  <format.icon className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <div className="font-medium">{format.name}</div>
                  <div className="text-xs text-muted-foreground mt-1">{format.description}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-muted-foreground mb-2">{format.size}</div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={format.handler}
                    disabled={!exportData || downloadingFormat !== null}
                  >
                    {downloadingFormat === format.id ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Downloading...
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </>
                    )}
                  </Button>
                </div>
              </div>
            ))}

            {/* Compliance Report */}
            <div className="flex items-center gap-4 p-4 rounded-lg border-2 border-purple-200 bg-purple-50 hover:border-purple-400 transition-colors">
              <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white flex-shrink-0">
                <FileText className="h-6 w-6" />
              </div>
              <div className="flex-1">
                <div className="font-medium">Compliance Report</div>
                <div className="text-xs text-muted-foreground mt-1">
                  Detailed FAR/DFARS compliance analysis with scores
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground mb-2">PDF</div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleDownloadComplianceReport}
                  disabled={downloadingFormat !== null}
                  className="border-purple-300 hover:bg-purple-100"
                >
                  {downloadingFormat === 'compliance' ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Export History */}
      {showHistory && exportHistory.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Recent Exports</CardTitle>
            <CardDescription>Previously generated exports</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {exportHistory.map((item) => (
                <div
                  key={item.export_id}
                  className="flex items-center gap-3 p-3 rounded-lg border bg-slate-50"
                >
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{item.project_name}</div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(item.export_date).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {item.files.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>

        {!showHistory && (
          <Button variant="ghost" onClick={loadHistory}>
            <Clock className="h-4 w-4 mr-2" />
            View History
          </Button>
        )}

        <Button
          className="ml-auto bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700"
          onClick={handleDownloadAll}
          disabled={!exportData || downloadingFormat !== null}
        >
          {downloadingFormat === 'all' ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Downloading...
            </>
          ) : (
            <>
              <Download className="h-4 w-4 mr-2" />
              Download All Files
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
