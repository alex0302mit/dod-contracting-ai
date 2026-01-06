"""
SF33 Field Extractor: Extract data from PWS/SOO/SOW documents for SF33 form population
"""

import re
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class SF33FieldExtractor:
    """
    Extract and structure data from generated PWS/SOO/SOW documents
    for SF33 Solicitation, Offer, and Award form population
    """

    def __init__(self):
        self.field_mapping = self._initialize_field_mapping()

    def _initialize_field_mapping(self) -> Dict:
        """
        Initialize SF33 field name mapping based on PDF form fields

        Returns:
            Dictionary mapping logical names to PDF form field names
        """
        return {
            # Header fields
            'rating': 'RATING[0]',
            'page_1': 'PG1[0]',
            'page_2': 'PG2[0]',
            'contract_number': 'CONTRACTNUM[0]',
            'solicitation_number': 'SOLICITATION[0]',
            'requisition_number': 'REQUNUM[0]',
            'date_issued': 'DateISSUED[0]',

            # Issued By (Block 7)
            'issued_by_code': 'ISSUECODE[0]',
            'issued_by': 'ISSUEDBY[0]',

            # Offer To Address (Block 8)
            'offer_to_address': 'FOFFERTOADDY[0]',

            # Solicitation details (Block 9)
            'sealed_offers': 'SEALEDOFFERS[0]',
            'located_in': 'LOCATEDIN[0]',
            'until': 'UNTIL[0]',
            'depository_date': 'DEPOSITORYDATE[0]',

            # Contact info (Block 10)
            'contact_name': 'NAME10A[0]',
            'area_code_1': 'AREACODE1[0]',
            'number_1': 'NUMBER1[0]',
            'ext_1': 'EXT1[0]',
            'email': 'EMAIL[0]',

            # Table of Contents (Block 11) - Section page numbers
            'pg_11_a': 'PG11A[0]',  # Section A
            'pg_11_b': 'PG11B[0]',  # Section B
            'pg_11_c': 'PG11C[0]',  # Section C
            'pg_11_d': 'PG11D[0]',  # Section D
            'pg_11_e': 'PG11E[0]',  # Section E
            'pg_11_f': 'PG11F[0]',  # Section F
            'pg_11_g': 'PG11G[0]',  # Section G
            'pg_11_h': 'PG11H[0]',  # Section H
            'pg_11_i': 'PG11I[0]',  # Section I
            'pg_11_j': 'PG11J[0]',  # Section J
            'pg_11_k': 'PG11K[0]',  # Section K
            'pg_11_l': 'PG11L[0]',  # Section L
            'pg_11_m': 'PG11M[0]',  # Section M

            # Offeror fields (Block 12-18) - Leave blank
            'calendar_days': 'CALDAYS[0]',
            'discount_10': 'CALANDAR10[0]',
            'discount_20': 'CALANDAR20[0]',
            'discount_30': 'CALENDAR30[0]',
            'discount_other': 'CALENDAR[0]',
            'discount_other_days': 'NUMBERFORCALENDAR[0]',
            'amendment_1': 'AMEND1[0]',
            'amendment_2': 'AMEND2[0]',
            'amendment_3': 'AMEND3[0]',
            'amendment_4': 'AMEND4[0]',
            'amendment_date_1': 'AMENDDate1[0]',
            'amendment_date_2': 'AMENDDate2[0]',
            'amendment_date_3': 'AMENDDate3[0]',
            'amendment_date_4': 'AMENDDate4[0]',
            'offeror_code': 'CODE15A[0]',
            'offeror_facility': 'FACILITY[0]',
            'offeror_address': 'OFFERORADDY[0]',
            'offeror_phone_area': 'AREA2[0]',
            'offeror_phone_number': 'NuMBER2[0]',
            'offeror_phone_ext': 'EXT2[0]',
            'authorized_title': 'TITLEAUTHORIZED[0]',
            'offer_date': 'OFFERDate[0]',

            # Award fields (Block 19-28) - Leave blank for government
            'accepted_items': 'ACCITEM[0]',
            'appropriation': 'APPROPRIATION[0]',
            'invoice_item': 'INVOICEITEM[0]',
            'liability': 'LIABILITY1[0]',
            'administered_by': 'ADMINISTEREDBY[0]',
            'payment_code': 'PAYMENTCODE[0]',
            'contracting_officer': 'CONTRACTINGOFFICER[0]',
            'award_date': 'AWARDDATE[0]',
            'payment_date': 'PAYMENTDate[0]'
        }

    def extract_from_markdown(self, markdown_path: str) -> Dict:
        """
        Extract project metadata from PWS/SOO/SOW markdown file

        Args:
            markdown_path: Path to markdown document

        Returns:
            Dictionary with extracted metadata
        """
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = {
            'document_type': self._detect_document_type(content),
            'program_name': self._extract_program_name(content),
            'organization': self._extract_organization(content),
            'date': self._extract_date(content),
            'author': self._extract_author(content),
            'budget': self._extract_budget(content),
            'period_of_performance': self._extract_period(content)
        }

        return metadata

    def _detect_document_type(self, content: str) -> str:
        """Detect if document is PWS, SOO, or SOW"""
        if 'Performance Work Statement (PWS)' in content or 'Performance Work Statement' in content:
            return 'PWS'
        elif 'Statement of Objectives (SOO)' in content or 'Statement of Objectives' in content:
            return 'SOO'
        elif 'Statement of Work' in content:
            return 'SOW'
        return 'Unknown'

    def _extract_program_name(self, content: str) -> Optional[str]:
        """Extract program name from document"""
        # Look for patterns like "**Program:** Name" or "## Program Name"
        patterns = [
            r'\*\*Program:\*\*\s*(.+?)(?:\n|$)',
            r'##\s*(.+?)(?:\n|$)',
            r'# (?:Performance Work Statement|Statement of Objectives|Statement of Work)\s*\n##\s*(.+?)(?:\n|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return None

    def _extract_organization(self, content: str) -> Optional[str]:
        """Extract organization from document"""
        patterns = [
            r'\*\*Organization:\*\*\s*(.+?)(?:\n|$)',
            r'- \*\*Organization\*\*:\s*(.+?)(?:\n|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return None

    def _extract_date(self, content: str) -> Optional[str]:
        """Extract date from document"""
        patterns = [
            r'\*\*Date:\*\*\s*(.+?)(?:\n|$)',
            r'- \*\*Date\*\*:\s*(.+?)(?:\n|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return None

    def _extract_author(self, content: str) -> Optional[str]:
        """Extract author from document"""
        patterns = [
            r'\*\*(?:Author|Prepared by):\*\*\s*(.+?)(?:\n|$)',
            r'- \*\*Author\*\*:\s*(.+?)(?:\n|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return None

    def _extract_budget(self, content: str) -> Optional[str]:
        """Extract budget information"""
        patterns = [
            r'\$[\d,\.]+\s*(?:million|M|k|K)',
            r'budget.*?\$[\d,\.]+'
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def _extract_period(self, content: str) -> Optional[str]:
        """Extract period of performance"""
        patterns = [
            r'(\d+)\s*months',
            r'Period of Performance.*?(\d+\s+months)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if '36' in match.group(0):
                    return '36 months'
                elif '24' in match.group(0):
                    return '24 months'
                elif '12' in match.group(0):
                    return '12 months'
                return match.group(1) if match.lastindex else match.group(0)

        return None

    def generate_solicitation_number(
        self,
        organization: str = "W911",
        fiscal_year: Optional[int] = None
    ) -> str:
        """
        Generate DoD-style solicitation number

        Format: W911XX-YY-R-XXXX
        Where: W911 = Army, YY = fiscal year, R = RFP, XXXX = sequential

        Args:
            organization: Organization code (default: W911 for Army)
            fiscal_year: Fiscal year (default: current year)

        Returns:
            Generated solicitation number
        """
        if fiscal_year is None:
            fiscal_year = datetime.now().year % 100  # Last 2 digits

        # Generate random 4-digit sequence number
        import random
        sequence = random.randint(1000, 9999)

        return f"{organization}XX-{fiscal_year:02d}-R-{sequence:04d}"

    def generate_contract_number(
        self,
        solicitation_number: str
    ) -> str:
        """
        Generate contract number from solicitation number

        Contract numbers often match solicitation numbers initially (TBD until award)

        Args:
            solicitation_number: Solicitation number

        Returns:
            Contract number (or TBD)
        """
        return "TBD"  # Contract number assigned upon award

    def build_table_of_contents(
        self,
        work_statement_pages: int = 1,
        include_sections: Optional[list] = None
    ) -> Dict[str, str]:
        """
        Build table of contents with page numbers

        Args:
            work_statement_pages: Number of pages in work statement
            include_sections: List of sections to include

        Returns:
            Dictionary mapping section codes to page numbers
        """
        if include_sections is None:
            include_sections = ['A', 'C', 'L', 'M', 'J']

        page_mapping = {}
        current_page = 1

        # Section A: SF33 (always page 1)
        if 'A' in include_sections:
            page_mapping['A'] = '1'
            current_page = 2

        # Section B: Supplies/Services (optional)
        if 'B' in include_sections:
            page_mapping['B'] = str(current_page)
            current_page += 1

        # Section C: Work Statement (main content)
        if 'C' in include_sections:
            page_mapping['C'] = str(current_page)
            current_page += work_statement_pages

        # Remaining sections (1 page each typically)
        for section in ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']:
            if section in include_sections:
                page_mapping[section] = str(current_page)
                current_page += 1

        return page_mapping

    def map_to_sf33_fields(
        self,
        metadata: Dict,
        solicitation_config: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Map extracted metadata to SF33 PDF form fields

        Args:
            metadata: Extracted document metadata
            solicitation_config: Additional solicitation configuration

        Returns:
            Dictionary mapping PDF field names to values
        """
        if solicitation_config is None:
            solicitation_config = {}

        # Generate solicitation number
        sol_number = self.generate_solicitation_number()

        # Build TOC
        toc = self.build_table_of_contents()

        # Map fields
        field_values = {
            # Header
            self.field_mapping['page_1']: '1',
            self.field_mapping['page_2']: solicitation_config.get('total_pages', '1'),
            self.field_mapping['solicitation_number']: sol_number,
            self.field_mapping['contract_number']: self.generate_contract_number(sol_number),
            self.field_mapping['date_issued']: metadata.get('date', datetime.now().strftime('%m/%d/%Y')),

            # Organization
            self.field_mapping['issued_by']: metadata.get('organization', ''),
            self.field_mapping['issued_by_code']: solicitation_config.get('org_code', ''),

            # Contact (if provided)
            self.field_mapping['contact_name']: metadata.get('author', ''),
            self.field_mapping['email']: solicitation_config.get('email', ''),

            # Table of Contents
            self.field_mapping['pg_11_a']: toc.get('A', '1'),
            self.field_mapping['pg_11_c']: toc.get('C', '2'),
            self.field_mapping['pg_11_l']: toc.get('L', ''),
            self.field_mapping['pg_11_m']: toc.get('M', ''),
            self.field_mapping['pg_11_j']: toc.get('J', ''),
        }

        # Remove None values
        field_values = {k: str(v) if v is not None else '' for k, v in field_values.items()}

        return field_values


# Example usage
if __name__ == "__main__":
    extractor = SF33FieldExtractor()

    # Test with PWS document
    pws_path = "outputs/pws/performance_work_statement.md"

    if Path(pws_path).exists():
        print("Extracting metadata from PWS...")
        metadata = extractor.extract_from_markdown(pws_path)
        print(f"\nExtracted Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

        print(f"\nGenerating SF33 field mappings...")
        sf33_fields = extractor.map_to_sf33_fields(metadata)
        print(f"\nSF33 Fields (sample):")
        for key, value in list(sf33_fields.items())[:10]:
            print(f"  {key}: {value}")
    else:
        print(f"PWS file not found: {pws_path}")
