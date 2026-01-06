/**
 * KnowledgeTab Component - Project-Scoped Document Library
 * 
 * A project-scoped knowledge hub with:
 * - Drag-and-drop upload zone for project documents
 * - Phase tagging for uploaded documents
 * - Category-based filtering (Regulations, Templates, Market Research, Prior Awards)
 * - RAG indexing status display
 * - Document cards with delete functionality
 * 
 * This component replaces the global UploadCenter with a project-centric approach.
 * All documents uploaded here are automatically associated with the current project
 * and indexed into the RAG pipeline for AI-powered document generation.
 * 
 * Dependencies:
 * - knowledgeApi from services/api for project-scoped document operations
 * - Shadcn UI components for styling
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { 
  Upload, FileText, Trash2, Search, 
  Loader2, FolderOpen, FileStack, AlertCircle, X,
  FileType, Calendar, HardDrive, Database, CheckCircle2,
  BookOpen, Scale, FileBarChart, Award, RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle 
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { knowledgeApi, type KnowledgeDocument } from "@/services/api";
import { format } from "date-fns";

// Props interface for the KnowledgeTab component
interface KnowledgeTabProps {
  projectId: string;
  currentPhase?: string;
}

// Document purpose types for categorization
type PurposeType = "all" | "regulation" | "template" | "market_research" | "prior_award" | "strategy_memo";

// Purpose configuration for UI display
const PURPOSE_CONFIG: Record<PurposeType, { 
  label: string; 
  icon: React.ReactNode; 
  color: string;
  bgGradient: string;
  description: string;
}> = {
  all: {
    label: "All Documents",
    icon: <FolderOpen className="h-4 w-4" />,
    color: "bg-slate-500",
    bgGradient: "from-slate-500 to-slate-600",
    description: "View all project knowledge documents"
  },
  regulation: {
    label: "Regulations",
    icon: <Scale className="h-4 w-4" />,
    color: "bg-blue-600",
    bgGradient: "from-blue-600 to-blue-700",
    description: "FAR, DFARS, and policy documents"
  },
  template: {
    label: "Templates",
    icon: <FileType className="h-4 w-4" />,
    color: "bg-amber-500",
    bgGradient: "from-amber-500 to-amber-600",
    description: "Standard forms and document templates"
  },
  market_research: {
    label: "Market Research",
    icon: <FileBarChart className="h-4 w-4" />,
    color: "bg-emerald-500",
    bgGradient: "from-emerald-500 to-emerald-600",
    description: "Market analysis and vendor research"
  },
  prior_award: {
    label: "Prior Awards",
    icon: <Award className="h-4 w-4" />,
    color: "bg-violet-500",
    bgGradient: "from-violet-500 to-violet-600",
    description: "Historical contract data and awards"
  },
  strategy_memo: {
    label: "Strategy Memos",
    icon: <BookOpen className="h-4 w-4" />,
    color: "bg-rose-500",
    bgGradient: "from-rose-500 to-rose-600",
    description: "Acquisition strategy documents"
  }
};

// Phase options for document tagging
const PHASE_OPTIONS = [
  { value: "pre_solicitation", label: "Pre-Solicitation" },
  { value: "solicitation", label: "Solicitation" },
  { value: "post_solicitation", label: "Post-Solicitation" },
];

export function KnowledgeTab({ projectId, currentPhase }: KnowledgeTabProps) {
  // Query client for cache invalidation
  const queryClient = useQueryClient();
  
  // State management
  const [activePurpose, setActivePurpose] = useState<PurposeType>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadPurpose, setUploadPurpose] = useState<PurposeType>("regulation");
  const [uploadPhase, setUploadPhase] = useState<string>(currentPhase || "pre_solicitation");
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeDocument | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  
  // File input ref for upload
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch documents from project knowledge API
  const { 
    data: documents = [], 
    isLoading, 
    isFetching,
    refetch 
  } = useQuery({
    queryKey: ['project-knowledge', projectId],
    queryFn: async () => {
      const response = await knowledgeApi.getProjectKnowledge(projectId);
      return response.documents || [];
    },
  });

  // Filter documents based on purpose and search
  const filteredDocs = documents.filter((doc: KnowledgeDocument) => {
    // Filter by purpose
    if (activePurpose !== "all" && doc.purpose !== activePurpose) {
      return false;
    }
    
    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      return (
        doc.filename.toLowerCase().includes(query) ||
        doc.file_type.toLowerCase().includes(query) ||
        (doc.phase && doc.phase.toLowerCase().includes(query))
      );
    }
    
    return true;
  });

  // Handle file upload with project context
  const handleUpload = async (file: File) => {
    setUploading(true);
    
    try {
      const result = await knowledgeApi.uploadToProject(
        projectId, 
        file, 
        uploadPhase, 
        uploadPurpose
      );
      toast.success(
        `${result.filename} uploaded successfully! Created ${result.chunks_created} chunks for RAG.`
      );
      
      // Refresh document list
      queryClient.invalidateQueries({ queryKey: ['project-knowledge', projectId] });
    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error(`Failed to upload: ${error.message}`);
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
    // Reset input
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
  }, [projectId, uploadPhase, uploadPurpose]);

  // Handle document deletion
  const handleDelete = async () => {
    if (!deleteTarget) return;
    
    setDeleting(true);
    try {
      await knowledgeApi.deleteFromProject(projectId, deleteTarget.id);
      toast.success(`${deleteTarget.filename} deleted successfully`);
      queryClient.invalidateQueries({ queryKey: ['project-knowledge', projectId] });
    } catch (error: any) {
      console.error('Delete error:', error);
      toast.error(`Failed to delete: ${error.message}`);
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  // Get file type icon based on extension
  const getFileIcon = (fileType: string) => {
    const type = fileType.toLowerCase();
    if (type === 'pdf') return <FileText className="h-5 w-5 text-red-500" />;
    if (type === 'docx' || type === 'doc') return <FileText className="h-5 w-5 text-blue-500" />;
    if (type === 'xlsx' || type === 'xls') return <FileStack className="h-5 w-5 text-green-500" />;
    if (type === 'pptx' || type === 'ppt') return <FileType className="h-5 w-5 text-orange-500" />;
    if (type === 'md' || type === 'txt') return <FileText className="h-5 w-5 text-slate-500" />;
    return <FileText className="h-5 w-5 text-slate-400" />;
  };

  // Format file size for display
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Get purpose counts for tabs
  const getPurposeCounts = () => {
    const counts: Record<PurposeType, number> = {
      all: documents.length,
      regulation: 0,
      template: 0,
      market_research: 0,
      prior_award: 0,
      strategy_memo: 0
    };
    
    documents.forEach((doc: KnowledgeDocument) => {
      if (doc.purpose && doc.purpose in counts) {
        counts[doc.purpose as PurposeType]++;
      }
    });
    
    return counts;
  };

  const purposeCounts = getPurposeCounts();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Database className="h-6 w-6 text-blue-600" />
          Project Knowledge
        </h2>
        <p className="text-muted-foreground mt-1">
          Upload reference documents to inform AI-powered document generation. 
          All documents are indexed for retrieval during generation.
        </p>
      </div>

      {/* Upload Zone with Phase & Purpose Selection */}
      <Card 
        className={`border-2 border-dashed transition-all duration-200 ${
          isDragOver 
            ? 'border-blue-500 bg-blue-50/50 scale-[1.005]' 
            : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50/50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="py-8">
          <div className="flex flex-col items-center justify-center text-center">
            <div className={`h-14 w-14 rounded-full flex items-center justify-center mb-4 transition-all ${
              isDragOver 
                ? 'bg-blue-100 text-blue-600 scale-110' 
                : 'bg-slate-100 text-slate-500'
            }`}>
              {uploading ? (
                <Loader2 className="h-7 w-7 animate-spin" />
              ) : (
                <Upload className="h-7 w-7" />
              )}
            </div>
            
            <h3 className="text-lg font-semibold mb-2">
              {uploading ? 'Uploading & Indexing...' : isDragOver ? 'Drop file here' : 'Add Knowledge Document'}
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              Drag & drop or click to browse • PDF, DOCX, PPTX, XLSX, TXT, MD
            </p>
            
            {/* Upload Options */}
            <div className="flex flex-wrap items-center justify-center gap-3 mb-4">
              {/* Phase Selector */}
              <Select value={uploadPhase} onValueChange={setUploadPhase}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="Select phase" />
                </SelectTrigger>
                <SelectContent>
                  {PHASE_OPTIONS.map((phase) => (
                    <SelectItem key={phase.value} value={phase.value}>
                      {phase.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Purpose Selector */}
              <Select 
                value={uploadPurpose} 
                onValueChange={(v) => setUploadPurpose(v as PurposeType)}
              >
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="Document type" />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(PURPOSE_CONFIG) as PurposeType[])
                    .filter(p => p !== 'all')
                    .map((purpose) => (
                      <SelectItem key={purpose} value={purpose}>
                        <div className="flex items-center gap-2">
                          {PURPOSE_CONFIG[purpose].icon}
                          {PURPOSE_CONFIG[purpose].label}
                        </div>
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.docx,.pptx,.xlsx,.txt,.md"
              onChange={handleFileChange}
              disabled={uploading}
            />
            
            <Button 
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="gap-2"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Select File
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Purpose Tabs & Search */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <Tabs value={activePurpose} onValueChange={(v) => setActivePurpose(v as PurposeType)}>
          <TabsList className="h-auto flex-wrap">
            {(Object.keys(PURPOSE_CONFIG) as PurposeType[]).map((purpose) => (
              <TabsTrigger 
                key={purpose} 
                value={purpose}
                className="gap-2 data-[state=active]:bg-white"
              >
                {PURPOSE_CONFIG[purpose].icon}
                <span className="hidden sm:inline">{PURPOSE_CONFIG[purpose].label}</span>
                <Badge variant="secondary" className="ml-1 h-5 min-w-[20px] text-xs">
                  {purposeCounts[purpose]}
                </Badge>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        <div className="flex items-center gap-2">
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6"
                onClick={() => setSearchQuery("")}
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
          
          {/* Refresh Button */}
          <Button
            variant="outline"
            size="icon"
            onClick={() => refetch()}
            disabled={isFetching}
            title="Refresh documents"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Document Grid */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                {PURPOSE_CONFIG[activePurpose].icon}
                {PURPOSE_CONFIG[activePurpose].label}
              </CardTitle>
              <CardDescription>
                {PURPOSE_CONFIG[activePurpose].description}
              </CardDescription>
            </div>
            <Badge variant="secondary" className="text-sm">
              {filteredDocs.length} document{filteredDocs.length !== 1 ? 's' : ''}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : filteredDocs.length > 0 ? (
            <ScrollArea className="h-[400px] pr-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredDocs.map((doc: KnowledgeDocument) => (
                  <Card 
                    key={doc.id} 
                    className="group hover:shadow-md transition-all duration-200 hover:border-blue-200"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        {/* File Icon */}
                        <div className={`h-10 w-10 rounded-lg bg-gradient-to-br ${
                          doc.purpose ? PURPOSE_CONFIG[doc.purpose as PurposeType]?.bgGradient : PURPOSE_CONFIG.regulation.bgGradient
                        } flex items-center justify-center text-white shadow-sm`}>
                          {getFileIcon(doc.file_type)}
                        </div>

                        {/* Document Info */}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-sm truncate" title={doc.filename}>
                            {doc.filename}
                          </h4>
                          
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            <Badge 
                              variant="outline" 
                              className={`text-[10px] uppercase ${
                                doc.purpose ? PURPOSE_CONFIG[doc.purpose as PurposeType]?.color : 'bg-slate-500'
                              } text-white border-0`}
                            >
                              {doc.file_type}
                            </Badge>
                            {doc.phase && (
                              <Badge variant="secondary" className="text-[10px]">
                                {doc.phase.replace('_', '-')}
                              </Badge>
                            )}
                            {/* RAG Indexed Indicator */}
                            {doc.rag_indexed && (
                              <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-300 bg-emerald-50">
                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                Indexed
                              </Badge>
                            )}
                          </div>

                          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <HardDrive className="h-3 w-3" />
                              {formatFileSize(doc.file_size)}
                            </span>
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {format(new Date(doc.upload_date), 'MMM d, yyyy')}
                            </span>
                          </div>
                        </div>

                        {/* Delete Button */}
                        <button
                          type="button"
                          className="h-8 w-8 rounded-md flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                          onClick={() => setDeleteTarget(doc)}
                          title="Delete document"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="h-16 w-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                <FolderOpen className="h-8 w-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-medium text-slate-700 mb-1">
                {searchQuery ? 'No matching documents' : 'No knowledge documents yet'}
              </h3>
              <p className="text-sm text-muted-foreground mb-4 max-w-md">
                {searchQuery 
                  ? 'Try adjusting your search or filter' 
                  : 'Upload regulations, templates, market research, or prior awards to help AI generate better documents.'}
              </p>
              {!searchQuery && (
                <Button 
                  variant="outline" 
                  onClick={() => fileInputRef.current?.click()}
                  className="gap-2"
                >
                  <Upload className="h-4 w-4" />
                  Upload First Document
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              Delete Knowledge Document
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete <strong>{deleteTarget?.filename}</strong>? 
              This will remove the document from this project's knowledge base and the RAG index. 
              AI-generated documents that used this source will not be affected.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
