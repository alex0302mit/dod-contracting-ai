# Inline Compliance Feedback - Implementation Guide

## Overview

The editor now includes **inline compliance feedback** that automatically detects and highlights compliance issues in DoD acquisition documents with visual wavy underlines and hover tooltips.

---

## Visual Indicators by Issue Type

### 🔴 **Error** (Red wavy underline)
- **Color**: Red (#ef4444)
- **When**: Critical issues that must be fixed
- **Example**: "Timeline contains TBD placeholder"

### 🟠 **Warning** (Orange wavy underline)
- **Color**: Orange (#f59e0b)
- **When**: Issues that should be addressed
- **Example**: "Clarify which instructions (specify Section L)"

### 🔵 **Info** (Blue wavy underline)
- **Color**: Blue (#3b82f6)
- **When**: Suggestions for improvement
- **Example**: "Consider adding citations to support statements"

### 🟣 **Compliance** (Purple wavy underline) - NEW!
- **Color**: Purple (#a855f7)
- **When**: FAR/DFARS compliance issues
- **Examples**:
  - Missing FAR references
  - Missing DFARS clause citations
  - Regulatory requirement violations

---

## Compliance Detection Rules

The system automatically detects compliance issues based on:

### 1. **Missing FAR References**
```typescript
if (!text.match(/FAR\s+\d+/i)) {
  // Highlights: "Government"
  // Tooltip: "Missing FAR reference - Add FAR citation for procurement authority"
}
```

### 2. **Evaluation Procedures**
```typescript
if (text.includes("evaluation") && !text.match(/FAR\s+15\.3/i)) {
  // Highlights: "evaluation"
  // Tooltip: "Evaluation procedures must cite FAR 15.304"
}
```

### 3. **CUI/DFARS Requirements**
```typescript
if (text.includes("CUI") && !text.includes("DFARS")) {
  // Highlights: "CUI"
  // Tooltip: "CUI handling requires DFARS 252.204-7012 reference"
}
```

### 4. **Award Decisions**
```typescript
if (text.includes("award") && !text.match(/FAR\s+15\./i)) {
  // Highlights: "award"
  // Tooltip: "Award decisions must reference FAR Part 15 procedures"
}
```

---

## How It Works

### Step 1: Text Analysis
When you type in the editor, the `computeIssues()` function analyzes the text for:
- Missing FAR/DFARS citations
- Regulatory keyword usage
- Compliance requirements

### Step 2: Issue Classification
Issues are automatically classified as `'compliance'` type if they contain:
- `'far'` keyword
- `'dfars'` keyword
- `'clause'` keyword
- `'compliance'` keyword
- `'regulation'` keyword

### Step 3: Visual Feedback
- **Purple wavy underline** appears under the problematic text
- **Hover tooltip** shows detailed explanation
- **Smooth animations** on hover (lifts up, thicker underline)

### Step 4: User Action
- Read the tooltip explanation
- Add required FAR/DFARS citation
- Issue disappears when fixed

---

## Tooltip Features

### Design:
- **Dark background** with gradient (based on issue type)
- **White text** for maximum readability
- **Drop shadow** for depth
- **Pointer arrow** pointing to highlighted text
- **Smooth animations** (fade in/out, lift up)

### Tooltip Colors:
```css
/* Compliance (Purple) */
background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%);

/* Error (Red) */
background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);

/* Warning (Orange) */
background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);

/* Info (Default Dark) */
background-color: #1e293b;
```

---

## Example Usage in Code

### Adding Custom Compliance Rules

Edit `/src/lib/editorUtils.ts`:

```typescript
export function computeIssues(text: string) {
  const issues: any[] = [];

  // Add your custom compliance rule
  if (text.includes("IDIQ") && !text.includes("FAR 16.5")) {
    issues.push({
      id: "c5",
      kind: "compliance",
      label: "IDIQ contracts must reference FAR 16.5",
      pattern: "IDIQ",
    });
  }

  return issues;
}
```

### Issue Object Structure

```typescript
interface Issue {
  id: string;              // Unique ID (e.g., "c1", "c2")
  kind: 'error' | 'warning' | 'info' | 'compliance';
  label: string;           // Tooltip text
  pattern: string;         // Text to highlight
  fix?: {                  // Optional auto-fix
    label: string;
    apply: (text: string) => string;
  };
}
```

---

## Common Compliance Patterns

### DoD Acquisition Regulations

| Keyword | Required Citation | Rule |
|---------|------------------|------|
| Evaluation | FAR 15.304 | Evaluation factors must be stated |
| Award | FAR Part 15 | Source selection procedures |
| CUI | DFARS 252.204-7012 | Controlled Unclassified Information |
| IDIQ | FAR 16.5 | Indefinite-Delivery contracts |
| Small Business | FAR Part 19 | Small business programs |
| Cybersecurity | DFARS 252.204-7012 | NIST 800-171 compliance |

### Example Compliance Checks

```typescript
// Check for security requirements
if (text.includes("cybersecurity") && !text.includes("NIST")) {
  issues.push({
    kind: "compliance",
    label: "Cybersecurity requirements must reference NIST 800-171"
  });
}

// Check for contract type clauses
if (text.includes("FFP") && !text.includes("FAR 16.2")) {
  issues.push({
    kind: "compliance",
    label: "Firm-Fixed-Price contracts require FAR 16.2 reference"
  });
}
```

---

## Visual Examples

### Before (No compliance feedback):
```
The Government will conduct an evaluation
based on technical merit and award to the
best value offeror.
```

### After (With compliance feedback):
```
The Government will conduct an [evaluation]
                                  ~~~~~~~~
                                  🟣 Purple wavy underline

Hover shows: "Evaluation procedures must cite FAR 15.304"
```

---

## Customization

### Change Compliance Color

Edit `/src/components/editor/editor-styles.css`:

```css
.quality-issue-compliance {
  border-bottom-color: #your-color;
  background-color: rgba(your-color-rgb, 0.1);
}

.quality-issue-compliance::before {
  background: linear-gradient(135deg, #your-color 0%, #darker-shade 100%);
}
```

### Add More Compliance Keywords

Edit `/src/components/LiveEditor.tsx`:

```typescript
const isCompliance =
  issue.label.toLowerCase().includes('far') ||
  issue.label.toLowerCase().includes('dfars') ||
  issue.label.toLowerCase().includes('nist') ||    // Add NIST
  issue.label.toLowerCase().includes('cmmc') ||    // Add CMMC
  issue.label.toLowerCase().includes('your-keyword');
```

---

## Advanced Features

### Multi-Pattern Matching

Highlight multiple instances of the same issue:

```typescript
const patterns = text.matchAll(/evaluation/gi);
for (const match of patterns) {
  issues.push({
    id: `eval-${match.index}`,
    kind: "compliance",
    label: "Add FAR 15.304 citation",
    from: match.index,
    to: match.index + match[0].length,
  });
}
```

### Contextual Compliance Checks

Different rules for different sections:

```typescript
if (sectionName === "Section M") {
  // Stricter evaluation criteria rules
  if (text.includes("factor") && !text.includes("FAR 15.304")) {
    issues.push({
      kind: "compliance",
      label: "Section M evaluation factors must cite FAR 15.304"
    });
  }
}
```

### API-Based Compliance Checking

Call backend for real-time compliance validation:

```typescript
const checkCompliance = async (text: string) => {
  const response = await fetch('/api/check-compliance', {
    method: 'POST',
    body: JSON.stringify({ text })
  });

  const complianceIssues = await response.json();
  return complianceIssues;
};
```

---

## Performance Considerations

### Debounce Issue Detection

Avoid running compliance checks on every keystroke:

```typescript
import { useDebouncedCallback } from 'use-debounce';

const debouncedComputeIssues = useDebouncedCallback(
  (text) => {
    const issues = computeIssues(text);
    setQualityIssues(issues);
  },
  500  // Wait 500ms after user stops typing
);
```

### Cache Compliance Rules

Pre-compile regex patterns:

```typescript
const COMPLIANCE_PATTERNS = {
  far: /FAR\s+\d+(\.\d+)?/gi,
  dfars: /DFARS\s+\d+(\.\d+)?/gi,
  evaluation: /evaluation|evaluate|evaluator/gi,
};
```

---

## Testing

### Manual Test Checklist

- [ ] Type "evaluation" → Purple underline appears
- [ ] Hover over "evaluation" → Tooltip shows "Must cite FAR 15.304"
- [ ] Add "FAR 15.304" → Purple underline disappears
- [ ] Type "CUI" → Purple underline appears
- [ ] Add "DFARS" reference → Underline disappears
- [ ] Type "TBD" → Red underline appears (error)
- [ ] Hover shows different colors for different issue types

---

## Summary

✅ **4 Issue Types**: Error, Warning, Info, Compliance
✅ **Visual Indicators**: Color-coded wavy underlines
✅ **Smart Detection**: Automatic FAR/DFARS compliance checking
✅ **Hover Tooltips**: Detailed explanations on hover
✅ **Extensible**: Easy to add custom compliance rules
✅ **Production Ready**: Build succeeded, ready to deploy!

The compliance feedback system helps users create FAR/DFARS-compliant documents by providing **real-time, inline guidance** as they write.
