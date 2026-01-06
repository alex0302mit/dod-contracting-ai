/**
 * SignaturePad Component
 * 
 * A DocuSign-style signature input component with two modes:
 * 1. Draw mode: Canvas-based freehand signature drawing
 * 2. Type mode: Text input with cursive font preview
 * 
 * Dependencies:
 * - Uses Canvas API for signature drawing (built-in browser API)
 * - shadcn/ui components: Button, Tabs, Input
 * - Outputs formatted signature text (e.g., "/s/ John Doe") for document insertion
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Pen, Type, Eraser, Check } from 'lucide-react';

interface SignaturePadProps {
  // Callback when signature is applied
  onApply: (signature: string) => void;
  // Callback when cancelled
  onCancel: () => void;
  // Optional initial value
  initialValue?: string;
  // Optional signer name for pre-filling type mode
  signerName?: string;
}

export function SignaturePad({ 
  onApply, 
  onCancel, 
  initialValue = '', 
  signerName = '' 
}: SignaturePadProps) {
  // Current tab mode: draw or type
  const [mode, setMode] = useState<'draw' | 'type'>('type');
  // Typed signature text
  const [typedSignature, setTypedSignature] = useState(signerName || initialValue);
  // Canvas drawing state
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);
  
  // Canvas ref for drawing
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);

  /**
   * Initialize canvas context when draw mode is active
   * Sets up line style for smooth signature appearance
   * Re-runs when mode changes to ensure canvas is properly sized
   */
  useEffect(() => {
    // Only initialize when in draw mode
    if (mode !== 'draw') return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    // Small delay to ensure the canvas is rendered and has dimensions
    const initCanvas = () => {
      const rect = canvas.getBoundingClientRect();

      // Skip if canvas has no dimensions yet
      if (rect.width === 0 || rect.height === 0) {
        requestAnimationFrame(initCanvas);
        return;
      }

      // Set canvas size to match display size
      canvas.width = rect.width * 2; // 2x for retina
      canvas.height = rect.height * 2;

      const context = canvas.getContext('2d');
      if (!context) return;

      // Scale for retina display
      context.scale(2, 2);

      // Configure line style for signature appearance
      context.lineCap = 'round';
      context.lineJoin = 'round';
      context.strokeStyle = '#1e3a5f'; // Dark blue signature color
      context.lineWidth = 2;

      contextRef.current = context;
    };

    // Use requestAnimationFrame to ensure DOM is ready
    requestAnimationFrame(initCanvas);
  }, [mode]);

  /**
   * Start drawing on mouse/touch down
   */
  const startDrawing = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current;
    const context = contextRef.current;
    if (!canvas || !context) return;

    setIsDrawing(true);
    setHasDrawn(true);

    const rect = canvas.getBoundingClientRect();
    let x: number, y: number;

    if ('touches' in e) {
      x = e.touches[0].clientX - rect.left;
      y = e.touches[0].clientY - rect.top;
    } else {
      x = e.clientX - rect.left;
      y = e.clientY - rect.top;
    }

    context.beginPath();
    context.moveTo(x, y);
  }, []);

  /**
   * Draw line as mouse/touch moves
   */
  const draw = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    const context = contextRef.current;
    if (!canvas || !context) return;

    const rect = canvas.getBoundingClientRect();
    let x: number, y: number;

    if ('touches' in e) {
      x = e.touches[0].clientX - rect.left;
      y = e.touches[0].clientY - rect.top;
    } else {
      x = e.clientX - rect.left;
      y = e.clientY - rect.top;
    }

    context.lineTo(x, y);
    context.stroke();
  }, [isDrawing]);

  /**
   * Stop drawing on mouse/touch up
   */
  const stopDrawing = useCallback(() => {
    setIsDrawing(false);
    contextRef.current?.closePath();
  }, []);

  /**
   * Clear the canvas
   */
  const clearCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const context = contextRef.current;
    if (!canvas || !context) return;

    // Use display dimensions (not canvas dimensions which are 2x scaled)
    const rect = canvas.getBoundingClientRect();
    context.clearRect(0, 0, rect.width, rect.height);
    setHasDrawn(false);
  }, []);

  /**
   * Apply the signature
   * For draw mode: converts canvas to data URL (simplified to text for document)
   * For type mode: formats as "/s/ Name"
   */
  const handleApply = useCallback(() => {
    if (mode === 'type') {
      // Format typed signature for legal document style
      const formattedSignature = typedSignature.trim() 
        ? `/s/ ${typedSignature.trim()}`
        : '';
      onApply(formattedSignature);
    } else {
      // For drawn signatures, we output a formatted text version
      // In a real implementation, you might save the image or use a more complex format
      if (hasDrawn) {
        onApply('/s/ [Signature on file]');
      }
    }
  }, [mode, typedSignature, hasDrawn, onApply]);

  /**
   * Check if apply button should be enabled
   */
  const canApply = mode === 'type' ? typedSignature.trim().length > 0 : hasDrawn;

  return (
    <div className="w-full space-y-4">
      {/* Mode selector tabs */}
      <Tabs value={mode} onValueChange={(v) => setMode(v as 'draw' | 'type')}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="type" className="gap-2">
            <Type className="h-4 w-4" />
            Type
          </TabsTrigger>
          <TabsTrigger value="draw" className="gap-2">
            <Pen className="h-4 w-4" />
            Draw
          </TabsTrigger>
        </TabsList>

        {/* Type mode content */}
        <TabsContent value="type" className="space-y-4">
          <div className="space-y-2">
            <Input
              placeholder="Enter your name"
              value={typedSignature}
              onChange={(e) => setTypedSignature(e.target.value)}
              className="text-lg"
              autoFocus
            />
            
            {/* Signature preview with cursive font */}
            {typedSignature && (
              <div className="p-4 border-2 border-dashed rounded-lg bg-slate-50">
                <p className="text-xs text-muted-foreground mb-2">Preview:</p>
                <p 
                  className="text-2xl text-slate-800"
                  style={{ 
                    fontFamily: "'Brush Script MT', 'Segoe Script', cursive",
                    fontStyle: 'italic'
                  }}
                >
                  /s/ {typedSignature}
                </p>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Draw mode content */}
        <TabsContent value="draw" className="space-y-4">
          <div className="relative">
            {/* Drawing canvas */}
            <canvas
              ref={canvasRef}
              className="w-full h-32 border-2 border-dashed rounded-lg bg-white cursor-crosshair touch-none"
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
              onTouchStart={startDrawing}
              onTouchMove={draw}
              onTouchEnd={stopDrawing}
            />
            
            {/* Signature line indicator */}
            <div className="absolute bottom-4 left-4 right-4 border-b border-slate-300" />
            
            {/* Clear button */}
            {hasDrawn && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearCanvas}
                className="absolute top-2 right-2 h-8 gap-1 text-xs"
              >
                <Eraser className="h-3 w-3" />
                Clear
              </Button>
            )}
            
            {/* Draw instruction */}
            {!hasDrawn && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <p className="text-sm text-muted-foreground">
                  Draw your signature above the line
                </p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Action buttons */}
      <div className="flex gap-2 pt-2">
        <Button 
          variant="outline" 
          onClick={onCancel}
          className="flex-1"
        >
          Cancel
        </Button>
        <Button 
          onClick={handleApply}
          disabled={!canApply}
          className="flex-1 bg-blue-600 hover:bg-blue-700"
        >
          <Check className="h-4 w-4 mr-2" />
          Apply Signature
        </Button>
      </div>
    </div>
  );
}

