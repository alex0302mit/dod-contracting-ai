"""
Enhanced Markdown to PDF Converter with Table Support

Converts markdown documents to professional PDF format using ReportLab.
Supports:
- Headers (H1, H2, H3)
- Bold text
- Paragraphs
- Tables (pipe-delimited markdown tables)
- Horizontal rules
- Lists (bullet and numbered)

Author: DoD Contracting Automation System
Version: 2.0 (with table support)
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, ListStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
    PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
import re
from typing import List, Tuple, Dict


def convert_markdown_bold_to_html(text: str) -> str:
    """
    Convert markdown **bold** to HTML <b>bold</b>

    Args:
        text: Text with markdown bold syntax

    Returns:
        Text with HTML bold tags
    """
    # Handle inline bold text
    while '**' in text:
        # Find first occurrence of **
        start = text.find('**')
        if start == -1:
            break
        # Find closing **
        end = text.find('**', start + 2)
        if end == -1:
            break
        # Replace with HTML tags
        text = text[:start] + '<b>' + text[start+2:end] + '</b>' + text[end+2:]
    return text


def convert_markdown_italic_to_html(text: str) -> str:
    """
    Convert markdown *italic* to HTML <i>italic</i>
    
    IMPORTANT: This must run AFTER bold conversion to avoid conflicts,
    since bold uses ** and italic uses single *.

    Args:
        text: Text with markdown italic syntax (single asterisks)

    Returns:
        Text with HTML italic tags
    """
    # Handle inline italic text with single asterisks
    # Use regex to find *text* patterns that aren't part of ** (already converted)
    # Pattern: single * not preceded or followed by another *
    result = []
    i = 0
    while i < len(text):
        # Check for single asterisk (not part of **)
        if text[i] == '*':
            # Make sure it's not escaped or part of **
            # Find closing single asterisk
            end = text.find('*', i + 1)
            if end != -1 and end > i + 1:
                # Found a closing asterisk - extract italic content
                italic_content = text[i + 1:end]
                # Make sure there's actual content (not empty)
                if italic_content.strip():
                    result.append('<i>')
                    result.append(italic_content)
                    result.append('</i>')
                    i = end + 1
                    continue
        result.append(text[i])
        i += 1
    return ''.join(result)


def convert_markdown_formatting_to_html(text: str) -> str:
    """
    Convert all markdown formatting to HTML tags.
    
    Handles:
    - **bold** -> <b>bold</b>
    - *italic* -> <i>italic</i>
    
    Order matters: bold must be converted first since it uses **,
    then italic can safely convert remaining single *.

    Args:
        text: Text with markdown formatting

    Returns:
        Text with HTML formatting tags
    """
    # First convert bold (**text**) - must come first
    text = convert_markdown_bold_to_html(text)
    # Then convert italic (*text*) - safe now since ** already removed
    text = convert_markdown_italic_to_html(text)
    return text


def is_table_row(line: str) -> bool:
    """
    Check if line is a markdown table row

    Args:
        line: Line to check

    Returns:
        True if line starts with | and contains at least one more |
    """
    stripped = line.strip()
    return stripped.startswith('|') and stripped.count('|') >= 2


def is_table_separator(line: str) -> bool:
    """
    Check if line is a markdown table separator (header separator)
    Example: |---|---|---|

    Args:
        line: Line to check

    Returns:
        True if line is a table separator
    """
    stripped = line.strip()
    if not stripped.startswith('|'):
        return False

    # Remove outer pipes and split
    inner = stripped.strip('|')
    cells = [cell.strip() for cell in inner.split('|')]

    # Check if all cells are made of dashes and colons
    for cell in cells:
        if not cell or not all(c in '-:' for c in cell):
            return False

    return True


def parse_table_alignment(separator_line: str) -> List[str]:
    """
    Parse alignment from table separator line
    Examples:
        |:---|    -> left
        |:---:|   -> center
        |---:|    -> right
        |---|     -> left (default)

    Args:
        separator_line: Table separator line

    Returns:
        List of alignments: 'LEFT', 'CENTER', 'RIGHT'
    """
    alignments = []
    inner = separator_line.strip().strip('|')
    cells = [cell.strip() for cell in inner.split('|')]

    for cell in cells:
        if cell.startswith(':') and cell.endswith(':'):
            alignments.append('CENTER')
        elif cell.endswith(':'):
            alignments.append('RIGHT')
        else:
            alignments.append('LEFT')

    return alignments


def parse_table_row(line: str) -> List[str]:
    """
    Parse a markdown table row into cells

    Args:
        line: Table row line

    Returns:
        List of cell contents
    """
    # Remove outer pipes and split
    inner = line.strip().strip('|')
    cells = [cell.strip() for cell in inner.split('|')]
    return cells


def parse_markdown_table(lines: List[str], start_idx: int) -> Tuple[List[List[str]], List[str], int]:
    """
    Parse a complete markdown table

    Args:
        lines: All markdown lines
        start_idx: Index where table starts

    Returns:
        Tuple of (table_data, alignments, end_idx)
        - table_data: 2D list of cell contents
        - alignments: List of column alignments
        - end_idx: Index after last table row
    """
    table_data = []
    alignments = []
    i = start_idx

    # Parse header row
    if i < len(lines) and is_table_row(lines[i]):
        header = parse_table_row(lines[i])
        table_data.append(header)
        i += 1

    # Parse separator row (contains alignment info)
    if i < len(lines) and is_table_separator(lines[i]):
        alignments = parse_table_alignment(lines[i])
        i += 1

    # Parse data rows
    while i < len(lines) and is_table_row(lines[i]):
        row = parse_table_row(lines[i])
        table_data.append(row)
        i += 1

    # Default alignments if not specified
    if not alignments and table_data:
        alignments = ['LEFT'] * len(table_data[0])

    return table_data, alignments, i


def create_pdf_table(table_data: List[List[str]], alignments: List[str], has_header: bool = True) -> Table:
    """
    Create a ReportLab Table object from markdown table data

    Args:
        table_data: 2D list of cell contents
        alignments: List of column alignments
        has_header: Whether first row is a header

    Returns:
        ReportLab Table object with professional styling
    """
    if not table_data:
        return None

    # Convert alignment strings to ReportLab constants
    alignment_map = {
        'LEFT': TA_LEFT,
        'CENTER': TA_CENTER,
        'RIGHT': TA_RIGHT
    }

    # Create cell styles for Paragraphs
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()

    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['BodyText'],
        fontSize=10,
        fontName='Times-Roman',
        textColor=colors.black,
        leading=12,
        alignment=TA_LEFT
    )

    header_cell_style = ParagraphStyle(
        'HeaderCellStyle',
        parent=styles['BodyText'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        leading=13,
        alignment=TA_CENTER
    )

    # Process cell contents - convert markdown bold to HTML and wrap in Paragraphs
    processed_data = []
    for row_idx, row in enumerate(table_data):
        processed_row = []
        for col_idx, cell in enumerate(row):
            # Convert markdown formatting (bold and italic) to HTML
            cell_text = convert_markdown_formatting_to_html(cell)

            # Determine which style to use
            if row_idx == 0 and has_header:
                # Header row
                para = Paragraph(cell_text, header_cell_style)
            else:
                # Data row - create style with appropriate alignment
                align = alignment_map.get(alignments[col_idx] if col_idx < len(alignments) else 'LEFT', TA_LEFT)
                data_style = ParagraphStyle(
                    f'CellStyle_{col_idx}',
                    parent=cell_style,
                    alignment=align
                )
                para = Paragraph(cell_text, data_style)

            processed_row.append(para)
        processed_data.append(processed_row)

    # Calculate column widths dynamically
    num_cols = len(processed_data[0])
    available_width = 7 * inch  # Page width minus margins
    col_widths = [available_width / num_cols] * num_cols

    # Create table
    table = Table(processed_data, colWidths=col_widths, repeatRows=1 if has_header else 0)

    # Create professional table style
    # Note: Font styling is now handled by Paragraph styles, not TableStyle
    style_commands = [
        # Global table styling
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]

    # Header row styling (background only, font handled by Paragraph)
    if has_header:
        style_commands.extend([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
        ])

    table.setStyle(TableStyle(style_commands))

    return table


def parse_bullet_list(lines: List[str], start_idx: int) -> Tuple[List[str], int]:
    """
    Parse a bullet list

    Args:
        lines: All markdown lines
        start_idx: Index where list starts

    Returns:
        Tuple of (list_items, end_idx)
    """
    list_items = []
    i = start_idx

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('- ') or line.startswith('* '):
            list_items.append(line[2:])
            i += 1
        elif not line:
            i += 1
            break
        else:
            break

    return list_items, i


def parse_numbered_list(lines: List[str], start_idx: int) -> Tuple[List[str], int]:
    """
    Parse a numbered list

    Args:
        lines: All markdown lines
        start_idx: Index where list starts

    Returns:
        Tuple of (list_items, end_idx)
    """
    list_items = []
    i = start_idx

    while i < len(lines):
        line = lines[i].strip()
        # Match patterns like "1. " or "1) "
        if re.match(r'^\d+[\.\)] ', line):
            # Extract text after number
            text = re.sub(r'^\d+[\.\)] ', '', line)
            list_items.append(text)
            i += 1
        elif not line:
            i += 1
            break
        else:
            break

    return list_items, i


def convert_markdown_to_pdf(md_file: str, pdf_file: str) -> None:
    """
    Convert markdown file to PDF with full table support

    Args:
        md_file: Path to input markdown file
        pdf_file: Path to output PDF file
    """
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Create PDF
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.black,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.black,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.black,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        fontName='Times-Roman'
    )

    bold_style = ParagraphStyle(
        'BoldBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.black,
        spaceAfter=6,
        fontName='Times-Bold'
    )

    # Build story
    story = []

    lines = md_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check for table
        if is_table_row(line):
            # Parse complete table
            table_data, alignments, end_idx = parse_markdown_table(lines, i)

            # Create and add table
            pdf_table = create_pdf_table(table_data, alignments, has_header=True)
            if pdf_table:
                story.append(Spacer(1, 0.1*inch))
                story.append(pdf_table)
                story.append(Spacer(1, 0.15*inch))

            i = end_idx
            continue

        # H1 - Title
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.2*inch))

        # H2 - Headings
        elif line.startswith('## '):
            text = line[3:].strip()
            text = convert_markdown_formatting_to_html(text)
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(text, heading_style))

        # H3 - Subheadings
        elif line.startswith('### '):
            text = line[4:].strip()
            text = convert_markdown_formatting_to_html(text)
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(text, subheading_style))

        # H4 - Sub-subheadings (from HTML h3 tags converted via html_to_markdown)
        elif line.startswith('#### '):
            text = line[5:].strip()
            text = convert_markdown_formatting_to_html(text)
            story.append(Spacer(1, 0.08*inch))
            story.append(Paragraph(text, subheading_style))

        # Bold text (metadata) - convert markdown bold to HTML bold
        elif line.startswith('**') and line.endswith('**'):
            text = line[2:-2]  # Remove ** from start and end
            text = f'<b>{text}</b>'
            story.append(Paragraph(text, body_style))

        # Horizontal rule
        elif line == '---':
            story.append(Spacer(1, 0.15*inch))

        # Bullet list
        elif line.startswith('- ') or line.startswith('* '):
            list_items, end_idx = parse_bullet_list(lines, i)
            if list_items:
                # Create bullet list with bold and italic support
                for item in list_items:
                    text = convert_markdown_formatting_to_html(item)
                    story.append(Paragraph(f'• {text}', body_style))
            i = end_idx
            continue

        # Numbered list
        elif re.match(r'^\d+[\.\)] ', line):
            list_items, end_idx = parse_numbered_list(lines, i)
            if list_items:
                # Create numbered list with bold and italic support
                for idx, item in enumerate(list_items, 1):
                    text = convert_markdown_formatting_to_html(item)
                    story.append(Paragraph(f'{idx}. {text}', body_style))
            i = end_idx
            continue

        # Regular paragraph
        else:
            # Convert markdown formatting (bold and italic) to HTML
            text = convert_markdown_formatting_to_html(line)

            # Continue reading if it's a multi-line paragraph
            paragraph_lines = [text]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                # Stop at empty lines, headers, tables, or lists
                if (not next_line or
                    next_line.startswith('#') or
                    next_line == '---' or
                    is_table_row(next_line) or
                    next_line.startswith('- ') or
                    next_line.startswith('* ') or
                    re.match(r'^\d+[\.\)] ', next_line)):
                    break
                # Convert markdown formatting (bold and italic) to HTML
                next_line = convert_markdown_formatting_to_html(next_line)
                paragraph_lines.append(next_line)
                i += 1

            full_paragraph = ' '.join(paragraph_lines)
            if full_paragraph:
                story.append(Paragraph(full_paragraph, body_style))
                story.append(Spacer(1, 0.1*inch))
            continue

        i += 1

    # Build PDF
    doc.build(story)
    print(f"✓ PDF created successfully: {pdf_file}")
    print(f"  - Tables rendered with professional formatting")
    print(f"  - Headers, paragraphs, and lists processed")


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        md_file = sys.argv[1]
        pdf_file = sys.argv[2]
    else:
        print("Usage: python convert_md_to_pdf.py <input.md> <output.pdf>")
        print("\nExample:")
        print("  python convert_md_to_pdf.py report.md report.pdf")
        sys.exit(1)

    try:
        convert_markdown_to_pdf(md_file, pdf_file)
    except FileNotFoundError:
        print(f"Error: File not found: {md_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error converting markdown to PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
