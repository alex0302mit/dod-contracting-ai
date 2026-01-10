"""
Core Processing Modules

Core functionality for document processing and evaluation:
- Market research generation
- Document evaluation and quality assessment
- Citation management
"""

from backend.core.market_research import MarketResearchFiller
from backend.core.evaluate_report import ReportEvaluator
from backend.core.add_citations import CitationInjector

__all__ = [
    'MarketResearchFiller',
    'ReportEvaluator',
    'CitationInjector',
]
