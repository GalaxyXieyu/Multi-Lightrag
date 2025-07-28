"""
LightRAG Mini - Lightweight Graph-based RAG System
"""

from .lightrag import LightRAGMini
from .document_processor import DocumentProcessor
from .graph_ops import GraphOperations

__version__ = "0.1.0"
__all__ = ["LightRAGMini", "DocumentProcessor", "GraphOperations"]