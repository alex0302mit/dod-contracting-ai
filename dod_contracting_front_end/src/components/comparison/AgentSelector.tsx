/**
 * Agent Selector Component
 *
 * UI for selecting agents and models for comparison
 * Part of Phase 6: Advanced Agent Comparison & Selection
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Play, Sparkles, Zap, Brain, AlertCircle } from 'lucide-react';

interface AgentVariantConfig {
  id: string;
  name: string;
  model: string;
  temperature: number;
  agentClass?: string;
  description: string;
  estimatedCost: string;
  estimatedTime: string;
}

interface AgentSelectorProps {
  documentName: string;
  isOpen: boolean;
  onClose: () => void;
  onStartComparison: (selectedVariants: AgentVariantConfig[]) => void;
}

const AVAILABLE_MODELS = [
  {
    id: 'claude-opus-4',
    name: 'Claude Opus 4',
    description: 'Most capable model, best for complex tasks',
    cost: '$$$',
    speed: 'Slower',
    icon: Brain,
    color: 'text-purple-600',
  },
  {
    id: 'claude-sonnet-4',
    name: 'Claude Sonnet 4',
    description: 'Balanced performance and cost',
    cost: '$$',
    speed: 'Medium',
    icon: Sparkles,
    color: 'text-blue-600',
  },
  {
    id: 'claude-haiku-4',
    name: 'Claude Haiku 4',
    description: 'Fastest and most cost-effective',
    cost: '$',
    speed: 'Fast',
    icon: Zap,
    color: 'text-green-600',
  },
];

const TEMPERATURE_PRESETS = [
  { value: 0.3, label: 'Focused', description: 'More deterministic, consistent output' },
  { value: 0.7, label: 'Balanced', description: 'Default creativity level' },
  { value: 1.0, label: 'Creative', description: 'More varied, creative output' },
];

export function AgentSelector({
  documentName,
  isOpen,
  onClose,
  onStartComparison,
}: AgentSelectorProps) {
  const [selectedModels, setSelectedModels] = useState<string[]>(['claude-sonnet-4']);
  const [temperature, setTemperature] = useState(0.7);
  const [useSpecializedAgent, setUseSpecializedAgent] = useState(true);
  const [compareTemperatures, setCompareTemperatures] = useState(false);

  const toggleModel = (modelId: string) => {
    if (selectedModels.includes(modelId)) {
      setSelectedModels(selectedModels.filter(id => id !== modelId));
    } else {
      setSelectedModels([...selectedModels, modelId]);
    }
  };

  const buildVariants = (): AgentVariantConfig[] => {
    const variants: AgentVariantConfig[] = [];

    if (compareTemperatures) {
      // Compare different temperatures with same model
      const primaryModel = selectedModels[0] || 'claude-sonnet-4';
      TEMPERATURE_PRESETS.forEach((preset) => {
        variants.push({
          id: `${primaryModel}-temp-${preset.value}`,
          name: `${AVAILABLE_MODELS.find(m => m.id === primaryModel)?.name} (${preset.label})`,
          model: primaryModel,
          temperature: preset.value,
          agentClass: useSpecializedAgent ? 'specialized' : 'generic',
          description: `Temperature ${preset.value} - ${preset.description}`,
          estimatedCost: AVAILABLE_MODELS.find(m => m.id === primaryModel)?.cost || '$$',
          estimatedTime: AVAILABLE_MODELS.find(m => m.id === primaryModel)?.speed || 'Medium',
        });
      });
    } else {
      // Compare different models
      selectedModels.forEach((modelId) => {
        const modelInfo = AVAILABLE_MODELS.find(m => m.id === modelId);
        if (modelInfo) {
          variants.push({
            id: `${modelId}-variant`,
            name: modelInfo.name,
            model: modelId,
            temperature,
            agentClass: useSpecializedAgent ? 'specialized' : 'generic',
            description: modelInfo.description,
            estimatedCost: modelInfo.cost,
            estimatedTime: modelInfo.speed,
          });
        }
      });
    }

    return variants;
  };

  const variants = buildVariants();
  const estimatedTotalCost = variants.reduce((sum, v) => {
    const cost = v.estimatedCost.length; // $ symbols
    return sum + cost;
  }, 0);

  const handleStartComparison = () => {
    if (variants.length < 2) {
      alert('Please select at least 2 variants to compare');
      return;
    }

    onStartComparison(variants);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Configure Agent Comparison
          </DialogTitle>
          <DialogDescription>
            Select models and parameters to compare for: <strong>{documentName}</strong>
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[calc(90vh-200px)] pr-4">
          <div className="space-y-6">
            {/* Comparison Mode */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Comparison Mode</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="compare-temperatures"
                    checked={compareTemperatures}
                    onCheckedChange={(checked) => setCompareTemperatures(checked as boolean)}
                  />
                  <Label htmlFor="compare-temperatures" className="text-sm cursor-pointer">
                    Compare temperature variations (uses single model)
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="use-specialized"
                    checked={useSpecializedAgent}
                    onCheckedChange={(checked) => setUseSpecializedAgent(checked as boolean)}
                  />
                  <Label htmlFor="use-specialized" className="text-sm cursor-pointer">
                    Use specialized agent for {documentName}
                  </Label>
                </div>
              </CardContent>
            </Card>

            {/* Model Selection */}
            {!compareTemperatures && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Select Models to Compare</CardTitle>
                  <CardDescription className="text-xs">
                    Choose 2-3 models for best comparison results
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {AVAILABLE_MODELS.map((model) => (
                      <div
                        key={model.id}
                        className={`border rounded-lg p-4 cursor-pointer transition ${
                          selectedModels.includes(model.id)
                            ? 'border-blue-500 bg-blue-50/50'
                            : 'border-border hover:bg-muted/50'
                        }`}
                        onClick={() => toggleModel(model.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className="flex items-center h-5 mt-0.5">
                              <Checkbox
                                checked={selectedModels.includes(model.id)}
                                onCheckedChange={() => toggleModel(model.id)}
                              />
                            </div>
                            <div>
                              <div className="font-semibold flex items-center gap-2">
                                <model.icon className={`h-4 w-4 ${model.color}`} />
                                {model.name}
                              </div>
                              <div className="text-xs text-muted-foreground mt-1">
                                {model.description}
                              </div>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Badge variant="outline" className="text-xs">
                              {model.cost}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {model.speed}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Temperature Selection */}
            {!compareTemperatures && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Temperature Setting</CardTitle>
                  <CardDescription className="text-xs">
                    Controls creativity vs consistency
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Select value={temperature.toString()} onValueChange={(v) => setTemperature(parseFloat(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TEMPERATURE_PRESETS.map((preset) => (
                        <SelectItem key={preset.value} value={preset.value.toString()}>
                          <div>
                            <div className="font-medium">{preset.label} ({preset.value})</div>
                            <div className="text-xs text-muted-foreground">{preset.description}</div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>
            )}

            {/* Preview */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Comparison Preview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {variants.length === 0 && (
                    <div className="text-sm text-muted-foreground text-center py-4">
                      <AlertCircle className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                      Select at least 2 models to begin comparison
                    </div>
                  )}

                  {variants.map((variant, index) => (
                    <div key={variant.id} className="border rounded-lg p-3 text-sm">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">Variant {index + 1}: {variant.name}</div>
                          <div className="text-xs text-muted-foreground mt-1">{variant.description}</div>
                        </div>
                        <div className="flex gap-2">
                          <Badge variant="outline" className="text-xs">
                            {variant.estimatedCost}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {variant.estimatedTime}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}

                  {variants.length > 0 && (
                    <>
                      <Separator className="my-3" />
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Estimated Total Cost:</span>
                        <Badge variant="outline">{'$'.repeat(estimatedTotalCost)}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Variants to Compare:</span>
                        <Badge>{variants.length}</Badge>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleStartComparison} disabled={variants.length < 2}>
            <Play className="h-4 w-4 mr-2" />
            Start Comparison ({variants.length} variants)
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
