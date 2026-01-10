"""
Q&A Manager Agent: Manages questions and answers during solicitation period
Tracks questions, generates responses, ensures fair disclosure per FAR 15.201(f)
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime
import re
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class QAManagerAgent(BaseAgent):
    """
    Q&A Manager Agent
    
    Manages questions and answers during solicitation period per FAR 15.201(f).
    
    Features:
    - Question tracking system (ID, date, vendor, category)
    - Response generation using RAG for consistency with RFP
    - Fair disclosure validation
    - Amendment requirement detection
    - Q&A document generation
    - SAM.gov posting format
    
    Dependencies:
    - BaseAgent: LLM interaction and common utilities
    - Retriever: RAG system for answering based on solicitation docs
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Q&A Manager Agent
        
        Args:
            api_key: Anthropic API key
            retriever: Optional RAG retriever for answering from solicitation
            model: Claude model to use
        """
        super().__init__(
            name="Q&A Manager Agent",
            api_key=api_key,
            model=model,
            temperature=0.3  # Low temperature for consistent answers
        )
        
        self.retriever = retriever
        self.template_path = Path(__file__).parent.parent / "templates" / "qa_response_template.md"
        
        # Load template
        with open(self.template_path, 'r') as f:
            self.template = f.read()
        
        # Q&A database (in-memory, could be JSON/SQLite in production)
        self.qa_database = []
        self.question_counter = 0
        
        print("\n" + "="*70)
        print("Q&A MANAGER AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Template loaded: {self.template_path.name}")
        if self.retriever:
            print(f"  ✓ RAG retriever available (answer generation enabled)")
        else:
            print(f"  ℹ RAG retriever not available (manual answers required)")
        print("="*70 + "\n")
    
    def add_question(
        self,
        question_text: str,
        submitter: str = "Anonymous",
        category: str = "General",
        solicitation_section: Optional[str] = None
    ) -> Dict:
        """
        Add a new question to the database
        
        Args:
            question_text: The question text
            submitter: Vendor name (default: Anonymous for fair disclosure)
            category: Question category (Technical, Pricing, Section L, etc.)
            solicitation_section: Related solicitation section
        
        Returns:
            Question record with assigned ID
        """
        self.question_counter += 1
        question_id = f"Q-{self.question_counter:03d}"
        
        question_record = {
            'id': question_id,
            'question': question_text,
            'submitter': submitter,
            'category': category,
            'section': solicitation_section,
            'date_received': datetime.now().isoformat(),
            'status': 'pending',
            'answer': None,
            'requires_amendment': False
        }
        
        self.qa_database.append(question_record)
        
        self.log(f"Added question {question_id}: {category}")
        return question_record
    
    def generate_answer(
        self,
        question_id: str,
        solicitation_content: Optional[str] = None,
        manual_answer: Optional[str] = None
    ) -> Dict:
        """
        Generate answer to a question
        
        Args:
            question_id: Question ID
            solicitation_content: Optional solicitation content for context
            manual_answer: Optional manual answer (overrides RAG)
        
        Returns:
            Updated question record with answer
        """
        # Find question
        question_record = None
        for q in self.qa_database:
            if q['id'] == question_id:
                question_record = q
                break
        
        if not question_record:
            return {'error': f'Question {question_id} not found'}
        
        # Use manual answer if provided
        if manual_answer:
            answer = manual_answer
        elif self.retriever and solicitation_content:
            # Use RAG to generate answer
            answer = self._generate_answer_with_rag(
                question_record['question'],
                solicitation_content
            )
        else:
            # Use LLM without RAG
            answer = self._generate_answer_with_llm(question_record['question'])
        
        # Determine if amendment is required
        requires_amendment = self._check_amendment_required(
            question_record['question'],
            answer
        )
        
        # Update record
        question_record['answer'] = answer
        question_record['status'] = 'answered'
        question_record['date_answered'] = datetime.now().isoformat()
        question_record['requires_amendment'] = requires_amendment
        
        self.log(f"Generated answer for {question_id}")
        if requires_amendment:
            self.log(f"  ⚠️ Question {question_id} requires solicitation amendment", level="WARNING")
        
        return question_record
    
    def _generate_answer_with_rag(self, question: str, solicitation_content: str) -> str:
        """Generate answer using RAG to search solicitation"""
        try:
            # Query RAG for relevant solicitation content
            results = self.retriever.retrieve(question, k=3)
            
            if not results:
                return self._generate_answer_with_llm(question)
            
            # Combine RAG results
            context = '\n\n'.join([r.get('text', '')[:500] for r in results[:2]])
            
            # Use LLM to generate answer based on context
            prompt = f"""You are answering a question about a government solicitation.
            
Question: {question}

Relevant solicitation content:
{context}

Provide a clear, concise answer based on the solicitation content. If the solicitation doesn't address the question, state that clearly and indicate if clarification will be provided via amendment.

