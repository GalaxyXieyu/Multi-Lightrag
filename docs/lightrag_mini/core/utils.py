"""
Utility functions for LightRAG Mini
"""

import re
import json
import hashlib
import logging
import tiktoken
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class EmbeddingFunc:
    """Embedding function wrapper"""
    embedding_dim: int
    max_token_size: int
    func: callable

class TiktokenTokenizer:
    """Tiktoken-based tokenizer"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base encoding
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def encode(self, text: str) -> List[int]:
        """Encode text to tokens"""
        return self.encoding.encode(text)
    
    def decode(self, tokens: List[int]) -> str:
        """Decode tokens to text"""
        return self.encoding.decode(tokens)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encode(text))

def compute_mdhash_id(content: str) -> str:
    """Compute MD5 hash ID for content"""
    return hashlib.md5(content.encode()).hexdigest()

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.,;:!?()-]', '', text)
    return text.strip()

def get_content_summary(text: str, max_length: int = 100) -> str:
    """Get a summary of content for display"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def convert_response_to_json(response: str) -> Dict[str, Any]:
    """Convert LLM response to JSON format"""
    try:
        # Try to parse as JSON directly
        return json.loads(response)
    except json.JSONDecodeError:
        # Extract JSON from code blocks or other formats
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON-like structure
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Fallback: return as text
        return {"content": response}

def pack_user_ass_to_openai_messages(user: str, assistant: str) -> List[Dict[str, str]]:
    """Pack user and assistant messages to OpenAI format"""
    return [
        {"role": "user", "content": user},
        {"role": "assistant", "content": assistant}
    ]

def split_string_by_multi_markers(text: str, markers: List[str]) -> List[str]:
    """Split text by multiple markers"""
    if not markers:
        return [text]
    
    pattern = '|'.join(re.escape(marker) for marker in markers)
    parts = re.split(pattern, text)
    return [part.strip() for part in parts if part.strip()]

def normalize_extracted_info(info: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize extracted entity/relation information"""
    normalized = {}
    for key, value in info.items():
        if isinstance(value, str):
            normalized[key] = clean_text(value)
        elif isinstance(value, list):
            normalized[key] = [clean_text(str(v)) if isinstance(v, str) else v for v in value]
        else:
            normalized[key] = value
    return normalized

async def use_llm_func_with_cache(
    llm_func: callable,
    cache_key: str,
    cache_storage: Optional[Dict] = None,
    **kwargs
) -> str:
    """Use LLM function with caching support"""
    # Check cache first
    if cache_storage and cache_key in cache_storage:
        return cache_storage[cache_key]
    
    # Call LLM function
    result = await llm_func(**kwargs)
    
    # Store in cache
    if cache_storage is not None:
        cache_storage[cache_key] = result
    
    return result