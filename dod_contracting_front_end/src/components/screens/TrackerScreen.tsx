/**
 * TrackerScreen Component
 * 
 * Wraps the existing ProcurementTracker with ACES layout.
 * Adds DependencyCallout integration for blocked documents.
 * 
 * Dependencies:
 * - ProcurementTracker for the main tracker functionality
 * - ProcurementHub for project selection
 * - useNavigation for project state
 */

import { ProcurementHub } from '@/components/procurement/ProcurementHub';
import { useNavigation } from '@/contexts/NavigationContext';

/**
 * TrackerScreen wraps ProcurementHub/ProcurementTracker
 */
export function TrackerScreen() {
  const { selectedProjectId, setSelectedProjectId } = useNavigation();
  
  // Handle project selection from the hub
  const handleProjectChange = (projectId: string | null) => {
    setSelectedProjectId(projectId);
  };
  
  return (
    <div className="h-full overflow-hidden">
      <ProcurementHub
        initialProjectId={selectedProjectId}
        onProjectChange={handleProjectChange}
      />
    </div>
  );
}

export default TrackerScreen;
