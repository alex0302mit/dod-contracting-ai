/**
 * QuickUploadStep Component
 * 
 * Step 1 of the Quick Generate wizard - handles document uploads.
 * Features:
 * - Drag-and-drop upload zone
 * - Category-based document organization
 * - File list with progress and delete functionality
 * - Optional context textarea for additional instructions
 * 
 * Dependencies:
 * - ragApi for document upload
 * - Shadcn UI components for styling
 * - Types from ./types.ts
 */

import { useState, useCallback, useRef } from "react";
import {
  Upload,
  FileText,
  Trash2,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X,
  FileType,
  HardDrive,
  ArrowRight,
  FolderOpen
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { ragApi } from "@/services/api";
import {
  QuickUploadStepProps,
  UploadedFile,
  DocumentCategory,
  CATEGORY_CONFIG
} from "./types";

/**
 * QuickUploadStep handles file uploads for the Quick Generate wizard.
 * Users can drag-drop files into category zones or use the file browser.
 */
export function QuickUploadStep({
  uploadedFiles,
  onFilesAdded,
  onFileRemoved,
  userContext,
  onContextChange,
  onContinue,
  isExtracting
}: QuickUploadStepProps) {
  // Drag-and-drop state
  const [isDragOver, setIsDragOver] = useState(false);
  const [dragOverCategory, setDragOverCategory] = useState<DocumentCategory | null>(null);
  
  // File input ref for programmatic triggering
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Track which category is being uploaded to
  const [uploadingToCategory, setUploadingToCategory] = useState<DocumentCategory | null>(null);

  /**
   * Generate a unique client-side ID for tracking uploads
   */
  const generateFileId = () => `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  /**
   * Format file size for display (bytes → KB/MB)
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  /**
   * Get appropriate icon based on file type
   */
  const getFileIcon = (fileType: string) => {
    const type = fileType.toLowerCase();
    if (type.includes('pdf')) return <FileText className="h-4 w-4 text-red-500" />;
    if (type.includes('doc')) return <FileText className="h-4 w-4 text-blue-500" />;
    if (type.includes('xls')) return <FileText className="h-4 w-4 text-green-500" />;
    if (type.includes('ppt')) return <FileType className="h-4 w-4 text-orange-500" />;
    return <FileText className="h-4 w-4 text-slate-400" />;
  };

  /**
   * Handle file upload to the backend
   */
  const uploadFile = async (file: File, category: DocumentCategory): Promise<UploadedFile> => {
    const fileId = generateFileId();
    
    // Create initial file entry
    const uploadEntry: UploadedFile = {
      id: fileId,
      filename: file.name,
      size: file.size,
      type: file.type,
      category,
      status: 'uploading',
      progress: 0
    };

    // Add to list immediately to show progress
    onFilesAdded([uploadEntry]);

    try {
      // Upload to backend
      const result = await ragApi.uploadDocument(file, category);
      
      // Update entry with success
      const updatedEntry: UploadedFile = {
        ...uploadEntry,
        status: 'ready',
        progress: 100,
        documentId: result.filename // Backend returns filename as ID
      };

      // Update the file in the list
      onFilesAdded([updatedEntry]);
      
      toast.success(`${file.name} uploaded successfully`);
      return updatedEntry;
    } catch (error: any) {
      // Update entry with error
      const errorEntry: UploadedFile = {
        ...uploadEntry,
        status: 'error',
        error: error.message || 'Upload failed'
      };
      
      onFilesAdded([errorEntry]);
      toast.error(`Failed to upload ${file.name}: ${error.message}`);
      return errorEntry;
    }
  };

  /**
   * Handle multiple file uploads
   */
  const handleFiles = async (files: FileList | File[], category: DocumentCategory) => {
    const fileArray = Array.from(files);
    
    // Validate file count
    if (uploadedFiles.length + fileArray.length > 25) {
      toast.error("Maximum 25 files allowed");
      return;
    }

    setUploadingToCategory(category);

    // Upload files sequentially to avoid overwhelming the server
    for (const file of fileArray) {
      // Validate file size (25MB max)
      if (file.size > 25 * 1024 * 1024) {
        toast.error(`${file.name} exceeds 25MB limit`);
        continue;
      }

      // Validate file type
      const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain',
        'text/markdown'
      ];
      
      if (!allowedTypes.includes(file.type) && !file.name.endsWith('.md')) {
        toast.error(`${file.name} has unsupported file type`);
        continue;
      }

      await uploadFile(file, category);
    }

    setUploadingToCategory(null);
  };

  /**
   * Handle drag over event
   */
  const handleDragOver = useCallback((e: React.DragEvent, category?: DocumentCategory) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
    if (category) {
      setDragOverCategory(category);
    }
  }, []);

  /**
   * Handle drag leave event
   */
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    setDragOverCategory(null);
  }, []);

  /**
   * Handle drop event
   */
  const handleDrop = useCallback((e: React.DragEvent, category: DocumentCategory) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    setDragOverCategory(null);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFiles(files, category);
    }
  }, [uploadedFiles.length]);

  /**
   * Handle file input change
   */
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>, category: DocumentCategory) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFiles(files, category);
    }
    // Reset input
    e.target.value = '';
  };

  /**
   * Open file browser for a specific category
   */
  const openFileBrowser = (category: DocumentCategory) => {
    setUploadingToCategory(category);
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Get files count by category
  const getFilesByCategory = (category: DocumentCategory) => 
    uploadedFiles.filter(f => f.category === category);

  // Check if any files are currently uploading
  const hasUploadingFiles = uploadedFiles.some(f => f.status === 'uploading');
  
  // Check if ready to continue (at least one ready file)
  const hasReadyFiles = uploadedFiles.some(f => f.status === 'ready');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold mb-2">Upload Source Documents</h2>
        <p className="text-muted-foreground">
          Upload the documents that will inform your contracting package. The AI will extract 
          assumptions and requirements from these files.
        </p>
      </div>

      {/* Category Drop Zones */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.values(CATEGORY_CONFIG).map((config) => {
          const categoryFiles = getFilesByCategory(config.key);
          const isDropTarget = dragOverCategory === config.key;
          const isUploading = uploadingToCategory === config.key;

          return (
            <Card
              key={config.key}
              className={`relative transition-all duration-200 ${
                isDropTarget
                  ? 'ring-2 ring-blue-500 border-blue-500 bg-blue-50'
                  : 'hover:border-slate-300'
              }`}
              onDragOver={(e) => handleDragOver(e, config.key)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, config.key)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-lg bg-gradient-to-br ${config.bgGradient}`}>
                      <FolderOpen className="h-4 w-4 text-white" />
                    </div>
                    <div>
                      <CardTitle className="text-sm">{config.label}</CardTitle>
                      <CardDescription className="text-xs">{config.description}</CardDescription>
                    </div>
                  </div>
                  {categoryFiles.length > 0 && (
                    <Badge variant="secondary">{categoryFiles.length}</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {/* Drop Zone */}
                <div
                  className={`
                    border-2 border-dashed rounded-lg p-4 text-center transition-all cursor-pointer
                    ${isDropTarget ? 'border-blue-400 bg-blue-50' : 'border-slate-200 hover:border-slate-300'}
                  `}
                  onClick={() => openFileBrowser(config.key)}
                >
                  {isUploading ? (
                    <div className="flex flex-col items-center gap-2">
                      <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                      <span className="text-sm text-muted-foreground">Uploading...</span>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-2">
                      <Upload className="h-6 w-6 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">
                        Drop files or click to browse
                      </span>
                    </div>
                  )}
                </div>

                {/* File List for this category */}
                {categoryFiles.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {categoryFiles.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center justify-between p-2 bg-slate-50 rounded-lg"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          {file.status === 'uploading' ? (
                            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                          ) : file.status === 'error' ? (
                            <AlertCircle className="h-4 w-4 text-red-500" />
                          ) : (
                            getFileIcon(file.type)
                          )}
                          <span className="text-sm truncate" title={file.filename}>
                            {file.filename}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">
                            {formatFileSize(file.size)}
                          </span>
                          {file.status === 'ready' && (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 text-slate-400 hover:text-red-500"
                            onClick={(e) => {
                              e.stopPropagation();
                              onFileRemoved(file.id);
                            }}
                            disabled={file.status === 'uploading'}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.doc,.txt,.md"
        multiple
        onChange={(e) => {
          if (uploadingToCategory) {
            handleFileInputChange(e, uploadingToCategory);
          }
        }}
      />

      {/* Files Summary */}
      {uploadedFiles.length > 0 && (
        <Card className="bg-slate-50">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <HardDrive className="h-5 w-5 text-slate-500" />
                <div>
                  <p className="font-medium">
                    {uploadedFiles.filter(f => f.status === 'ready').length} of {uploadedFiles.length} files ready
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Total size: {formatFileSize(uploadedFiles.reduce((sum, f) => sum + f.size, 0))}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                {Object.values(CATEGORY_CONFIG).map((config) => {
                  const count = getFilesByCategory(config.key).filter(f => f.status === 'ready').length;
                  if (count === 0) return null;
                  return (
                    <Badge key={config.key} className={config.color}>
                      {config.label}: {count}
                    </Badge>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Optional Context */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            Additional Context
            <Badge variant="outline" className="text-xs font-normal">Optional</Badge>
          </CardTitle>
          <CardDescription>
            Provide any additional context about your procurement to help the AI generate better content.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder="E.g., This is a cloud migration project for a DoD agency. We need FedRAMP High authorization and CMMC Level 2 compliance..."
            value={userContext}
            onChange={(e) => onContextChange(e.target.value)}
            className="min-h-[100px] resize-none"
          />
        </CardContent>
      </Card>

      {/* Continue Button */}
      <div className="flex justify-end pt-4">
        <Button
          onClick={onContinue}
          disabled={!hasReadyFiles || hasUploadingFiles || isExtracting}
          className="gap-2"
        >
          {isExtracting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Extracting...
            </>
          ) : (
            <>
              Extract & Continue
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
