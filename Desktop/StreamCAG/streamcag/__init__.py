"""
StreamCAG: Streamlined Cache-Augmented Generation
An intelligent caching system for LLMs that optimizes context management.
"""

from .core import StreamCAG
from .cache import SemanticCache, PersistentCache
from .optimizer import ContextOptimizer

__version__ = "0.1.0"
__all__ = ["StreamCAG", "SemanticCache", "PersistentCache", "ContextOptimizer"]