Answer:"""
            
            answer = self.call_llm(prompt, max_tokens=500)
            return answer.strip()
            
        except Exception as e:
            self.log(f"RAG answer generation failed: {e}", level="WARNING")
            return self._generate_answer_with_llm(question)
    
    def _generate_answer_with_llm(self, question: str) -> str:
        """Generate answer using LLM without RAG"""
        prompt = f"""Generate a professional response to this question about a government solicitation:

Question: {question}

Provide a clear answer or state that the information will be provided via amendment.

Answer:"""
        
        answer = self.call_llm(prompt, max_tokens=300)
        return answer.strip()
    
    def _check_amendment_required(self, question: str, answer: str) -> bool:
        """Determine if question requires solicitation amendment"""
        # Keywords indicating amendment needed
        amendment_keywords = [
            'amendment',
            'will be revised',
            'will be clarified',
            'correction',
            'error in solicitation',
            'will be updated'
        ]
        
        answer_lower = answer.lower()
        return any(keyword in answer_lower for keyword in amendment_keywords)
    
    def generate_qa_document(self, solicitation_info: Dict, config: Dict) -> Dict:
        """
        Generate complete Q&A document from all questions
        
        Args:
            solicitation_info: Solicitation details
            config: Configuration
        
        Returns:
            Dictionary with Q&A document content
        """
        print("\n" + "="*70)
        print("GENERATING Q&A DOCUMENT")
        print("="*70)
        print(f"Total Questions: {len(self.qa_database)}")
        print(f"Answered: {sum(1 for q in self.qa_database if q['status'] == 'answered')}")
        print("="*70 + "\n")

        # NEW: Cross-reference lookup - Find PWS/SOW/SOO for context
        program_name = solicitation_info.get('program_name', 'Unknown')

        if program_name != 'Unknown':
            try:
                print("🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for PWS/SOW/SOO (source solicitation documents)
                latest_pws = metadata_store.find_latest_document('pws', program_name)
                latest_sow = metadata_store.find_latest_document('sow', program_name)
                latest_soo = metadata_store.find_latest_document('soo', program_name)

                if latest_pws:
                    print(f"✅ Found PWS: {latest_pws['id']}")
                    self._pws_reference = latest_pws['id']
                elif latest_sow:
                    print(f"✅ Found SOW: {latest_sow['id']}")
                    self._sow_reference = latest_sow['id']
                elif latest_soo:
                    print(f"✅ Found SOO: {latest_soo['id']}")
                    self._soo_reference = latest_soo['id']
                else:
                    print(f"⚠️  No work statement found for {program_name}")
                    self._pws_reference = None
                    self._sow_reference = None
                    self._soo_reference = None

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._pws_reference = None
                self._sow_reference = None
                self._soo_reference = None
        else:
            self._pws_reference = None
            self._sow_reference = None
            self._soo_reference = None
        
        # Organize questions by category
        questions_by_category = {}
        for q in self.qa_database:
            category = q.get('category', 'Other')
            if category not in questions_by_category:
                questions_by_category[category] = []
            questions_by_category[category].append(q)
        
        # Generate category sections
        category_sections = {}
        for category, questions in questions_by_category.items():
            section_content = self._generate_category_section(questions)
            category_sections[category.lower().replace(' ', '_') + '_qa_section'] = section_content
        
        # Populate template
        content = self._populate_qa_template(
            solicitation_info,
            questions_by_category,
            category_sections,
            config
        )
        
        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()

                # Extract structured data from Q&A
                extracted_data = {
                    'total_questions': len(self.qa_database),
                    'answered_questions': sum(1 for q in self.qa_database if q['status'] == 'answered'),
                    'categories': list(questions_by_category.keys()),
                    'requires_amendment': sum(1 for q in self.qa_database if q.get('requires_amendment', False)),
                    'qa_database': self.qa_database
                }

                # Build references dict
                references = {}
                if hasattr(self, '_pws_reference') and self._pws_reference:
                    references['pws'] = self._pws_reference
                if hasattr(self, '_sow_reference') and self._sow_reference:
                    references['sow'] = self._sow_reference
                if hasattr(self, '_soo_reference') and self._soo_reference:
                    references['soo'] = self._soo_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='qa_document',
                    program=program_name,
                    content=content,
                    file_path='',  # Will be set by orchestrator
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Document metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save document metadata: {str(e)}")

        return {
            'status': 'success',
            'content': content,
            'metadata': {
                'total_questions': len(self.qa_database),
                'answered_questions': sum(1 for q in self.qa_database if q['status'] == 'answered'),
                'categories': len(questions_by_category),
                'requires_amendment': sum(1 for q in self.qa_database if q.get('requires_amendment', False))
            }
        }
    
    def _generate_category_section(self, questions: List[Dict]) -> str:
        """Generate Q&A section for a category"""
        section = []
        
        for q in questions:
            if q['status'] != 'answered':
                continue
            
            amendment_flag = " **⚠️ SOLICITATION CHANGE**" if q.get('requires_amendment') else ""
            
            qa_entry = f"""
