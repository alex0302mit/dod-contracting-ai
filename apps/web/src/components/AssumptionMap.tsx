import { useState } from "react";
import { ArrowLeft, FileSearch, Plus, Trash2, Edit2, Check, X, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

interface Assumption {
  id: string;
  text: string;
  source: string;
  status?: 'approved' | 'needs_review';
}

interface AssumptionMapProps {
  assumptions: Assumption[];
  setAssumptions: (assumptions: Assumption[]) => void;
  onTrace: () => void;
  onBack: () => void;
}

export function AssumptionMap({ assumptions, setAssumptions, onTrace, onBack }: AssumptionMapProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [editSource, setEditSource] = useState("");
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [newText, setNewText] = useState("");
  const [newSource, setNewSource] = useState("");

  // Start editing an assumption
  const startEdit = (assumption: Assumption) => {
    setEditingId(assumption.id);
    setEditText(assumption.text);
    setEditSource(assumption.source);
  };

  // Save edited assumption
  const saveEdit = () => {
    if (!editText.trim()) {
      toast.error("Assumption text cannot be empty");
      return;
    }

    setAssumptions(
      assumptions.map((a) =>
        a.id === editingId
          ? { ...a, text: editText.trim(), source: editSource.trim() }
          : a
      )
    );
    setEditingId(null);
    setEditText("");
    setEditSource("");
    toast.success("Assumption updated");
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingId(null);
    setEditText("");
    setEditSource("");
  };

  // Delete an assumption
  const deleteAssumption = (id: string) => {
    setAssumptions(assumptions.filter((a) => a.id !== id));
    toast.success("Assumption removed");
  };

  // Toggle approval status
  const toggleStatus = (id: string) => {
    setAssumptions(
      assumptions.map((a) => {
        if (a.id === id) {
          const newStatus = a.status === 'approved' ? 'needs_review' : 'approved';
          return { ...a, status: newStatus };
        }
        return a;
      })
    );
  };

  // Add new assumption
  const addNewAssumption = () => {
    if (!newText.trim()) {
      toast.error("Assumption text cannot be empty");
      return;
    }

    // Generate new ID
    const maxId = assumptions.reduce((max, a) => {
      const num = parseInt(a.id.replace('a', ''));
      return num > max ? num : max;
    }, 0);

    const newAssumption: Assumption = {
      id: `a${maxId + 1}`,
      text: newText.trim(),
      source: newSource.trim() || "User Added",
      status: 'needs_review'
    };

    setAssumptions([...assumptions, newAssumption]);
    setIsAddingNew(false);
    setNewText("");
    setNewSource("");
    toast.success("New assumption added");
  };

  // Cancel adding new
  const cancelAdd = () => {
    setIsAddingNew(false);
    setNewText("");
    setNewSource("");
  };

  const approvedCount = assumptions.filter(a => a.status === 'approved').length;
  const reviewCount = assumptions.filter(a => a.status === 'needs_review').length;

  return (
    <div className="container mx-auto p-8 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-3">
          Assumption Map
        </h1>
        <p className="text-lg text-muted-foreground">
          Review and curate extracted assumptions from your documents
        </p>
      </div>

      <div className="mb-8">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Curated Assumptions</CardTitle>
                <CardDescription>Review, edit, and approve assumptions that will guide document generation</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                {approvedCount > 0 && (
                  <Badge variant="default" className="bg-green-600">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    {approvedCount} approved
                  </Badge>
                )}
                {reviewCount > 0 && (
                  <Badge variant="secondary">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    {reviewCount} review
                  </Badge>
                )}
                <Badge variant="outline">{assumptions.length} total</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {assumptions.map((assumption) => (
                <Card
                  key={assumption.id}
                  className={`border-2 transition-all ${
                    assumption.status === 'approved'
                      ? 'border-green-200 bg-green-50/50'
                      : 'border-amber-200 bg-amber-50/50 hover:shadow-md'
                  }`}
                >
                  <CardContent className="pt-6">
                    {editingId === assumption.id ? (
                      // Edit Mode
                      <div className="space-y-3">
                        <div className="flex items-start gap-4">
                          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                            {assumption.id.replace("a", "")}
                          </div>
                          <div className="flex-1 space-y-3">
                            <Textarea
                              value={editText}
                              onChange={(e) => setEditText(e.target.value)}
                              placeholder="Assumption text..."
                              className="min-h-[80px]"
                            />
                            <Input
                              value={editSource}
                              onChange={(e) => setEditSource(e.target.value)}
                              placeholder="Source reference..."
                            />
                          </div>
                        </div>
                        <div className="flex items-center gap-2 justify-end">
                          <Button size="sm" variant="outline" onClick={cancelEdit}>
                            <X className="h-4 w-4 mr-1" />
                            Cancel
                          </Button>
                          <Button size="sm" onClick={saveEdit}>
                            <Check className="h-4 w-4 mr-1" />
                            Save
                          </Button>
                        </div>
                      </div>
                    ) : (
                      // View Mode
                      <div className="flex items-start gap-4">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                          {assumption.id.replace("a", "")}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium mb-2">{assumption.text}</p>
                          <div className="flex items-center gap-2">
                            <FileSearch className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">{assumption.source}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant={assumption.status === 'approved' ? 'default' : 'outline'}
                            onClick={() => toggleStatus(assumption.id)}
                            className={assumption.status === 'approved' ? 'bg-green-600 hover:bg-green-700' : ''}
                          >
                            {assumption.status === 'approved' ? (
                              <>
                                <CheckCircle2 className="h-4 w-4 mr-1" />
                                Approved
                              </>
                            ) : (
                              <>
                                <AlertCircle className="h-4 w-4 mr-1" />
                                Review
                              </>
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => startEdit(assumption)}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => deleteAssumption(assumption.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}

              {/* Add New Assumption Card */}
              {isAddingNew ? (
                <Card className="border-2 border-dashed border-blue-300 bg-blue-50/50">
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="flex items-start gap-4">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                          <Plus className="h-4 w-4" />
                        </div>
                        <div className="flex-1 space-y-3">
                          <Textarea
                            value={newText}
                            onChange={(e) => setNewText(e.target.value)}
                            placeholder="Enter assumption text..."
                            className="min-h-[80px]"
                            autoFocus
                          />
                          <Input
                            value={newSource}
                            onChange={(e) => setNewSource(e.target.value)}
                            placeholder="Source reference (optional)..."
                          />
                        </div>
                      </div>
                      <div className="flex items-center gap-2 justify-end">
                        <Button size="sm" variant="outline" onClick={cancelAdd}>
                          <X className="h-4 w-4 mr-1" />
                          Cancel
                        </Button>
                        <Button size="sm" onClick={addNewAssumption}>
                          <Check className="h-4 w-4 mr-1" />
                          Add Assumption
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Button
                  variant="outline"
                  className="w-full border-2 border-dashed border-blue-300 bg-blue-50/50 hover:bg-blue-100/50 text-blue-700"
                  onClick={() => setIsAddingNew(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add New Assumption
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Button onClick={onTrace} className="ml-auto">
          Continue to Traceability
        </Button>
      </div>
    </div>
  );
}
