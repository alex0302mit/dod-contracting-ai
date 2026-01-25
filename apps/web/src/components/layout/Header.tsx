/**
 * Header Component
 * 
 * Top control bar for the ACES application containing:
 * - ACES logo and branding
 * - Project switcher dropdown
 * - Global search input (placeholder for future)
 * - Sync status indicator
 * - Notification center
 * - User menu with sign out and personal analytics
 * 
 * Dependencies:
 * - useProcurementProjects for project list
 * - NotificationCenter component
 * - useAuth for user info
 * - useNavigation for project selection
 * - useUserStats for personal analytics (lazy loaded on dropdown open)
 */

import { useState, useEffect } from 'react';
import {
  Search,
  ChevronDown,
  User,
  LogOut,
  Check,
  FolderKanban,
  Clock,
  FileText,
  Loader2
} from 'lucide-react';
import { AcesLogo } from '@/components/shared/AcesLogo';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { NotificationCenter } from '@/components/procurement/NotificationCenter';
import { useProcurementProjects } from '@/hooks/useProcurementProjects';
import { useUserStats } from '@/hooks/useUserStats';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigation } from '@/contexts/NavigationContext';
import { cn } from '@/lib/utils';

/**
 * SyncIndicator shows WebSocket connection status
 * Shows "Synced" when connected, "Syncing..." when reconnecting
 */
function SyncIndicator() {
  const [synced, setSynced] = useState(true);
  
  // Simulate sync status - in production this would connect to WebSocket
  useEffect(() => {
    // For now, always show as synced
    // TODO: Integrate with createWebSocket from api.ts
    setSynced(true);
  }, []);
  
  return (
    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
      <div className={cn(
        "h-2 w-2 rounded-full transition-colors",
        synced ? "bg-success" : "bg-warning animate-sync-pulse"
      )} />
      <span className="hidden sm:inline">
        {synced ? 'Synced' : 'Syncing...'}
      </span>
    </div>
  );
}

/**
 * Header component - top control bar
 */
export function Header() {
  const { user, signOut } = useAuth();
  const { projects } = useProcurementProjects();
  const { selectedProjectId, setSelectedProjectId, navigateToProject } = useNavigation();
  const [searchQuery, setSearchQuery] = useState('');
  
  // Personal analytics - lazy loaded when dropdown opens
  const { stats, loading: statsLoading, fetchStats, hasLoaded } = useUserStats();
  
  // Fetch stats when user dropdown opens (lazy loading)
  const handleDropdownOpenChange = (open: boolean) => {
    if (open && !hasLoaded) {
      fetchStats();
    }
  };
  
  // Handle project selection from dropdown
  const handleProjectSelect = (projectId: string) => {
    if (projectId === 'none') {
      setSelectedProjectId(null);
    } else {
      navigateToProject(projectId);
    }
  };
  
  // Get selected project name for display
  const selectedProject = projects.find(p => p.id === selectedProjectId);
  
  return (
    <header className="h-14 border-b border-border bg-card shadow-sm sticky top-0 z-50">
      <div className="h-full px-4 flex items-center justify-between gap-4">
        {/* Left section: Logo and branding */}
        <div className="flex items-center gap-4">
          {/* ACES Logo */}
          <AcesLogo size="md" showText={true} />
          
          {/* Vertical separator */}
          <div className="h-6 w-px bg-border hidden lg:block" />
          
          {/* Project Switcher */}
          <div className="hidden lg:block">
            <Select
              value={selectedProjectId || 'none'}
              onValueChange={handleProjectSelect}
            >
              <SelectTrigger className="w-[200px] h-8 text-sm">
                <FolderKanban className="h-4 w-4 mr-2 text-muted-foreground" />
                <SelectValue placeholder="Select project...">
                  {selectedProject ? (
                    <span className="truncate">{selectedProject.name}</span>
                  ) : (
                    <span className="text-muted-foreground">Select project...</span>
                  )}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">
                  <span className="text-muted-foreground">No project selected</span>
                </SelectItem>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    <div className="flex items-center gap-2">
                      <span className="truncate">{project.name}</span>
                      {project.id === selectedProjectId && (
                        <Check className="h-4 w-4 text-success ml-auto" />
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        
        {/* Center section: Search */}
        <div className="flex-1 max-w-md hidden md:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search documents, projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-8 bg-muted/50 border-transparent focus:border-input focus:bg-background"
            />
          </div>
        </div>
        
        {/* Right section: Status, notifications, user */}
        <div className="flex items-center gap-2">
          {/* Sync indicator */}
          <SyncIndicator />
          
          {/* Notifications */}
          <NotificationCenter />
          
          {/* User Menu with Personal Analytics */}
          {user && (
            <DropdownMenu onOpenChange={handleDropdownOpenChange}>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2 h-8">
                  <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <span className="hidden lg:inline text-sm font-medium max-w-[100px] truncate">
                    {user.name}
                  </span>
                  <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-72">
                {/* User Info Section */}
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span className="font-medium">{user.name}</span>
                    <span className="text-xs text-muted-foreground capitalize">
                      {user.role?.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-muted-foreground mt-0.5">
                      {user.email}
                    </span>
                  </div>
                </DropdownMenuLabel>
                
                <DropdownMenuSeparator />
                
                {/* Personal Analytics Section */}
                <div className="px-2 py-3">
                  <p className="text-xs font-medium text-muted-foreground mb-2">
                    Your Activity (this month)
                  </p>
                  
                  {statsLoading ? (
                    // Loading state
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                    </div>
                  ) : stats ? (
                    // Stats loaded successfully
                    <>
                      <div className="grid grid-cols-2 gap-2 mb-2">
                        {/* Time Saved Card */}
                        <div className="bg-muted/50 rounded-md p-2.5 text-center">
                          <div className="flex items-center justify-center gap-1 mb-1">
                            <Clock className="h-3.5 w-3.5 text-primary" />
                          </div>
                          <p className="text-lg font-semibold">
                            {stats.estimatedHoursSaved > 0 
                              ? `~${stats.estimatedHoursSaved}` 
                              : '0'}
                            <span className="text-xs font-normal ml-0.5">hrs</span>
                          </p>
                          <p className="text-xs text-muted-foreground">Time saved</p>
                        </div>
                        
                        {/* Documents Generated Card */}
                        <div className="bg-muted/50 rounded-md p-2.5 text-center">
                          <div className="flex items-center justify-center gap-1 mb-1">
                            <FileText className="h-3.5 w-3.5 text-primary" />
                          </div>
                          <p className="text-lg font-semibold">
                            {stats.documentsGenerated}
                          </p>
                          <p className="text-xs text-muted-foreground">Docs generated</p>
                        </div>
                      </div>
                      
                      {/* Projects Contributed Row */}
                      <div className="bg-muted/50 rounded-md p-2 flex items-center justify-center gap-2">
                        <FolderKanban className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-sm">
                          <span className="font-medium">{stats.projectsContributed}</span>
                          <span className="text-muted-foreground ml-1">
                            {stats.projectsContributed === 1 ? 'project' : 'projects'} contributed
                          </span>
                        </span>
                      </div>
                    </>
                  ) : (
                    // No stats or error - show empty state
                    <div className="text-center py-2 text-sm text-muted-foreground">
                      No activity yet this month
                    </div>
                  )}
                </div>
                
                <DropdownMenuSeparator />
                
                {/* Sign Out Button */}
                <DropdownMenuItem 
                  onClick={() => signOut()} 
                  className="text-destructive cursor-pointer focus:text-destructive focus:bg-destructive/10"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
