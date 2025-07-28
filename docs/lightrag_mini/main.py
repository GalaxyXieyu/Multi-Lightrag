"""
LightRAG Mini - FastAPI Server
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from core import LightRAGMini
from core.utils import EmbeddingFunc
from core.storage import DocStatus

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global RAG instance
rag: Optional[LightRAGMini] = None

# Request/Response models
class TextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: str = Field(default="text_input")

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    mode: str = Field(default="hybrid", regex="^(naive|local|global|hybrid)$")
    top_k: Optional[int] = Field(default=None, ge=1, le=100)

class QueryResponse(BaseModel):
    response: str

class GraphRequest(BaseModel):
    entity_name: Optional[str] = None
    max_depth: int = Field(default=2, ge=1, le=5)
    max_nodes: int = Field(default=100, ge=10, le=1000)

class EntityUpdateRequest(BaseModel):
    entity_name: str
    updated_data: Dict[str, Any]

class RelationUpdateRequest(BaseModel):
    source: str
    target: str
    updated_data: Dict[str, Any]

# LLM Functions
async def openai_llm_func(prompt: str, **kwargs) -> str:
    """OpenAI LLM function"""
    try:
        import openai
        
        # Configure OpenAI client
        api_key = os.getenv("LLM_BINDING_API_KEY")
        base_url = os.getenv("LLM_BINDING_HOST")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=float(os.getenv("TEMPERATURE", "0")),
            max_tokens=int(os.getenv("MAX_TOKENS", "32768")),
            **kwargs
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI LLM error: {str(e)}")
        raise

async def openai_embedding_func(texts: List[str]) -> List[List[float]]:
    """OpenAI embedding function"""
    try:
        import openai
        
        # Configure OpenAI client
        api_key = os.getenv("EMBEDDING_BINDING_API_KEY")
        base_url = os.getenv("EMBEDDING_BINDING_HOST")
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
        client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        response = await client.embeddings.create(
            model=model,
            input=texts
        )
        
        return [item.embedding for item in response.data]
        
    except Exception as e:
        logger.error(f"OpenAI embedding error: {str(e)}")
        raise

def get_llm_func():
    """Get LLM function based on configuration"""
    llm_binding = os.getenv("LLM_BINDING", "openai").lower()
    
    if llm_binding == "openai":
        return openai_llm_func
    else:
        raise ValueError(f"Unsupported LLM binding: {llm_binding}")

def get_embedding_func():
    """Get embedding function based on configuration"""
    embedding_binding = os.getenv("EMBEDDING_BINDING", "openai").lower()
    embedding_dim = int(os.getenv("EMBEDDING_DIM", "1024"))
    max_token_size = int(os.getenv("MAX_EMBED_TOKENS", "8192"))
    
    if embedding_binding == "openai":
        return EmbeddingFunc(
            embedding_dim=embedding_dim,
            max_token_size=max_token_size,
            func=openai_embedding_func
        )
    else:
        raise ValueError(f"Unsupported embedding binding: {embedding_binding}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global rag
    
    # Initialize LightRAG
    try:
        logger.info("Initializing LightRAG Mini...")
        
        rag = LightRAGMini(
            working_dir=os.getenv("WORKING_DIR", "./cache"),
            input_dir=os.getenv("INPUT_DIR", "./inputs"),
            llm_model_func=get_llm_func(),
            llm_model_name=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            embedding_func=get_embedding_func(),
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "1024")),
            chunk_token_size=int(os.getenv("CHUNK_SIZE", "1200")),
            chunk_overlap_token_size=int(os.getenv("CHUNK_OVERLAP_SIZE", "100")),
            max_async=int(os.getenv("MAX_ASYNC", "4")),
            enable_llm_cache=os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true",
            enable_llm_cache_for_extract=os.getenv("ENABLE_LLM_CACHE_FOR_EXTRACT", "true").lower() == "true",
            top_k=int(os.getenv("TOP_K", "60")),
            cosine_threshold=float(os.getenv("COSINE_THRESHOLD", "0.2"))
        )
        
        logger.info("LightRAG Mini initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize LightRAG: {str(e)}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down LightRAG Mini...")

# Create FastAPI app
app = FastAPI(
    title=os.getenv("WEBUI_TITLE", "LightRAG Mini API"),
    description=os.getenv("WEBUI_DESCRIPTION", "Lightweight Graph-based RAG System API"),
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "LightRAG Mini API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        system_info = await rag.get_system_info()
        return {
            "status": "healthy",
            "system_info": system_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload and process a file"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Save uploaded file
        input_dir = Path(rag.input_dir)
        file_path = input_dir / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process file in background
        background_tasks.add_task(process_file_background, file_path)
        
        return {
            "message": f"File '{file.filename}' uploaded successfully. Processing in background.",
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_file_background(file_path: Path):
    """Background task to process uploaded file"""
    try:
        doc_id = await rag.ainsert(file_path)
        logger.info(f"Successfully processed file: {file_path.name}, doc_id: {doc_id}")
    except Exception as e:
        logger.error(f"Error processing file {file_path.name}: {str(e)}")

@app.post("/text")
async def insert_text(request: TextRequest, background_tasks: BackgroundTasks):
    """Insert text content"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Process text in background
        background_tasks.add_task(process_text_background, request.text, request.source)
        
        return {
            "message": "Text content received. Processing in background.",
            "source": request.source
        }
        
    except Exception as e:
        logger.error(f"Error inserting text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_text_background(text: str, source: str):
    """Background task to process text"""
    try:
        doc_id = await rag.ainsert(text, source)
        logger.info(f"Successfully processed text from source: {source}, doc_id: {doc_id}")
    except Exception as e:
        logger.error(f"Error processing text from {source}: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the RAG system"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        response = await rag.aquery(
            query=request.query,
            mode=request.mode,
            top_k=request.top_k
        )
        
        return QueryResponse(response=response)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/graph")
async def get_graph(request: GraphRequest):
    """Get knowledge graph data"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        graph_data = await rag.get_knowledge_graph(
            entity_name=request.entity_name,
            max_depth=request.max_depth,
            max_nodes=request.max_nodes
        )
        
        return graph_data
        
    except Exception as e:
        logger.error(f"Error getting graph data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/stats")
async def get_graph_stats():
    """Get graph statistics"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        stats = await rag.get_graph_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting graph stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_documents():
    """Get document statuses"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        statuses = {}
        for status in DocStatus:
            docs = await rag.get_docs_by_status(status)
            if docs:
                statuses[status.value] = docs
        
        return statuses
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/entity/update")
async def update_entity(request: EntityUpdateRequest):
    """Update entity data"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        success = await rag.update_entity(request.entity_name, request.updated_data)
        
        if success:
            return {"message": f"Entity '{request.entity_name}' updated successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Entity '{request.entity_name}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating entity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/relation/update")
async def update_relation(request: RelationUpdateRequest):
    """Update relationship data"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        success = await rag.update_relationship(
            request.source, 
            request.target, 
            request.updated_data
        )
        
        if success:
            return {"message": f"Relationship '{request.source}'-'{request.target}' updated successfully"}
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Relationship '{request.source}'-'{request.target}' not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/entity/{entity_name}")
async def delete_entity(entity_name: str):
    """Delete an entity"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        success = await rag.delete_entity(entity_name)
        
        if success:
            return {"message": f"Entity '{entity_name}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting entity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/relation/{source}/{target}")
async def delete_relation(source: str, target: str):
    """Delete a relationship"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        success = await rag.delete_relationship(source, target)
        
        if success:
            return {"message": f"Relationship '{source}'-'{target}' deleted successfully"}
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Relationship '{source}'-'{target}' not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/clear")
async def clear_cache():
    """Clear LLM cache"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        await rag.clear_cache()
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )