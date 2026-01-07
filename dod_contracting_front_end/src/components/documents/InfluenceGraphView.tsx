/**
 * InfluenceGraphView Component
 * 
 * A simple SVG-based visualization showing the influence graph of documents.
 * Displays source documents on the left flowing into the generated document on the right.
 * 
 * Design decisions:
 * - Uses custom SVG instead of external library (no additional dependencies)
 * - Simple left-to-right flow layout (sources → generated)
 * - Color-coded nodes by type (source vs generated)
 * - Edge thickness based on relevance score
 * - Hover tooltips for additional details
 * 
 * Dependencies:
 * - lineageApi.getInfluenceGraph for fetching graph data
 * - Shadcn UI components for styling
 * - React Query for data fetching
 */

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Loader2,
  AlertCircle,
  GitBranch,
  FileText,
  Sparkles,
  Database,
  ZoomIn,
  ZoomOut,
  Maximize2,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { lineageApi, type GraphNode, type GraphEdge } from '@/services/api';

// Props interface for InfluenceGraphView
interface InfluenceGraphViewProps {
  documentId: string;
  documentName?: string;
  compact?: boolean;
}

// SVG dimensions and layout constants
const SVG_WIDTH = 600;
const SVG_HEIGHT = 400;
const NODE_WIDTH = 140;
const NODE_HEIGHT = 60;
const PADDING = 40;

// Node colors by type
const NODE_COLORS = {
  source: {
    fill: '#dbeafe', // blue-100
    stroke: '#3b82f6', // blue-500
    text: '#1e40af', // blue-800
  },
  generated: {
    fill: '#f3e8ff', // violet-100
    stroke: '#8b5cf6', // violet-500
    text: '#5b21b6', // violet-800
  },
};

/**
 * Calculate node positions for left-to-right flow layout
 */
function calculateLayout(nodes: GraphNode[], edges: GraphEdge[], centerId: string) {
  // Separate nodes into sources (left) and generated (right)
  const sourceNodes = nodes.filter(n => n.type === 'source');
  const generatedNodes = nodes.filter(n => n.type === 'generated');
  
  // Find the central node (the one we're viewing)
  const centerNode = nodes.find(n => n.id === centerId);
  const isCenterGenerated = centerNode?.type === 'generated';
  
  const positions: Record<string, { x: number; y: number }> = {};
  
  if (isCenterGenerated) {
    // Center is generated: sources on left, center on right
    const leftX = PADDING;
    const rightX = SVG_WIDTH - PADDING - NODE_WIDTH;
    
    // Position source nodes vertically on the left
    const sourceSpacing = (SVG_HEIGHT - 2 * PADDING) / Math.max(sourceNodes.length, 1);
    sourceNodes.forEach((node, index) => {
      positions[node.id] = {
        x: leftX,
        y: PADDING + index * sourceSpacing + sourceSpacing / 2 - NODE_HEIGHT / 2,
      };
    });
    
    // Position generated node (center) on the right
    if (centerNode) {
      positions[centerNode.id] = {
        x: rightX,
        y: SVG_HEIGHT / 2 - NODE_HEIGHT / 2,
      };
    }
    
    // Position other generated nodes below center
    generatedNodes.filter(n => n.id !== centerId).forEach((node, index) => {
      positions[node.id] = {
        x: rightX,
        y: SVG_HEIGHT / 2 + NODE_HEIGHT + 20 + index * (NODE_HEIGHT + 20),
      };
    });
  } else {
    // Center is source: center on left, generated on right
    const leftX = PADDING;
    const rightX = SVG_WIDTH - PADDING - NODE_WIDTH;
    
    // Position center source on the left
    if (centerNode) {
      positions[centerNode.id] = {
        x: leftX,
        y: SVG_HEIGHT / 2 - NODE_HEIGHT / 2,
      };
    }
    
    // Position other source nodes above/below
    sourceNodes.filter(n => n.id !== centerId).forEach((node, index) => {
      positions[node.id] = {
        x: leftX,
        y: PADDING + index * (NODE_HEIGHT + 20),
      };
    });
    
    // Position generated nodes on the right
    const genSpacing = (SVG_HEIGHT - 2 * PADDING) / Math.max(generatedNodes.length, 1);
    generatedNodes.forEach((node, index) => {
      positions[node.id] = {
        x: rightX,
        y: PADDING + index * genSpacing + genSpacing / 2 - NODE_HEIGHT / 2,
      };
    });
  }
  
  return positions;
}

