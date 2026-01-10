# Segmented Tracker Bar Component

## Overview
The `SegmentedTrackerBar` component is a horizontal progress tracker inspired by delivery tracking interfaces (like Domino's Pizza tracker), specifically designed for procurement workflows based on the hand-drawn sketch provided.

## Visual Design
The component replicates the sketch design with the following elements:
- **Rounded/pill-shaped horizontal bar** with smooth ends
- **Diagonal segment dividers** (visual markers)
- **Labels positioned above each segment** for clear phase identification
- **Animated progress fill** showing completion status
- **Status indicators** (checkmarks for completed, animated pulse for active)
- **"Contract Close out" notation** at the end when complete

## Component Structure

### Main Component: `SegmentedTrackerBar`
Located at: `src/components/procurement/SegmentedTrackerBar.tsx`

**Props:**
```typescript
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
```

### Procurement-Specific Component: `ProcurementTrackerBar`
Pre-configured component matching the procurement phases from the sketch.

**Props:**
```typescript
interface ProcurementTrackerBarProps {
  currentPhase: string;
}
```

**Phases:**
1. **Requirements** - Initial needs identification
2. **Pre-Solicitation** - Planning and strategy
3. **Solicitation** - RFP/RFQ process
4. **Pre-Award** - Evaluation phase
5. **Award** - Contract award
6. **Contract** - Active contract
7. **Close out** - Completion (shown in label)

## Visual Features

### Colors
- **Completed segments**: Green (#10B981)
  - Background: `bg-green-500`
  - Indicator: Checkmark icon

- **Active segment**: Blue (#2563EB)
  - Background: `bg-blue-600`
  - Indicator: Pulsing dot
  - Animation: Pulse effect

- **Pending segments**: Gray (#CBD5E1)
  - Background: `bg-slate-300`
  - Indicator: Empty circle

### Progress Animation
- Smooth transition with 500ms ease-out timing
- Gradient fill from `blue-500` to `blue-600`
- Real-time progress calculation based on completed segments

### Responsive Design
- Full width container
- Labels stack appropriately on smaller screens
- Touch-friendly spacing
- Maintains proportions across viewport sizes

## Usage Examples

### Basic Usage
```tsx
import { ProcurementTrackerBar } from '@/components/procurement/SegmentedTrackerBar';

function MyComponent() {
  return (
    <ProcurementTrackerBar currentPhase="solicitation" />
  );
}
```

### Custom Segments
```tsx
import { SegmentedTrackerBar } from '@/components/procurement/SegmentedTrackerBar';

const customSegments = [
  { id: '1', label: 'Planning', status: 'completed' },
  { id: '2', label: 'Execution', status: 'active' },
  { id: '3', label: 'Review', status: 'pending' },
  { id: '4', label: 'Approval', status: 'pending' },
];

function CustomTracker() {
  return <SegmentedTrackerBar segments={customSegments} />;
}
```

## Integration with Procurement Tracker

The component is integrated into the main `ProcurementTracker` view with a tabbed interface:

1. **Segmented View** - Uses the new tracker bar design
2. **Circular View** - Uses the original circular phase indicators

Users can toggle between views using tabs at the top of the tracker interface.

## Technical Implementation

### Key Technologies
- **React** - Component framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling and animations
- **Lucide React** - Icons (CheckCircle2, Circle)
- **shadcn/ui** - Base UI components

### Animation Details
- CSS transitions for smooth color changes
- SVG for diagonal divider lines (visual only)
- Pulsing animation for active segment indicator
- Gradient progress fill with dynamic width

### Accessibility
- Clear visual distinction between states
- Text labels for all phases
- High contrast ratios
- Keyboard navigable (when interactive)
- Screen reader compatible with proper ARIA labels

## Matching the Original Sketch

The implementation closely follows the hand-drawn design:

✅ **Horizontal pill-shaped bar** - Rounded ends with `rounded-full`
✅ **Diagonal dividers** - Implemented with dashed SVG lines
✅ **Phase labels above** - Positioned above each segment
✅ **Progress indication** - Animated fill showing completion
✅ **Status markers** - Checkmarks, pulses, and empty circles
✅ **"Contract close out"** - Shown when all phases complete

## Color Palette
```css
/* Completed */
--completed-bg: #10B981 (green-500)
--completed-border: #059669 (green-600)

/* Active */
--active-bg: #2563EB (blue-600)
--active-border: #1E40AF (blue-700)
--active-gradient: linear-gradient(to right, #3B82F6, #2563EB)

/* Pending */
--pending-bg: #E2E8F0 (slate-200)
--pending-border: #CBD5E1 (slate-300)

/* Text */
--label-active: #1E40AF (blue-700)
--label-completed: #047857 (green-700)
--label-pending: #64748B (slate-500)
```

## Performance Considerations
- Lightweight SVG for divider lines
- CSS-only animations (GPU accelerated)
- Minimal re-renders with proper React optimization
- No external dependencies beyond existing UI library

## Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS Grid and Flexbox support required
- SVG support required
- CSS animations support required

## Future Enhancements
- Click handlers for segment navigation
- Tooltip details on hover
- Estimated time remaining display
- Configurable color themes
- Export as image/PDF
- Mobile swipe gestures
