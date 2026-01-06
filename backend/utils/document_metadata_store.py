"""
Document Metadata Store

Tracks generated documents and their extracted data for cross-referencing.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class DocumentMetadataStore:
    """
    Store and retrieve metadata about generated documents

    Enables cross-referencing by tracking:
    - What documents have been generated
    - Key data extracted from each document
    - Relationships between documents
    """

    def __init__(self, metadata_file: str = 'data/document_metadata.json'):
        """
        Initialize metadata store

        Args:
            metadata_file: Path to JSON file storing metadata
        """
        self.metadata_file = metadata_file
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load metadata from file, create empty if doesn't exist"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️  Warning: Could not parse {self.metadata_file}, starting fresh")
                return {'documents': {}, 'version': '1.0'}
        else:
            # Create parent directory if needed
            Path(self.metadata_file).parent.mkdir(parents=True, exist_ok=True)
            return {'documents': {}, 'version': '1.0'}

    def _save_metadata(self):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def save_document(
        self,
        doc_type: str,
        program: str,
        content: str,
        file_path: str,
        extracted_data: Dict,
        references: Optional[Dict] = None
    ) -> str:
        """
        Save document metadata

        Args:
            doc_type: Type of document (igce, pws, acquisition_plan, etc.)
            program: Program name (ALMS, etc.)
            content: Full document content
            file_path: Path where document was saved
            extracted_data: Extracted structured data from document
            references: Dict of referenced documents {doc_type: doc_id}

        Returns:
            Document ID (e.g., "igce_alms_2025-10-16_001")
        """
        # Generate unique document ID
        date_str = datetime.now().strftime('%Y-%m-%d')
        base_id = f"{doc_type}_{program}_{date_str}"

        # Check if document with this ID already exists, add counter if needed
        counter = 1
        doc_id = base_id
        while doc_id in self.metadata['documents']:
            doc_id = f"{base_id}_{counter:03d}"
            counter += 1

        # Calculate word count
        word_count = len(content.split())

        # Create metadata entry
        self.metadata['documents'][doc_id] = {
            'id': doc_id,
            'type': doc_type,
            'program': program,
            'generated_date': datetime.now().isoformat(),
            'file_path': file_path,
            'word_count': word_count,
            'extracted_data': extracted_data,
            'references': references or {}
        }

        # Save to file
        self._save_metadata()

        print(f"✅ Saved document metadata: {doc_id}")
        return doc_id

    def find_latest_document(
        self,
        doc_type: str,
        program: str,
        before_date: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find the most recent document of a given type for a program

        Args:
            doc_type: Type of document to find
            program: Program name
            before_date: Optional ISO date string - find latest before this date

        Returns:
            Document metadata dict or None if not found
        """
        matching_docs = [
            doc for doc_id, doc in self.metadata['documents'].items()
            if doc['type'] == doc_type and doc['program'] == program
        ]

        # Filter by date if specified
        if before_date:
            matching_docs = [
                doc for doc in matching_docs
                if doc['generated_date'] < before_date
            ]

        if not matching_docs:
            return None

        # Return most recent
        return sorted(
            matching_docs,
            key=lambda d: d['generated_date'],
            reverse=True
        )[0]

    def find_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """Find document by exact ID"""
        return self.metadata['documents'].get(doc_id)

    def list_documents(
        self,
        doc_type: Optional[str] = None,
        program: Optional[str] = None
    ) -> List[Dict]:
        """
        List all documents, optionally filtered by type and/or program

        Args:
            doc_type: Filter by document type
            program: Filter by program name

        Returns:
            List of document metadata dicts
        """
        docs = list(self.metadata['documents'].values())

        if doc_type:
            docs = [doc for doc in docs if doc['type'] == doc_type]

        if program:
            docs = [doc for doc in docs if doc['program'] == program]

        # Sort by date (most recent first)
        return sorted(docs, key=lambda d: d['generated_date'], reverse=True)

    def get_cross_references(self, doc_id: str) -> Dict[str, Dict]:
        """
        Get all documents referenced by this document

        Args:
            doc_id: Document ID

        Returns:
            Dict of {ref_type: referenced_document_metadata}
        """
        doc = self.find_document_by_id(doc_id)
        if not doc:
            return {}

        references = doc.get('references', {})
        resolved_refs = {}

        for ref_type, ref_doc_id in references.items():
            ref_doc = self.find_document_by_id(ref_doc_id)
            if ref_doc:
                resolved_refs[ref_type] = ref_doc

        return resolved_refs

    def get_referring_documents(self, doc_id: str) -> List[Dict]:
        """
        Get all documents that reference this document

        Args:
            doc_id: Document ID

        Returns:
            List of documents that reference this one
        """
        referring_docs = []

        for other_doc in self.metadata['documents'].values():
            if doc_id in other_doc.get('references', {}).values():
                referring_docs.append(other_doc)

        return referring_docs

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document metadata

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deleted, False if not found
        """
        if doc_id in self.metadata['documents']:
            del self.metadata['documents'][doc_id]
            self._save_metadata()
            print(f"✅ Deleted document metadata: {doc_id}")
            return True
        return False

    def get_statistics(self) -> Dict:
        """Get statistics about stored documents"""
        total_docs = len(self.metadata['documents'])

        # Count by type
        by_type = {}
        for doc in self.metadata['documents'].values():
            doc_type = doc['type']
            by_type[doc_type] = by_type.get(doc_type, 0) + 1

        # Count by program
        by_program = {}
        for doc in self.metadata['documents'].values():
            program = doc['program']
            by_program[program] = by_program.get(program, 0) + 1

        # Total word count
        total_words = sum(
            doc.get('word_count', 0)
            for doc in self.metadata['documents'].values()
        )

        return {
            'total_documents': total_docs,
            'by_type': by_type,
            'by_program': by_program,
            'total_words': total_words
        }

    def print_summary(self):
        """Print a summary of stored documents"""
        stats = self.get_statistics()

        print("\n" + "="*70)
        print("DOCUMENT METADATA STORE SUMMARY")
        print("="*70)
        print(f"Total Documents: {stats['total_documents']}")
        print(f"Total Words: {stats['total_words']:,}")

        print(f"\nBy Document Type:")
        for doc_type, count in sorted(stats['by_type'].items()):
            print(f"  • {doc_type}: {count}")

        print(f"\nBy Program:")
        for program, count in sorted(stats['by_program'].items()):
            print(f"  • {program}: {count}")

        print("="*70 + "\n")


if __name__ == '__main__':
    # Example usage
    store = DocumentMetadataStore()

    # Example: Save an IGCE document
    igce_data = {
        'total_cost': 2847500,
        'total_cost_formatted': '$2,847,500',
        'base_year_cost': 1245000,
        'option_year_1_cost': 801250,
        'option_year_2_cost': 801250,
        'period_of_performance': '36 months',
        'labor_categories_count': 8
    }

    doc_id = store.save_document(
        doc_type='igce',
        program='ALMS',
        content='... IGCE content ...',
        file_path='output/igce_alms_20251016.md',
        extracted_data=igce_data
    )

    print(f"Saved document: {doc_id}")

    # Find it back
    latest_igce = store.find_latest_document('igce', 'ALMS')
    if latest_igce:
        print(f"Found latest IGCE: {latest_igce['id']}")
        print(f"Total cost: {latest_igce['extracted_data']['total_cost_formatted']}")

    # Print summary
    store.print_summary()
