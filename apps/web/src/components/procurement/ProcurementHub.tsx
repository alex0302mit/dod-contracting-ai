import { useState, useEffect } from 'react';
import { ProjectDashboard } from './ProjectDashboard';
import { ProcurementTracker } from './ProcurementTracker';

interface ProcurementHubProps {
  /** Optional initial project ID to display (e.g., from Dashboard navigation) */
  initialProjectId?: string | null;
  /** Callback when project selection changes */
  onProjectChange?: (projectId: string | null) => void;
}

export function ProcurementHub({ initialProjectId, onProjectChange }: ProcurementHubProps) {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(initialProjectId || null);

  // Sync with initialProjectId when it changes (e.g., from Dashboard)
  useEffect(() => {
    if (initialProjectId !== undefined) {
      setSelectedProjectId(initialProjectId);
    }
  }, [initialProjectId]);

  // Handle project selection with callback
  const handleSelectProject = (projectId: string | null) => {
    setSelectedProjectId(projectId);
    onProjectChange?.(projectId);
  };

  return (
    <div className="h-full">
      {selectedProjectId ? (
        <ProcurementTracker
          projectId={selectedProjectId}
          onBack={() => handleSelectProject(null)}
        />
      ) : (
        <ProjectDashboard onSelectProject={handleSelectProject} />
      )}
    </div>
  );
}
