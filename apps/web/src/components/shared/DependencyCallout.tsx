/**
 * DependencyCallout Component
 * 
 * Amber callout displayed when document dependencies are not met.
 * Shows missing dependencies and provides a "Resolve" action.
 * 
 * Used in Tracker screen when generation is blocked by missing prereqs.
 * 
 * Dependencies:
 * - Alert from shadcn/ui
 * - Sheet for resolution panel
 */

import { useState } from 'react';
import { AlertTriangle, ChevronRight, FileText, CheckCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface DependencyCalloutProps {
  /** List of missing dependency names */
  missingDependencies: string[];
  /** List of available/satisfied dependencies */
  availableDependencies?: string[];
  /** Document name this applies to */
  documentName?: string;
  /** Callback when resolve button is clicked */
  onResolve?: () => void;
  /** Callback when a specific dependency is clicked */
  onDependencyClick?: (dependency: string) => void;
  /** Additional className */
  className?: string;
  /** Whether to show inline or as a full callout */
  inline?: boolean;
}

/**
 * DependencyCallout alerts users about missing prerequisites
 */
export function DependencyCallout({
  missingDependencies,
  availableDependencies = [],
  documentName,
  onResolve,
  onDependencyClick,
  className,
  inline = false,
}: DependencyCalloutProps) {
  const [sheetOpen, setSheetOpen] = useState(false);
  
  // Handle resolve button click
  const handleResolve = () => {
    if (onResolve) {
      onResolve();
    } else {
      setSheetOpen(true);
    }
  };
  
  // Inline version - minimal display
  if (inline) {
    return (
      <div className={cn(
        "flex items-center gap-2 text-warning text-sm",
        className
      )}>
        <AlertTriangle className="h-4 w-4 flex-shrink-0" />
        <span>
          {missingDependencies.length} missing {missingDependencies.length === 1 ? 'dependency' : 'dependencies'}
        </span>
        <Button
          variant="link"
          size="sm"
          onClick={handleResolve}
          className="h-auto p-0 text-warning hover:text-warning/80"
        >
          Resolve
          <ChevronRight className="h-3 w-3 ml-1" />
        </Button>
      </div>
    );
  }
  
  return (
    <>
      <Alert className={cn("border-warning/50 bg-warning/10", className)}>
        <AlertTriangle className="h-4 w-4 text-warning" />
        <AlertTitle className="text-warning">
          Dependencies Required
        </AlertTitle>
        <AlertDescription className="mt-2">
          <p className="text-sm text-muted-foreground mb-3">
            {documentName 
              ? `"${documentName}" requires the following documents to be completed first:`
              : 'The following prerequisites must be completed before proceeding:'
            }
          </p>
          
          {/* Missing dependencies list */}
          <div className="flex flex-wrap gap-2 mb-3">
            {missingDependencies.map((dep, idx) => (
              <Badge
                key={idx}
                variant="outline"
                className="border-warning/50 text-warning cursor-pointer hover:bg-warning/10"
                onClick={() => onDependencyClick?.(dep)}
              >
                <FileText className="h-3 w-3 mr-1" />
                {dep}
              </Badge>
            ))}
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleResolve}
            className="border-warning/50 text-warning hover:bg-warning/10 hover:text-warning"
          >
            Resolve Dependencies
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </AlertDescription>
      </Alert>
      
      {/* Resolution Sheet */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent className="w-full sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>Resolve Dependencies</SheetTitle>
            <SheetDescription>
              Complete the following documents to unblock generation
            </SheetDescription>
          </SheetHeader>
          
          <ScrollArea className="h-[calc(100vh-150px)] mt-6">
            <div className="space-y-6">
              {/* Missing Dependencies */}
              {missingDependencies.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-warning flex items-center gap-2 mb-3">
                    <AlertTriangle className="h-4 w-4" />
                    Missing ({missingDependencies.length})
                  </h4>
                  <div className="space-y-2">
                    {missingDependencies.map((dep, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 rounded-lg border border-warning/30 bg-warning/5"
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-warning" />
                          <span className="text-sm">{dep}</span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            onDependencyClick?.(dep);
                            setSheetOpen(false);
                          }}
                        >
                          Generate
                          <ChevronRight className="h-4 w-4 ml-1" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Available Dependencies */}
              {availableDependencies.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-success flex items-center gap-2 mb-3">
                    <CheckCircle className="h-4 w-4" />
                    Completed ({availableDependencies.length})
                  </h4>
                  <div className="space-y-2">
                    {availableDependencies.map((dep, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 p-3 rounded-lg border bg-success/5 border-success/30"
                      >
                        <CheckCircle className="h-4 w-4 text-success" />
                        <span className="text-sm">{dep}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </SheetContent>
      </Sheet>
    </>
  );
}

export default DependencyCallout;
