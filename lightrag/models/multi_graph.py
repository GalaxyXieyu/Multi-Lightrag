"""
多图谱支持的数据模型定义
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class GraphStatus(str, Enum):
    """图谱状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class GraphMetadata:
    """图谱元数据模型"""
    graph_id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    working_dir: str = ""
    status: GraphStatus = GraphStatus.ACTIVE
    is_active: bool = False
    entity_count: int = 0
    relation_count: int = 0
    document_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "graph_id": self.graph_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "working_dir": self.working_dir,
            "status": self.status.value,
            "is_active": self.is_active,
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "document_count": self.document_count,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GraphMetadata:
        """从字典创建实例"""
        return cls(
            graph_id=data["graph_id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data["updated_at"], str) else data["updated_at"],
            working_dir=data.get("working_dir", ""),
            status=GraphStatus(data.get("status", GraphStatus.ACTIVE.value)),
            is_active=data.get("is_active", False),
            entity_count=data.get("entity_count", 0),
            relation_count=data.get("relation_count", 0),
            document_count=data.get("document_count", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class ExtendedDocProcessingStatus:
    """扩展的文档处理状态，支持多图谱"""
    # 原有字段
    content: str
    content_summary: str
    content_length: int
    file_path: str
    status: str  # DocStatus
    created_at: str
    updated_at: str
    chunks_count: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 新增字段：图谱关联
    graph_id: str = "default"
    graph_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "content_summary": self.content_summary,
            "content_length": self.content_length,
            "file_path": self.file_path,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "chunks_count": self.chunks_count,
            "error": self.error,
            "metadata": self.metadata,
            "graph_id": self.graph_id,
            "graph_name": self.graph_name
        }


@dataclass
class ExtendedEntityData:
    """扩展的实体数据，支持多图谱"""
    entity_name: str
    entity_type: str = "UNKNOWN"
    description: str = ""
    source_id: str = ""
    file_path: str = ""
    created_at: Optional[str] = None
    
    # 新增字段：图谱关联
    graph_id: str = "default"
    graph_name: Optional[str] = None
    
    # 向量和其他数据
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "description": self.description,
            "source_id": self.source_id,
            "file_path": self.file_path,
            "created_at": self.created_at,
            "graph_id": self.graph_id,
            "graph_name": self.graph_name,
            "embedding": self.embedding,
            "metadata": self.metadata
        }


@dataclass
class ExtendedRelationshipData:
    """扩展的关系数据，支持多图谱"""
    src_id: str
    tgt_id: str
    description: str = ""
    weight: float = 1.0
    keywords: List[str] = field(default_factory=list)
    source_id: str = ""
    file_path: str = ""
    created_at: Optional[str] = None
    
    # 新增字段：图谱关联
    graph_id: str = "default"
    graph_name: Optional[str] = None
    
    # 其他数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "src_id": self.src_id,
            "tgt_id": self.tgt_id,
            "description": self.description,
            "weight": self.weight,
            "keywords": self.keywords,
            "source_id": self.source_id,
            "file_path": self.file_path,
            "created_at": self.created_at,
            "graph_id": self.graph_id,
            "graph_name": self.graph_name,
            "metadata": self.metadata
        }


# Pydantic 模型用于API接口
class GraphMetadataResponse(BaseModel):
    """图谱元数据响应模型"""
    graph_id: str = Field(..., description="图谱唯一标识")
    name: str = Field(..., description="图谱名称")
    description: str = Field("", description="图谱描述")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    working_dir: str = Field(..., description="工作目录")
    status: str = Field(..., description="图谱状态")
    is_active: bool = Field(False, description="是否为当前活跃图谱")
    entity_count: int = Field(0, description="实体数量")
    relation_count: int = Field(0, description="关系数量")
    document_count: int = Field(0, description="文档数量")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "graph_id": "medical_kg",
                "name": "医学知识图谱",
                "description": "用于存储医学相关的实体和关系",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "working_dir": "./graphs/medical_kg",
                "status": "active",
                "is_active": True,
                "entity_count": 1250,
                "relation_count": 3400,
                "document_count": 45,
                "metadata": {}
            }
        }


class GraphCreateRequest(BaseModel):
    """创建图谱请求模型"""
    name: str = Field(..., description="图谱名称", min_length=1, max_length=100)
    description: str = Field("", description="图谱描述", max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "医学知识图谱",
                "description": "用于存储医学相关的实体和关系",
                "metadata": {
                    "domain": "medical",
                    "language": "zh-CN"
                }
            }
        }


class GraphUpdateRequest(BaseModel):
    """更新图谱请求模型"""
    name: Optional[str] = Field(None, description="图谱名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="图谱描述", max_length=500)
    status: Optional[str] = Field(None, description="图谱状态")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class GraphListResponse(BaseModel):
    """图谱列表响应模型"""
    status: str = Field("success", description="响应状态")
    graphs: List[GraphMetadataResponse] = Field([], description="图谱列表")
    total: int = Field(0, description="图谱总数")
    current_graph: Optional[str] = Field(None, description="当前活跃图谱ID")


class GraphOperationResponse(BaseModel):
    """图谱操作响应模型"""
    status: str = Field("success", description="操作状态")
    message: str = Field("", description="操作消息")
    graph_id: Optional[str] = Field(None, description="图谱ID")
    graph_info: Optional[GraphMetadataResponse] = Field(None, description="图谱信息")
