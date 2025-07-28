"""
LightRAG Mini - Core implementation
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .utils import TiktokenTokenizer, EmbeddingFunc, compute_mdhash_id
from .storage import JsonKVStorage, NanoVectorDB, NetworkXStorage, DocStatusStorage, DocStatus
from .document_processor import DocumentProcessor
from .graph_ops import GraphOperations
from .operate import chunking_by_token_size, extract_entities, naive_query, kg_query

logger = logging.getLogger(__name__)

@dataclass
class LightRAGMini:
    """
    Lightweight RAG system with knowledge graph capabilities
    """
    
    # Directory settings
    working_dir: str = field(default="./cache")
    input_dir: str = field(default="./inputs")
    
    # Model settings
    llm_model_func: Optional[Callable] = field(default=None)
    llm_model_name: str = field(default="gpt-4o-mini")
    llm_model_kwargs: Dict[str, Any] = field(default_factory=dict)
    
    # Embedding settings
    embedding_func: Optional[EmbeddingFunc] = field(default=None)
    embedding_dim: int = field(default=1024)
    
    # Text processing settings
    chunk_token_size: int = field(default=1200)
    chunk_overlap_token_size: int = field(default=100)
    max_async: int = field(default=4)
    
    # Cache settings
    enable_llm_cache: bool = field(default=True)
    enable_llm_cache_for_extract: bool = field(default=True)
    
    # Query settings
    top_k: int = field(default=60)
    cosine_threshold: float = field(default=0.2)
    
    # Internal components
    _tokenizer: Optional[TiktokenTokenizer] = field(default=None, init=False)
    _document_processor: Optional[DocumentProcessor] = field(default=None, init=False)
    _graph_ops: Optional[GraphOperations] = field(default=None, init=False)
    
    # Storage components
    _kv_storage: Optional[JsonKVStorage] = field(default=None, init=False)
    _text_chunks: Optional[JsonKVStorage] = field(default=None, init=False)
    _entities_vdb: Optional[NanoVectorDB] = field(default=None, init=False)
    _relationships_vdb: Optional[NanoVectorDB] = field(default=None, init=False)
    _graph_storage: Optional[NetworkXStorage] = field(default=None, init=False)
    _doc_status: Optional[DocStatusStorage] = field(default=None, init=False)
    _llm_cache: Optional[Dict[str, Any]] = field(default=None, init=False)
    
    def __post_init__(self):
        """Initialize components after instance creation"""
        # Create directories
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)
        Path(self.input_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize tokenizer
        self._tokenizer = TiktokenTokenizer(self.llm_model_name)
        
        # Initialize document processor
        self._document_processor = DocumentProcessor()
        
        # Initialize storage components
        self._init_storage()
        
        # Initialize graph operations
        self._graph_ops = GraphOperations(self._graph_storage, self._entities_vdb)
        
        # Initialize cache
        if self.enable_llm_cache or self.enable_llm_cache_for_extract:
            self._llm_cache = {}
    
    def _init_storage(self):
        """Initialize storage components"""
        storage_dir = Path(self.working_dir)
        
        # Key-value storage for general data
        self._kv_storage = JsonKVStorage(storage_dir / "kv_store.json")
        
        # Text chunks storage
        self._text_chunks = JsonKVStorage(storage_dir / "text_chunks.json")
        
        # Vector databases
        self._entities_vdb = NanoVectorDB(storage_dir / "entities_vdb.pkl", self.embedding_dim)
        self._relationships_vdb = NanoVectorDB(storage_dir / "relationships_vdb.pkl", self.embedding_dim)
        
        # Graph storage
        self._graph_storage = NetworkXStorage(storage_dir / "graph.graphml")
        
        # Document status storage
        self._doc_status = DocStatusStorage(storage_dir / "doc_status.json")
    
    async def ainsert(self, content: Union[str, Path], source: str = "unknown") -> str:
        """
        Insert content (text or file) into the system
        
        Args:
            content: Text content or file path
            source: Source identifier
        
        Returns:
            Document ID
        """
        if self.llm_model_func is None:
            raise ValueError("LLM model function not configured")
        
        try:
            if isinstance(content, (str, Path)) and Path(content).exists():
                # File input
                file_path = Path(content)
                if not self._document_processor.is_supported_file(str(file_path)):
                    raise ValueError(f"Unsupported file type: {file_path.suffix}")
                
                result = await self._document_processor.process_file(
                    file_path=file_path,
                    tokenizer=self._tokenizer,
                    llm_func=self._get_llm_func(),
                    chunk_size=self.chunk_token_size,
                    chunk_overlap=self.chunk_overlap_token_size,
                    cache_storage=self._llm_cache if self.enable_llm_cache_for_extract else None,
                    **self.llm_model_kwargs
                )
            else:
                # Text input
                result = await self._document_processor.process_text(
                    text=str(content),
                    source=source,
                    tokenizer=self._tokenizer,
                    llm_func=self._get_llm_func(),
                    chunk_size=self.chunk_token_size,
                    chunk_overlap=self.chunk_overlap_token_size,
                    cache_storage=self._llm_cache if self.enable_llm_cache_for_extract else None,
                    **self.llm_model_kwargs
                )
            
            if "error" in result:
                raise Exception(result["error"])
            
            doc_id = result["doc_id"]
            
            # Store document status
            await self._doc_status.set_doc_status(doc_id, result["doc_status"])
            
            # Store text chunks
            for i, chunk in enumerate(result["chunks"]):
                chunk_id = f"{doc_id}_chunk_{i}"
                await self._text_chunks.set(chunk_id, chunk)
            
            # Merge and add entities
            entities = await self._graph_ops.merge_entities(result["entities"])
            await self._graph_ops.add_entities(entities, self._get_embedding_func())
            
            # Merge and add relationships
            relationships = await self._graph_ops.merge_relationships(result["relationships"])
            await self._graph_ops.add_relationships(relationships, self._get_embedding_func())
            
            logger.info(f"Successfully processed document {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error inserting content: {str(e)}")
            raise
    
    async def aquery(
        self, 
        query: str, 
        mode: str = "hybrid",
        top_k: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Query the system
        
        Args:
            query: Query text
            mode: Query mode ("naive", "local", "global", "hybrid")
            top_k: Number of top results to return
            **kwargs: Additional arguments
        
        Returns:
            Generated response
        """
        if self.llm_model_func is None:
            raise ValueError("LLM model function not configured")
        
        if top_k is None:
            top_k = self.top_k
        
        try:
            if mode == "naive":
                return await self._naive_query(query, top_k, **kwargs)
            elif mode == "local":
                return await self._local_query(query, top_k, **kwargs)
            elif mode == "global":
                return await self._global_query(query, top_k, **kwargs)
            elif mode == "hybrid":
                return await self._hybrid_query(query, top_k, **kwargs)
            else:
                raise ValueError(f"Unsupported query mode: {mode}")
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    async def _naive_query(self, query: str, top_k: int, **kwargs) -> str:
        """Naive query using text chunks"""
        # Get all text chunks
        all_chunks_data = await self._text_chunks.get_all()
        chunks = list(all_chunks_data.values())
        
        return await naive_query(
            query=query,
            chunks=chunks,
            llm_func=self._get_llm_func(),
            top_k=top_k,
            **self.llm_model_kwargs
        )
    
    async def _local_query(self, query: str, top_k: int, **kwargs) -> str:
        """Local query focusing on entities"""
        # Get entities from graph
        all_entities = await self._graph_ops.get_all_entities()
        entities = []
        
        for entity_name in all_entities:
            entity_data = await self._graph_ops.get_entity(entity_name)
            if entity_data:
                entities.append(entity_data)
        
        return await kg_query(
            query=query,
            entities=entities,
            relationships=[],
            llm_func=self._get_llm_func(),
            top_k=top_k,
            **self.llm_model_kwargs
        )
    
    async def _global_query(self, query: str, top_k: int, **kwargs) -> str:
        """Global query focusing on relationships"""
        # Get relationships from graph
        all_edges = await self._graph_ops.get_all_relationships()
        relationships = []
        
        for source, target in all_edges:
            rel_data = await self._graph_ops.get_relationship(source, target)
            if rel_data:
                rel_data["source"] = source
                rel_data["target"] = target
                relationships.append(rel_data)
        
        return await kg_query(
            query=query,
            entities=[],
            relationships=relationships,
            llm_func=self._get_llm_func(),
            top_k=top_k,
            **self.llm_model_kwargs
        )
    
    async def _hybrid_query(self, query: str, top_k: int, **kwargs) -> str:
        """Hybrid query combining entities and relationships"""
        # Get both entities and relationships
        all_entities = await self._graph_ops.get_all_entities()
        entities = []
        
        for entity_name in all_entities:
            entity_data = await self._graph_ops.get_entity(entity_name)
            if entity_data:
                entities.append(entity_data)
        
        all_edges = await self._graph_ops.get_all_relationships()
        relationships = []
        
        for source, target in all_edges:
            rel_data = await self._graph_ops.get_relationship(source, target)
            if rel_data:
                rel_data["source"] = source
                rel_data["target"] = target
                relationships.append(rel_data)
        
        return await kg_query(
            query=query,
            entities=entities,
            relationships=relationships,
            llm_func=self._get_llm_func(),
            top_k=top_k,
            **self.llm_model_kwargs
        )
    
    async def get_knowledge_graph(
        self, 
        entity_name: Optional[str] = None,
        max_depth: int = 2,
        max_nodes: int = 100
    ) -> Dict[str, Any]:
        """
        Get knowledge graph data
        
        Args:
            entity_name: Starting entity (if None, returns full graph)
            max_depth: Maximum depth for subgraph
            max_nodes: Maximum number of nodes
        
        Returns:
            Graph data with nodes and edges
        """
        if entity_name:
            return await self._graph_ops.get_subgraph(entity_name, max_depth, max_nodes)
        else:
            return await self._graph_ops.export_graph()
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return await self._graph_ops.get_graph_statistics()
    
    async def get_docs_by_status(self, status: DocStatus) -> Dict[str, Any]:
        """Get documents by processing status"""
        return await self._doc_status.get_docs_by_status(status)
    
    async def delete_entity(self, entity_name: str) -> bool:
        """Delete an entity"""
        return await self._graph_ops.delete_entity(entity_name)
    
    async def delete_relationship(self, source: str, target: str) -> bool:
        """Delete a relationship"""
        return await self._graph_ops.delete_relationship(source, target)
    
    async def update_entity(self, entity_name: str, updated_data: Dict[str, Any]) -> bool:
        """Update entity data"""
        return await self._graph_ops.update_entity(
            entity_name, 
            updated_data, 
            self._get_embedding_func()
        )
    
    async def update_relationship(
        self, 
        source: str, 
        target: str, 
        updated_data: Dict[str, Any]
    ) -> bool:
        """Update relationship data"""
        return await self._graph_ops.update_relationship(
            source, 
            target, 
            updated_data,
            self._get_embedding_func()
        )
    
    def _get_llm_func(self) -> Callable:
        """Get LLM function with cache support"""
        if self.enable_llm_cache and self._llm_cache is not None:
            # Return a wrapper that handles caching
            async def cached_llm_func(**kwargs):
                cache_key = str(kwargs)
                if cache_key in self._llm_cache:
                    return self._llm_cache[cache_key]
                
                result = await self.llm_model_func(**kwargs)
                self._llm_cache[cache_key] = result
                return result
            
            return cached_llm_func
        else:
            return self.llm_model_func
    
    def _get_embedding_func(self) -> Optional[Callable]:
        """Get embedding function"""
        if self.embedding_func:
            return self.embedding_func.func
        return None
    
    async def clear_cache(self):
        """Clear LLM cache"""
        if self._llm_cache:
            self._llm_cache.clear()
            logger.info("LLM cache cleared")
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        stats = await self.get_graph_statistics()
        
        return {
            "working_dir": self.working_dir,
            "input_dir": self.input_dir,
            "llm_model": self.llm_model_name,
            "embedding_dim": self.embedding_dim,
            "chunk_size": self.chunk_token_size,
            "chunk_overlap": self.chunk_overlap_token_size,
            "cache_enabled": self.enable_llm_cache,
            "graph_stats": stats
        }