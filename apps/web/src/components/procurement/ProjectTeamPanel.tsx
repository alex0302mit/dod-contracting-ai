/**
 * ProjectTeamPanel - Team member list with role badges and management.
 * Shows OWNER/EDITOR/VIEWER permissions and allows adding/removing members.
 */
import { useState } from 'react';
import { UserPlus, Shield, Pencil, Eye, Trash2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useProjectTeam } from '@/hooks/useProjectTeam';
import { useAuth } from '@/contexts/AuthContext';
import { authApi, type User } from '@/services/api';
import { toast } from 'sonner';

interface ProjectTeamPanelProps {
  projectId: string;
}

const ROLE_CONFIG = {
  owner: { label: 'Owner', icon: Shield, color: 'bg-amber-100 text-amber-800 border-amber-200' },
  editor: { label: 'Editor', icon: Pencil, color: 'bg-blue-100 text-blue-800 border-blue-200' },
  viewer: { label: 'Viewer', icon: Eye, color: 'bg-slate-100 text-slate-800 border-slate-200' },
};

export function ProjectTeamPanel({ projectId }: ProjectTeamPanelProps) {
  const { team, loading, addMember, updateMember, removeMember } = useProjectTeam(projectId);
  const { user, hasRole } = useAuth();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('viewer');

  const canManageTeam = hasRole(['admin', 'contracting_officer', 'program_manager']);

  const handleOpenAdd = async () => {
    setShowAddDialog(true);
    setLoadingUsers(true);
    try {
      const response = await authApi.getUsers();
      // Filter out users already on the team
      const teamUserIds = new Set(team.map(t => t.user_id));
      setUsers(response.users.filter(u => !teamUserIds.has(u.id)));
    } catch {
      toast.error('Failed to load users');
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleAdd = async () => {
    if (!selectedUserId) return;
    try {
      await addMember({ userId: selectedUserId, permissionLevel: selectedLevel });
      toast.success('Team member added');
      setShowAddDialog(false);
      setSelectedUserId('');
      setSelectedLevel('viewer');
    } catch {
      toast.error('Failed to add team member');
    }
  };

  const handleUpdateRole = async (userId: string, newLevel: string) => {
    try {
      await updateMember({ userId, permissionLevel: newLevel });
      toast.success('Permission updated');
    } catch {
      toast.error('Failed to update permission');
    }
  };

  const handleRemove = async (userId: string, userName: string) => {
    try {
      await removeMember(userId);
      toast.success(`${userName} removed from team`);
    } catch {
      toast.error('Failed to remove team member');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Project Team</h3>
        {canManageTeam && (
          <Button size="sm" onClick={handleOpenAdd} className="gap-2">
            <UserPlus className="h-4 w-4" />
            Add Member
          </Button>
        )}
      </div>

      {team.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No team members assigned yet
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {team.map((member) => {
            const config = ROLE_CONFIG[member.permission_level as keyof typeof ROLE_CONFIG] ?? ROLE_CONFIG.viewer;
            const Icon = config.icon;
            const isCurrentUser = member.user_id === user?.id;

            return (
              <Card key={member.id}>
                <CardContent className="flex items-center justify-between py-3 px-4">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-slate-200 flex items-center justify-center text-sm font-medium">
                      {member.user?.name?.charAt(0)?.toUpperCase() ?? '?'}
                    </div>
                    <div>
                      <p className="text-sm font-medium">
                        {member.user?.name ?? 'Unknown'}
                        {isCurrentUser && <span className="text-muted-foreground ml-1">(you)</span>}
                      </p>
                      <p className="text-xs text-muted-foreground">{member.user?.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {canManageTeam && !isCurrentUser ? (
                      <Select
                        value={member.permission_level}
                        onValueChange={(val) => handleUpdateRole(member.user_id, val)}
                      >
                        <SelectTrigger className="w-[100px] h-8 text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="owner">Owner</SelectItem>
                          <SelectItem value="editor">Editor</SelectItem>
                          <SelectItem value="viewer">Viewer</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      <Badge variant="outline" className={config.color}>
                        <Icon className="h-3 w-3 mr-1" />
                        {config.label}
                      </Badge>
                    )}
                    {canManageTeam && !isCurrentUser && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-slate-400 hover:text-red-500"
                        onClick={() => handleRemove(member.user_id, member.user?.name ?? 'User')}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Member Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Team Member</DialogTitle>
            <DialogDescription>Select a user and permission level for the project</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">User</label>
              {loadingUsers ? (
                <div className="flex items-center gap-2 h-10 px-3 border rounded-md bg-slate-50">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm text-slate-500">Loading users...</span>
                </div>
              ) : (
                <Select value={selectedUserId} onValueChange={setSelectedUserId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select user" />
                  </SelectTrigger>
                  <SelectContent>
                    {users.map((u) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.name} ({u.email})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Permission Level</label>
              <Select value={selectedLevel} onValueChange={setSelectedLevel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="owner">Owner - Full control</SelectItem>
                  <SelectItem value="editor">Editor - Can edit documents</SelectItem>
                  <SelectItem value="viewer">Viewer - Read-only access</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>Cancel</Button>
            <Button onClick={handleAdd} disabled={!selectedUserId}>Add Member</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
