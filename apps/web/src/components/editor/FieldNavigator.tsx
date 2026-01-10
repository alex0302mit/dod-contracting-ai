/**
 * FieldNavigator Component
 * 
 * DocuSign-style field navigation component that guides users through
 * fillable fields in the document one-by-one.
 * 
 * Features:
 * - Progress bar with completion percentage (handles 50+ fields gracefully)
 * - Section-based navigation dropdown for jumping to specific areas
 * - Quick "Apply & Next" workflow for fast filling
 * - Keyboard shortcuts (Enter to apply, Tab to skip)
 * - Visual progress tracking with filled/remaining counts
 * 
 * Dependencies:
 * - FillableField interface from editorUtils.ts
 * - SignaturePad component for signature fields
 * - DatePickerField component for date fields
 * - shadcn/ui components: Button, Dialog, Input, Badge, Select
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { 
  ArrowLeft, 
  ArrowRight, 
  Check, 
  X, 
  Pen, 
  Calendar, 
  Type,
  Play,
  CheckCircle2,
  MapPin,
  FileText,
  Lightbulb,
  DollarSign,
  User,
  Building2,
  Mail,
  Phone,
  Hash,
  ChevronDown,
  SkipForward,
  Keyboard
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { SignaturePad } from './SignaturePad';
import { DatePickerField } from './DatePickerField';
import { FillableField } from '@/lib/editorUtils';

interface FieldNavigatorProps {
  // Array of detected fillable fields
  fields: FillableField[];
  // Current document content
  content: string;
  // Callback when a field value is applied
  onFieldApply: (field: FillableField, value: string) => void;
  // Callback when navigator is closed
  onClose: () => void;
  // Whether the navigator is active/open
  isOpen: boolean;
}

/**
 * Get icon component based on field type
 */
function getFieldIcon(type: FillableField['type']) {
  switch (type) {
    case 'signature':
      return <Pen className="h-4 w-4" />;
    case 'date':
      return <Calendar className="h-4 w-4" />;
    default:
      return <Type className="h-4 w-4" />;
  }
}

/**
 * Get field type label for display
 */
function getFieldTypeLabel(type: FillableField['type']) {
  switch (type) {
    case 'signature':
      return 'Signature';
    case 'date':
      return 'Date';
    default:
      return 'Text';
  }
}

/**
 * Get icon for expected value type
 */
function getExpectedTypeIcon(expectedType?: string) {
  if (!expectedType) return <Type className="h-4 w-4" />;
  
  const type = expectedType.toLowerCase();
  
  if (type.includes('signature')) return <Pen className="h-4 w-4" />;
  if (type.includes('date')) return <Calendar className="h-4 w-4" />;
  if (type.includes('company') || type.includes('organization')) return <Building2 className="h-4 w-4" />;
  if (type.includes('name') || type.includes('person')) return <User className="h-4 w-4" />;
  if (type.includes('dollar') || type.includes('amount') || type.includes('price')) return <DollarSign className="h-4 w-4" />;
  if (type.includes('email')) return <Mail className="h-4 w-4" />;
  if (type.includes('phone')) return <Phone className="h-4 w-4" />;
  if (type.includes('number') || type.includes('reference')) return <Hash className="h-4 w-4" />;
  
  return <Type className="h-4 w-4" />;
}

/**
 * Section info for grouping fields
 */
interface SectionInfo {
  name: string;
  startIndex: number;
  endIndex: number;
  total: number;
  filled: number;
}

/**
 * Context Card Component
 * 
 * Shows the document context around a fillable field to help users
 * understand what value should be entered.
 */
function ContextCard({ field }: { field: FillableField }) {
  return (
    <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200">
      {/* Section indicator */}
      {field.section && (
        <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-200">
          <FileText className="h-4 w-4 text-slate-500" />
          <span className="text-xs font-medium text-slate-600">
            Section: {field.section}
          </span>
        </div>
      )}
      
      {/* Document context preview */}
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0 mt-0.5">
          <MapPin className="h-4 w-4 text-amber-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-slate-500 mb-1">Document context:</p>
          <p className="text-sm text-slate-700 leading-relaxed">
            {/* Context before the field */}
            <span className="text-slate-500">{field.contextBefore}</span>
            {/* Highlighted field pattern */}
            <span className="bg-amber-200 px-1 py-0.5 rounded font-medium text-amber-800 mx-0.5">
              {field.pattern}
            </span>
            {/* Context after the field */}
            <span className="text-slate-500">{field.contextAfter}</span>
          </p>
        </div>
      </div>
      
      {/* Expected type hint */}
      {field.hint && (
        <div className="flex items-center gap-2 mt-3 pt-2 border-t border-slate-200">
          <Lightbulb className="h-4 w-4 text-blue-500" />
          <span className="text-xs text-blue-600">{field.hint}</span>
        </div>
      )}
    </div>
  );
}

