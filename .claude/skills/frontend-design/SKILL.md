---
name: frontend-design
description: Design and implement React components following Tailwind CSS and shadcn/ui patterns for the DoD contracting application. Use when building UI components, improving layouts, implementing responsive design, creating forms, designing dialogs/modals, improving accessibility, or refactoring component structure. Applies to React TypeScript components.
---

# Frontend Design Skill

## Overview

This skill helps design and implement React components following established patterns in the DoD Contracting AI application.

## Tech Stack

- **React 18.3.1** with TypeScript
- **Tailwind CSS** for styling
- **shadcn/ui** + **Radix UI** for base components
- **Tiptap** for rich text editing
- **Vite** for build tooling

## Available UI Components

Import from `@/components/ui/`:

| Component | Usage |
|-----------|-------|
| `button` | Primary actions, variants: default, secondary, destructive, outline, ghost, link |
| `dialog` | Modals and popups |
| `card` | Content containers |
| `tabs` | Tabbed navigation |
| `table` | Data display |
| `form` | Form wrapper with validation |
| `input`, `textarea` | Text inputs |
| `select` | Dropdowns |
| `checkbox`, `switch` | Toggle controls |
| `badge` | Status indicators |
| `alert` | Notifications |
| `progress` | Loading indicators |
| `skeleton` | Loading placeholders |
| `tooltip` | Hover hints |
| `dropdown-menu` | Context menus |
| `sheet` | Slide-out panels |
| `accordion` | Collapsible sections |
| `scroll-area` | Custom scrollbars |

## Design Principles

### 1. Component Structure
```tsx
// Good: Single responsibility, typed props
interface DocumentCardProps {
  document: ProjectDocument;
  onSelect: (id: string) => void;
  isSelected?: boolean;
}

export const DocumentCard = ({ document, onSelect, isSelected = false }: DocumentCardProps) => {
  return (
    <Card className={cn("cursor-pointer", isSelected && "ring-2 ring-primary")}>
      {/* content */}
    </Card>
  );
};
```

### 2. Styling Approach
- Use Tailwind utility classes
- Use `cn()` helper for conditional classes
- Follow spacing scale: 1, 2, 4, 6, 8, 12, 16, 24
- Colors: Use semantic tokens (primary, secondary, destructive, muted)

```tsx
import { cn } from "@/lib/utils";

<div className={cn(
  "p-4 rounded-lg border",
  isActive ? "bg-primary text-primary-foreground" : "bg-muted"
)} />
```

### 3. Responsive Breakpoints
```tsx
// Mobile-first approach
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Responsive grid */}
</div>

// Hide/show based on screen size
<span className="hidden md:inline">Full text</span>
<span className="md:hidden">Short</span>
```

Breakpoints: `sm:640px`, `md:768px`, `lg:1024px`, `xl:1280px`

### 4. Accessibility (a11y)
- Use semantic HTML (`<button>`, `<nav>`, `<main>`, `<aside>`)
- Include `aria-label` for icon-only buttons
- Ensure focus states are visible
- Support keyboard navigation

```tsx
<Button variant="ghost" size="icon" aria-label="Close dialog">
  <X className="h-4 w-4" />
</Button>
```

## Common Patterns

### Dialog with Form
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const CreateProjectDialog = ({ open, onOpenChange }: Props) => {
  const [name, setName] = useState("");

  const handleSubmit = () => {
    // submit logic
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create Project</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Project Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter project name"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Create</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

### Data Table with Actions
```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MoreHorizontal } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

export const DocumentTable = ({ documents }: Props) => (
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Name</TableHead>
        <TableHead>Status</TableHead>
        <TableHead className="w-[50px]"></TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {documents.map((doc) => (
        <TableRow key={doc.id}>
          <TableCell className="font-medium">{doc.name}</TableCell>
          <TableCell>
            <Badge variant={doc.status === "approved" ? "default" : "secondary"}>
              {doc.status}
            </Badge>
          </TableCell>
          <TableCell>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>Edit</DropdownMenuItem>
                <DropdownMenuItem>Download</DropdownMenuItem>
                <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
);
```

### Loading States
```tsx
import { Skeleton } from "@/components/ui/skeleton";

// Skeleton for card
export const DocumentCardSkeleton = () => (
  <Card className="p-4">
    <Skeleton className="h-6 w-3/4 mb-2" />
    <Skeleton className="h-4 w-1/2" />
  </Card>
);

// Loading spinner
import { Loader2 } from "lucide-react";

<Button disabled>
  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
  Generating...
</Button>
```

### Tabs with Content
```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

<Tabs defaultValue="overview" className="w-full">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="documents">Documents</TabsTrigger>
    <TabsTrigger value="settings">Settings</TabsTrigger>
  </TabsList>
  <TabsContent value="overview" className="mt-4">
    {/* Overview content */}
  </TabsContent>
  <TabsContent value="documents" className="mt-4">
    {/* Documents content */}
  </TabsContent>
  <TabsContent value="settings" className="mt-4">
    {/* Settings content */}
  </TabsContent>
</Tabs>
```

## Project-Specific Patterns

### Document Status Badge
```tsx
const statusColors: Record<string, string> = {
  draft: "bg-yellow-100 text-yellow-800",
  generated: "bg-blue-100 text-blue-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
};

<Badge className={statusColors[status]}>{status}</Badge>
```

### Procurement Phase Indicator
```tsx
const phases = ["pre-solicitation", "solicitation", "post-solicitation", "award"];

<div className="flex items-center gap-2">
  {phases.map((phase, i) => (
    <div
      key={phase}
      className={cn(
        "flex items-center gap-1",
        currentPhase === phase ? "text-primary font-medium" : "text-muted-foreground"
      )}
    >
      <div className={cn(
        "w-6 h-6 rounded-full flex items-center justify-center text-sm",
        currentPhase === phase ? "bg-primary text-white" : "bg-muted"
      )}>
        {i + 1}
      </div>
      <span className="hidden sm:inline capitalize">{phase.replace("-", " ")}</span>
    </div>
  ))}
</div>
```

## Key Files Reference

- `dod_contracting_front_end/src/components/ui/` - Base shadcn/ui components
- `dod_contracting_front_end/src/components/AIContractingUI.tsx` - Main container
- `dod_contracting_front_end/src/components/LiveEditor.tsx` - Document editor
- `dod_contracting_front_end/src/components/procurement/` - Procurement components
- `dod_contracting_front_end/src/lib/utils.ts` - Utility functions (`cn()`)

## Icon Usage

Use `lucide-react` for icons:
```tsx
import { FileText, Download, Check, X, ChevronRight, Loader2 } from "lucide-react";

<FileText className="h-4 w-4" />
```

Common icons: `FileText`, `Download`, `Upload`, `Check`, `X`, `ChevronRight`, `ChevronDown`, `Plus`, `Trash2`, `Edit`, `Eye`, `Loader2`, `AlertCircle`, `CheckCircle`
