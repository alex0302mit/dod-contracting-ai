import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';

interface AddDocumentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd: (document: {
    document_name: string;
    description: string;
    category: string;
    phase: string | null;
    is_required: boolean;
    requires_approval: boolean;
    deadline: string | null;
    expiration_date: string | null;
    display_order: number;
  }) => Promise<void>;
}

export function AddDocumentDialog({ open, onOpenChange, onAdd }: AddDocumentDialogProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    document_name: '',
    description: '',
    category: 'General',
    phase: '',
    is_required: true,
    requires_approval: false,
    deadline: '',
    expiration_date: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.document_name.trim()) {
      toast.error('Document name is required');
      return;
    }

    setLoading(true);
    try {
      await onAdd({
        document_name: formData.document_name.trim(),
        description: formData.description.trim() || '',
        category: formData.category,
        phase: formData.phase || null,
        is_required: formData.is_required,
        requires_approval: formData.requires_approval,
        deadline: formData.deadline || null,
        expiration_date: formData.expiration_date || null,
        display_order: 999,
      });

      toast.success('Document added successfully');
      onOpenChange(false);

      setFormData({
        document_name: '',
        description: '',
        category: 'General',
        phase: '',
        is_required: true,
        requires_approval: false,
        deadline: '',
        expiration_date: '',
      });
    } catch (error) {
      console.error('Error adding document:', error);
      toast.error('Failed to add document');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Add New Document</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="document_name">Document Name *</Label>
            <Input
              id="document_name"
              value={formData.document_name}
              onChange={(e) => setFormData({ ...formData, document_name: e.target.value })}
              placeholder="e.g., Technical Evaluation Report"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Detailed description of the document and its purpose"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select
                value={formData.category}
                onValueChange={(value) => setFormData({ ...formData, category: value })}
              >
                <SelectTrigger id="category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="General">General</SelectItem>
                  <SelectItem value="Strategic">Strategic</SelectItem>
                  <SelectItem value="Technical">Technical</SelectItem>
                  <SelectItem value="Financial">Financial</SelectItem>
                  <SelectItem value="Legal">Legal</SelectItem>
                  <SelectItem value="Administrative">Administrative</SelectItem>
                  <SelectItem value="Security">Security</SelectItem>
                  <SelectItem value="Evaluation">Evaluation</SelectItem>
                  <SelectItem value="Research">Research</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phase">Associated Phase</Label>
              <Select
                value={formData.phase}
                onValueChange={(value) => setFormData({ ...formData, phase: value })}
              >
                <SelectTrigger id="phase">
                  <SelectValue placeholder="Select phase (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="pre_solicitation">Pre-Solicitation</SelectItem>
                  <SelectItem value="solicitation">Solicitation</SelectItem>
                  <SelectItem value="post_solicitation">Post-Solicitation</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="deadline">Deadline</Label>
              <Input
                id="deadline"
                type="date"
                value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="expiration_date">Expiration Date</Label>
              <Input
                id="expiration_date"
                type="date"
                value={formData.expiration_date}
                onChange={(e) => setFormData({ ...formData, expiration_date: e.target.value })}
              />
            </div>
          </div>

          <div className="space-y-4 pt-4 border-t">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="is_required">Required Document</Label>
                <p className="text-sm text-slate-600">Mark this document as mandatory for the project</p>
              </div>
              <Switch
                id="is_required"
                checked={formData.is_required}
                onCheckedChange={(checked) => setFormData({ ...formData, is_required: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="requires_approval">Requires Approval</Label>
                <p className="text-sm text-slate-600">Document must be approved before acceptance</p>
              </div>
              <Switch
                id="requires_approval"
                checked={formData.requires_approval}
                onCheckedChange={(checked) => setFormData({ ...formData, requires_approval: checked })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Adding...' : 'Add Document'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
