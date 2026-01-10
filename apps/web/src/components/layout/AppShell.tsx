/**
 * AppShell Component
 * 
 * Main layout wrapper for the ACES application providing:
 * - Top header with ACES branding and controls
 * - Left navigation sidebar (collapsible)
 * - Main work surface content area
 * - Right verification console rail (collapsible)
 * 
 * Uses react-resizable-panels for adjustable panel widths.
 * 
 * Dependencies:
 * - Header, LeftNav, ConsoleRail components
 * - ConsoleRailContext for rail state management
 * - react-resizable-panels for layout
 */

import { ReactNode } from 'react';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import { useConsoleRail } from '@/contexts/ConsoleRailContext';
import { Header } from './Header';
import { LeftNav } from './LeftNav';
import { ConsoleRail } from './ConsoleRail';
import { AcesLogoIcon } from '@/components/shared/AcesLogo';
import { cn } from '@/lib/utils';

interface AppShellProps {
  /** Main content to render in the work surface */
  children: ReactNode;
  /** Whether to show the ConsoleRail (default: true) */
  showConsoleRail?: boolean;
  /** Additional className for the main content area */
  className?: string;
}

/**
 * AppShell provides the consistent layout structure for all ACES screens.
 * 
 * Layout:
 * ┌─────────────────────────────────────────────────────┐
 * │                    Header                           │
 * ├───────┬─────────────────────────────────┬──────────┤
 * │       │                                 │          │
 * │ Left  │         Main Content            │ Console  │
 * │ Nav   │          (children)             │  Rail    │
 * │       │                                 │          │
 * └───────┴─────────────────────────────────┴──────────┘
 */
export function AppShell({ 
  children, 
  showConsoleRail = true,
  className 
}: AppShellProps) {
  const { isOpen: isRailOpen } = useConsoleRail();
  
  // Determine if we should show the rail based on prop and context
  const shouldShowRail = showConsoleRail && isRailOpen;
  
  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Top Header - fixed height */}
      <Header />
      
      {/* Main content area with sidebar and optional rail */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Navigation Sidebar */}
        <LeftNav />
        
        {/* Main work surface with optional right rail */}
        <ResizablePanelGroup 
          direction="horizontal" 
          className="flex-1"
        >
          {/* Main Content Panel */}
          <ResizablePanel
            defaultSize={shouldShowRail ? 70 : 100}
            minSize={40}
            className="flex flex-col"
          >
            <main className={cn(
              "h-full overflow-auto relative",
              className
            )}>
              {/* Background watermark */}
              <div className="fixed inset-0 pointer-events-none flex items-center justify-center z-0 overflow-hidden">
                <AcesLogoIcon size={500} className="opacity-[0.03]" />
              </div>
              {/* Main content */}
              <div className="relative z-10">
                {children}
              </div>
            </main>
          </ResizablePanel>
          
          {/* Console Rail (when visible) */}
          {showConsoleRail && (
            <>
              {isRailOpen && <ResizableHandle withHandle />}
              <ConsoleRail />
            </>
          )}
        </ResizablePanelGroup>
      </div>
    </div>
  );
}

/**
 * AppShellWithoutRail - Convenience wrapper for screens that never show the rail
 * 
 * Use this for screens like Overview, Documents, Tracker, Sources
 * where the ConsoleRail should not appear.
 */
export function AppShellWithoutRail({ 
  children, 
  className 
}: Omit<AppShellProps, 'showConsoleRail'>) {
  return (
    <AppShell showConsoleRail={false} className={className}>
      {children}
    </AppShell>
  );
}

export default AppShell;
