"""
Export Service

Handles document export in multiple formats (PDF, DOCX, JSON)
"""

import os
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import existing conversion utilities
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.convert_md_to_pdf import convert_markdown_to_pdf
from utils.convert_md_to_docx import convert_markdown_to_docx
from utils.export_formatter import (
    assemble_document,
    create_citations_section,
    create_metadata_section,
    calculate_document_size,
    format_file_size
)


class ExportService:
    """Service for managing document exports"""

    def __init__(self, exports_dir: str = "data/exports"):
        """
        Initialize export service

        Args:
            exports_dir: Directory to store temporary export files
        """
        self.exports_dir = Path(exports_dir)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def prepare_export(
        self,
        sections: Dict[str, str],
        citations: List[Dict] = None,
        metadata: Dict = None,
        section_order: List[str] = None
    ) -> Tuple[str, Dict[str, str]]:
        """
        Prepare export by assembling document and creating temp files

        Args:
            sections: Dictionary of section name -> HTML content
            citations: List of citation dictionaries
            metadata: Document metadata
            section_order: Optional custom section order

        Returns:
            Tuple of (export_id, file_sizes dict)
        """
        # Generate unique export ID
        export_id = str(uuid.uuid4())

        # Create export directory
        export_path = self.exports_dir / export_id
        export_path.mkdir(parents=True, exist_ok=True)

        # Prepare metadata
        if metadata is None:
            metadata = {}

        metadata['export_id'] = export_id
        metadata['export_date'] = datetime.now().isoformat()

        # Assemble complete document
        full_document = assemble_document(
            sections=sections,
            section_order=section_order,
            include_toc=True,
            include_title_page=True,
            metadata=metadata
        )

        # Add citations section if provided
        if citations:
            full_document += "\n\n---\n\n"
            full_document += create_citations_section(citations)

        # Add metadata appendix
        if metadata:
            full_document += "\n\n---\n\n"
            full_document += create_metadata_section(metadata)

        # Save markdown file
        md_file = export_path / "document.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(full_document)

        # Save metadata JSON
        metadata_file = export_path / "metadata.json"
        full_metadata = {
            'sections': sections,
            'citations': citations or [],
            'metadata': metadata,
            'section_order': section_order or list(sections.keys())
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(full_metadata, f, indent=2, default=str)

        # Calculate estimated file sizes
        base_size = calculate_document_size(sections)
        file_sizes = {
            'pdf': format_file_size(base_size * 3),  # PDF is roughly 3x markdown
            'docx': format_file_size(base_size * 2),  # DOCX is roughly 2x markdown
            'json': format_file_size(len(json.dumps(full_metadata)))
        }

        return export_id, file_sizes

    def generate_pdf(self, export_id: str) -> Path:
        """
        Generate PDF from prepared export

        Args:
            export_id: Export identifier

        Returns:
            Path to generated PDF file

        Raises:
            FileNotFoundError: If export_id doesn't exist
        """
        export_path = self.exports_dir / export_id

        if not export_path.exists():
            raise FileNotFoundError(f"Export {export_id} not found")

        md_file = export_path / "document.md"
        pdf_file = export_path / "document.pdf"

        # Convert markdown to PDF using existing utility
        convert_markdown_to_pdf(str(md_file), str(pdf_file))

        return pdf_file

    def generate_docx(self, export_id: str, program_name: str = None) -> Path:
        """
        Generate DOCX from prepared export

        Args:
            export_id: Export identifier
            program_name: Optional program name for document metadata

        Returns:
            Path to generated DOCX file

        Raises:
            FileNotFoundError: If export_id doesn't exist
        """
        export_path = self.exports_dir / export_id

        if not export_path.exists():
            raise FileNotFoundError(f"Export {export_id} not found")

        md_file = export_path / "document.md"
        docx_file = export_path / "document.docx"

        # Load metadata to get program name if not provided
        if program_name is None:
            metadata_file = export_path / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    program_name = metadata.get('metadata', {}).get('project_name', 'Procurement Document')

        # Convert markdown to DOCX using existing utility
        convert_markdown_to_docx(str(md_file), str(docx_file), program_name)

        return docx_file

    def generate_json(self, export_id: str) -> Path:
        """
        Get JSON metadata file from prepared export

        Args:
            export_id: Export identifier

        Returns:
            Path to JSON metadata file

        Raises:
            FileNotFoundError: If export_id doesn't exist
        """
        export_path = self.exports_dir / export_id

        if not export_path.exists():
            raise FileNotFoundError(f"Export {export_id} not found")

        metadata_file = export_path / "metadata.json"

        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found for export {export_id}")

        return metadata_file

    def generate_compliance_report(
        self,
        compliance_analysis: Dict,
        export_id: str = None
    ) -> Path:
        """
        Generate compliance report PDF

        Args:
            compliance_analysis: Compliance analysis data from complianceUtils
            export_id: Optional export_id to associate with

        Returns:
            Path to generated compliance report PDF
        """
        # Create export directory if needed
        if export_id is None:
            export_id = str(uuid.uuid4())

        export_path = self.exports_dir / export_id
        export_path.mkdir(parents=True, exist_ok=True)

        # Create compliance report markdown
        report_md = self._format_compliance_report(compliance_analysis)

        # Save markdown
        md_file = export_path / "compliance_report.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(report_md)

        # Convert to PDF
        pdf_file = export_path / "compliance_report.pdf"
        convert_markdown_to_pdf(str(md_file), str(pdf_file))

        return pdf_file

    def _format_compliance_report(self, analysis: Dict) -> str:
        """
        Format compliance analysis as markdown report

        Args:
            analysis: Compliance analysis data

        Returns:
            Markdown formatted report
        """
        parts = []

        # Title
        parts.append("# Compliance Analysis Report\n\n")
        parts.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}\n\n")
        parts.append("---\n\n")

        # Overall Summary
        parts.append("## Overall Compliance Status\n\n")
        parts.append(f"**Overall Score:** {analysis['overallScore']}/100\n\n")
        parts.append(f"**Status:** {analysis['overallStatus'].upper()}\n\n")
        parts.append(f"**Sections Analyzed:** {analysis['sectionsAnalyzed']}\n\n")
        parts.append(f"**Critical Issues:** {len(analysis['criticalIssues'])}\n\n")
        parts.append("---\n\n")

        # Section-by-Section Analysis
        parts.append("## Section-by-Section Analysis\n\n")

        for section in analysis['sectionCompliance']:
            parts.append(f"### {section['sectionName']}\n\n")
            parts.append(f"**Score:** {section['score']}/100 ({section['status'].upper()})\n\n")
            parts.append(f"**Word Count:** {section['wordCount']}\n\n")

            # Quality breakdown
            parts.append("**Quality Breakdown:**\n\n")
            breakdown = section['qualityBreakdown']
            parts.append(f"- Readability: {breakdown['readability']}/100\n")
            parts.append(f"- Citations: {breakdown['citations']}/100\n")
            parts.append(f"- Compliance: {breakdown['compliance']}/100\n")
            parts.append(f"- Length: {breakdown['length']}/100\n\n")

            # Issues
            if section['issues']:
                parts.append(f"**Issues ({len(section['issues'])}):**\n\n")
                for issue in section['issues']:
                    parts.append(f"- [{issue['kind'].upper()}] {issue['label']}\n")
                parts.append("\n")

            parts.append("---\n\n")

        # Critical Issues
        if analysis['criticalIssues']:
            parts.append("## Critical Issues Summary\n\n")
            for issue in analysis['criticalIssues']:
                parts.append(f"### {issue['sectionName']}: {issue['label']}\n\n")
                parts.append(f"**Type:** {issue['kind'].upper()}\n\n")
                if 'fix' in issue and issue['fix']:
                    parts.append(f"**Suggested Fix:** {issue['fix'].get('label', 'N/A')}\n\n")
                parts.append("---\n\n")

        # FAR Coverage
        parts.append("## FAR (Federal Acquisition Regulation) Coverage\n\n")

        if analysis['farCoverage']:
            parts.append("**Found FAR References:**\n\n")
            for far in analysis['farCoverage']:
                sections_str = ', '.join(far['sections'])
                parts.append(f"- {far['clause']} (Used in: {sections_str})\n")
            parts.append("\n")

        if analysis['missingFAR']:
            parts.append("**Missing FAR References:**\n\n")
            for far in analysis['missingFAR']:
                parts.append(f"- {far} (May be required)\n")
            parts.append("\n")

        # DFARS Coverage
        parts.append("## DFARS (Defense FAR Supplement) Coverage\n\n")

        if analysis['dfarsCoverage']:
            parts.append("**Found DFARS References:**\n\n")
            for dfars in analysis['dfarsCoverage']:
                sections_str = ', '.join(dfars['sections'])
                parts.append(f"- {dfars['clause']} (Used in: {sections_str})\n")
            parts.append("\n")

        if analysis['missingDFARS']:
            parts.append("**Missing DFARS References:**\n\n")
            for dfars in analysis['missingDFARS']:
                parts.append(f"- {dfars} (Required for CUI handling)\n")
            parts.append("\n")

        return ''.join(parts)

    def cleanup_old_exports(self, max_age_hours: int = 24):
        """
        Remove exports older than specified age

        Args:
            max_age_hours: Maximum age in hours before deletion
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        for export_dir in self.exports_dir.iterdir():
            if not export_dir.is_dir():
                continue

            # Check directory modification time
            dir_mtime = datetime.fromtimestamp(export_dir.stat().st_mtime)

            if dir_mtime < cutoff_time:
                try:
                    shutil.rmtree(export_dir)
                    print(f"Cleaned up old export: {export_dir.name}")
                except Exception as e:
                    print(f"Error cleaning up {export_dir.name}: {e}")

    def get_export_history(self, max_count: int = 10) -> List[Dict]:
        """
        Get list of recent exports

        Args:
            max_count: Maximum number of exports to return

        Returns:
            List of export info dictionaries
        """
        exports = []

        for export_dir in self.exports_dir.iterdir():
            if not export_dir.is_dir():
                continue

            export_id = export_dir.name
            metadata_file = export_dir / "metadata.json"

            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                export_info = {
                    'export_id': export_id,
                    'export_date': metadata.get('metadata', {}).get('export_date'),
                    'project_name': metadata.get('metadata', {}).get('project_name', 'Unknown'),
                    'files': []
                }

                # Check which files exist
                if (export_dir / "document.pdf").exists():
                    export_info['files'].append('pdf')
                if (export_dir / "document.docx").exists():
                    export_info['files'].append('docx')
                if (export_dir / "metadata.json").exists():
                    export_info['files'].append('json')
                if (export_dir / "compliance_report.pdf").exists():
                    export_info['files'].append('compliance')

                exports.append(export_info)

        # Sort by date (newest first)
        exports.sort(key=lambda x: x['export_date'] or '', reverse=True)

        return exports[:max_count]
