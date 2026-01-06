/**
 * Smart Tag Popover Component
 *
 * Allows users to create and edit smart tags with type selection and description
 */

import { useState } from 'react';
import { Editor } from '@tiptap/react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Tag, X } from 'lucide-react';

interface SmartTagPopoverProps {
  editor: Editor | null;
  children?: React.ReactNode;
}

const TAG_TYPES = [
  { value: 'requirement', label: 'Requirement', color: 'blue' },
  { value: 'assumption', label: 'Assumption', color: 'purple' },
  { value: 'risk', label: 'Risk', color: 'red' },
  { value: 'decision', label: 'Decision', color: 'green' },
  { value: 'action-item', label: 'Action Item', color: 'orange' },
  { value: 'note', label: 'Note', color: 'gray' },
] as const;

export function SmartTagPopover({ editor, children }: SmartTagPopoverProps) {
  const [open, setOpen] = useState(false);
  const [tagType, setTagType] = useState<string>('note');
  const [tagLabel, setTagLabel] = useState('');
  const [tagDescription, setTagDescription] = useState('');

  const handleInsertTag = () => {
    if (!editor || !tagLabel.trim()) {
      return;
    }

    editor
      .chain()
      .focus()
      .insertSmartTag({
        tagId: `tag-${Date.now()}`,
        tagType: tagType as any,
        tagLabel: tagLabel.trim(),
        tagDescription: tagDescription.trim() || undefined,
      })
      .run();

    // Reset form
    setTagLabel('');
    setTagDescription('');
    setTagType('note');
    setOpen(false);
  };

  const handleCancel = () => {
    setTagLabel('');
    setTagDescription('');
    setTagType('note');
    setOpen(false);
  };

  const canInsert = editor && tagLabel.trim().length > 0;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        {children || (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            title="Insert Smart Tag (Ctrl+Shift+T)"
          >
            <Tag className="h-4 w-4" />
          </Button>
        )}
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-sm">Insert Smart Tag</h4>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={handleCancel}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-3">
            {/* Tag Type Selector */}
            <div className="space-y-2">
              <Label htmlFor="tag-type" className="text-xs font-medium">
                Tag Type
              </Label>
              <Select value={tagType} onValueChange={setTagType}>
                <SelectTrigger id="tag-type" className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TAG_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex items-center gap-2">
                        <div
                          className={`h-2 w-2 rounded-full bg-${type.color}-500`}
                        />
                        {type.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Tag Label */}
            <div className="space-y-2">
              <Label htmlFor="tag-label" className="text-xs font-medium">
                Label *
              </Label>
              <Input
                id="tag-label"
                placeholder="e.g., REQ-001, ASSUMPTION-A"
                value={tagLabel}
                onChange={(e) => setTagLabel(e.target.value)}
                className="h-9"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && canInsert) {
                    e.preventDefault();
                    handleInsertTag();
                  }
                }}
              />
            </div>

            {/* Tag Description (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="tag-description" className="text-xs font-medium">
                Description (Optional)
              </Label>
              <Textarea
                id="tag-description"
                placeholder="Brief description for tooltip..."
                value={tagDescription}
                onChange={(e) => setTagDescription(e.target.value)}
                className="h-20 resize-none text-sm"
              />
            </div>
          </div>

          {/* Preview */}
          {tagLabel && (
            <div className="space-y-2">
              <Label className="text-xs font-medium">Preview</Label>
              <div className="p-2 bg-slate-50 rounded border">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-${TAG_TYPES.find(t => t.value === tagType)?.color}-100 text-${TAG_TYPES.find(t => t.value === tagType)?.color}-800 border border-${TAG_TYPES.find(t => t.value === tagType)?.color}-200`}
                >
                  [{tagLabel}]
                </span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2">
            <Button
              size="sm"
              onClick={handleInsertTag}
              disabled={!canInsert}
              className="flex-1"
            >
              Insert Tag
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleCancel}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
