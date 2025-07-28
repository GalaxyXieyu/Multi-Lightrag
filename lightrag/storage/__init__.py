"""
LightRAG 多图谱存储模块
"""

from .multi_graph_storage import (
    MultiGraphStorageManager,
    get_storage_manager,
    initialize_multi_graph_storage
)

__all__ = [
    "MultiGraphStorageManager",
    "get_storage_manager", 
    "initialize_multi_graph_storage"
]
