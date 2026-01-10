/**
 * ApprovalsScreen Component
 * 
 * Wraps the existing PendingApprovalsView with ConsoleRail integration.
 * Opens ConsoleRail with Audit tab when viewing approval details.
 * 
 * Dependencies:
 * - PendingApprovalsView for approval management
 * - useConsoleRail for rail state
 * - approvalsApi for audit data
 */

import { useEffect } from 'react';
import { PendingApprovalsView } from '@/components/procurement/PendingApprovalsView';
import { useConsoleRail } from '@/contexts/ConsoleRailContext';

/**
 * ApprovalsScreen wraps PendingApprovalsView with ConsoleRail
 */
export function ApprovalsScreen() {
  const { closeRail } = useConsoleRail();
  
  // Close ConsoleRail - Approvals has its own UI
  useEffect(() => {
    closeRail();
  }, [closeRail]);
  
  return (
    <div className="h-full overflow-auto p-6">
      <PendingApprovalsView />
    </div>
  );
}

export default ApprovalsScreen;
