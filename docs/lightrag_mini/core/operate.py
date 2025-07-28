"""
Core operations for text chunking and entity extraction
"""

import json
import re
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from .utils import (
    TiktokenTokenizer, 
    convert_response_to_json, 
    normalize_extracted_info,
    clean_text,
    use_llm_func_with_cache
)

# Default prompts for entity extraction
ENTITY_EXTRACTION_PROMPT = """
从以下文本中提取关键实体和它们之间的关系。请以JSON格式返回结果：

```json
{
  "entities": [
    {
      "name": "实体名称",
      "type": "实体类型", 
      "description": "实体描述"
    }
  ],
  "relationships": [
    {
      "source": "源实体",
      "target": "目标实体", 
      "relation": "关系类型",
      "description": "关系描述"
    }
  ]
}
```

文本内容：
{content}

请确保提取的实体和关系准确且相关。
"""

QUERY_PROMPT = """
基于以下知识图谱信息，回答用户的问题：

知识图谱信息：
{context}

用户问题：{query}

请基于提供的信息给出准确、详细的回答。如果信息不足以回答问题，请说明。
"""

def chunking_by_token_size(
    tokenizer: TiktokenTokenizer,
    content: str,
    split_by_character: Optional[str] = None,
    split_by_character_only: bool = False,
    overlap_token_size: int = 128,
    max_token_size: int = 1024,
) -> List[Dict[str, Any]]:
    """
    Split text into chunks by token size
    
    Args:
        tokenizer: Tokenizer instance
        content: Text content to split
        split_by_character: Character to split by (optional)
        split_by_character_only: Whether to split only by character
        overlap_token_size: Number of overlapping tokens
        max_token_size: Maximum tokens per chunk
    
    Returns:
        List of chunk dictionaries with content, tokens, and chunk_order_index
    """
    tokens = tokenizer.encode(content)
    results: List[Dict[str, Any]] = []
    
    if split_by_character:
        raw_chunks = content.split(split_by_character)
        new_chunks = []
        
        if split_by_character_only:
            for chunk in raw_chunks:
                _tokens = tokenizer.encode(chunk)
                new_chunks.append((len(_tokens), chunk))
        else:
            for chunk in raw_chunks:
                _tokens = tokenizer.encode(chunk)
                if len(_tokens) > max_token_size:
                    # Further split large chunks
                    for start in range(0, len(_tokens), max_token_size - overlap_token_size):
                        chunk_content = tokenizer.decode(_tokens[start:start + max_token_size])
                        new_chunks.append((min(max_token_size, len(_tokens) - start), chunk_content))
                else:
                    new_chunks.append((len(_tokens), chunk))
        
        for index, (_len, chunk) in enumerate(new_chunks):
            results.append({
                "tokens": _len,
                "content": chunk.strip(),
                "chunk_order_index": index,
            })
    else:
        # Split by token size directly
        for index, start in enumerate(range(0, len(tokens), max_token_size - overlap_token_size)):
            chunk_content = tokenizer.decode(tokens[start:start + max_token_size])
            results.append({
                "tokens": min(max_token_size, len(tokens) - start),
                "content": chunk_content.strip(),
                "chunk_order_index": index,
            })
    
    return results

async def extract_entities(
    llm_func: callable,
    chunk_content: str,
    chunk_id: str,
    cache_storage: Optional[Dict] = None,
    prompt_template: str = ENTITY_EXTRACTION_PROMPT,
    **llm_kwargs
) -> Dict[str, Any]:
    """
    Extract entities and relationships from text chunk
    
    Args:
        llm_func: LLM function to call
        chunk_content: Text content to process
        chunk_id: Unique identifier for the chunk
        cache_storage: Optional cache storage
        prompt_template: Prompt template for extraction
        **llm_kwargs: Additional LLM arguments
    
    Returns:
        Dictionary containing extracted entities and relationships
    """
    # Create cache key
    cache_key = f"entity_extract_{chunk_id}"
    
    # Prepare prompt
    prompt = prompt_template.format(content=chunk_content)
    
    # Call LLM with caching
    response = await use_llm_func_with_cache(
        llm_func=llm_func,
        cache_key=cache_key,
        cache_storage=cache_storage,
        prompt=prompt,
        **llm_kwargs
    )
    
    # Convert response to JSON
    try:
        result = convert_response_to_json(response)
        
        # Normalize extracted information
        if "entities" in result:
            result["entities"] = [normalize_extracted_info(entity) for entity in result["entities"]]
        if "relationships" in result:
            result["relationships"] = [normalize_extracted_info(rel) for rel in result["relationships"]]
        
        return result
    except Exception as e:
        print(f"Error parsing entity extraction result: {e}")
        return {"entities": [], "relationships": []}