/**
 * GraphNodeElement - Renders a single node in the graph
 */
function GraphNodeElement({
  node,
  x,
  y,
  isCenter,
  onHover,
}: {
  node: GraphNode;
  x: number;
  y: number;
  isCenter: boolean;
  onHover: (node: GraphNode | null) => void;
}) {
  const colors = NODE_COLORS[node.type];
  const Icon = node.type === 'source' ? FileText : Sparkles;
  
  // Truncate label if too long
  const displayLabel = node.label.length > 18 
    ? node.label.slice(0, 16) + '...' 
    : node.label;

  return (
    <g
      transform={`translate(${x}, ${y})`}
      onMouseEnter={() => onHover(node)}
      onMouseLeave={() => onHover(null)}
      style={{ cursor: 'pointer' }}
    >
      {/* Node background */}
      <rect
        width={NODE_WIDTH}
        height={NODE_HEIGHT}
        rx={8}
        ry={8}
        fill={colors.fill}
        stroke={colors.stroke}
        strokeWidth={isCenter ? 3 : 1.5}
        className="transition-all duration-200 hover:opacity-90"
      />
      
      {/* Center indicator ring */}
      {isCenter && (
        <rect
          x={-3}
          y={-3}
          width={NODE_WIDTH + 6}
          height={NODE_HEIGHT + 6}
          rx={10}
          ry={10}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={1}
          strokeDasharray="4 2"
          opacity={0.5}
        />
      )}
      
      {/* Node content */}
      <foreignObject x={8} y={8} width={NODE_WIDTH - 16} height={NODE_HEIGHT - 16}>
        <div className="flex flex-col h-full justify-center">
          <div className="flex items-center gap-1.5">
            <Icon 
              className="h-3.5 w-3.5 shrink-0" 
              style={{ color: colors.text }} 
            />
            <span 
              className="text-xs font-medium truncate"
              style={{ color: colors.text }}
              title={node.label}
            >
              {displayLabel}
            </span>
          </div>
          <span 
            className="text-[10px] mt-1 opacity-70"
            style={{ color: colors.text }}
          >
            {node.type === 'source' ? 'Source' : 'Generated'}
          </span>
        </div>
      </foreignObject>
    </g>
  );
}

/**
 * GraphEdgeElement - Renders an edge (relationship) between nodes
 */
function GraphEdgeElement({
  edge,
  sourcePos,
  targetPos,
}: {
  edge: GraphEdge;
  sourcePos: { x: number; y: number };
  targetPos: { x: number; y: number };
}) {
  // Calculate edge path (curved bezier)
  const startX = sourcePos.x + NODE_WIDTH;
  const startY = sourcePos.y + NODE_HEIGHT / 2;
  const endX = targetPos.x;
  const endY = targetPos.y + NODE_HEIGHT / 2;
  
  // Control points for smooth curve
  const controlX = (startX + endX) / 2;
  
  const path = `M ${startX} ${startY} C ${controlX} ${startY}, ${controlX} ${endY}, ${endX} ${endY}`;
  
  // Edge thickness based on relevance (1-4px)
  const strokeWidth = Math.max(1, Math.min(4, edge.weight * 4));
  
  // Edge opacity based on chunks count
  const opacity = Math.max(0.3, Math.min(0.8, 0.3 + edge.chunks_count * 0.1));

  return (
    <g>
      <path
        d={path}
        fill="none"
        stroke="#94a3b8" // slate-400
        strokeWidth={strokeWidth}
        opacity={opacity}
        className="transition-all duration-200"
      />
      {/* Arrow head */}
      <polygon
        points={`${endX},${endY} ${endX - 8},${endY - 4} ${endX - 8},${endY + 4}`}
        fill="#94a3b8"
        opacity={opacity}
      />
    </g>
  );
}

export function InfluenceGraphView({
  documentId,
  documentName,
  compact = false,
}: InfluenceGraphViewProps) {
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState(1);

  // Fetch graph data
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['influence-graph', documentId],
    queryFn: () => lineageApi.getInfluenceGraph(documentId),
    enabled: !!documentId,
    staleTime: 2 * 60 * 1000, // Cache for 2 minutes
  });

  // Calculate node positions
  const positions = useMemo(() => {
    if (!data?.nodes) return {};
    return calculateLayout(data.nodes, data.edges, documentId);
  }, [data, documentId]);

  // Zoom handlers
  const handleZoomIn = () => setZoom(z => Math.min(z + 0.2, 2));
  const handleZoomOut = () => setZoom(z => Math.max(z - 0.2, 0.5));
  const handleZoomReset = () => setZoom(1);

  // Loading state
  if (isLoading) {
    return (
      <Card className={compact ? 'border-0 shadow-none' : ''}>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (isError) {
    return (
      <Card className={compact ? 'border-0 shadow-none' : ''}>
        <CardContent className="flex flex-col items-center justify-center py-12 text-red-600">
          <AlertCircle className="h-6 w-6 mb-2" />
          <p className="text-sm">Failed to load influence graph</p>
          <p className="text-xs text-muted-foreground mt-1">
            {(error as Error)?.message || 'Unknown error'}
          </p>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!data?.nodes || data.nodes.length === 0) {
    return (
      <Card className={compact ? 'border-0 shadow-none' : ''}>
        {!compact && (
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              Influence Graph
            </CardTitle>
          </CardHeader>
        )}
        <CardContent className={compact ? 'py-4' : ''}>
          <div className="text-center py-8 text-muted-foreground">
            <GitBranch className="h-10 w-10 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No influence relationships found</p>
            <p className="text-xs mt-1">Connections will appear after AI generation</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const nodes = data.nodes;
  const edges = data.edges;
  const sourceCount = nodes.filter(n => n.type === 'source').length;
  const generatedCount = nodes.filter(n => n.type === 'generated').length;

  return (
    <Card className={compact ? 'border-0 shadow-none' : ''}>
      {!compact && (
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-blue-600" />
            Influence Graph
          </CardTitle>
          <CardDescription className="text-xs">
            {sourceCount} source{sourceCount !== 1 ? 's' : ''} → {generatedCount} generated document{generatedCount !== 1 ? 's' : ''}
          </CardDescription>
        </CardHeader>
      )}

      <CardContent className={compact ? 'py-2' : ''}>
        {/* Graph legend and controls */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-blue-100 border border-blue-500" />
              <span className="text-xs text-muted-foreground">Source</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-violet-100 border border-violet-500" />
              <span className="text-xs text-muted-foreground">Generated</span>
            </div>
          </div>
          
          {/* Zoom controls */}
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleZoomOut}
              title="Zoom out"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleZoomReset}
              title="Reset zoom"
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleZoomIn}
              title="Zoom in"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* SVG Graph */}
        <div 
          className="border rounded-lg bg-slate-50/50 overflow-hidden"
          style={{ height: compact ? 250 : 350 }}
        >
          <svg
            width="100%"
            height="100%"
            viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
            preserveAspectRatio="xMidYMid meet"
            style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
          >
            {/* Render edges first (behind nodes) */}
            <g>
              {edges.map((edge, index) => {
                const sourcePos = positions[edge.source];
                const targetPos = positions[edge.target];
                if (!sourcePos || !targetPos) return null;
                
                return (
                  <GraphEdgeElement
                    key={`edge-${index}`}
                    edge={edge}
                    sourcePos={sourcePos}
                    targetPos={targetPos}
                  />
                );
              })}
            </g>

            {/* Render nodes */}
            <g>
              {nodes.map((node) => {
                const pos = positions[node.id];
                if (!pos) return null;
                
                return (
                  <GraphNodeElement
                    key={node.id}
                    node={node}
                    x={pos.x}
                    y={pos.y}
                    isCenter={node.id === documentId}
                    onHover={setHoveredNode}
                  />
                );
              })}
            </g>
          </svg>
        </div>

        {/* Hovered node tooltip */}
        {hoveredNode && (
          <div className="mt-3 p-3 rounded-lg bg-slate-100 border text-sm">
            <div className="flex items-center gap-2 mb-1">
              {hoveredNode.type === 'source' ? (
                <FileText className="h-4 w-4 text-blue-600" />
              ) : (
                <Sparkles className="h-4 w-4 text-violet-600" />
              )}
              <span className="font-medium">{hoveredNode.label}</span>
              <Badge variant="outline" className="text-[10px]">
                {hoveredNode.type}
              </Badge>
            </div>
            {hoveredNode.metadata && Object.keys(hoveredNode.metadata).length > 0 && (
              <div className="text-xs text-muted-foreground mt-1 space-x-2">
                {hoveredNode.metadata.category && (
                  <span>Category: {String(hoveredNode.metadata.category)}</span>
                )}
                {hoveredNode.metadata.phase && (
                  <span>Phase: {String(hoveredNode.metadata.phase)}</span>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
