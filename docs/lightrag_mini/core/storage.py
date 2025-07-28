"""
Simplified storage implementations for LightRAG Mini
"""

import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import networkx as nx
from dataclasses import dataclass, asdict
from enum import Enum

class DocStatus(Enum):
    """Document processing status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

@dataclass
class DocProcessingStatus:
    """Document processing status information"""
    content_summary: str
    content_length: int
    status: DocStatus
    created_at: str
    updated_at: str
    chunks_count: Optional[int] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    file_path: str = ""

@dataclass
class TextChunkSchema:
    """Text chunk schema"""
    content: str
    chunk_order_index: int
    tokens: int

class JsonKVStorage:
    """Simple JSON-based key-value storage"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load data from file"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save(self):
        """Save data to file"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
    
    async def set(self, key: str, value: Any):
        """Set key-value pair"""
        self._data[key] = value
        self._save()
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value by key"""
        return self._data.get(key, default)
    
    async def delete(self, key: str):
        """Delete key"""
        if key in self._data:
            del self._data[key]
            self._save()
    
    async def has(self, key: str) -> bool:
        """Check if key exists"""
        return key in self._data
    
    async def get_all(self) -> Dict[str, Any]:
        """Get all key-value pairs"""
        return self._data.copy()

class NanoVectorDB:
    """Simple vector database using numpy for similarity search"""
    
    def __init__(self, file_path: str, embedding_dim: int = 1024):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_dim = embedding_dim
        self._vectors = {}
        self._metadata = {}
        self._load()
    
    def _load(self):
        """Load vectors from file"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'rb') as f:
                    data = pickle.load(f)
                    self._vectors = data.get('vectors', {})
                    self._metadata = data.get('metadata', {})
            except (pickle.PickleError, IOError):
                self._vectors = {}
                self._metadata = {}
    
    def _save(self):
        """Save vectors to file"""
        data = {
            'vectors': self._vectors,
            'metadata': self._metadata
        }
        with open(self.file_path, 'wb') as f:
            pickle.dump(data, f)
    
    async def upsert(self, node_id: str, vector: List[float], metadata: Dict[str, Any] = None):
        """Insert or update vector"""
        self._vectors[node_id] = vector
        self._metadata[node_id] = metadata or {}
        self._save()
    
    async def query(self, query_vector: List[float], top_k: int = 10) -> List[tuple]:
        """Query similar vectors"""
        import numpy as np
        
        if not self._vectors:
            return []
        
        query_np = np.array(query_vector)
        similarities = []
        
        for node_id, vector in self._vectors.items():
            vector_np = np.array(vector)
            # Cosine similarity
            similarity = np.dot(query_np, vector_np) / (np.linalg.norm(query_np) * np.linalg.norm(vector_np))
            similarities.append((node_id, similarity, self._metadata.get(node_id, {})))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    async def delete(self, node_id: str):
        """Delete vector"""
        if node_id in self._vectors:
            del self._vectors[node_id]
        if node_id in self._metadata:
            del self._metadata[node_id]
        self._save()

class NetworkXStorage:
    """NetworkX-based graph storage"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._graph = nx.DiGraph()
        self._load()
    
    def _load(self):
        """Load graph from file"""
        if self.file_path.exists():
            try:
                self._graph = nx.read_graphml(str(self.file_path))
            except Exception:
                self._graph = nx.DiGraph()
    
    def _save(self):
        """Save graph to file"""
        try:
            nx.write_graphml(self._graph, str(self.file_path))
        except Exception:
            # Fallback to pickle if GraphML fails
            pickle_path = str(self.file_path).replace('.graphml', '.pkl')
            with open(pickle_path, 'wb') as f:
                pickle.dump(self._graph, f)
    
    async def add_node(self, node_id: str, **attributes):
        """Add node to graph"""
        self._graph.add_node(node_id, **attributes)
        self._save()
    
    async def add_edge(self, source: str, target: str, **attributes):
        """Add edge to graph"""
        self._graph.add_edge(source, target, **attributes)
        self._save()
    
    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node attributes"""
        if self._graph.has_node(node_id):
            return dict(self._graph.nodes[node_id])
        return None
    
    async def get_edge(self, source: str, target: str) -> Optional[Dict[str, Any]]:
        """Get edge attributes"""
        if self._graph.has_edge(source, target):
            return dict(self._graph.edges[source, target])
        return None
    
    async def get_neighbors(self, node_id: str) -> List[str]:
        """Get node neighbors"""
        if self._graph.has_node(node_id):
            return list(self._graph.neighbors(node_id))
        return []
    
    async def get_all_nodes(self) -> List[str]:
        """Get all node IDs"""
        return list(self._graph.nodes())
    
    async def get_all_edges(self) -> List[tuple]:
        """Get all edges"""
        return list(self._graph.edges())
    
    async def delete_node(self, node_id: str):
        """Delete node"""
        if self._graph.has_node(node_id):
            self._graph.remove_node(node_id)
            self._save()
    
    async def delete_edge(self, source: str, target: str):
        """Delete edge"""
        if self._graph.has_edge(source, target):
            self._graph.remove_edge(source, target)
            self._save()
    
    async def has_node(self, node_id: str) -> bool:
        """Check if node exists"""
        return self._graph.has_node(node_id)
    
    async def has_edge(self, source: str, target: str) -> bool:
        """Check if edge exists"""
        return self._graph.has_edge(source, target)

class DocStatusStorage:
    """Document status storage"""
    
    def __init__(self, file_path: str):
        self.storage = JsonKVStorage(file_path)
    
    async def set_doc_status(self, doc_id: str, status: DocProcessingStatus):
        """Set document status"""
        await self.storage.set(doc_id, asdict(status))
    
    async def get_doc_status(self, doc_id: str) -> Optional[DocProcessingStatus]:
        """Get document status"""
        data = await self.storage.get(doc_id)
        if data:
            # Convert status string back to enum
            data['status'] = DocStatus(data['status'])
            return DocProcessingStatus(**data)
        return None
    
    async def get_docs_by_status(self, status: DocStatus) -> Dict[str, DocProcessingStatus]:
        """Get documents by status"""
        all_docs = await self.storage.get_all()
        result = {}
        for doc_id, doc_data in all_docs.items():
            if doc_data.get('status') == status.value:
                doc_data['status'] = status
                result[doc_id] = DocProcessingStatus(**doc_data)
        return result
    
    async def delete_doc_status(self, doc_id: str):
        """Delete document status"""
        await self.storage.delete(doc_id)