async def naive_query(
    query: str,
    chunks: List[Dict[str, Any]],
    llm_func: callable,
    top_k: int = 5,
    **llm_kwargs
) -> str:
    """
    Naive query using simple text matching
    
    Args:
        query: User query
        chunks: List of text chunks
        llm_func: LLM function for generating response
        top_k: Number of top chunks to use
        **llm_kwargs: Additional LLM arguments
    
    Returns:
        Generated response
    """
    # Simple keyword matching
    query_lower = query.lower()
    scored_chunks = []
    
    for chunk in chunks:
        content = chunk.get("content", "").lower()
        # Calculate simple overlap score
        query_words = set(query_lower.split())
        content_words = set(content.split())
        overlap = len(query_words & content_words)
        if overlap > 0:
            scored_chunks.append((chunk, overlap))
    
    # Sort by score and take top_k
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for chunk, _ in scored_chunks[:top_k]]
    
    # Prepare context
    context = "\n\n".join([chunk.get("content", "") for chunk in top_chunks])
    
    # Generate response
    prompt = QUERY_PROMPT.format(context=context, query=query)
    response = await llm_func(prompt=prompt, **llm_kwargs)
    
    return response

async def kg_query(
    query: str,
    entities: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    llm_func: callable,
    top_k: int = 10,
    **llm_kwargs
) -> str:
    """
    Knowledge graph-based query
    
    Args:
        query: User query
        entities: List of entities
        relationships: List of relationships
        llm_func: LLM function for generating response
        top_k: Number of top entities/relationships to use
        **llm_kwargs: Additional LLM arguments
    
    Returns:
        Generated response
    """
    query_lower = query.lower()
    
    # Find relevant entities
    relevant_entities = []
    for entity in entities:
        entity_name = entity.get("name", "").lower()
        entity_desc = entity.get("description", "").lower()
        if query_lower in entity_name or any(word in entity_desc for word in query_lower.split()):
            relevant_entities.append(entity)
    
    # Find relevant relationships
    relevant_relationships = []
    entity_names = {entity.get("name", "").lower() for entity in relevant_entities}
    
    for rel in relationships:
        source = rel.get("source", "").lower()
        target = rel.get("target", "").lower()
        rel_desc = rel.get("description", "").lower()
        
        if (source in entity_names or target in entity_names or 
            any(word in rel_desc for word in query_lower.split())):
            relevant_relationships.append(rel)
    
    # Prepare context
    context_parts = []
    
    if relevant_entities:
        entities_text = "\n".join([
            f"- {entity.get('name', '')}: {entity.get('description', '')}"
            for entity in relevant_entities[:top_k]
        ])
        context_parts.append(f"相关实体：\n{entities_text}")
    
    if relevant_relationships:
        relationships_text = "\n".join([
            f"- {rel.get('source', '')} -> {rel.get('target', '')}: {rel.get('description', '')}"
            for rel in relevant_relationships[:top_k]
        ])
        context_parts.append(f"相关关系：\n{relationships_text}")
    
    context = "\n\n".join(context_parts) if context_parts else "未找到相关的知识图谱信息。"
    
    # Generate response
    prompt = QUERY_PROMPT.format(context=context, query=query)
    response = await llm_func(prompt=prompt, **llm_kwargs)
    
    return response

def merge_duplicate_entities(entities: List[Dict[str, Any]], similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
    """
    Merge duplicate entities based on name similarity
    
    Args:
        entities: List of entity dictionaries
        similarity_threshold: Similarity threshold for merging
    
    Returns:
        List of merged entities
    """
    if not entities:
        return []
    
    merged = []
    processed = set()
    
    for i, entity in enumerate(entities):
        if i in processed:
            continue
            
        # Find similar entities
        similar_entities = [entity]
        entity_name = entity.get("name", "").lower()
        
        for j, other_entity in enumerate(entities[i+1:], i+1):
            if j in processed:
                continue
                
            other_name = other_entity.get("name", "").lower()
            
            # Simple string similarity check
            if entity_name == other_name or entity_name in other_name or other_name in entity_name:
                similar_entities.append(other_entity)
                processed.add(j)
        
        # Merge similar entities
        if len(similar_entities) == 1:
            merged.append(entity)
        else:
            # Merge descriptions and other attributes
            merged_entity = {
                "name": entity.get("name", ""),
                "type": entity.get("type", ""),
                "description": "; ".join([e.get("description", "") for e in similar_entities if e.get("description")])
            }
            merged.append(merged_entity)
        
        processed.add(i)
    
    return merged

def merge_duplicate_relationships(relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge duplicate relationships
    
    Args:
        relationships: List of relationship dictionaries
    
    Returns:
        List of merged relationships
    """
    if not relationships:
        return []
    
    # Group by source-target pairs
    rel_groups = {}
    
    for rel in relationships:
        source = rel.get("source", "").lower()
        target = rel.get("target", "").lower()
        key = f"{source}->{target}"
        
        if key not in rel_groups:
            rel_groups[key] = []
        rel_groups[key].append(rel)
    
    # Merge relationships in each group
    merged = []
    for group in rel_groups.values():
        if len(group) == 1:
            merged.append(group[0])
        else:
            # Merge descriptions
            merged_rel = {
                "source": group[0].get("source", ""),
                "target": group[0].get("target", ""),
                "relation": group[0].get("relation", ""),
                "description": "; ".join([r.get("description", "") for r in group if r.get("description")])
            }
            merged.append(merged_rel)
    
    return merged