/**
 * Progress Bar Component
 * 
 * Shows overall completion progress with visual indicators
 */
function ProgressBar({ 
  current, 
  total, 
  filled 
}: { 
  current: number; 
  total: number; 
  filled: number; 
}) {
  const progressPercent = total > 0 ? ((current + 1) / total) * 100 : 0;
  const filledPercent = total > 0 ? (filled / total) * 100 : 0;
  
  return (
    <div className="w-48">
      {/* Labels */}
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="font-medium text-slate-700">Field {current + 1}</span>
        <span className="text-slate-500">of {total}</span>
      </div>
      
      {/* Progress bar with dual indicators */}
      <div className="h-2 bg-slate-200 rounded-full overflow-hidden relative">
        {/* Filled fields (green) */}
        <div 
          className="absolute h-full bg-emerald-400 rounded-full transition-all duration-300"
          style={{ width: `${filledPercent}%` }}
        />
        {/* Current position indicator (blue) */}
        <div 
          className="absolute h-full w-1 bg-blue-600 rounded-full transition-all duration-300"
          style={{ left: `calc(${progressPercent}% - 2px)` }}
        />
      </div>
      
      {/* Stats */}
      <div className="flex justify-between text-[10px] mt-1">
        <span className="text-emerald-600 font-medium">{filled} filled</span>
        <span className="text-slate-400">{total - filled} remaining</span>
      </div>
    </div>
  );
}

