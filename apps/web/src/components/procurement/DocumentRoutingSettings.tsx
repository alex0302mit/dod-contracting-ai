/**
 * DocumentRoutingSettings - Component for configuring document approval routing
 * 
 * Allows CO/PM/Admin users to configure how a document's approvals are routed:
 * - auto_co: Automatically route to project's Contracting Officer
 * - default: Route to a specific default approver
 * - manual: Require manual approver selection each time
 * 
 * Dependencies:
 * - @/components/ui/card, button, label, radio-group, select
 * - @/services/api for approvalsApi and authApi
 * - lucide-react for icons
 */
import { useState, useEffect } from 'react';
import { Settings, Save, Building2, User, List, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { approvalsApi, authApi, type User as UserType, type ApprovalRouting } from '@/services/api';

interface DocumentRoutingSettingsProps {
  documentId: string;
  documentName: string;
  currentRouting: ApprovalRouting;
  currentDefaultApproverId?: string;
  onUpdate: () => void;
}

export function DocumentRoutingSettings({
  documentId,
  documentName,
  currentRouting,
  currentDefaultApproverId,
  onUpdate,
}: DocumentRoutingSettingsProps) {
  // Routing selection state
  const [routing, setRouting] = useState<ApprovalRouting>(currentRouting);
  const [defaultApproverId, setDefaultApproverId] = useState(currentDefaultApproverId || '');
  
  // UI state
  const [approvers, setApprovers] = useState<UserType[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingApprovers, setLoadingApprovers] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Track changes from initial state
  useEffect(() => {
    const routingChanged = routing !== currentRouting;
    const approverChanged = defaultApproverId !== (currentDefaultApproverId || '');
    setHasChanges(routingChanged || approverChanged);
  }, [routing, defaultApproverId, currentRouting, currentDefaultApproverId]);

  // Fetch approvers when default routing is selected
  const fetchApprovers = async () => {
    setLoadingApprovers(true);
    try {
      const response = await authApi.getUsers();
      // Filter to only show users who can approve
      const eligible = response.users.filter((user: UserType) =>
        ['contracting_officer', 'program_manager', 'approver'].includes(user.role) &&
        user.is_active
      );
      setApprovers(eligible);
    } catch (error) {
      console.error('Error fetching approvers:', error);
      toast.error('Failed to load approvers');
    } finally {
      setLoadingApprovers(false);
    }
  };

  // Handle routing type change
  const handleRoutingChange = (value: ApprovalRouting) => {
    setRouting(value);
    // Fetch approvers if switching to default routing
    if (value === 'default' && approvers.length === 0) {
      fetchApprovers();
    }
  };

  // Save routing settings
  const handleSave = async () => {
    // Validate default approver is selected when using default routing
    if (routing === 'default' && !defaultApproverId) {
      toast.error('Please select a default approver');
      return;
    }

    setLoading(true);
    try {
      await approvalsApi.updateDocumentRouting(
        documentId,
        routing,
        routing === 'default' ? defaultApproverId : undefined
      );
      toast.success('Routing settings updated successfully');
      onUpdate();
    } catch (error: any) {
      console.error('Error updating routing:', error);
      toast.error(error.message || 'Failed to update routing settings');
    } finally {
      setLoading(false);
    }
  };

  // Get description text for each routing type
  const getRoutingDescription = (type: ApprovalRouting): string => {
    switch (type) {
      case 'auto_co':
        return 'Approvals automatically route to the project\'s Contracting Officer';
      case 'default':
        return 'Approvals route to a specific user you designate';
      case 'manual':
        return 'Users must manually select approvers each time';
      default:
        return '';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Settings className="h-5 w-5" />
          Approval Routing Settings
        </CardTitle>
        <CardDescription>
          Configure how "{documentName}" is routed for approval
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Routing Type Selection */}
        <RadioGroup
          value={routing}
          onValueChange={(value) => handleRoutingChange(value as ApprovalRouting)}
          className="space-y-2"
        >
          {/* Auto-CO Option */}
          <div 
            className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors
              ${routing === 'auto_co' ? 'border-blue-500 bg-blue-50' : 'hover:bg-slate-50'}`}
            onClick={() => handleRoutingChange('auto_co')}
          >
            <RadioGroupItem value="auto_co" id="settings_auto_co" />
            <div className="flex-1">
              <Label htmlFor="settings_auto_co" className="flex items-center gap-2 cursor-pointer font-medium">
                <Building2 className="h-4 w-4 text-blue-600" />
                Auto-route to Project CO
              </Label>
              <p className="text-xs text-slate-500 mt-1">
                {getRoutingDescription('auto_co')}
              </p>
            </div>
          </div>
          
          {/* Default Approver Option */}
          <div 
            className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors
              ${routing === 'default' ? 'border-green-500 bg-green-50' : 'hover:bg-slate-50'}`}
            onClick={() => handleRoutingChange('default')}
          >
            <RadioGroupItem value="default" id="settings_default" />
            <div className="flex-1">
              <Label htmlFor="settings_default" className="flex items-center gap-2 cursor-pointer font-medium">
                <User className="h-4 w-4 text-green-600" />
                Default Approver
              </Label>
              <p className="text-xs text-slate-500 mt-1">
                {getRoutingDescription('default')}
              </p>
            </div>
          </div>
          
          {/* Manual Selection Option */}
          <div 
            className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors
              ${routing === 'manual' ? 'border-orange-500 bg-orange-50' : 'hover:bg-slate-50'}`}
            onClick={() => handleRoutingChange('manual')}
          >
            <RadioGroupItem value="manual" id="settings_manual" />
            <div className="flex-1">
              <Label htmlFor="settings_manual" className="flex items-center gap-2 cursor-pointer font-medium">
                <List className="h-4 w-4 text-orange-600" />
                Manual Selection
              </Label>
              <p className="text-xs text-slate-500 mt-1">
                {getRoutingDescription('manual')}
              </p>
            </div>
          </div>
        </RadioGroup>

        {/* Default Approver Selection (shown when default routing selected) */}
        {routing === 'default' && (
          <div className="space-y-2 pt-2 border-t">
            <Label className="text-sm font-medium">Select Default Approver</Label>
            {loadingApprovers ? (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading approvers...
              </div>
            ) : (
              <Select
                value={defaultApproverId}
                onValueChange={setDefaultApproverId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select an approver..." />
                </SelectTrigger>
                <SelectContent>
                  {approvers.map((user) => (
                    <SelectItem key={user.id} value={user.id}>
                      <div className="flex flex-col">
                        <span>{user.name}</span>
                        <span className="text-xs text-slate-500 capitalize">
                          {user.role.replace('_', ' ')}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {!defaultApproverId && routing === 'default' && (
              <p className="text-xs text-amber-600">
                Please select a default approver to save this setting
              </p>
            )}
          </div>
        )}

        {/* Save Button */}
        <Button 
          onClick={handleSave} 
          disabled={loading || !hasChanges || (routing === 'default' && !defaultApproverId)} 
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Routing Settings
            </>
          )}
        </Button>

        {/* No changes indicator */}
        {!hasChanges && (
          <p className="text-xs text-center text-slate-500">
            No changes to save
          </p>
        )}
      </CardContent>
    </Card>
  );
}
