import { useState } from 'react';
import { ProjectDashboard } from './ProjectDashboard';
import { ProcurementTracker } from './ProcurementTracker';

export function ProcurementHub() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  return (
    <div className="h-full">
      {selectedProjectId ? (
        <ProcurementTracker
          projectId={selectedProjectId}
          onBack={() => setSelectedProjectId(null)}
        />
      ) : (
        <ProjectDashboard onSelectProject={setSelectedProjectId} />
      )}
    </div>
  );
}
