import { useState, useMemo } from 'react';
import { Plus, Search, Filter, CheckCircle2, Clock, FileText, AlertTriangle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import { DocumentItemRow } from './DocumentItemRow';
import { DocumentDetailDialog } from './DocumentDetailDialog';
import { AddDocumentDialog } from './AddDocumentDialog';
import { PhaseGenerationWizard } from './PhaseGenerationWizard';
import { documentGenerationApi } from '@/services/api';

interface DocumentChecklistProps {
  projectId: string;
  documents: any[];
  canEdit: boolean;
  onUpdate: () => void;
}

export function DocumentChecklist({ projectId, documents, canEdit, onUpdate }: DocumentChecklistProps) {
  // Calculate stats from props
  const getDocumentStats = () => {
    const total = documents.length;
    const pending = documents.filter((d) => d.status === 'pending').length;
    const uploaded = documents.filter((d) => d.status === 'uploaded').length;
    const underReview = documents.filter((d) => d.status === 'under_review').length;
    const approved = documents.filter((d) => d.status === 'approved').length;
    const rejected = documents.filter((d) => d.status === 'rejected').length;
    const expired = documents.filter((d) => d.status === 'expired').length;
    const required = documents.filter((d) => d.is_required).length;
    const requiredComplete = documents.filter((d) => d.is_required && d.status === 'approved').length;

    return {
      total,
      pending,
      uploaded,
      underReview,
      approved,
      rejected,
      expired,
      required,
      requiredComplete,
      completionPercentage: required > 0 ? Math.round((requiredComplete / required) * 100) : 0,
    };
  };

  const addDocument = async (docData: any) => {
    // Note: Document creation not yet implemented in backend
    console.log('Add document:', docData);
    alert('Document management features are being migrated to the new backend. This feature will be available soon.');
  };

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [phaseFilter, setPhaseFilter] = useState<string>('all');
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showGenerateWizard, setShowGenerateWizard] = useState(false);

  const stats = getDocumentStats();

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchesSearch =
        doc.document_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.description?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
      const matchesCategory = categoryFilter === 'all' || doc.category === categoryFilter;
      const matchesPhase = phaseFilter === 'all' || doc.phase === phaseFilter;
      return matchesSearch && matchesStatus && matchesCategory && matchesPhase;
    });
  }, [documents, searchQuery, statusFilter, categoryFilter, phaseFilter]);

  const categories = useMemo(() => {
    const cats = new Set(documents.map((d) => d.category));
    return Array.from(cats).sort();
  }, [documents]);

  const handleDocumentSelect = (doc: any) => {
    setSelectedDocument(doc);
    setShowDetailDialog(true);
  };

  const handleAddDocument = async (docData: any) => {
    await addDocument(docData);
  };

  // Quick generate handler for individual documents
  const handleQuickGenerate = async (doc: any) => {
    try {
      const assumptions = [
        { id: 'doc_type', text: `Document Type: ${doc.document_name}`, source: 'Document Checklist' },
      ];
      
      const response = await documentGenerationApi.generate(doc.id, assumptions);
      toast.info(`Started generating ${doc.document_name}...`);
      
      // Refresh after a delay to show status
      setTimeout(() => onUpdate(), 2000);
    } catch (error: any) {
      toast.error(`Failed to generate: ${error.message}`);
    }
  };

  // Count pending documents that can be generated
  const pendingCount = documents.filter(d => d.status === 'pending').length;

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-slate-900">Document Checklist</h3>
            <p className="text-sm text-slate-600 mt-1">
              Track required documents and deliverables for this project
            </p>
          </div>
          <div className="flex gap-2">
            {canEdit && pendingCount > 0 && (
              <Button
                onClick={() => setShowGenerateWizard(true)}
                variant="outline"
                className="gap-2 text-purple-600 border-purple-200 hover:bg-purple-50"
              >
                <Sparkles className="h-4 w-4" />
                Generate with AI
              </Button>
            )}
          {canEdit && (
            <Button onClick={() => setShowAddDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Document
            </Button>
          )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Total Documents</p>
                  <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Approved</p>
                  <p className="text-2xl font-bold text-slate-900">{stats.approved}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle2 className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Pending</p>
                  <p className="text-2xl font-bold text-slate-900">{stats.pending}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-amber-100 flex items-center justify-center">
                  <Clock className="h-6 w-6 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Under Review</p>
                  <p className="text-2xl font-bold text-slate-900">{stats.underReview}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                  <AlertTriangle className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Completion Progress</CardTitle>
                <CardDescription>
                  {stats.requiredComplete} of {stats.required} required documents approved
                </CardDescription>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-slate-900">{stats.completionPercentage}%</div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Progress value={stats.completionPercentage} className="h-3" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-48">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="uploaded">Uploaded</SelectItem>
                  <SelectItem value="under_review">Under Review</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="expired">Expired</SelectItem>
                </SelectContent>
              </Select>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-full md:w-48">
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={phaseFilter} onValueChange={setPhaseFilter}>
                <SelectTrigger className="w-full md:w-48">
                  <SelectValue placeholder="Filter by phase" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Phases</SelectItem>
                  <SelectItem value="pre_solicitation">Pre-Solicitation</SelectItem>
                  <SelectItem value="solicitation">Solicitation</SelectItem>
                  <SelectItem value="post_solicitation">Post-Solicitation</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {filteredDocuments.length === 0 ? (
              <div className="text-center py-12">
                <Filter className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">No documents found</h3>
                <p className="text-slate-600">
                  {searchQuery || statusFilter !== 'all' || categoryFilter !== 'all' || phaseFilter !== 'all'
                    ? 'Try adjusting your filters'
                    : 'Add your first document to get started'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredDocuments.map((doc) => (
                  <DocumentItemRow
                    key={doc.id}
                    document={doc}
                    onSelect={handleDocumentSelect}
                    canEdit={canEdit}
                    onQuickGenerate={handleQuickGenerate}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {selectedDocument && (
        <DocumentDetailDialog
          document={selectedDocument}
          open={showDetailDialog}
          onOpenChange={setShowDetailDialog}
          onUpdate={onUpdate}
          canEdit={canEdit}
        />
      )}

      <AddDocumentDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        onAdd={handleAddDocument}
      />

      <PhaseGenerationWizard
        open={showGenerateWizard}
        onOpenChange={setShowGenerateWizard}
        projectId={projectId}
        documents={documents}
        onComplete={onUpdate}
      />
    </>
  );
}
