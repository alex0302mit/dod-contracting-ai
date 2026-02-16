/**
 * LeftNav Component
 * 
 * Collapsible left navigation sidebar for the ACES application.
 * Provides navigation to all main screens.
 * 
 * Features:
 * - Collapsible: 64px (icons only) / 200px (expanded with labels)
 * - Active state indicator with deep navy background
 * - Tooltips on collapsed items
 * - Admin items only visible to admin users
 * 
 * Dependencies:
 * - useNavigation for route state
 * - useAuth for user role checking
 * - Tooltip component for collapsed labels
 */

import { useState } from 'react';
import {
  Home,
  Sparkles,
  FileText,
  FolderOpen,
  TrendingUp,
  UserCheck,
  Database,
  Download,
  Settings,
  ScrollText,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  Building2,
  FilePlus2,
  FileStack,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useNavigation, type RouteType } from '@/contexts/NavigationContext';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

// Navigation item configuration
interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  route: RouteType;
  adminOnly?: boolean;
}

// Main navigation items
const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: Home, route: 'OVERVIEW' },
  { id: 'generate', label: 'Generate', icon: FilePlus2, route: 'GENERATE_DOCUMENT' },
  { id: 'quick-generate', label: 'Quick Generate', icon: Sparkles, route: 'QUICK_GENERATE' },
  { id: 'editor', label: 'Editor', icon: FileText, route: 'EDITOR' },
  { id: 'my-documents', label: 'My Documents', icon: FileStack, route: 'MY_DOCUMENTS' },
  { id: 'documents', label: 'Documents', icon: FolderOpen, route: 'DOCUMENTS' },
  { id: 'tracker', label: 'Tracker', icon: TrendingUp, route: 'TRACKER' },
  { id: 'approvals', label: 'Approvals', icon: UserCheck, route: 'APPROVALS' },
  { id: 'sources', label: 'Sources', icon: Database, route: 'SOURCES' },
  { id: 'export', label: 'Export', icon: Download, route: 'EXPORT' },
];

// Bottom navigation items (settings, admin)
const bottomNavItems: NavItem[] = [
  { id: 'organizations', label: 'Organizations', icon: Building2, route: 'ADMIN_ORGS', adminOnly: true },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, route: 'ADMIN_ANALYTICS', adminOnly: true },
  { id: 'audit-logs', label: 'Audit Logs', icon: ScrollText, route: 'ADMIN_AUDIT_LOGS', adminOnly: true },
  { id: 'settings', label: 'Settings', icon: Settings, route: 'SETTINGS', adminOnly: true },
];

/**
 * NavButton - Single navigation item button
 */
interface NavButtonProps {
  item: NavItem;
  isActive: boolean;
  isCollapsed: boolean;
  onClick: () => void;
}

function NavButton({ item, isActive, isCollapsed, onClick }: NavButtonProps) {
  const Icon = item.icon;
  
  const button = (
    <Button
      variant="ghost"
      onClick={onClick}
      className={cn(
        "w-full justify-start gap-3 h-10 px-3 transition-colors",
        isCollapsed && "justify-center px-0",
        isActive
          ? "bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground"
          : "text-muted-foreground hover:text-foreground hover:bg-muted"
      )}
    >
      <Icon className={cn("h-5 w-5 flex-shrink-0", isActive && "text-primary-foreground")} />
      {!isCollapsed && (
        <span className="truncate">{item.label}</span>
      )}
    </Button>
  );
  
  // Wrap in tooltip when collapsed
  if (isCollapsed) {
    return (
      <Tooltip delayDuration={0}>
        <TooltipTrigger asChild>
          {button}
        </TooltipTrigger>
        <TooltipContent side="right" sideOffset={10}>
          {item.label}
        </TooltipContent>
      </Tooltip>
    );
  }
  
  return button;
}

/**
 * LeftNav component - collapsible sidebar navigation
 */
export function LeftNav() {
  const { user } = useAuth();
  const { currentRoute, navigate } = useNavigation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  // Filter items based on user role
  const visibleNavItems = navItems.filter(
    item => !item.adminOnly || user?.role === 'admin'
  );
  const visibleBottomItems = bottomNavItems.filter(
    item => !item.adminOnly || user?.role === 'admin'
  );
  
  return (
    <TooltipProvider>
      <nav
        className={cn(
          "h-full bg-card border-r border-border flex flex-col transition-all duration-200",
          isCollapsed ? "w-16" : "w-52"
        )}
      >
        {/* Main navigation items */}
        <div className="flex-1 py-2 px-2 space-y-1 overflow-y-auto">
          {visibleNavItems.map((item) => (
            <NavButton
              key={item.id}
              item={item}
              isActive={currentRoute === item.route}
              isCollapsed={isCollapsed}
              onClick={() => navigate(item.route)}
            />
          ))}
        </div>
        
        {/* Bottom items (settings, admin) */}
        {visibleBottomItems.length > 0 && (
          <div className="py-2 px-2 space-y-1 border-t border-border">
            {visibleBottomItems.map((item) => (
              <NavButton
                key={item.id}
                item={item}
                isActive={currentRoute === item.route}
                isCollapsed={isCollapsed}
                onClick={() => navigate(item.route)}
              />
            ))}
          </div>
        )}
        
        {/* Collapse toggle button */}
        <div className="p-2 border-t border-border">
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsCollapsed(!isCollapsed)}
                className={cn(
                  "w-full h-8 text-muted-foreground hover:text-foreground",
                  isCollapsed ? "justify-center px-0" : "justify-end"
                )}
              >
                {isCollapsed ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <>
                    <span className="text-xs mr-2">Collapse</span>
                    <ChevronLeft className="h-4 w-4" />
                  </>
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={10}>
              {isCollapsed ? 'Expand navigation' : 'Collapse navigation'}
            </TooltipContent>
          </Tooltip>
        </div>
      </nav>
    </TooltipProvider>
  );
}

export default LeftNav;
