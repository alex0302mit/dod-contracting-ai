/**
 * Smart Tag Manager Component
 *
 * Sidebar panel for managing smart tags and tooltips in documents
 * Features: tag list, filtering, statistics, AI auto-detection
 */

import { useState, useMemo } from 'react';
import { Editor } from '@tiptap/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Tag,
  Sparkles,
  Search,
  Filter,
  Edit2,
  Trash2,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Info,
  FileText,
  ListChecks,
  Target,
} from 'lucide-react';
import { SmartTagPopover } from './SmartTagPopover';
import { autoDetectSmartTags } from '@/lib/smartTagAutomation';
import { autoGenerateTooltips } from '@/lib/tooltipAutomation';

interface SmartTagManagerProps {
  editor: Editor | null;
  content: string;
}

interface TagItem {
  tagId: string;
  tagType: 'requirement' | 'assumption' | 'risk' | 'decision' | 'action-item' | 'note';
  tagLabel: string;
  tagDescription?: string;
  position: number;
  text: string;
}

interface TooltipItem {
  tooltipId: string;
  tooltipText: string;
  tooltipType: 'definition' | 'acronym' | 'reference' | 'help';
  position: number;
  text: string;
}

const TAG_TYPE_CONFIG = {
  requirement: { label: 'Requirements', color: 'blue', icon: FileText },
  assumption: { label: 'Assumptions', color: 'purple', icon: Info },
  risk: { label: 'Risks', color: 'red', icon: AlertTriangle },
  decision: { label: 'Decisions', color: 'green', icon: CheckCircle2 },
  'action-item': { label: 'Action Items', color: 'orange', icon: ListChecks },
  note: { label: 'Notes', color: 'gray', icon: Tag },
} as const;

export function SmartTagManager({ editor, content }: SmartTagManagerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string | null>(null);
  const [isAutoDetecting, setIsAutoDetecting] = useState(false);
  const [isAutoTooltipping, setIsAutoTooltipping] = useState(false);

  // Extract all smart tags from the editor
  const smartTags = useMemo(() => {
    if (!editor) return [];

    const tags: TagItem[] = [];
    const { doc } = editor.state;

    doc.descendants((node, pos) => {
      if (!node.marks) return;

      node.marks.forEach((mark) => {
        if (mark.type.name === 'smartTag') {
          tags.push({
            tagId: mark.attrs.tagId,
            tagType: mark.attrs.tagType,
            tagLabel: mark.attrs.tagLabel,
            tagDescription: mark.attrs.tagDescription,
            position: pos,
            text: node.text || '',
          });
        }
      });
    });

    return tags;
  }, [editor, content]);

  // Extract all tooltips from the editor
  const tooltips = useMemo(() => {
    if (!editor) return [];

    const tips: TooltipItem[] = [];
    const { doc } = editor.state;

    doc.descendants((node, pos) => {
      if (!node.marks) return;

      node.marks.forEach((mark) => {
        if (mark.type.name === 'tooltip') {
          tips.push({
            tooltipId: mark.attrs.tooltipId,
            tooltipText: mark.attrs.tooltipText,
            tooltipType: mark.attrs.tooltipType,
            position: pos,
            text: node.text || '',
          });
        }
      });
    });

    return tips;
  }, [editor, content]);

  // Filter tags based on search and type
  const filteredTags = useMemo(() => {
    let filtered = smartTags;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (tag) =>
          tag.tagLabel.toLowerCase().includes(query) ||
          tag.tagDescription?.toLowerCase().includes(query) ||
          tag.text.toLowerCase().includes(query)
      );
    }

    if (filterType) {
      filtered = filtered.filter((tag) => tag.tagType === filterType);
    }

    return filtered;
  }, [smartTags, searchQuery, filterType]);

  // Tag statistics
  const tagStats = useMemo(() => {
    const stats = {
      total: smartTags.length,
      byType: {} as Record<string, number>,
    };

    smartTags.forEach((tag) => {
      stats.byType[tag.tagType] = (stats.byType[tag.tagType] || 0) + 1;
    });

    return stats;
  }, [smartTags]);

  const handleAutoDetectTags = async () => {
    if (!editor) return;

    setIsAutoDetecting(true);
    try {
      const suggestions = await autoDetectSmartTags(content);

      // Insert detected tags into the editor
      suggestions.forEach((suggestion) => {
        // Find the text in the document
        const { doc } = editor.state;
        let foundPosition: { from: number; to: number } | null = null;

        doc.descendants((node, pos) => {
          if (foundPosition) return;

          if (node.isText && node.text) {
            const index = node.text.indexOf(suggestion.text);
            if (index !== -1) {
              foundPosition = {
                from: pos + index,
                to: pos + index + suggestion.text.length,
              };
            }
          }
        });

        if (foundPosition) {
          editor
            .chain()
            .setTextSelection(foundPosition)
            .insertSmartTag({
              tagId: `tag-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              tagType: suggestion.tagType,
              tagLabel: suggestion.tagLabel,
              tagDescription: suggestion.tagDescription,
            })
            .run();
        }
      });
    } catch (error) {
      console.error('Auto-detect tags failed:', error);
    } finally {
      setIsAutoDetecting(false);
    }
  };

  const handleAutoGenerateTooltips = async () => {
    if (!editor) return;

    setIsAutoTooltipping(true);
    try {
      const suggestions = await autoGenerateTooltips(content);

      // Insert generated tooltips into the editor
      suggestions.forEach((suggestion) => {
        // Find the text in the document
        const { doc } = editor.state;
        let foundPosition: { from: number; to: number } | null = null;

        doc.descendants((node, pos) => {
          if (foundPosition) return;

          if (node.isText && node.text) {
            const index = node.text.indexOf(suggestion.text);
            if (index !== -1) {
              foundPosition = {
                from: pos + index,
                to: pos + index + suggestion.text.length,
              };
            }
          }
        });

        if (foundPosition) {
          editor
            .chain()
            .setTextSelection(foundPosition)
            .addTooltip({
              tooltipId: `tooltip-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              tooltipText: suggestion.tooltipText,
              tooltipType: suggestion.tooltipType,
            })
            .run();
        }
      });
    } catch (error) {
      console.error('Auto-generate tooltips failed:', error);
    } finally {
      setIsAutoTooltipping(false);
    }
  };

  const handleRemoveTag = (tagId: string) => {
    if (!editor) return;
    editor.chain().focus().removeSmartTag(tagId).run();
  };

  const handleRemoveTooltip = (tooltipId: string) => {
    if (!editor) return;
    editor.chain().focus().removeTooltip(tooltipId).run();
  };

  const handleJumpToTag = (position: number) => {
    if (!editor) return;
    editor.chain().focus().setTextSelection(position).run();
  };

  return (
    <div className="space-y-4">
      {/* AI Automation Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-600" />
            AI Automation
          </CardTitle>
          <CardDescription className="text-xs">
            Automatically detect tags and generate tooltips
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button
            size="sm"
            className="w-full gap-2"
            onClick={handleAutoDetectTags}
            disabled={isAutoDetecting || !editor}
          >
            <Zap className="h-4 w-4" />
            {isAutoDetecting ? 'Detecting...' : 'Auto-Detect Tags'}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="w-full gap-2"
            onClick={handleAutoGenerateTooltips}
            disabled={isAutoTooltipping || !editor}
          >
            <Target className="h-4 w-4" />
            {isAutoTooltipping ? 'Generating...' : 'Auto-Generate Tooltips'}
          </Button>
        </CardContent>
      </Card>

      {/* Smart Tags Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Smart Tags
              </CardTitle>
              <CardDescription className="text-xs mt-1">
                {tagStats.total} tags in document
              </CardDescription>
            </div>
            <SmartTagPopover editor={editor}>
              <Button size="sm" variant="outline" className="h-7 text-xs">
                + Add Tag
              </Button>
            </SmartTagPopover>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Search and Filter */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9 text-sm"
              />
            </div>

            {/* Type Filters */}
            <div className="flex flex-wrap gap-1">
              <Button
                size="sm"
                variant={filterType === null ? 'default' : 'outline'}
                onClick={() => setFilterType(null)}
                className="h-6 px-2 text-xs"
              >
                All ({tagStats.total})
              </Button>
              {Object.entries(TAG_TYPE_CONFIG).map(([type, config]) => {
                const count = tagStats.byType[type] || 0;
                if (count === 0) return null;

                return (
                  <Button
                    key={type}
                    size="sm"
                    variant={filterType === type ? 'default' : 'outline'}
                    onClick={() => setFilterType(type)}
                    className="h-6 px-2 text-xs"
                  >
                    {config.label} ({count})
                  </Button>
                );
              })}
            </div>
          </div>

          <Separator />

          {/* Tag List */}
          <ScrollArea className="h-64">
            <div className="space-y-2">
              {filteredTags.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-xs">
                  {searchQuery || filterType
                    ? 'No tags match your filters'
                    : 'No tags yet. Add tags or use AI auto-detection.'}
                </div>
              ) : (
                filteredTags.map((tag) => {
                  const config = TAG_TYPE_CONFIG[tag.tagType];
                  const Icon = config.icon;

                  return (
                    <div
                      key={tag.tagId}
                      className="border rounded-lg p-2 bg-muted/30 hover:bg-muted/50 transition-colors group"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Icon className={`h-3 w-3 text-${config.color}-600 flex-shrink-0`} />
                            <Badge
                              variant="outline"
                              className={`text-[10px] bg-${config.color}-50 text-${config.color}-800 border-${config.color}-200`}
                            >
                              {tag.tagLabel}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2 mb-1">
                            "{tag.text}"
                          </p>
                          {tag.tagDescription && (
                            <p className="text-[10px] text-muted-foreground italic">
                              {tag.tagDescription}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 w-6 p-0"
                            onClick={() => handleJumpToTag(tag.position)}
                            title="Jump to tag"
                          >
                            <Search className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 w-6 p-0 text-destructive"
                            onClick={() => handleRemoveTag(tag.tagId)}
                            title="Remove tag"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Tooltips Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Info className="h-4 w-4" />
            Tooltips
          </CardTitle>
          <CardDescription className="text-xs">
            {tooltips.length} contextual helps
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-48">
            <div className="space-y-2">
              {tooltips.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground text-xs">
                  No tooltips yet. Add tooltips or use AI auto-generation.
                </div>
              ) : (
                tooltips.map((tooltip) => (
                  <div
                    key={tooltip.tooltipId}
                    className="border rounded-lg p-2 bg-muted/30 hover:bg-muted/50 transition-colors group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium mb-1">"{tooltip.text}"</p>
                        <p className="text-[10px] text-muted-foreground">
                          {tooltip.tooltipText}
                        </p>
                        <Badge
                          variant="outline"
                          className="text-[9px] mt-1 h-4 px-1"
                        >
                          {tooltip.tooltipType}
                        </Badge>
                      </div>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0"
                          onClick={() => handleJumpToTag(tooltip.position)}
                          title="Jump to tooltip"
                        >
                          <Search className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0 text-destructive"
                          onClick={() => handleRemoveTooltip(tooltip.tooltipId)}
                          title="Remove tooltip"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
