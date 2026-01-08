/**
 * ZoomControl Component
 * 
 * Microsoft Word-style zoom slider for adjusting document view scale.
 * Provides slider, preset buttons, and percentage display.
 * 
 * Features:
 * - Slider from 50% to 200%
 * - Minus/Plus buttons for step adjustments
 * - Click on percentage to reset to 100%
 * - Preset zoom levels
 * 
 * Dependencies:
 *   - Shadcn Slider component
 *   - Lucide icons
 */

import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Minus, Plus } from 'lucide-react';

// Props interface for ZoomControl
interface ZoomControlProps {
  zoomLevel: number;
  onZoomChange: (zoom: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

// Preset zoom levels for quick selection
const ZOOM_PRESETS = [50, 75, 100, 125, 150, 200];

// Zoom step for increment/decrement buttons
const ZOOM_STEP = 10;

/**
 * ZoomControl - Zoom slider with increment/decrement buttons
 * 
 * Provides intuitive zoom control similar to Microsoft Word's
 * bottom-right zoom slider.
 */
export function ZoomControl({
  zoomLevel,
  onZoomChange,
  min = 50,
  max = 200,
  step = 10,
}: ZoomControlProps) {
  // Handle slider change
  const handleSliderChange = (value: number[]) => {
    onZoomChange(value[0]);
  };

  // Handle increment button
  const handleIncrement = () => {
    const newZoom = Math.min(max, zoomLevel + ZOOM_STEP);
    onZoomChange(newZoom);
  };

  // Handle decrement button
  const handleDecrement = () => {
    const newZoom = Math.max(min, zoomLevel - ZOOM_STEP);
    onZoomChange(newZoom);
  };

  // Reset to 100%
  const handleReset = () => {
    onZoomChange(100);
  };

  // Snap to nearest preset
  const handleSnapToPreset = () => {
    const nearestPreset = ZOOM_PRESETS.reduce((prev, curr) =>
      Math.abs(curr - zoomLevel) < Math.abs(prev - zoomLevel) ? curr : prev
    );
    onZoomChange(nearestPreset);
  };

  return (
    <div className="zoom-control flex items-center gap-2">
      {/* Decrement button */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={handleDecrement}
        disabled={zoomLevel <= min}
        className="h-6 w-6 p-0 hover:bg-gray-200"
        title="Zoom out"
      >
        <Minus className="h-3 w-3" />
      </Button>

      {/* Slider */}
      <div className="w-24">
        <Slider
          value={[zoomLevel]}
          onValueChange={handleSliderChange}
          min={min}
          max={max}
          step={step}
          className="cursor-pointer"
        />
      </div>

      {/* Increment button */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={handleIncrement}
        disabled={zoomLevel >= max}
        className="h-6 w-6 p-0 hover:bg-gray-200"
        title="Zoom in"
      >
        <Plus className="h-3 w-3" />
      </Button>

      {/* Percentage display (click to reset) */}
      <button
        type="button"
        onClick={handleReset}
        className="text-xs text-slate-600 hover:text-slate-900 hover:underline min-w-[40px] text-right"
        title="Click to reset to 100%"
      >
        {zoomLevel}%
      </button>
    </div>
  );
}

/**
 * ZoomControlCompact - Minimal zoom control for tight spaces
 * 
 * Just the percentage display and +/- buttons without slider.
 */
export function ZoomControlCompact({
  zoomLevel,
  onZoomChange,
  min = 50,
  max = 200,
}: Omit<ZoomControlProps, 'step'>) {
  return (
    <div className="zoom-control-compact flex items-center gap-1">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => onZoomChange(Math.max(min, zoomLevel - 10))}
        disabled={zoomLevel <= min}
        className="h-5 w-5 p-0"
        title="Zoom out"
      >
        <Minus className="h-3 w-3" />
      </Button>
      
      <span className="text-xs text-slate-600 min-w-[36px] text-center">
        {zoomLevel}%
      </span>
      
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => onZoomChange(Math.min(max, zoomLevel + 10))}
        disabled={zoomLevel >= max}
        className="h-5 w-5 p-0"
        title="Zoom in"
      >
        <Plus className="h-3 w-3" />
      </Button>
    </div>
  );
}

export default ZoomControl;
