import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, FilePlus, Replace, Plus, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ImportResult, ImportPlacement } from '@/hooks/useDocumentImport';

interface ImportOptionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  importResult: ImportResult | null;
  currentSectionName: string;
  existingSections: string[];
  onConfirm: (placement: ImportPlacement, sectionName?: string) => void;
}

export function ImportOptionsDialog({
  open,
  onOpenChange,
  importResult,
  currentSectionName,
  existingSections,
  onConfirm,
}: ImportOptionsDialogProps) {
  const [placement, setPlacement] = useState<ImportPlacement>('new_section');
  const [newSectionName, setNewSectionName] = useState('');
  const [nameError, setNameError] = useState<string | null>(null);

  // Generate default section name from filename
  const defaultSectionName = importResult
    ? importResult.filename.replace(/\.(pdf|docx)$/i, '').replace(/[-_]/g, ' ')
    : '';

  const handleConfirm = () => {
    if (placement === 'new_section') {
      const name = newSectionName.trim() || defaultSectionName;

      // Validate section name
      if (!name) {
        setNameError('Please enter a section name');
        return;
      }

      if (existingSections.includes(name)) {
        setNameError('A section with this name already exists');
        return;
      }

      onConfirm(placement, name);
    } else {
      onConfirm(placement);
    }

    // Reset state
    setPlacement('new_section');
    setNewSectionName('');
    setNameError(null);
  };

  const handleCancel = () => {
    onOpenChange(false);
    setPlacement('new_section');
    setNewSectionName('');
    setNameError(null);
  };

  // Strip HTML for preview
  const previewText = importResult?.html
    ? importResult.html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
    : '';

  const truncatedPreview = previewText.length > 300
    ? previewText.slice(0, 300) + '...'
    : previewText;

  return (
    <Dialog open={open} onOpenChange={handleCancel}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Import Document
          </DialogTitle>
          <DialogDescription>
            Choose where to place the imported content
          </DialogDescription>
        </DialogHeader>

        {importResult && (
          <div className="space-y-4">
            {/* File Info */}
            <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
              <div className={cn(
                'p-2 rounded-lg',
                importResult.fileType === 'pdf' ? 'bg-red-100' : 'bg-blue-100'
              )}>
                <FileText className={cn(
                  'h-5 w-5',
                  importResult.fileType === 'pdf' ? 'text-red-600' : 'text-blue-600'
                )} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{importResult.filename}</p>
                <p className="text-xs text-muted-foreground uppercase">
                  {importResult.fileType} document
                </p>
              </div>
            </div>

            {/* Warnings */}
            {importResult.warnings && importResult.warnings.length > 0 && (
              <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <div className="text-xs text-amber-800">
                  <p className="font-medium mb-1">Conversion warnings:</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    {importResult.warnings.slice(0, 3).map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                    {importResult.warnings.length > 3 && (
                      <li>...and {importResult.warnings.length - 3} more</li>
                    )}
                  </ul>
                </div>
              </div>
            )}

            {/* Preview */}
            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">Content preview</Label>
              <ScrollArea className="h-24 rounded-md border p-3">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {truncatedPreview || 'No text content extracted'}
                </p>
              </ScrollArea>
            </div>

            {/* Placement Options */}
            <RadioGroup
              value={placement}
              onValueChange={(v) => {
                setPlacement(v as ImportPlacement);
                setNameError(null);
              }}
              className="space-y-3"
            >
              {/* New Section Option */}
              <div className={cn(
                'flex items-start gap-3 p-3 rounded-lg border-2 transition-colors cursor-pointer',
                placement === 'new_section'
                  ? 'border-primary bg-primary/5'
                  : 'border-transparent bg-slate-50 hover:bg-slate-100'
              )}
              onClick={() => setPlacement('new_section')}
              >
                <RadioGroupItem value="new_section" id="new_section" className="mt-1" />
                <div className="flex-1 space-y-2">
                  <Label htmlFor="new_section" className="flex items-center gap-2 cursor-pointer">
                    <FilePlus className="h-4 w-4" />
                    Create new section
                  </Label>
                  {placement === 'new_section' && (
                    <div className="space-y-1">
                      <Input
                        placeholder={defaultSectionName || 'Enter section name'}
                        value={newSectionName}
                        onChange={(e) => {
                          setNewSectionName(e.target.value);
                          setNameError(null);
                        }}
                        className="h-8 text-sm"
                      />
                      {nameError && (
                        <p className="text-xs text-destructive">{nameError}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Replace Current Option */}
              <div className={cn(
                'flex items-start gap-3 p-3 rounded-lg border-2 transition-colors cursor-pointer',
                placement === 'replace_current'
                  ? 'border-primary bg-primary/5'
                  : 'border-transparent bg-slate-50 hover:bg-slate-100'
              )}
              onClick={() => setPlacement('replace_current')}
              >
                <RadioGroupItem value="replace_current" id="replace_current" className="mt-1" />
                <Label htmlFor="replace_current" className="flex items-center gap-2 cursor-pointer">
                  <Replace className="h-4 w-4" />
                  Replace "{currentSectionName}"
                </Label>
              </div>

              {/* Append Option */}
              <div className={cn(
                'flex items-start gap-3 p-3 rounded-lg border-2 transition-colors cursor-pointer',
                placement === 'append_current'
                  ? 'border-primary bg-primary/5'
                  : 'border-transparent bg-slate-50 hover:bg-slate-100'
              )}
              onClick={() => setPlacement('append_current')}
              >
                <RadioGroupItem value="append_current" id="append_current" className="mt-1" />
                <Label htmlFor="append_current" className="flex items-center gap-2 cursor-pointer">
                  <Plus className="h-4 w-4" />
                  Append to "{currentSectionName}"
                </Label>
              </div>
            </RadioGroup>
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={!importResult}>
            Import
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
