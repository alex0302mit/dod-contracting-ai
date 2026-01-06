/**
 * UploadCenter Component - Redesigned
 * 
 * A unified document library with:
 * - Drag-and-drop upload zone
 * - Category-based filtering tabs
 * - Document cards with delete functionality
 * - Visual categorization with color-coded badges
 * 
 * Dependencies:
 * - ragApi from services/api for document operations
 * - Shadcn UI components for styling
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { 
  ArrowLeft, Upload, FileText, Trash2, Search, 
  Sparkles, Loader2, CheckCircle2, Filter, 
  FolderOpen, FileStack, AlertCircle, X,
  FileType, Calendar, HardDrive
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle 
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { ragApi, type RAGDocument } from "@/services/api";
import { format } from "date-fns";

// Props interface for the UploadCenter component
interface UploadCenterProps {
  uploads: { strategy: string[]; reqs: string[]; market_research: string[]; templates: string[] };
  setUploads: (uploads: any) => void;
  parsed: any;
  setParsed: (parsed: any) => void;
  onExtract: (assumptions: any[]) => void;
  onBack: () => void;
}

// Category type definition for document categorization
type CategoryType = "all" | "strategy" | "market_research" | "requirements" | "templates";

// Category configuration for UI display
const CATEGORY_CONFIG: Record<CategoryType, { 
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
    description: "View all uploaded documents"
  },
  strategy: {
    label: "Acquisition Strategy",
    icon: <FileText className="h-4 w-4" />,
    color: "bg-blue-500",
    bgGradient: "from-blue-500 to-blue-600",
    description: "Strategy and planning documents"
  },
  market_research: {
    label: "Market Research",
    icon: <Search className="h-4 w-4" />,
    color: "bg-emerald-500",
    bgGradient: "from-emerald-500 to-emerald-600",
    description: "Market analysis and reports"
  },
  requirements: {
    label: "Requirements",
    icon: <FileStack className="h-4 w-4" />,
    color: "bg-violet-500",
    bgGradient: "from-violet-500 to-violet-600",
    description: "Requirements and CDRLs"
  },
  templates: {
    label: "Templates",
    icon: <FileType className="h-4 w-4" />,
    color: "bg-amber-500",
    bgGradient: "from-amber-500 to-amber-600",
    description: "Standard forms and templates"
  }
};

// Extended RAGDocument with category
interface CategorizedDocument extends RAGDocument {
  category?: CategoryType;
}

export function UploadCenter({ 
  uploads, 
  setUploads, 
  parsed: _parsed, 
  setParsed: _setParsed, 
  onExtract, 
  onBack 
}: UploadCenterProps) {
  // State management
  const [documents, setDocuments] = useState<CategorizedDocument[]>([]);
  const [filteredDocs, setFilteredDocs] = useState<CategorizedDocument[]>([]);
  const [activeCategory, setActiveCategory] = useState<CategoryType>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadingCategory, setUploadingCategory] = useState<CategoryType | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<CategorizedDocument | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  
  // File input ref for upload
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  // Filter documents when category or search changes
  useEffect(() => {
    let filtered = documents;
    
    // Filter by category
    if (activeCategory !== "all") {
      filtered = filtered.filter(doc => doc.category === activeCategory);
    }
    
    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(doc => 
        doc.filename.toLowerCase().includes(query) ||
        doc.file_type.toLowerCase().includes(query)
      );
    }
    
    setFilteredDocs(filtered);
  }, [documents, activeCategory, searchQuery]);

  // Load documents from backend
  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await ragApi.listDocuments();
      // Parse category from filename or metadata
      const categorizedDocs: CategorizedDocument[] = response.documents.map(doc => ({
        ...doc,
        category: inferCategory(doc.filename)
      }));
      setDocuments(categorizedDocs);
    } catch (error) {
      console.error('Error loading documents:', error);
      toast.error("Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  // Infer document category from filename patterns
  const inferCategory = (filename: string): CategoryType => {
    const lower = filename.toLowerCase();
    if (lower.includes('strategy') || lower.includes('acquisition') || lower.includes('plan')) {
      return 'strategy';
    }
    if (lower.includes('market') || lower.includes('research') || lower.includes('analysis')) {
      return 'market_research';
    }
    if (lower.includes('requirement') || lower.includes('cdrl') || lower.includes('spec')) {
      return 'requirements';
    }
    if (lower.includes('template') || lower.includes('form') || lower.includes('sf-')) {
      return 'templates';
    }
    return 'strategy'; // Default category
  };

  // Handle file upload
  const handleUpload = async (file: File, category: CategoryType = 'strategy') => {
    setUploading(true);
    setUploadingCategory(category === 'all' ? 'strategy' : category);
    
    try {
      const result = await ragApi.uploadDocument(file, category === 'all' ? undefined : category);
      toast.success(`${result.filename} uploaded successfully! Created ${result.chunks_created} chunks.`);
      
      // Refresh document list
      await loadDocuments();
      
      // Update legacy uploads state for compatibility
      const categoryKey = category === "requirements" ? "reqs" : category === "all" ? "strategy" : category;
      if (categoryKey in uploads) {
        setUploads({
          ...uploads,
          [categoryKey]: [...uploads[categoryKey as keyof typeof uploads], result.filename],
        });
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error(`Failed to upload: ${error.message}`);
    } finally {
      setUploading(false);
      setUploadingCategory(null);
    }
  };

  // Handle file input change
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      await handleUpload(file, activeCategory);
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
      // Upload first file (can be extended for batch upload)
      await handleUpload(files[0], activeCategory);
    }
  }, [activeCategory]);

  // Handle document deletion
  const handleDelete = async () => {
    if (!deleteTarget) return;
    
    setDeleting(true);
    try {
      await ragApi.deleteDocument(deleteTarget.filename);
      toast.success(`${deleteTarget.filename} deleted successfully`);
      await loadDocuments();
    } catch (error: any) {
      console.error('Delete error:', error);
      toast.error(`Failed to delete: ${error.message}`);
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  // Handle extract assumptions
  const handleExtractAssumptions = async () => {
    if (documents.length === 0) {
      toast.error("Please upload at least one document first");
      return;
    }

    setExtracting(true);
    try {
      const result = await ragApi.extractAssumptions();
      toast.success(`Extracted ${result.total} assumptions from ${result.documents_analyzed} documents`);
      onExtract(result.assumptions);
    } catch (error: any) {
      console.error('Extract error:', error);
      toast.error(`Failed to extract assumptions: ${error.message}`);
    } finally {
      setExtracting(false);
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

  // Get category counts for tabs
  const getCategoryCounts = () => {
    const counts: Record<CategoryType, number> = {
      all: documents.length,
      strategy: 0,
      market_research: 0,
      requirements: 0,
      templates: 0
    };
    
    documents.forEach(doc => {
      if (doc.category && doc.category in counts) {
        counts[doc.category]++;
      }
    });
    
    return counts;
  };

  const categoryCounts = getCategoryCounts();

  return (
    <div className="container mx-auto p-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-3">
          Document Library
        </h1>
        <p className="text-lg text-muted-foreground">
          Upload, organize, and manage your acquisition documents for AI-powered generation
        </p>
      </div>

      {/* Upload Zone with Drag & Drop */}
      <Card 
        className={`mb-8 border-2 border-dashed transition-all duration-200 ${
          isDragOver 
            ? 'border-blue-500 bg-blue-50/50 scale-[1.01]' 
            : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50/50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="py-12">
          <div className="flex flex-col items-center justify-center text-center">
            <div className={`h-16 w-16 rounded-full flex items-center justify-center mb-4 transition-all ${
              isDragOver 
                ? 'bg-blue-100 text-blue-600 scale-110' 
                : 'bg-slate-100 text-slate-500'
            }`}>
              {uploading ? (
                <Loader2 className="h-8 w-8 animate-spin" />
              ) : (
                <Upload className="h-8 w-8" />
              )}
            </div>
            
            <h3 className="text-lg font-semibold mb-2">
              {uploading ? 'Uploading...' : isDragOver ? 'Drop file here' : 'Drag & drop files here'}
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              or click to browse • Supports PDF, DOCX, PPTX, XLSX, TXT, MD
            </p>
            
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.docx,.pptx,.xlsx,.txt,.md"
              onChange={handleFileChange}
              disabled={uploading}
            />
            
            {/* Select File Button - opens file picker dialog */}
            <Button 
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="gap-2"
              aria-label={uploading ? `Uploading to ${uploadingCategory}` : "Select file to upload"}
              title={uploading ? `Uploading to ${uploadingCategory}` : "Select file to upload"}
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Uploading to {uploadingCategory}...
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

      {/* Category Tabs & Search */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
        <Tabs value={activeCategory} onValueChange={(v) => setActiveCategory(v as CategoryType)}>
          <TabsList className="h-auto flex-wrap">
            {(Object.keys(CATEGORY_CONFIG) as CategoryType[]).map((category) => (
              <TabsTrigger 
                key={category} 
                value={category}
                className="gap-2 data-[state=active]:bg-white"
              >
                {CATEGORY_CONFIG[category].icon}
                <span className="hidden sm:inline">{CATEGORY_CONFIG[category].label}</span>
                <Badge variant="secondary" className="ml-1 h-5 min-w-[20px] text-xs">
                  {categoryCounts[category]}
                </Badge>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        <div className="relative w-full md:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
          {/* Clear Search Button - clears the search input */}
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6"
              onClick={() => setSearchQuery("")}
              aria-label="Clear search"
              title="Clear search"
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* Document Grid */}
      <Card className="mb-8">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">
                {CATEGORY_CONFIG[activeCategory].label}
              </CardTitle>
              <CardDescription>
                {CATEGORY_CONFIG[activeCategory].description}
              </CardDescription>
            </div>
            <Badge variant="secondary" className="text-sm">
              {filteredDocs.length} document{filteredDocs.length !== 1 ? 's' : ''}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : filteredDocs.length > 0 ? (
            <ScrollArea className="h-[400px] pr-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredDocs.map((doc, idx) => (
                  <Card 
                    key={idx} 
                    className="group hover:shadow-md transition-all duration-200 hover:border-blue-200"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        {/* File Icon */}
                        <div className={`h-10 w-10 rounded-lg bg-gradient-to-br ${
                          doc.category ? CATEGORY_CONFIG[doc.category].bgGradient : CATEGORY_CONFIG.strategy.bgGradient
                        } flex items-center justify-center text-white shadow-sm`}>
                          {getFileIcon(doc.file_type)}
                        </div>

                        {/* Document Info */}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-sm truncate" title={doc.filename}>
                            {doc.filename}
                          </h4>
                          
                          <div className="flex items-center gap-2 mt-1">
                            <Badge 
                              variant="outline" 
                              className={`text-[10px] uppercase ${
                                doc.category ? CATEGORY_CONFIG[doc.category].color : 'bg-slate-500'
                              } text-white border-0`}
                            >
                              {doc.file_type}
                            </Badge>
                            {doc.category && doc.category !== 'all' && (
                              <Badge variant="secondary" className="text-[10px]">
                                {CATEGORY_CONFIG[doc.category].label}
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

                        {/* Delete Button - always visible with clear styling */}
                        <button
                          type="button"
                          className="h-8 w-8 rounded-md flex items-center justify-center text-slate-500 hover:text-red-500 hover:bg-red-50 transition-colors"
                          onClick={() => setDeleteTarget(doc)}
                          aria-label="Delete document"
                          title="Delete document"
                        >
                          <Trash2 className="h-5 w-5 shrink-0" />
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
                {searchQuery ? 'No matching documents' : 'No documents yet'}
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchQuery 
                  ? 'Try adjusting your search or filter' 
                  : 'Upload your first document to get started'}
              </p>
              {/* Upload Document Button - shown when no documents exist */}
              {!searchQuery && (
                <Button 
                  variant="outline" 
                  onClick={() => fileInputRef.current?.click()}
                  className="gap-2"
                  aria-label="Upload your first document"
                  title="Upload your first document"
                >
                  <Upload className="h-4 w-4" />
                  Upload Document
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        {/* Back Button - returns to previous screen */}
        <Button 
          variant="outline" 
          onClick={onBack} 
          disabled={extracting}
          aria-label="Go back to previous screen"
          title="Go back"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        
        {/* Refresh Button - reloads document list from server */}
        <Button 
          variant="outline" 
          onClick={loadDocuments} 
          disabled={loading}
          className="gap-2"
          aria-label={loading ? "Loading documents..." : "Refresh document list"}
          title={loading ? "Loading..." : "Refresh document list"}
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Filter className="h-4 w-4" />
          )}
          Refresh
        </Button>

        {/* Extract Assumptions Button - AI processes all documents to extract key information */}
        <Button
          onClick={handleExtractAssumptions}
          className="ml-auto gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
          disabled={extracting || documents.length === 0}
          aria-label={extracting ? "Extracting assumptions from documents..." : `Extract assumptions from ${documents.length} documents`}
          title={extracting ? "Extracting..." : `Extract assumptions from ${documents.length} documents`}
        >
          {extracting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Extracting...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Extract Assumptions ({documents.length} docs)
            </>
          )}
        </Button>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              Delete Document
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete <strong>{deleteTarget?.filename}</strong>? 
              This will remove the document and all its associated data from the AI library. 
              This action cannot be undone.
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
