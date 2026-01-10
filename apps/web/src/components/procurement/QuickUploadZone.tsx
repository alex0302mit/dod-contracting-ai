/**
 * QuickUploadZone Component - Compact Upload Zone for Phase Steps
 * 
 * A minimal-footprint upload component designed to be embedded within
 * phase step headers. It automatically tags uploads with the current phase
 * and provides quick access to the full Knowledge tab.
 * 
 * Features:
 * - Collapsible card design for minimal UI footprint
 * - Auto-tags uploads with phase and optional step context
 * - Shows upload count for the current phase
 * - Quick link to full Knowledge tab
 * - Drag-and-drop support
 * 
 * Dependencies:
 * - knowledgeApi from services/api for document upload
 * - Shadcn UI components for styling
 */

import { useState, useRef, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { 
  Upload, FileText, FolderOpen, Loader2, 
  ChevronDown, ChevronUp, ExternalLink, Database
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Collapsible, 
  CollapsibleContent, 
  CollapsibleTrigger 
} from "@/components/ui/collapsible";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { knowledgeApi, type KnowledgeDocument } from "@/services/api";

// Props interface for QuickUploadZone
interface QuickUploadZoneProps {
  projectId: string;
  phaseId: string;      // Phase ID for API calls
  phaseName: string;    // Display name for the phase
  stepName?: string;    // Optional step context for tagging
  onUploadComplete?: () => void; // Callback after successful upload
}

// Purpose options for quick upload
const PURPOSE_OPTIONS = [
  { value: "regulation", label: "Regulation" },
  { value: "template", label: "Template" },
  { value: "market_research", label: "Market Research" },
  { value: "prior_award", label: "Prior Award" },
  { value: "strategy_memo", label: "Strategy Memo" },
];

export function QuickUploadZone({ 
  projectId, 
  phaseId, 
  phaseName, 
  stepName,
  onUploadComplete 
}: QuickUploadZoneProps) {
  // Query client for cache invalidation
  const queryClient = useQueryClient();
  
  // State management
  const [isOpen, setIsOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [purpose, setPurpose] = useState("regulation");
  const [isDragOver, setIsDragOver] = useState(false);
  
  // File input ref
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch document count for this phase
  const { data: phaseDocCount = 0 } = useQuery({
    queryKey: ['project-knowledge-phase-count', projectId, phaseId],
    queryFn: async () => {
      const response = await knowledgeApi.getProjectKnowledge(projectId);
      const docs = response.documents || [];
      return docs.filter((doc: KnowledgeDocument) => doc.phase === phaseId).length;
    },
    staleTime: 30000, // Cache for 30 seconds
  });

  // Handle file upload
  const handleUpload = async (file: File) => {
    setUploading(true);
    
    try {
      const result = await knowledgeApi.uploadToProject(
        projectId, 
        file, 
        phaseId,
        purpose
      );
      
      toast.success(
        `${result.filename} uploaded to ${phaseName}! Created ${result.chunks_created} chunks.`
      );
      
      // Invalidate queries to refresh counts
      queryClient.invalidateQueries({ queryKey: ['project-knowledge', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-knowledge-phase-count', projectId, phaseId] });
      
      // Call optional callback
      onUploadComplete?.();
    } catch (error: any) {
      console.error('Quick upload error:', error);
      toast.error(`Upload failed: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  // Handle file input change
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      await handleUpload(file);
    }
    event.target.value = '';
  };

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      await handleUpload(files[0]);
    }
  }, [projectId, phaseId, purpose]);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className={`border ${isDragOver ? 'border-blue-400 bg-blue-50/30' : 'border-slate-200'} shadow-sm`}>
        {/* Trigger Header - Always Visible */}
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-50/50 transition-colors rounded-t-lg"
          >
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-blue-100 flex items-center justify-center">
                <Database className="h-4 w-4 text-blue-600" />
              </div>
              <div className="text-left">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-700">
                    Phase Knowledge
                  </span>
                  <Badge 
                    variant="secondary" 
                    className="bg-blue-100 text-blue-700 text-[10px] px-1.5"
                  >
                    {phaseDocCount} doc{phaseDocCount !== 1 ? 's' : ''}
                  </Badge>
                </div>
                <span className="text-xs text-muted-foreground">
                  Upload reference documents for {phaseName}
                </span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {isOpen ? (
                <ChevronUp className="h-4 w-4 text-slate-400" />
              ) : (
                <ChevronDown className="h-4 w-4 text-slate-400" />
              )}
            </div>
          </button>
        </CollapsibleTrigger>

        {/* Expanded Content */}
        <CollapsibleContent>
          <CardContent className="pt-0 pb-4 px-4">
            <div 
              className={`border-2 border-dashed rounded-lg p-4 transition-all ${
                isDragOver 
                  ? 'border-blue-400 bg-blue-50/50' 
                  : 'border-slate-200 hover:border-slate-300'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="flex flex-col sm:flex-row items-center gap-4">
                {/* Upload Area */}
                <div className="flex items-center gap-3 flex-1">
                  <div className={`h-10 w-10 rounded-full flex items-center justify-center transition-all ${
                    isDragOver 
                      ? 'bg-blue-100 text-blue-600' 
                      : 'bg-slate-100 text-slate-500'
                  }`}>
                    {uploading ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <Upload className="h-5 w-5" />
                    )}
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium text-slate-700">
                      {uploading ? 'Uploading...' : isDragOver ? 'Drop here' : 'Add document'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Auto-tagged to {phaseName}
                    </p>
                  </div>
                </div>

                {/* Purpose Selector */}
                <Select value={purpose} onValueChange={setPurpose}>
                  <SelectTrigger className="w-[140px] h-9 text-xs">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent>
                    {PURPOSE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-xs">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Hidden File Input */}
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept=".pdf,.docx,.pptx,.xlsx,.txt,.md"
                  onChange={handleFileChange}
                  disabled={uploading}
                />

                {/* Upload Button */}
                <Button 
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="gap-1.5"
                >
                  {uploading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Upload className="h-4 w-4" />
                  )}
                  Upload
                </Button>
              </div>
            </div>

            {/* Footer with link to full Knowledge tab */}
            <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
              <span>
                PDF, DOCX, PPTX, XLSX, TXT, MD supported
              </span>
              <a 
                href="#" 
                onClick={(e) => {
                  e.preventDefault();
                  // Emit custom event to switch to Knowledge tab
                  window.dispatchEvent(new CustomEvent('navigate-to-knowledge-tab', {
                    detail: { projectId, phase: phaseId }
                  }));
                }}
                className="flex items-center gap-1 text-blue-600 hover:underline"
              >
                View all knowledge
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