**{q['id']}:** {q['question']}{amendment_flag}

**Answer:** {q.get('answer', 'Pending response')}

*Date Received:* {datetime.fromisoformat(q['date_received']).strftime('%B %d, %Y')}
"""
            section.append(qa_entry)
        
        return '\n'.join(section) if section else "No questions in this category."
    
    def _populate_qa_template(
        self,
        solicitation_info: Dict,
        questions_by_category: Dict,
        category_sections: Dict,
        config: Dict
    ) -> str:
        """Populate Q&A template"""
        content = self.template
        
        # Basic information
        content = content.replace('{{solicitation_number}}', solicitation_info.get('solicitation_number', 'TBD'))
        content = content.replace('{{program_name}}', solicitation_info.get('program_name', 'TBD'))
        content = content.replace('{{qa_document_number}}', f"QA-{datetime.now().strftime('%Y%m%d')}")
        content = content.replace('{{issue_date}}', datetime.now().strftime('%B %d, %Y'))
        content = content.replace('{{classification}}', config.get('classification', 'UNCLASSIFIED'))
        
        # POC information
        content = content.replace('{{issuing_office}}', solicitation_info.get('office', 'Contracting Office'))
        content = content.replace('{{poc_name}}', solicitation_info.get('contracting_officer', 'John Doe'))
        content = content.replace('{{poc_title}}', 'Contracting Officer')
        content = content.replace('{{poc_email}}', solicitation_info.get('co_email', 'contracting@agency.mil'))
        content = content.replace('{{poc_phone}}', solicitation_info.get('co_phone', '(703) 555-0000'))
        
        # Dates
        content = content.replace('{{original_issue_date}}', solicitation_info.get('issue_date', 'TBD'))
        content = content.replace('{{proposal_due_date}}', solicitation_info.get('proposal_due_date', 'TBD'))
        content = content.replace('{{questions_deadline}}', solicitation_info.get('questions_deadline', 'TBD'))
        
        # Statistics
        content = content.replace('{{total_questions}}', str(len(self.qa_database)))
        
        # Category sections
        for key, value in category_sections.items():
            content = content.replace('{{' + key + '}}', value)
        
        # Topic areas list
        topic_list = '\n'.join([f"- {cat}" for cat in questions_by_category.keys()])
        content = content.replace('{{topic_areas_list}}', topic_list)
        
        # Statistics table
        stats_table = '\n'.join([
            f"| {cat} | {len(qs)} | {len(qs)/len(self.qa_database)*100:.1f}% |"
            for cat, qs in questions_by_category.items()
        ])
        content = content.replace('{{question_statistics_table}}', stats_table)
        
        # Fill remaining placeholders
        content = re.sub(r'\{\{[^}]+\}\}', 'None', content)
        
        return content
    
    def save_qa_database(self, filepath: str):
        """Save Q&A database to JSON file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.qa_database, f, indent=2)
        
        self.log(f"Q&A database saved: {filepath}")
    
    def load_qa_database(self, filepath: str):
        """Load Q&A database from JSON file"""
        try:
            with open(filepath, 'r') as f:
                self.qa_database = json.load(f)
            
            self.question_counter = len(self.qa_database)
            self.log(f"Q&A database loaded: {len(self.qa_database)} questions")
        except Exception as e:
            self.log(f"Failed to load Q&A database: {e}", level="WARNING")
    
    def save_to_file(self, content: str, output_path: str, convert_to_pdf: bool = True) -> Dict:
        """Save Q&A document to file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(content)
        
        result = {'markdown': output_path}
        
        if convert_to_pdf:
            pdf_path = output_path.replace('.md', '.pdf')
            try:
                from utils.convert_md_to_pdf import convert_markdown_to_pdf
                convert_markdown_to_pdf(output_path, pdf_path)
                result['pdf'] = pdf_path
                print(f"  ✓ PDF saved: {pdf_path}")
            except Exception as e:
                print(f"  ⚠ PDF generation failed: {e}")
                result['pdf'] = None
        
        return result
    
    def get_questions_requiring_amendment(self) -> List[Dict]:
        """Get list of questions that require solicitation amendment"""
        return [q for q in self.qa_database if q.get('requires_amendment', False)]
    
    def export_statistics(self) -> Dict:
        """Export Q&A statistics"""
        categories = {}
        for q in self.qa_database:
            cat = q.get('category', 'Other')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_questions': len(self.qa_database),
            'answered': sum(1 for q in self.qa_database if q['status'] == 'answered'),
            'pending': sum(1 for q in self.qa_database if q['status'] == 'pending'),
            'requires_amendment': sum(1 for q in self.qa_database if q.get('requires_amendment', False)),
            'by_category': categories
        }

