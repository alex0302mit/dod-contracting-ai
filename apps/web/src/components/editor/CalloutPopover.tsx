/**
 * Callout Popover Component
 *
 * UI for inserting callout blocks with different types
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
import { MessageSquare } from 'lucide-react';
import { CalloutType } from './CalloutExtension';
import { calloutPresets, getPresetIcon, getPresetTitle } from '@/lib/calloutPresets';

interface CalloutPopoverProps {
  editor: Editor | null;
  children?: React.ReactNode;
}

export function CalloutPopover({ editor, children }: CalloutPopoverProps) {
  const [open, setOpen] = useState(false);
  const [calloutType, setCalloutType] = useState<CalloutType>('info');
  const [title, setTitle] = useState('');

  const handleInsertCallout = () => {
    if (!editor) return;

    const defaultTitle = title || getPresetTitle(calloutType);

    editor
      .chain()
      .focus()
      .insertCallout({
        type: calloutType,
        title: defaultTitle,
        icon: getPresetIcon(calloutType),
      })
      .run();

    // Reset and close
    setTitle('');
    setCalloutType('info');
    setOpen(false);
  };

  const handleCancel = () => {
    setTitle('');
    setCalloutType('info');
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        {children || (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            title="Insert Callout (Ctrl+Shift+C)"
          >
            <MessageSquare className="h-4 w-4" />
          </Button>
        )}
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-sm">Insert Callout</h4>
          </div>

          <div className="space-y-3">
            {/* Callout Type Selector */}
            <div className="space-y-2">
              <Label htmlFor="callout-type" className="text-xs font-medium">
                Callout Type
              </Label>
              <Select value={calloutType} onValueChange={(v) => setCalloutType(v as CalloutType)}>
                <SelectTrigger id="callout-type" className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {calloutPresets.map((preset) => (
                    <SelectItem key={preset.type} value={preset.type}>
                      <div className="flex items-center gap-2">
                        <span>{preset.icon}</span>
                        <div>
                          <div className="font-medium">{preset.title}</div>
                          <div className="text-xs text-muted-foreground">
                            {preset.description}
                          </div>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Custom Title (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="callout-title" className="text-xs font-medium">
                Custom Title (Optional)
              </Label>
              <Input
                id="callout-title"
                placeholder={getPresetTitle(calloutType)}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="h-9"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleInsertCallout();
                  }
                }}
              />
            </div>

            {/* Preview */}
            <div className="space-y-2">
              <Label className="text-xs font-medium">Preview</Label>
              <div className={`callout callout-${calloutType} p-3 rounded border-l-4`}>
                <div className="callout-title text-sm font-semibold flex items-center gap-2">
                  <span>{getPresetIcon(calloutType)}</span>
                  {title || getPresetTitle(calloutType)}
                </div>
                <div className="callout-content text-xs mt-2">
                  {calloutPresets.find((p) => p.type === calloutType)?.example}
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2">
            <Button size="sm" onClick={handleInsertCallout} className="flex-1">
              Insert Callout
            </Button>
            <Button size="sm" variant="outline" onClick={handleCancel} className="flex-1">
              Cancel
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
