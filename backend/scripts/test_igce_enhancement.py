"""
Quick test for enhanced IGCE agent with RAG
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def test_enhanced_igce():
    """Test the enhanced IGCE agent"""

    print("\n" + "="*70)
    print("TESTING ENHANCED IGCE AGENT WITH RAG")
    print("="*70 + "\n")

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key'")
        return

    # Initialize RAG system
    print("Step 1: Initializing RAG system...")
    try:
        vector_store = VectorStore(api_key)
        vector_store.load()
        retriever = Retriever(vector_store, top_k=5)
        print("✓ RAG system loaded with", vector_store.index.ntotal, "vectors\n")
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")
        return

    # Initialize IGCE agent
    print("Step 2: Initializing IGCE Generator Agent...")
    igce_agent = IGCEGeneratorAgent(api_key=api_key, retriever=retriever)
    print()

    # Prepare test task
    project_info = {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'organization': 'Department of Defense / U.S. Army',
        'estimated_value': '$5M - $10M',
        'period_of_performance': '36 months',
        'background': 'Cloud-based logistics management system'
    }

    requirements_content = """
    Performance Work Statement for Advanced Logistics Management System

    The contractor shall provide a cloud-based logistics management system with:
    - Real-time inventory tracking
    - Automated reordering
    - Mobile access for warehouse personnel
    - Integration with SAP
    - Support for 2,800 users
    """

    config = {
        'contract_type': 'services',
        'prepared_by': 'Cost Analyst (Test)'
    }

    task = {
        'project_info': project_info,
        'requirements_content': requirements_content,
        'config': config
    }

    # Execute IGCE generation
    print("Step 3: Generating IGCE with enhanced RAG...")
    print("="*70)
    result = igce_agent.execute(task)

    if result['status'] == 'success':
        print("\n" + "="*70)
        print("✅ IGCE GENERATION SUCCESSFUL")
        print("="*70)

        # Save to file
        output_path = "outputs/test/enhanced_igce_test.md"
        files = igce_agent.save_to_file(result['content'], output_path, convert_to_pdf=True)

        print(f"\n📁 Files generated:")
        print(f"   - Markdown: {files.get('markdown')}")
        print(f"   - PDF: {files.get('pdf')}")

        # Count TBDs
        tbd_count = result['content'].count('TBD')
        print(f"\n📊 Quality metrics:")
        print(f"   - Total characters: {len(result['content'])}")
        print(f"   - TBD instances: {tbd_count}")
        print(f"   - Labor cost: {result['metadata']['total_labor_cost']}")
        print(f"   - Materials cost: {result['metadata']['total_materials_cost']}")

        if tbd_count < 30:
            print(f"   ✅ TBD count is LOW ({tbd_count}) - Enhancement working!")
        elif tbd_count < 60:
            print(f"   ⚠️  TBD count is MODERATE ({tbd_count}) - Some improvement")
        else:
            print(f"   ❌ TBD count is HIGH ({tbd_count}) - Needs more work")

        # Show first 1000 characters
        print(f"\n📄 Preview (first 1000 chars):")
        print("-"*70)
        print(result['content'][:1000])
        print("-"*70)

        return True
    else:
        print(f"\n❌ IGCE generation failed")
        return False


if __name__ == "__main__":
    success = test_enhanced_igce()
    sys.exit(0 if success else 1)
