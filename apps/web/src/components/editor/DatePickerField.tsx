/**
 * DatePickerField Component
 * 
 * A date picker wrapper for the DocuSign-style field navigator.
 * Provides a calendar popup with:
 * - Month/year navigation
 * - Today button for quick selection
 * - Configurable date format output
 * 
 * Dependencies:
 * - Uses shadcn/ui Calendar component (react-day-picker under the hood)
 * - shadcn/ui Popover for the calendar dropdown
 * - date-fns for date formatting (already a dependency of react-day-picker)
 */

import { useState } from 'react';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';

interface DatePickerFieldProps {
  // Callback when date is applied
  onApply: (dateString: string) => void;
  // Callback when cancelled
  onCancel: () => void;
  // Optional initial date value
  initialValue?: Date;
  // Date format for output string (default: "MMMM d, yyyy" -> "November 28, 2025")
  dateFormat?: string;
  // Optional label for the field
  label?: string;
}

export function DatePickerField({
  onApply,
  onCancel,
  initialValue,
  dateFormat = 'MMMM d, yyyy',
  label = 'Select Date',
}: DatePickerFieldProps) {
  // Currently selected date
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(initialValue);
  // Popover open state
  const [isOpen, setIsOpen] = useState(true);

  /**
   * Handle date selection from calendar
   */
  const handleSelect = (date: Date | undefined) => {
    setSelectedDate(date);
  };

  /**
   * Apply the selected date
   */
  const handleApply = () => {
    if (selectedDate) {
      const formattedDate = format(selectedDate, dateFormat);
      onApply(formattedDate);
    }
  };

  /**
   * Quick select today's date
   */
  const handleSelectToday = () => {
    const today = new Date();
    setSelectedDate(today);
  };

  return (
    <div className="w-full space-y-4">
      {/* Label */}
      <p className="text-sm font-medium text-slate-700">{label}</p>

      {/* Date picker button with popover */}
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              'w-full justify-start text-left font-normal h-12',
              !selectedDate && 'text-muted-foreground'
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {selectedDate ? (
              <span className="text-base">{format(selectedDate, dateFormat)}</span>
            ) : (
              <span>Click to select a date...</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={handleSelect}
            initialFocus
            className="rounded-md border"
          />
          {/* Today button */}
          <div className="border-t p-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSelectToday}
              className="w-full text-xs"
            >
              Today
            </Button>
          </div>
        </PopoverContent>
      </Popover>

      {/* Preview of selected date */}
      {selectedDate && (
        <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
          <p className="text-xs text-blue-600 mb-1">Selected date:</p>
          <p className="text-lg font-medium text-blue-800">
            {format(selectedDate, dateFormat)}
          </p>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2 pt-2">
        <Button 
          variant="outline" 
          onClick={onCancel}
          className="flex-1"
        >
          <X className="h-4 w-4 mr-2" />
          Cancel
        </Button>
        <Button 
          onClick={handleApply}
          disabled={!selectedDate}
          className="flex-1 bg-blue-600 hover:bg-blue-700"
        >
          <Check className="h-4 w-4 mr-2" />
          Apply Date
        </Button>
      </div>
    </div>
  );
}

