import { CheckCircle2, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TrackerSegment {
  id: string;
  label: string;
  sublabel?: string;
  status: 'completed' | 'active' | 'pending';
}

interface SegmentedTrackerBarProps {
  segments: TrackerSegment[];
  className?: string;
}

export function SegmentedTrackerBar({ segments, className }: SegmentedTrackerBarProps) {
  const completedCount = segments.filter(s => s.status === 'completed').length;
  const activeIndex = segments.findIndex(s => s.status === 'active');
  const progressPercentage = activeIndex >= 0
    ? ((activeIndex + 0.5) / segments.length) * 100
    : (completedCount / segments.length) * 100;

  return (
    <div className={cn('w-full', className)}>
      <div className="relative">
        <div className="flex items-end justify-between mb-2 px-4">
          {segments.map((segment) => (
            <div
              key={segment.id}
              className="flex flex-col items-center"
              style={{ width: `${100 / segments.length}%` }}
            >
              <div className="text-center mb-1">
                <div className={cn(
                  'text-xs font-semibold transition-colors',
                  segment.status === 'completed'
                    ? 'text-green-700'
                    : segment.status === 'active'
                    ? 'text-blue-700'
                    : 'text-slate-500'
                )}>
                  {segment.label}
                </div>
                {segment.sublabel && (
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    {segment.sublabel}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="relative h-16 bg-slate-100 rounded-full overflow-hidden border-2 border-slate-300">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />

          <svg
            className="absolute inset-0 w-full h-full"
            viewBox="0 0 1000 100"
            preserveAspectRatio="none"
          >
            {segments.map((_, index) => {
              if (index === 0) return null;
              const x = (index / segments.length) * 1000;
              return (
                <line
                  key={index}
                  x1={x}
                  y1="0"
                  x2={x}
                  y2="100"
                  stroke="#475569"
                  strokeWidth="2"
                  strokeDasharray="4,4"
                  opacity="0.3"
                />
              );
            })}
          </svg>

          <div className="absolute inset-0 flex items-center justify-around px-4">
            {segments.map((segment) => (
              <div
                key={segment.id}
                className="flex items-center justify-center"
              >
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all shadow-md',
                    segment.status === 'completed'
                      ? 'bg-green-500 border-green-600 text-white'
                      : segment.status === 'active'
                      ? 'bg-blue-600 border-blue-700 text-white animate-pulse'
                      : 'bg-white border-slate-300 text-slate-400'
                  )}
                >
                  {segment.status === 'completed' ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <Circle className="w-4 h-4" fill="currentColor" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end mt-2 pr-4">
          <div className="text-xs text-slate-600 italic">
            {completedCount === segments.length ? 'Contract Close Out' : 'In Progress'}
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span className="text-slate-600">Completed</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-blue-600"></div>
          <span className="text-slate-600">Active</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-slate-300"></div>
          <span className="text-slate-600">Pending</span>
        </div>
      </div>
    </div>
  );
}

export function ProcurementTrackerBar({ currentPhase }: { currentPhase: string }) {
  const segments: TrackerSegment[] = [
    {
      id: 'requirements',
      label: 'Requirements',
      status: ['pre_solicitation', 'solicitation', 'post_solicitation'].includes(currentPhase)
        ? 'completed'
        : currentPhase === 'requirements'
        ? 'active'
        : 'pending',
    },
    {
      id: 'pre_solicitation',
      label: 'Pre-Solicitation',
      status: ['solicitation', 'post_solicitation'].includes(currentPhase)
        ? 'completed'
        : currentPhase === 'pre_solicitation'
        ? 'active'
        : 'pending',
    },
    {
      id: 'solicitation',
      label: 'Solicitation',
      status: currentPhase === 'post_solicitation'
        ? 'completed'
        : currentPhase === 'solicitation'
        ? 'active'
        : 'pending',
    },
    {
      id: 'pre_award',
      label: 'Pre-Award',
      sublabel: 'Evaluation',
      status: ['award', 'contract', 'closeout'].includes(currentPhase)
        ? 'completed'
        : currentPhase === 'post_solicitation'
        ? 'active'
        : 'pending',
    },
    {
      id: 'award',
      label: 'Award',
      status: ['contract', 'closeout'].includes(currentPhase)
        ? 'completed'
        : currentPhase === 'award'
        ? 'active'
        : 'pending',
    },
    {
      id: 'contract',
      label: 'Contract',
      sublabel: 'Active',
      status: currentPhase === 'closeout'
        ? 'completed'
        : currentPhase === 'contract'
        ? 'active'
        : 'pending',
    },
  ];

  return <SegmentedTrackerBar segments={segments} />;
}
