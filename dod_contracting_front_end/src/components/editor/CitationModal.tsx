/**
 * Citation Modal Component
 *
 * Displays a searchable list of citations that can be inserted into the editor
 */

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Search, FileText } from "lucide-react";

interface Citation {
  id: number;
  source: string;
  page: number;
  text: string;
  bbox?: { x: number; y: number; w: number; h: number };
}

interface CitationModalProps {
  open: boolean;
  onClose: () => void;
  citations: Citation[];
  onInsertCitation: (citation: Citation) => void;
}

export function CitationModal({ open, onClose, citations, onInsertCitation }: CitationModalProps) {
  const [searchTerm, setSearchTerm] = useState("");

  // Filter citations based on search
  const filteredCitations = citations.filter((citation) => {
    const searchLower = searchTerm.toLowerCase();
    return (
      citation.source.toLowerCase().includes(searchLower) ||
      citation.text.toLowerCase().includes(searchLower) ||
      citation.id.toString().includes(searchLower)
    );
  });

  const handleInsert = (citation: Citation) => {
    onInsertCitation(citation);
    onClose();
    setSearchTerm(""); // Reset search
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Insert Citation
          </DialogTitle>
          <DialogDescription>
            Search and select a citation to insert into your document
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search citations by source, text, or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              autoFocus
            />
          </div>

          {/* Citations List */}
          <ScrollArea className="h-[400px] border rounded-lg">
            <div className="p-4 space-y-2">
              {filteredCitations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No citations found</p>
                  {searchTerm && (
                    <p className="text-sm mt-1">Try a different search term</p>
                  )}
                </div>
              ) : (
                filteredCitations.map((citation) => (
                  <Button
                    key={citation.id}
                    variant="outline"
                    className="w-full h-auto py-3 px-4 text-left justify-start hover:bg-blue-50 hover:border-blue-300 transition-colors"
                    onClick={() => handleInsert(citation)}
                  >
                    <div className="flex items-start gap-3 w-full">
                      {/* Citation ID Badge */}
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-sm">
                        [{citation.id}]
                      </div>

                      {/* Citation Details */}
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-sm mb-1 flex items-center justify-between gap-2">
                          <span className="truncate">{citation.source}</span>
                          <span className="text-xs text-muted-foreground flex-shrink-0">
                            Page {citation.page}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {citation.text}
                        </p>
                      </div>
                    </div>
                  </Button>
                ))
              )}
            </div>
          </ScrollArea>

          {/* Footer Info */}
          <div className="text-xs text-muted-foreground text-center">
            {filteredCitations.length} citation{filteredCitations.length !== 1 ? 's' : ''} available
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
