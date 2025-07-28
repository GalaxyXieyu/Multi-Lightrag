"""
Graph operations for LightRAG Mini
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
import logging

from .storage import NetworkXStorage, NanoVectorDB
from .operate import merge_duplicate_entities, merge_duplicate_relationships

logger = logging.getLogger(__name__)

class GraphOperations:
    """Knowledge graph operations"""
    
    def __init__(self, graph_storage: NetworkXStorage, vector_storage: NanoVectorDB):
        self.graph_storage = graph_storage
        self.vector_storage = vector_storage
    
    async def add_entities(self, entities: List[Dict[str, Any]], embedding_func: callable = None):
        """Add entities to the graph"""
        for entity in entities:
            name = entity.get("name", "")
            if not name:
                continue
            
            # Add to graph storage
            await self.graph_storage.add_node(
                node_id=name,
                **entity
            )
            
            # Add to vector storage if embedding function is provided
            if embedding_func:
                try:
                    # Create text for embedding
                    text = f"{name} {entity.get('description', '')}"
                    embeddings = await embedding_func([text])
                    if embeddings and len(embeddings) > 0:
                        await self.vector_storage.upsert(
                            node_id=name,
                            vector=embeddings[0],
                            metadata=entity
                        )
                except Exception as e:
                    logger.error(f"Error creating embedding for entity {name}: {str(e)}")
    
    async def add_relationships(self, relationships: List[Dict[str, Any]], embedding_func: callable = None):
        """Add relationships to the graph"""
        for rel in relationships:
            source = rel.get("source", "")
            target = rel.get("target", "")
            
            if not source or not target:
                continue
            
            # Ensure nodes exist
            if not await self.graph_storage.has_node(source):
                await self.graph_storage.add_node(source, name=source)
            if not await self.graph_storage.has_node(target):
                await self.graph_storage.add_node(target, name=target)
            
            # Add edge
            await self.graph_storage.add_edge(
                source=source,
                target=target,
                **rel
            )
            
            # Add to vector storage if embedding function is provided
            if embedding_func:
                try:
                    # Create text for embedding
                    rel_id = f"{source}->{target}"
                    text = f"{source} {rel.get('relation', '')} {target} {rel.get('description', '')}"
                    embeddings = await embedding_func([text])
                    if embeddings and len(embeddings) > 0:
                        await self.vector_storage.upsert(
                            node_id=rel_id,
                            vector=embeddings[0],
                            metadata=rel
                        )
                except Exception as e:
                    logger.error(f"Error creating embedding for relationship {source}->{target}: {str(e)}")
    
    async def get_entity(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """Get entity by name"""
        return await self.graph_storage.get_node(entity_name)
    
    async def get_relationship(self, source: str, target: str) -> Optional[Dict[str, Any]]:
        """Get relationship between two entities"""
        return await self.graph_storage.get_edge(source, target)
    
    async def get_entity_neighbors(self, entity_name: str) -> List[str]:
        """Get neighbors of an entity"""
        return await self.graph_storage.get_neighbors(entity_name)
    
    async def search_entities(self, query: str, top_k: int = 10) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search entities using vector similarity"""
        # This would require embedding the query and searching
        # For now, return empty list if no embedding function is available
        return []
    
    async def get_subgraph(
        self, 
        entity_name: str, 
        max_depth: int = 2, 
        max_nodes: int = 100
    ) -> Dict[str, Any]:
        """
        Get a subgraph around an entity
        
        Args:
            entity_name: Starting entity
            max_depth: Maximum depth to traverse
            max_nodes: Maximum number of nodes to return
        
        Returns:
            Dictionary containing nodes and edges
        """
        if not await self.graph_storage.has_node(entity_name):
            return {"nodes": [], "edges": []}
        
        visited = set()
        nodes = []
        edges = []
        queue = deque([(entity_name, 0)])  # (node, depth)
        
        while queue and len(nodes) < max_nodes:
            current_node, depth = queue.popleft()
            
            if current_node in visited or depth > max_depth:
                continue
            
            visited.add(current_node)
            
            # Get node data
            node_data = await self.graph_storage.get_node(current_node)
            if node_data:
                nodes.append({
                    "id": current_node,
                    "label": current_node,
                    **node_data
                })
            
            # Get neighbors
            if depth < max_depth:
                neighbors = await self.graph_storage.get_neighbors(current_node)
                for neighbor in neighbors:
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
                    
                    # Get edge data
                    edge_data = await self.graph_storage.get_edge(current_node, neighbor)
                    if edge_data:
                        edges.append({
                            "source": current_node,
                            "target": neighbor,
                            **edge_data
                        })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    async def get_all_entities(self) -> List[str]:
        """Get all entity names"""
        return await self.graph_storage.get_all_nodes()
    
    async def get_all_relationships(self) -> List[Tuple[str, str]]:
        """Get all relationships (source, target pairs)"""
        return await self.graph_storage.get_all_edges()
    
    async def delete_entity(self, entity_name: str) -> bool:
        """Delete an entity and its relationships"""
        try:
            if await self.graph_storage.has_node(entity_name):
                await self.graph_storage.delete_node(entity_name)
                await self.vector_storage.delete(entity_name)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting entity {entity_name}: {str(e)}")
            return False
    
    async def delete_relationship(self, source: str, target: str) -> bool:
        """Delete a relationship"""
        try:
            if await self.graph_storage.has_edge(source, target):
                await self.graph_storage.delete_edge(source, target)
                rel_id = f"{source}->{target}"
                await self.vector_storage.delete(rel_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting relationship {source}->{target}: {str(e)}")
            return False
    
    async def update_entity(
        self, 
        entity_name: str, 
        updated_data: Dict[str, Any],
        embedding_func: callable = None
    ) -> bool:
        """Update entity data"""
        try:
            current_data = await self.graph_storage.get_node(entity_name)
            if not current_data:
                return False
            
            # Merge with updated data
            merged_data = {**current_data, **updated_data}
            
            # Update in graph storage
            await self.graph_storage.add_node(entity_name, **merged_data)
            
            # Update in vector storage if embedding function provided
            if embedding_func:
                try:
                    text = f"{entity_name} {merged_data.get('description', '')}"
                    embeddings = await embedding_func([text])
                    if embeddings and len(embeddings) > 0:
                        await self.vector_storage.upsert(
                            node_id=entity_name,
                            vector=embeddings[0],
                            metadata=merged_data
                        )
                except Exception as e:
                    logger.error(f"Error updating embedding for entity {entity_name}: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error updating entity {entity_name}: {str(e)}")
            return False
    
    async def update_relationship(
        self,
        source: str,
        target: str,
        updated_data: Dict[str, Any],
        embedding_func: callable = None
    ) -> bool:
        """Update relationship data"""
        try:
            current_data = await self.graph_storage.get_edge(source, target)
            if not current_data:
                return False
            
            # Merge with updated data
            merged_data = {**current_data, **updated_data}
            
            # Update in graph storage
            await self.graph_storage.add_edge(source, target, **merged_data)
            
            # Update in vector storage if embedding function provided
            if embedding_func:
                try:
                    rel_id = f"{source}->{target}"
                    text = f"{source} {merged_data.get('relation', '')} {target} {merged_data.get('description', '')}"
                    embeddings = await embedding_func([text])
                    if embeddings and len(embeddings) > 0:
                        await self.vector_storage.upsert(
                            node_id=rel_id,
                            vector=embeddings[0],
                            metadata=merged_data
                        )
                except Exception as e:
                    logger.error(f"Error updating embedding for relationship {source}->{target}: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error updating relationship {source}->{target}: {str(e)}")
            return False
    
    async def merge_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge duplicate entities"""
        return merge_duplicate_entities(entities)
    
    async def merge_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge duplicate relationships"""
        return merge_duplicate_relationships(relationships)
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        all_nodes = await self.get_all_entities()
        all_edges = await self.get_all_relationships()
        
        return {
            "total_entities": len(all_nodes),
            "total_relationships": len(all_edges),
            "entity_names": all_nodes[:10] if len(all_nodes) > 10 else all_nodes  # Sample
        }
    
    async def export_graph(self) -> Dict[str, Any]:
        """Export the entire graph"""
        nodes = []
        edges = []
        
        # Get all nodes
        all_node_ids = await self.get_all_entities()
        for node_id in all_node_ids:
            node_data = await self.graph_storage.get_node(node_id)
            if node_data:
                nodes.append({
                    "id": node_id,
                    "label": node_id,
                    **node_data
                })
        
        # Get all edges
        all_edges = await self.get_all_relationships()
        for source, target in all_edges:
            edge_data = await self.graph_storage.get_edge(source, target)
            if edge_data:
                edges.append({
                    "source": source,
                    "target": target,
                    **edge_data
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }