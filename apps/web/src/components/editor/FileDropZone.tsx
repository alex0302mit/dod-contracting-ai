import { useState, useRef, useCallback } from 'react';
import { Upload, FileText, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDocumentImport } from '@/hooks/useDocumentImport';
import { Progress } from '@/components/ui/progress';

interface FileDropZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  converting?: boolean;
  progress?: number;
  className?: string;
  compact?: boolean;
}

export function FileDropZone({
  onFileSelect,
  disabled = false,
  converting = false,
  progress = 0,
  className,
  compact = false,
}: FileDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { acceptedTypes, isSupported } = useDocumentImport();

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !converting) {
      setIsDragOver(true);
    }
  }, [disabled, converting]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled || converting) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (isSupported(file)) {
        onFileSelect(file);
      }
    }
  }, [disabled, converting, isSupported, onFileSelect]);

  const handleClick = useCallback(() => {
    if (!disabled && !converting) {
      fileInputRef.current?.click();
    }
  }, [disabled, converting]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (isSupported(file)) {
        onFileSelect(file);
      }
    }
    // Reset input value to allow selecting the same file again
    e.target.value = '';
  }, [isSupported, onFileSelect]);

  if (compact) {
    return (
      <div
        className={cn(
          'relative border-2 border-dashed rounded-lg transition-all duration-200 cursor-pointer',
          isDragOver && !disabled && !converting
            ? 'border-primary bg-primary/5'
            : 'border-slate-200 hover:border-slate-300',
          disabled && 'opacity-50 cursor-not-allowed',
          converting && 'cursor-wait',
          className
        )}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedTypes}
          onChange={handleFileChange}
          className="hidden"
          disabled={disabled || converting}
        />

        <div className="flex items-center justify-center gap-2 py-3 px-4">
          {converting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span className="text-xs text-muted-foreground">Converting...</span>
            </>
          ) : (
            <>
              <Upload className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">
                Drop PDF/DOCX
              </span>
            </>
          )}
        </div>

        {converting && progress > 0 && (
          <Progress value={progress} className="absolute bottom-0 left-0 right-0 h-1 rounded-none" />
        )}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'relative border-2 border-dashed rounded-lg transition-all duration-200 cursor-pointer',
        isDragOver && !disabled && !converting
          ? 'border-primary bg-primary/5 scale-[1.02]'
          : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50',
        disabled && 'opacity-50 cursor-not-allowed',
        converting && 'cursor-wait',
        className
      )}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedTypes}
        onChange={handleFileChange}
        className="hidden"
        disabled={disabled || converting}
      />

      <div className="flex flex-col items-center justify-center gap-3 py-6 px-4">
        {converting ? (
          <>
            <div className="relative">
              <FileText className="h-10 w-10 text-primary/30" />
              <Loader2 className="h-5 w-5 animate-spin text-primary absolute -bottom-1 -right-1" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-foreground">Converting document...</p>
              <p className="text-xs text-muted-foreground mt-1">
                {progress}% complete
              </p>
            </div>
            <Progress value={progress} className="w-full max-w-[200px] h-2" />
          </>
        ) : (
          <>
            <div className={cn(
              'rounded-full p-3 transition-colors',
              isDragOver ? 'bg-primary/10' : 'bg-slate-100'
            )}>
              <Upload className={cn(
                'h-6 w-6 transition-colors',
                isDragOver ? 'text-primary' : 'text-muted-foreground'
              )} />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-foreground">
                {isDragOver ? 'Drop to import' : 'Import document'}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Drag & drop or click to browse
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                PDF, DOCX (max 25MB)
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
