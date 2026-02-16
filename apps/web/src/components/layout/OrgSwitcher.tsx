/**
 * OrgSwitcher - Organization context switcher for the header.
 * Shows current org and allows switching between user's organizations.
 * Changing org updates activeOrgId and triggers project list refetch.
 */
import { Building2, ChevronDown, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuth } from '@/contexts/AuthContext';

export function OrgSwitcher() {
  const { activeOrgId, setActiveOrgId, userOrganizations } = useAuth();

  if (userOrganizations.length <= 1) {
    // Single org — show label only, no dropdown
    const orgName = userOrganizations[0]?.organization?.name ?? 'Default Organization';
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground">
        <Building2 className="h-4 w-4" />
        <span className="truncate max-w-[160px]">{orgName}</span>
      </div>
    );
  }

  const activeOrg = userOrganizations.find(m => m.organization_id === activeOrgId);
  const activeOrgName = activeOrg?.organization?.name ?? 'Select Organization';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2 max-w-[200px]">
          <Building2 className="h-4 w-4 flex-shrink-0" />
          <span className="truncate">{activeOrgName}</span>
          <ChevronDown className="h-3 w-3 flex-shrink-0 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[220px]">
        {userOrganizations.map((membership) => (
          <DropdownMenuItem
            key={membership.organization_id}
            onClick={() => setActiveOrgId(membership.organization_id)}
            className="gap-2"
          >
            <Check
              className={`h-4 w-4 ${
                membership.organization_id === activeOrgId ? 'opacity-100' : 'opacity-0'
              }`}
            />
            <span className="truncate">{membership.organization?.name}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
