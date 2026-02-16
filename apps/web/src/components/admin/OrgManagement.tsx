/**
 * OrgManagement - Organization hierarchy CRUD for admins.
 * Interactive tree view with create/edit/deactivate/member management.
 */
import { useState } from 'react';
import { Building2, ChevronRight, ChevronDown, Plus, Users, Pencil, Trash2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useOrganizations, useOrgMembers } from '@/hooks/useOrganizations';
import { authApi, type User, type Organization } from '@/services/api';
import { toast } from 'sonner';

export function OrgManagement() {
  const { organizations, loading, createOrganization } = useOrganizations();
  const [expandedOrgs, setExpandedOrgs] = useState<Set<string>>(new Set());
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createParentId, setCreateParentId] = useState<string | null>(null);

  // Build tree structure from flat list
  const orgMap = new Map(organizations.map(o => [o.id, o]));
  const rootOrgs = organizations.filter(o => !o.parent_id);
  const childrenOf = (parentId: string) => organizations.filter(o => o.parent_id === parentId);

  const toggleExpand = (orgId: string) => {
    const next = new Set(expandedOrgs);
    if (next.has(orgId)) next.delete(orgId);
    else next.add(orgId);
    setExpandedOrgs(next);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="border-b bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Organizations</h2>
            <p className="text-sm text-slate-600 mt-1">Manage organizational hierarchy and memberships</p>
          </div>
          <Button onClick={() => { setCreateParentId(null); setShowCreateDialog(true); }} className="gap-2">
            <Plus className="h-4 w-4" />
            New Organization
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tree view */}
          <div className="lg:col-span-2 space-y-2">
            {rootOrgs.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  No organizations yet. Create your first one.
                </CardContent>
              </Card>
            ) : (
              rootOrgs.map(org => (
                <OrgTreeNode
                  key={org.id}
                  org={org}
                  childrenOf={childrenOf}
                  expandedOrgs={expandedOrgs}
                  selectedOrgId={selectedOrgId}
                  onToggle={toggleExpand}
                  onSelect={setSelectedOrgId}
                  onCreateChild={(parentId) => { setCreateParentId(parentId); setShowCreateDialog(true); }}
                  depth={0}
                />
              ))
            )}
          </div>

          {/* Details panel */}
          <div>
            {selectedOrgId ? (
              <OrgDetailPanel orgId={selectedOrgId} />
            ) : (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  <Building2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  Select an organization to view details
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      <CreateOrgDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        parentId={createParentId}
        organizations={organizations}
        onCreate={createOrganization}
      />
    </div>
  );
}

interface OrgTreeNodeProps {
  org: Organization;
  childrenOf: (parentId: string) => Organization[];
  expandedOrgs: Set<string>;
  selectedOrgId: string | null;
  onToggle: (id: string) => void;
  onSelect: (id: string) => void;
  onCreateChild: (parentId: string) => void;
  depth: number;
}

function OrgTreeNode({ org, childrenOf, expandedOrgs, selectedOrgId, onToggle, onSelect, onCreateChild, depth }: OrgTreeNodeProps) {
  const children = childrenOf(org.id);
  const isExpanded = expandedOrgs.has(org.id);
  const isSelected = selectedOrgId === org.id;
  const hasChildren = children.length > 0;

  return (
    <div>
      <div
        className={`flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors ${
          isSelected ? 'bg-primary/10 border border-primary/20' : 'hover:bg-muted'
        }`}
        style={{ marginLeft: depth * 24 }}
        onClick={() => onSelect(org.id)}
      >
        <button
          onClick={(e) => { e.stopPropagation(); onToggle(org.id); }}
          className="h-5 w-5 flex items-center justify-center"
        >
          {hasChildren ? (
            isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
          ) : (
            <span className="h-4 w-4" />
          )}
        </button>
        <Building2 className="h-4 w-4 text-slate-500" />
        <span className="text-sm font-medium flex-1">{org.name}</span>
        {!org.is_active && <Badge variant="secondary" className="text-xs">Inactive</Badge>}
        <Badge variant="outline" className="text-xs">{children.length} sub</Badge>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 opacity-0 group-hover:opacity-100"
          onClick={(e) => { e.stopPropagation(); onCreateChild(org.id); }}
          title="Add child organization"
        >
          <Plus className="h-3 w-3" />
        </Button>
      </div>
      {isExpanded && children.map(child => (
        <OrgTreeNode
          key={child.id}
          org={child}
          childrenOf={childrenOf}
          expandedOrgs={expandedOrgs}
          selectedOrgId={selectedOrgId}
          onToggle={onToggle}
          onSelect={onSelect}
          onCreateChild={onCreateChild}
          depth={depth + 1}
        />
      ))}
    </div>
  );
}

function OrgDetailPanel({ orgId }: { orgId: string }) {
  const { members, loading, addMember, removeMember } = useOrgMembers(orgId);
  const { organizations } = useOrganizations();
  const org = organizations.find(o => o.id === orgId);

  if (!org) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{org.name}</CardTitle>
        {org.description && (
          <p className="text-sm text-muted-foreground">{org.description}</p>
        )}
        <div className="flex gap-2 mt-2">
          <Badge variant="outline">Depth: {org.depth}</Badge>
          <Badge variant="outline">Slug: {org.slug}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
          <Users className="h-4 w-4" />
          Members ({members.length})
        </h4>
        {loading ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : members.length === 0 ? (
          <p className="text-sm text-muted-foreground">No members</p>
        ) : (
          <div className="space-y-2">
            {members.map(member => (
              <div key={member.id} className="flex items-center justify-between text-sm">
                <div>
                  <span className="font-medium">{member.user?.name}</span>
                  <span className="text-muted-foreground ml-1">({member.org_role})</span>
                </div>
                {member.is_primary && <Badge variant="secondary" className="text-xs">Primary</Badge>}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface CreateOrgDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  parentId: string | null;
  organizations: Organization[];
  onCreate: (data: { name: string; slug: string; description?: string; parent_id?: string }) => Promise<unknown>;
}

function CreateOrgDialog({ open, onOpenChange, parentId, organizations, onCreate }: CreateOrgDialogProps) {
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const parentOrg = parentId ? organizations.find(o => o.id === parentId) : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !slug) return;

    setLoading(true);
    try {
      await onCreate({
        name,
        slug,
        description: description || undefined,
        parent_id: parentId ?? undefined,
      });
      toast.success('Organization created');
      onOpenChange(false);
      setName('');
      setSlug('');
      setDescription('');
    } catch {
      toast.error('Failed to create organization');
    } finally {
      setLoading(false);
    }
  };

  // Auto-generate slug from name
  const handleNameChange = (value: string) => {
    setName(value);
    setSlug(value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Organization</DialogTitle>
          <DialogDescription>
            {parentOrg ? `Create a child organization under ${parentOrg.name}` : 'Create a top-level organization'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Name *</Label>
              <Input value={name} onChange={(e) => handleNameChange(e.target.value)} placeholder="e.g., NAVAIR" required />
            </div>
            <div className="space-y-2">
              <Label>Slug *</Label>
              <Input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="e.g., navair" required />
              <p className="text-xs text-muted-foreground">URL-safe identifier (auto-generated from name)</p>
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" rows={2} />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={loading || !name || !slug}>
              {loading ? 'Creating...' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