export function FieldNavigator({
  fields,
  content,
  onFieldApply,
  onClose,
  isOpen,
}: FieldNavigatorProps) {
  // Current field index
  const [currentIndex, setCurrentIndex] = useState(0);
  // Track which fields have been filled
  const [filledFields, setFilledFields] = useState<Set<string>>(new Set());
  // Text input value for text fields
  const [textValue, setTextValue] = useState('');
  // Show the input dialog
  const [showInput, setShowInput] = useState(false);
  // Navigator started (user clicked Start)
  const [isStarted, setIsStarted] = useState(false);

  // Current field being edited
  const currentField = fields[currentIndex];

  // Count of remaining fields
  const remainingCount = fields.length - filledFields.size;

  /**
   * Group fields by section for the dropdown
   */
  const sections = useMemo<SectionInfo[]>(() => {
    const sectionMap = new Map<string, { indices: number[]; filled: number }>();
    
    fields.forEach((field, index) => {
      const sectionName = field.section || 'Other Fields';
      if (!sectionMap.has(sectionName)) {
        sectionMap.set(sectionName, { indices: [], filled: 0 });
      }
      const section = sectionMap.get(sectionName)!;
      section.indices.push(index);
      if (filledFields.has(field.id)) {
        section.filled++;
      }
    });
    
    return Array.from(sectionMap.entries()).map(([name, data]) => ({
      name,
      startIndex: Math.min(...data.indices),
      endIndex: Math.max(...data.indices),
      total: data.indices.length,
      filled: data.filled,
    }));
  }, [fields, filledFields]);

  /**
   * Get current section name (with safe bounds checking)
   */
  const currentSection = useMemo(() => {
    const safeIdx = Math.min(Math.max(0, currentIndex), fields.length - 1);
    return sections.find(s => safeIdx >= s.startIndex && safeIdx <= s.endIndex)?.name || 'Other Fields';
  }, [sections, currentIndex, fields.length]);

  /**
   * Reset state when navigator opens (not when fields change to avoid losing progress)
   * Only reset when transitioning from closed to open
   */
  const [wasOpen, setWasOpen] = useState(false);
  
  useEffect(() => {
    // Only reset when transitioning from closed to open
    if (isOpen && !wasOpen && fields.length > 0) {
      setCurrentIndex(0);
      setFilledFields(new Set());
      setTextValue('');
      setIsStarted(false);
    }
    setWasOpen(isOpen);
  }, [isOpen, wasOpen, fields.length]);

  /**
   * Ensure currentIndex stays within bounds when fields change
   */
  useEffect(() => {
    if (fields.length > 0 && currentIndex >= fields.length) {
      setCurrentIndex(fields.length - 1);
    }
  }, [fields.length, currentIndex]);

  /**
   * Keyboard shortcuts handler
   * Note: Uses refs to avoid stale closures in event handler
   */
  useEffect(() => {
    if (!showInput || !isStarted) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
      // Tab to skip to next field
      if (e.key === 'Tab' && !e.shiftKey) {
        e.preventDefault();
        // Navigate to next field
        setCurrentIndex(prev => {
          if (prev < fields.length - 1) {
            setTextValue('');
            return prev + 1;
          }
          setShowInput(false);
          return prev;
        });
      }
      // Shift+Tab to go to previous field
      if (e.key === 'Tab' && e.shiftKey) {
        e.preventDefault();
        setCurrentIndex(prev => {
          if (prev > 0) {
            setTextValue('');
            return prev - 1;
          }
          return prev;
        });
      }
      // Escape to close dialog
      if (e.key === 'Escape') {
        setShowInput(false);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showInput, isStarted, fields.length]);

  /**
   * Start the field filling flow
   */
  const handleStart = useCallback(() => {
    setIsStarted(true);
    setShowInput(true);
  }, []);

  /**
   * Navigate to next field
   */
  const handleNext = useCallback(() => {
    if (currentIndex < fields.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setTextValue('');
    }
  }, [currentIndex, fields.length]);

  /**
   * Navigate to previous field
   */
  const handlePrev = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setTextValue('');
    }
  }, [currentIndex]);

  /**
   * Jump to a specific section
   */
  const handleJumpToSection = useCallback((sectionName: string) => {
    const section = sections.find(s => s.name === sectionName);
    if (section) {
      setCurrentIndex(section.startIndex);
      setTextValue('');
      setShowInput(true);
    }
  }, [sections]);

  /**
   * Apply text field value and auto-advance
   * Uses functional state update for reliability
   */
  const handleTextApply = useCallback(() => {
    const safeIdx = Math.min(Math.max(0, currentIndex), fields.length - 1);
    const field = fields[safeIdx];
    
    if (field && textValue.trim()) {
      onFieldApply(field, textValue.trim());
      setFilledFields(prev => new Set(prev).add(field.id));
      setTextValue('');
      
      // Auto-advance to next field if available
      if (safeIdx < fields.length - 1) {
        setCurrentIndex(safeIdx + 1);
      } else {
        // All done - close dialog
        setShowInput(false);
      }
    }
  }, [currentIndex, fields, textValue, onFieldApply]);

  /**
   * Apply signature and auto-advance
   */
  const handleSignatureApply = useCallback((signature: string) => {
    const safeIdx = Math.min(Math.max(0, currentIndex), fields.length - 1);
    const field = fields[safeIdx];
    
    if (field) {
      onFieldApply(field, signature);
      setFilledFields(prev => new Set(prev).add(field.id));
      
      if (safeIdx < fields.length - 1) {
        setCurrentIndex(safeIdx + 1);
        setTextValue('');
      } else {
        setShowInput(false);
      }
    }
  }, [currentIndex, fields, onFieldApply]);

  /**
   * Apply date and auto-advance
   */
  const handleDateApply = useCallback((dateString: string) => {
    const safeIdx = Math.min(Math.max(0, currentIndex), fields.length - 1);
    const field = fields[safeIdx];
    
    if (field) {
      onFieldApply(field, dateString);
      setFilledFields(prev => new Set(prev).add(field.id));
      
      if (safeIdx < fields.length - 1) {
        setCurrentIndex(safeIdx + 1);
        setTextValue('');
      } else {
        setShowInput(false);
      }
    }
  }, [currentIndex, fields, onFieldApply]);

  /**
   * Skip current field and move to next
   */
  const handleSkip = useCallback(() => {
    const safeIdx = Math.min(Math.max(0, currentIndex), fields.length - 1);
    
    if (safeIdx < fields.length - 1) {
      setCurrentIndex(safeIdx + 1);
      setTextValue('');
    } else {
      setShowInput(false);
    }
  }, [currentIndex, fields.length]);

  /**
   * Complete and close the navigator
   */
  const handleComplete = useCallback(() => {
    onClose();
  }, [onClose]);

  // Don't render if not open or no fields
  if (!isOpen || fields.length === 0) {
    return null;
  }

  // Safety check: ensure currentField exists
  // This prevents crashes if currentIndex is somehow out of bounds
  const safeCurrentIndex = Math.min(Math.max(0, currentIndex), fields.length - 1);
  const safeCurrentField = fields[safeCurrentIndex] || null;

  // Next field preview (for showing what's coming)
  const nextField = fields[safeCurrentIndex + 1] || null;

  return (
    <>
      {/* Floating Navigation Bar */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
        <div className="flex items-center gap-4 px-6 py-4 bg-white rounded-2xl shadow-2xl border border-slate-200">
          {!isStarted ? (
            <>
              {/* Start state */}
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                  <Type className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="font-semibold text-slate-800">
                    {fields.length} fields to fill
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Click Start to begin guided filling
                  </p>
                </div>
              </div>
              <Button 
                onClick={handleStart}
                className="bg-blue-600 hover:bg-blue-700 gap-2"
              >
                <Play className="h-4 w-4" />
                Start
              </Button>
              <Button 
                variant="ghost" 
                size="icon"
                onClick={onClose}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              {/* Progress section with label */}
              <div className="flex flex-col items-start">
                <span className="text-[10px] font-medium text-slate-500 mb-1">Progress</span>
                <ProgressBar
                  current={safeCurrentIndex}
                  total={fields.length}
                  filled={filledFields.size}
                />
              </div>

              {/* Divider */}
              <div className="h-10 w-px bg-slate-200" />

              {/* Section dropdown with label */}
              {sections.length > 0 && (
                <div className="flex flex-col items-start">
                  <span className="text-[10px] font-medium text-slate-500 mb-1">Section</span>
                  <Select value={currentSection} onValueChange={handleJumpToSection}>
                    <SelectTrigger className="w-[160px] h-9 text-xs">
                      <FileText className="h-3 w-3 mr-1 text-slate-400" />
                      <SelectValue placeholder="Jump to section" />
                    </SelectTrigger>
                    <SelectContent>
                      {sections.map(section => (
                        <SelectItem key={section.name} value={section.name}>
                          <div className="flex items-center justify-between w-full gap-2">
                            <span className="truncate max-w-[100px]">{section.name}</span>
                            <Badge
                              variant="outline"
                              className={`text-[10px] ${
                                section.filled === section.total
                                  ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                                  : 'bg-slate-50'
                              }`}
                            >
                              {section.filled}/{section.total}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Divider */}
              <div className="h-10 w-px bg-slate-200" />

              {/* Current field navigation with label */}
              <div className="flex flex-col items-start">
                <span className="text-[10px] font-medium text-slate-500 mb-1">Current Field</span>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handlePrev}
                    disabled={safeCurrentIndex === 0}
                    className="h-9 px-2 gap-1"
                    title="Previous field (Shift+Tab)"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    <span className="text-xs">Prev</span>
                  </Button>

                  {/* Current field button */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowInput(true)}
                    className="gap-2 min-w-[140px] justify-start h-9"
                  >
                    {getFieldIcon(safeCurrentField?.type || 'text')}
                    <span className="truncate max-w-[100px] text-xs">
                      {safeCurrentField?.name || 'Field'}
                    </span>
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleNext}
                    disabled={safeCurrentIndex >= fields.length - 1}
                    className="h-9 px-2 gap-1"
                    title="Next field (Tab)"
                  >
                    <span className="text-xs">Next</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Divider */}
              <div className="h-10 w-px bg-slate-200" />

              {/* Action section with label */}
              <div className="flex flex-col items-start">
                <span className="text-[10px] font-medium text-slate-500 mb-1">Action</span>
                <Button
                  size="sm"
                  onClick={() => setShowInput(true)}
                  className="bg-blue-600 hover:bg-blue-700 gap-1 h-9"
                >
                  Fill Field
                </Button>
              </div>

              {/* Done/Close with label */}
              <div className="flex flex-col items-start">
                <span className="text-[10px] font-medium text-slate-500 mb-1">
                  {remainingCount === 0 ? 'Complete' : 'Exit'}
                </span>
                {remainingCount === 0 ? (
                  <Button
                    size="sm"
                    onClick={handleComplete}
                    className="bg-emerald-600 hover:bg-emerald-700 gap-1 h-9"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    Done
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                    className="text-slate-400 hover:text-slate-600 h-9 px-2 gap-1"
                  >
                    <X className="h-4 w-4" />
                    <span className="text-xs">Close</span>
                  </Button>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Field Input Dialog - only render if we have a valid field */}
      <Dialog open={showInput && isStarted && safeCurrentField !== null} onOpenChange={setShowInput}>
        <DialogContent className="max-w-lg">
          {safeCurrentField && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {/* Icon based on expected type for better visual cue */}
                  <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
                    {getExpectedTypeIcon(safeCurrentField.expectedType)}
                  </div>
                  <div className="flex-1">
                    <span className="text-lg">{safeCurrentField.name || 'Fill Field'}</span>
                    {/* Expected type badge */}
                    {safeCurrentField.expectedType && (
                      <Badge 
                        variant="outline" 
                        className="ml-2 text-xs bg-blue-50 text-blue-600 border-blue-200"
                      >
                        {safeCurrentField.expectedType}
                      </Badge>
                    )}
                  </div>
                </DialogTitle>
                <DialogDescription className="flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-xs">
                    {getFieldTypeLabel(safeCurrentField.type)}
                  </Badge>
                  <span className="text-slate-400">•</span>
                  <span>
                    Field {safeCurrentIndex + 1} of {fields.length}
                  </span>
                  <span className="text-slate-400">•</span>
                  <span className="text-emerald-600">{filledFields.size} filled</span>
                </DialogDescription>
              </DialogHeader>

              {/* Context Card - shows document location and preview */}
              <ContextCard field={safeCurrentField} />

              {/* Field-specific input */}
              <div className="py-2">
                {safeCurrentField.type === 'signature' ? (
                  <SignaturePad
                    onApply={handleSignatureApply}
                    onCancel={handleSkip}
                  />
                ) : safeCurrentField.type === 'date' ? (
                  <DatePickerField
                    label={safeCurrentField.name}
                    onApply={handleDateApply}
                    onCancel={handleSkip}
                  />
                ) : (
                  /* Text input */
                  <div className="space-y-4">
                    {/* Input with placeholder hint */}
                    <Input
                      placeholder={safeCurrentField.hint || `Enter ${safeCurrentField.name?.toLowerCase() || 'value'}...`}
                      value={textValue}
                      onChange={(e) => setTextValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && textValue.trim()) {
                          e.preventDefault();
                          handleTextApply();
                        }
                      }}
                      className="text-lg h-12"
                      autoFocus
                    />
                    
                    {/* Preview of entered value */}
                    {textValue && (
                      <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-100">
                        <p className="text-xs text-emerald-600 mb-1">Your input:</p>
                        <p className="text-base font-medium text-emerald-800">{textValue}</p>
                      </div>
                    )}

                    {/* Quick action buttons with next field preview */}
                    <div className="space-y-3">
                      {/* Main action buttons */}
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          onClick={handleSkip}
                          className="flex-1 gap-1"
                        >
                          <SkipForward className="h-4 w-4" />
                          Skip
                        </Button>
                        <Button 
                          onClick={handleTextApply}
                          disabled={!textValue.trim()}
                          className="flex-1 bg-blue-600 hover:bg-blue-700 gap-1"
                        >
                          <Check className="h-4 w-4" />
                          {safeCurrentIndex < fields.length - 1 ? 'Apply & Next' : 'Apply'}
                        </Button>
                      </div>
                      
                      {/* Next field preview */}
                      {nextField && (
                        <div className="flex items-center justify-center gap-2 text-xs text-slate-500 pt-2 border-t">
                          <span>Next:</span>
                          <span className="font-medium text-slate-700">{nextField.name}</span>
                          <Badge variant="outline" className="text-[10px]">
                            {getFieldTypeLabel(nextField.type)}
                          </Badge>
                        </div>
                      )}
                      
                      {/* Keyboard shortcuts hint */}
                      <div className="flex items-center justify-center gap-4 text-[10px] text-slate-400">
                        <span className="flex items-center gap-1">
                          <Keyboard className="h-3 w-3" />
                          Enter to apply
                        </span>
                        <span>Tab to skip</span>
                        <span>Shift+Tab for previous</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

/**
 * FieldNavigatorButton Component
 * 
 * A button to trigger the field navigator when fillable fields are detected.
 * Shows the count of detected fields and provides a visual indicator.
 */
interface FieldNavigatorButtonProps {
  // Number of detected fields
  fieldCount: number;
  // Callback when button is clicked
  onClick: () => void;
  // Whether the button is disabled
  disabled?: boolean;
}

export function FieldNavigatorButton({
  fieldCount,
  onClick,
  disabled = false,
}: FieldNavigatorButtonProps) {
  if (fieldCount === 0) {
    return null;
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onClick}
      disabled={disabled}
      className="gap-2 border-amber-300 text-amber-700 hover:bg-amber-50 hover:border-amber-400"
    >
      <Type className="h-4 w-4" />
      Fill Fields
      <Badge 
        variant="secondary" 
        className="ml-1 bg-amber-100 text-amber-700 hover:bg-amber-100"
      >
        {fieldCount}
      </Badge>
    </Button>
  );
}
