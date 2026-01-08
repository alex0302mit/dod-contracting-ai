/**
 * SourcesScreen Component
 * 
 * Combines upload functionality with knowledge document management.
 * Shows upload cards by category and uploaded files with indexing status.
 * 
 * Dependencies:
 * - knowledgeApi for document data
 * - UploadCenter / KnowledgeTab for UI
 * - useNavigation for project state
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  FileText, 
  BookOpen, 
  Folder, 
  BarChart3,
  Loader2,
  FolderOpen,
  Database
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { knowledgeApi, type KnowledgeStats } from '@/services/api';
import { useNavigation } from '@/contexts/NavigationContext';
import { KnowledgeTab } from '@/components/procurement/KnowledgeTab';
import { cn } from '@/lib/utils';

// Category configuration for upload cards
const CATEGORIES = [
  { id: 'regulation', label: 'Regulations', description: 'FAR/DFARS and policy documents', icon: BookOpen, color: 'text-info' },
  { id: 'template', label: 'Templates', description: 'Standard document templates', icon: FileText, color: 'text-ai' },
  { id: 'market_research', label: 'Market Research', description: 'Market analysis and research', icon: BarChart3, color: 'text-warning' },
  { id: 'prior_award', label: 'Past Contracts', description: 'Prior award documents', icon: Folder, color: 'text-success' },
];

/**
 * UploadCard - Category upload card
 */
interface UploadCardProps {
  category: typeof CATEGORIES[0];
  count: number;
  onClick: () => void;
}

function UploadCard({ category, count, onClick }: UploadCardProps) {
  const Icon = category.icon;
  
  return (
    <Card 
      className="cursor-pointer hover:shadow-md transition-all hover:border-primary/30"
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className={cn("h-12 w-12 rounded-lg flex items-center justify-center bg-muted", category.color)}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium">{category.label}</h3>
            <p className="text-sm text-muted-foreground">{category.description}</p>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold">{count}</span>
            <p className="text-xs text-muted-foreground">documents</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * ContextSetSummary - Shows overall knowledge stats
 */
interface ContextSetSummaryProps {
  stats: KnowledgeStats | undefined;
  isLoading: boolean;
}

function ContextSetSummary({ stats, isLoading }: ContextSetSummaryProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }
  
  if (!stats) return null;
  
  const indexedPercent = stats.total > 0 
    ? Math.round((stats.indexed_count / stats.total) * 100) 
    : 0;
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Database className="h-5 w-5" />
          Context Set Summary
        </CardTitle>
        <CardDescription>
          Documents indexed for AI generation
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Indexing progress */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Indexed</span>
              <span className="text-sm text-muted-foreground">
                {stats.indexed_count} / {stats.total} documents
              </span>
            </div>
            <Progress value={indexedPercent} className="h-2" />
          </div>
          
          {/* Phase breakdown */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-2">By Phase</p>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Pre-Solicitation</span>
                  <Badge variant="outline">{stats.by_phase.pre_solicitation}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Solicitation</span>
                  <Badge variant="outline">{stats.by_phase.solicitation}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Post-Solicitation</span>
                  <Badge variant="outline">{stats.by_phase.post_solicitation}</Badge>
                </div>
              </div>
            </div>
            
            <div>
              <p className="text-xs text-muted-foreground mb-2">By Purpose</p>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Regulations</span>
                  <Badge variant="outline">{stats.by_purpose.regulation}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Templates</span>
                  <Badge variant="outline">{stats.by_purpose.template}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Research</span>
                  <Badge variant="outline">{stats.by_purpose.market_research}</Badge>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * SourcesScreen - Knowledge and upload management
 */
export function SourcesScreen() {
  const { selectedProjectId, navigate } = useNavigation();
  const [activeTab, setActiveTab] = useState('overview');
  
  // Fetch knowledge stats
  const { data: stats, isLoading: statsLoading } = useQuery<KnowledgeStats>({
    queryKey: ['knowledge-stats', selectedProjectId],
    queryFn: () => knowledgeApi.getStats(selectedProjectId!),
    enabled: !!selectedProjectId,
  });
  
  // Get category counts from stats
  const getCategoryCount = (categoryId: string): number => {
    if (!stats) return 0;
    return stats.by_purpose[categoryId as keyof typeof stats.by_purpose] || 0;
  };
  
  // Handle category click - navigates to documents tab
  const handleCategoryClick = (_categoryId: string) => {
    setActiveTab('documents');
  };
  
  // No project selected
  if (!selectedProjectId) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <FolderOpen className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
          <h2 className="text-lg font-medium mb-2">No Project Selected</h2>
          <p className="text-muted-foreground mb-4">
            Select a project to manage knowledge sources
          </p>
          <Button onClick={() => navigate('TRACKER')}>
            Go to Tracker
          </Button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full overflow-auto">
      <div className="container mx-auto px-6 py-6 max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Knowledge Sources</h1>
          <p className="text-muted-foreground mt-1">
            Manage documents for AI-powered generation
          </p>
        </div>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-6">
            {/* Upload category cards */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Upload by Category</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {CATEGORIES.map((category) => (
                  <UploadCard
                    key={category.id}
                    category={category}
                    count={getCategoryCount(category.id)}
                    onClick={() => handleCategoryClick(category.id)}
                  />
                ))}
              </div>
            </div>
            
            {/* Context set summary */}
            <ContextSetSummary stats={stats} isLoading={statsLoading} />
          </TabsContent>
          
          <TabsContent value="documents">
            <KnowledgeTab projectId={selectedProjectId} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default SourcesScreen;
