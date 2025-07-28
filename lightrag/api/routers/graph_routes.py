"""
This module contains all graph-related routes for the LightRAG API.
"""

from typing import Optional, Dict, Any, List
import traceback
import shutil
import json
import os
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from lightrag.utils import logger
from ..utils_api import get_combined_auth_dependency

# 导入多图谱支持的数据模型
try:
    from lightrag.models.multi_graph import (
        GraphMetadata,
        GraphStatus,
        GraphCreateRequest as MultiGraphCreateRequest,
        GraphUpdateRequest,
        GraphMetadataResponse,
        GraphListResponse,
        GraphOperationResponse,
        ExtendedDocProcessingStatus,
        ExtendedEntityData,
        ExtendedRelationshipData
    )
    MULTI_GRAPH_SUPPORT = True
except ImportError:
    # 如果新模型不可用，使用现有模型
    MULTI_GRAPH_SUPPORT = False
    logger.warning("多图谱模型不可用，使用现有模型")

router = APIRouter(tags=["graph"])





class EntityUpdateRequest(BaseModel):
    entity_name: str
    updated_data: Dict[str, Any]
    allow_rename: bool = False


class RelationUpdateRequest(BaseModel):
    source_id: str
    target_id: str
    updated_data: Dict[str, Any]


# 多图谱管理相关的请求模型
class GraphCreateRequest(BaseModel):
    """创建新图谱的请求模型"""
    name: str = Field(..., description="图谱名称", min_length=1, max_length=100)
    description: str = Field("", description="图谱描述", max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "医学知识图谱",
                "description": "用于存储医学相关的实体和关系"
            }
        }


class GraphInfo(BaseModel):
    """图谱信息模型"""
    name: str = Field(..., description="图谱名称")
    description: str = Field("", description="图谱描述")
    working_dir: str = Field(..., description="工作目录路径")
    created_at: str = Field(..., description="创建时间")
    is_active: bool = Field(False, description="是否为当前活跃图谱")
    entity_count: int = Field(0, description="实体数量")
    relation_count: int = Field(0, description="关系数量")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "医学知识图谱",
                "description": "用于存储医学相关的实体和关系",
                "working_dir": "./graphs/medical_kg",
                "created_at": "2024-01-15T10:30:00Z",
                "is_active": True,
                "entity_count": 1250,
                "relation_count": 3400
            }
        }


class NodeCreateRequest(BaseModel):
    """手动创建节点的请求模型"""
    entity_name: str = Field(..., description="实体名称", min_length=1, max_length=200)
    entity_type: str = Field("", description="实体类型", max_length=100)
    description: str = Field("", description="实体描述", max_length=1000)
    source_id: str = Field("manual", description="数据源ID")
    file_path: str = Field("manual_input", description="文件路径")

    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "阿司匹林",
                "entity_type": "药物",
                "description": "一种常用的解热镇痛药，具有抗炎、解热、镇痛的作用",
                "source_id": "manual_drug_001",
                "file_path": "manual_input"
            }
        }


class NodeBatchCreateRequest(BaseModel):
    """批量创建节点的请求模型"""
    nodes: List[NodeCreateRequest] = Field(..., description="节点列表", min_items=1, max_items=100)

    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [
                    {
                        "entity_name": "阿司匹林",
                        "entity_type": "药物",
                        "description": "一种常用的解热镇痛药",
                        "source_id": "manual_drug_001",
                        "file_path": "manual_input"
                    },
                    {
                        "entity_name": "心脏病",
                        "entity_type": "疾病",
                        "description": "影响心脏功能的疾病",
                        "source_id": "manual_disease_001",
                        "file_path": "manual_input"
                    }
                ]
            }
        }


class RelationCreateRequest(BaseModel):
    """手动创建关系的请求模型"""
    source_entity: str = Field(..., description="源实体名称", min_length=1, max_length=200)
    target_entity: str = Field(..., description="目标实体名称", min_length=1, max_length=200)
    description: str = Field("", description="关系描述", max_length=1000)
    keywords: str = Field("", description="关系关键词", max_length=500)
    weight: float = Field(1.0, description="关系权重", ge=0.0, le=10.0)
    source_id: str = Field("manual", description="数据源ID")
    file_path: str = Field("manual_input", description="文件路径")

    class Config:
        json_schema_extra = {
            "example": {
                "source_entity": "阿司匹林",
                "target_entity": "心脏病",
                "description": "阿司匹林可用于预防心脏病",
                "keywords": "预防 治疗 药物",
                "weight": 2.5,
                "source_id": "manual_relation_001",
                "file_path": "manual_input"
            }
        }


class RelationBatchCreateRequest(BaseModel):
    """批量创建关系的请求模型"""
    relations: List[RelationCreateRequest] = Field(..., description="关系列表", min_items=1, max_items=100)

    class Config:
        json_schema_extra = {
            "example": {
                "relations": [
                    {
                        "source_entity": "阿司匹林",
                        "target_entity": "心脏病",
                        "description": "阿司匹林可用于预防心脏病",
                        "keywords": "预防 治疗",
                        "weight": 2.5,
                        "source_id": "manual_relation_001",
                        "file_path": "manual_input"
                    }
                ]
            }
        }


# 全局变量存储图谱管理器
_graph_manager = None


class GraphManager:
    """多图谱管理器"""

    def __init__(self, base_dir: str = "./graphs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.graphs_config_file = self.base_dir / "graphs_config.json"
        self.current_rag = None
        self.current_graph_id = None  # 使用graph_id而不是graph_name

    def _generate_graph_id(self, name: str) -> str:
        """生成安全的图谱ID"""
        import re
        # 移除特殊字符，保留字母数字和下划线
        graph_id = re.sub(r'[^\w\-]', '_', name.lower())
        # 移除连续的下划线
        graph_id = re.sub(r'_+', '_', graph_id)
        # 移除开头和结尾的下划线
        graph_id = graph_id.strip('_')

        # 如果为空，使用默认名称
        if not graph_id:
            graph_id = "unnamed_graph"

        # 确保唯一性
        config = self._load_graphs_config()
        original_id = graph_id
        counter = 1
        while graph_id in config:
            graph_id = f"{original_id}_{counter}"
            counter += 1

        return graph_id

    def _load_graphs_config(self) -> Dict[str, Any]:
        """加载图谱配置"""
        if self.graphs_config_file.exists():
            import json
            try:
                with open(self.graphs_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载图谱配置失败: {e}")
                return {}
        return {}

    def _save_graphs_config(self, config: Dict[str, Any]):
        """保存图谱配置"""
        import json
        try:
            with open(self.graphs_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存图谱配置失败: {e}")
            raise HTTPException(status_code=500, detail=f"保存图谱配置失败: {e}")

    async def create_graph(self, name: str, description: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建新的知识图谱"""
        config = self._load_graphs_config()

        # 生成图谱ID（使用名称的安全版本）
        graph_id = self._generate_graph_id(name)

        # 检查图谱是否已存在
        if graph_id in config:
            raise HTTPException(status_code=400, detail=f"图谱 '{name}' 已存在")

        # 创建图谱工作目录
        graph_dir = self.base_dir / graph_id
        graph_dir.mkdir(parents=True, exist_ok=True)

        # 创建图谱元数据
        if MULTI_GRAPH_SUPPORT:
            graph_metadata = GraphMetadata(
                graph_id=graph_id,
                name=name,
                description=description,
                working_dir=str(graph_dir),
                status=GraphStatus.ACTIVE,
                is_active=len(config) == 0,  # 第一个图谱设为活跃
                metadata=metadata or {}
            )
            config[graph_id] = graph_metadata.to_dict()
        else:
            # 兼容旧格式
            created_at = datetime.now().isoformat()
            config[graph_id] = {
                "name": name,
                "description": description,
                "working_dir": str(graph_dir),
                "created_at": created_at,
                "entity_count": 0,
                "relation_count": 0,
                "is_active": len(config) == 0
            }

        self._save_graphs_config(config)

        # 返回创建结果
        if MULTI_GRAPH_SUPPORT:
            return {
                "status": "success",
                "message": f"图谱 '{name}' 创建成功",
                "graph_info": config[graph_id]
            }
        else:
            return {
                "status": "success",
                "message": f"图谱 '{name}' 创建成功",
                "graph_info": config[graph_id]
            }

    async def get_current_graph(self) -> Optional[Dict[str, Any]]:
        """获取当前活跃图谱"""
        config = self._load_graphs_config()

        # 查找活跃图谱
        for graph_id, graph_info in config.items():
            if graph_info.get("is_active", False):
                # 更新统计信息
                entity_count, relation_count = await self._count_graph_elements(graph_info["working_dir"])
                graph_info["entity_count"] = entity_count
                graph_info["relation_count"] = relation_count
                return graph_info

        return None

    async def switch_graph(self, graph_id: str) -> Dict[str, Any]:
        """切换到指定图谱"""
        config = self._load_graphs_config()

        if graph_id not in config:
            raise HTTPException(status_code=404, detail=f"图谱 '{graph_id}' 不存在")

        # 取消所有图谱的活跃状态
        for gid, graph_info in config.items():
            graph_info["is_active"] = False

        # 设置目标图谱为活跃
        config[graph_id]["is_active"] = True
        config[graph_id]["updated_at"] = datetime.now().isoformat()

        # 保存配置
        self._save_graphs_config(config)

        # 更新当前图谱
        self.current_graph_id = graph_id
        # 注意：不要设置 current_rag = None，因为重新初始化需要用到它

        # 重新初始化RAG实例指向新的工作目录
        await self._reinitialize_rag_for_graph(graph_id, config[graph_id])

        return {
            "status": "success",
            "message": f"已切换到图谱 '{config[graph_id].get('name', graph_id)}'",
            "current_graph": graph_id
        }

    async def list_graphs(self) -> List[Dict[str, Any]]:
        """列出所有图谱"""
        config = self._load_graphs_config()
        graphs = []

        for graph_id, info in config.items():
            # 统计实体和关系数量
            entity_count, relation_count = await self._count_graph_elements(info["working_dir"])

            # 更新统计信息
            info["entity_count"] = entity_count
            info["relation_count"] = relation_count

            if MULTI_GRAPH_SUPPORT:
                # 使用新的数据模型
                graph_data = {
                    "graph_id": graph_id,
                    "name": info.get("name", graph_id),
                    "description": info.get("description", ""),
                    "working_dir": info["working_dir"],
                    "created_at": info.get("created_at", ""),
                    "updated_at": info.get("updated_at", info.get("created_at", "")),
                    "status": info.get("status", "active"),
                    "is_active": info.get("is_active", False),
                    "entity_count": entity_count,
                    "relation_count": relation_count,
                    "document_count": info.get("document_count", 0),
                    "metadata": info.get("metadata", {})
                }
            else:
                # 兼容旧格式
                graph_data = {
                    "name": info.get("name", graph_id),
                    "description": info.get("description", ""),
                    "working_dir": info["working_dir"],
                    "created_at": info.get("created_at", ""),
                    "is_active": info.get("is_active", False),
                    "entity_count": entity_count,
                    "relation_count": relation_count
                }

            graphs.append(graph_data)

        return graphs

    async def _count_graph_elements(self, working_dir: str) -> tuple[int, int]:
        """统计图谱中的实体和关系数量"""
        try:
            import os
            import json
            from pathlib import Path
            import networkx as nx

            # 检查图谱存储文件
            graph_dir = Path(working_dir)

            # 确保使用绝对路径
            if not graph_dir.is_absolute():
                graph_dir = Path.cwd() / working_dir

            # 检查目录是否存在
            if not graph_dir.exists():
                logger.debug(f"图谱目录不存在: {graph_dir}")
                return 0, 0

            entity_count = 0
            relation_count = 0

            # 1. 尝试读取NetworkX GraphML文件（LightRAG的主要存储格式）
            graphml_files = list(graph_dir.glob("graph_*.graphml"))
            if graphml_files:
                try:
                    # 使用第一个找到的GraphML文件
                    graphml_file = graphml_files[0]
                    graph = nx.read_graphml(graphml_file)
                    entity_count = graph.number_of_nodes()
                    relation_count = graph.number_of_edges()
                    logger.debug(f"从GraphML文件 {graphml_file} 读取统计: {entity_count} 实体, {relation_count} 关系")
                    return entity_count, relation_count
                except Exception as e:
                    logger.debug(f"读取GraphML文件失败: {e}")

            # 2. 尝试从向量数据库文件统计实体数量
            vdb_files = list(graph_dir.glob("vdb_*.json"))
            for vdb_file in vdb_files:
                if "entities" in vdb_file.name.lower():
                    try:
                        with open(vdb_file, 'r', encoding='utf-8') as f:
                            vdb_data = json.load(f)
                            if isinstance(vdb_data, dict) and "data" in vdb_data:
                                entity_count = len(vdb_data["data"])
                                logger.debug(f"从向量数据库文件读取实体数量: {entity_count}")
                                break
                    except Exception as e:
                        logger.debug(f"读取向量数据库文件失败: {e}")

                # 尝试统计关系数量
                if "relationships" in vdb_file.name.lower():
                    try:
                        with open(vdb_file, 'r', encoding='utf-8') as f:
                            vdb_data = json.load(f)
                            if isinstance(vdb_data, dict) and "data" in vdb_data:
                                relation_count = len(vdb_data["data"])
                                logger.debug(f"从向量数据库文件读取关系数量: {relation_count}")
                    except Exception as e:
                        logger.debug(f"读取关系向量数据库文件失败: {e}")

            # 3. 检查是否有存储文件但无法解析
            storage_files = list(graph_dir.glob("*.json")) + list(graph_dir.glob("*.pkl")) + list(graph_dir.glob("*.graphml"))
            if storage_files and entity_count == 0 and relation_count == 0:
                logger.debug(f"图谱 {working_dir} 找到存储文件但无法解析统计信息: {[f.name for f in storage_files]}")
            elif not storage_files:
                logger.debug(f"图谱 {working_dir} 目录为空，没有找到存储文件")

            logger.debug(f"图谱 {working_dir} 最终统计: {entity_count} 实体, {relation_count} 关系")
            return entity_count, relation_count

        except Exception as e:
            logger.warning(f"统计图谱元素数量失败: {e}")
            return 0, 0

    async def _reinitialize_rag_for_graph(self, graph_id: str, graph_info: Dict[str, Any]):
        """为指定图谱重新初始化RAG实例"""
        try:
            # 获取图谱工作目录
            working_dir = graph_info.get("working_dir", f"graphs/{graph_id}")

            # 确保使用绝对路径
            if not os.path.isabs(working_dir):
                working_dir = os.path.abspath(working_dir)

            # 检查目录是否存在
            if not os.path.exists(working_dir):
                logger.error(f"图谱工作目录不存在: {working_dir}")
                return

            logger.info(f"重新初始化RAG实例，工作目录: {working_dir}")

            if not self.current_rag:
                logger.error("当前RAG实例为空，无法重新初始化")
                return

            # 更新RAG实例的工作目录
            self.current_rag.working_dir = working_dir

            # 更新所有存储组件的global_config中的working_dir
            for storage in (
                self.current_rag.full_docs,
                self.current_rag.text_chunks,
                self.current_rag.entities_vdb,
                self.current_rag.relationships_vdb,
                self.current_rag.chunks_vdb,
                self.current_rag.chunk_entity_relation_graph,
                self.current_rag.llm_response_cache,
                self.current_rag.doc_status,
            ):
                if storage and hasattr(storage, 'global_config'):
                    storage.global_config["working_dir"] = working_dir
                    logger.info(f"Updated {storage.__class__.__name__} working_dir to {working_dir}")

                    # 对于支持update_working_dir的存储组件，调用该方法重新加载数据
                    if hasattr(storage, 'update_working_dir'):
                        storage.update_working_dir(working_dir)

            # 重新初始化存储组件
            await self.current_rag.initialize_storages()

            # 更新当前图谱ID
            self.current_graph_id = graph_id

            logger.info(f"RAG实例已重新初始化为图谱 '{graph_id}'")

        except Exception as e:
            logger.error(f"重新初始化RAG实例失败: {e}")
            logger.error(traceback.format_exc())

    async def migrate_data_to_graph(self, source_dir: str, target_graph_id: str) -> Dict[str, Any]:
        """将数据从源目录迁移到目标图谱"""
        try:
            import shutil
            from pathlib import Path

            config = self._load_graphs_config()

            if target_graph_id not in config:
                raise HTTPException(status_code=404, detail=f"目标图谱 '{target_graph_id}' 不存在")

            source_path = Path(source_dir)
            target_path = Path(config[target_graph_id]["working_dir"])

            if not source_path.exists():
                raise HTTPException(status_code=404, detail=f"源目录 '{source_dir}' 不存在")

            # 确保目标目录存在
            target_path.mkdir(parents=True, exist_ok=True)

            # 获取需要迁移的文件
            files_to_migrate = [
                "graph_chunk_entity_relation.graphml",
                "kv_store_doc_status.json",
                "kv_store_full_docs.json",
                "kv_store_llm_response_cache.json",
                "kv_store_text_chunks.json",
                "vdb_chunks.json",
                "vdb_entities.json",
                "vdb_relationships.json"
            ]

            migrated_files = []
            skipped_files = []

            for file_name in files_to_migrate:
                source_file = source_path / file_name
                target_file = target_path / file_name

                if source_file.exists():
                    if target_file.exists():
                        # 备份现有文件
                        backup_file = target_path / f"{file_name}.backup"
                        shutil.copy2(target_file, backup_file)
                        logger.info(f"备份现有文件: {target_file} -> {backup_file}")

                    # 复制文件
                    shutil.copy2(source_file, target_file)
                    migrated_files.append(file_name)
                    logger.info(f"迁移文件: {source_file} -> {target_file}")
                else:
                    skipped_files.append(file_name)

            # 更新图谱统计信息
            entity_count, relation_count = await self._count_graph_elements(str(target_path))
            config[target_graph_id]["entity_count"] = entity_count
            config[target_graph_id]["relation_count"] = relation_count
            config[target_graph_id]["updated_at"] = datetime.now().isoformat()

            # 保存配置
            self._save_graphs_config(config)

            return {
                "status": "success",
                "message": f"数据已成功迁移到图谱 '{target_graph_id}'",
                "migrated_files": migrated_files,
                "skipped_files": skipped_files,
                "entity_count": entity_count,
                "relation_count": relation_count
            }

        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"数据迁移失败: {str(e)}")

    async def delete_graph(self, graph_id: str) -> Dict[str, Any]:
        """删除指定的知识图谱"""
        config = self._load_graphs_config()

        if graph_id not in config:
            raise HTTPException(status_code=404, detail=f"图谱 '{graph_id}' 不存在")

        graph_info = config[graph_id]
        graph_name = graph_info.get("name", graph_id)

        # 如果是当前活跃图谱，需要先切换
        if graph_id == self.current_graph_id:
            self.current_graph_id = None
            self.current_rag = None

        # 删除图谱目录
        graph_dir = Path(graph_info["working_dir"])
        if graph_dir.exists():
            shutil.rmtree(graph_dir)

        # 从配置中移除
        del config[graph_id]
        self._save_graphs_config(config)

        return {
            "status": "success",
            "message": f"图谱 '{graph_name}' 删除成功"
        }

    async def update_graph(self, graph_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新图谱信息"""
        config = self._load_graphs_config()

        if graph_id not in config:
            raise HTTPException(status_code=404, detail=f"图谱 '{graph_id}' 不存在")

        graph_info = config[graph_id]

        # 更新允许的字段
        if "name" in update_data:
            graph_info["name"] = update_data["name"]
        if "description" in update_data:
            graph_info["description"] = update_data["description"]
        if "status" in update_data:
            graph_info["status"] = update_data["status"]
        if "metadata" in update_data:
            graph_info["metadata"] = update_data["metadata"]

        # 更新时间戳
        graph_info["updated_at"] = datetime.now().isoformat()

        # 保存配置
        self._save_graphs_config(config)

        return {
            "status": "success",
            "message": f"图谱 '{graph_info.get('name', graph_id)}' 更新成功",
            "graph_info": graph_info
        }


def create_graph_routes(rag, api_key: Optional[str] = None):
    combined_auth = get_combined_auth_dependency(api_key)

    # 初始化全局图谱管理器
    global _graph_manager
    if _graph_manager is None:
        _graph_manager = GraphManager()
        # 设置当前RAG实例
        _graph_manager.current_rag = rag

    # ==================== 多图谱管理API ====================

    @router.post("/graphs", dependencies=[Depends(combined_auth)])
    async def create_knowledge_graph(request: MultiGraphCreateRequest if MULTI_GRAPH_SUPPORT else GraphCreateRequest):
        """
        创建新的知识图谱

        Args:
            request: 包含图谱名称和描述的请求

        Returns:
            Dict: 创建结果和图谱信息
        """
        try:
            if MULTI_GRAPH_SUPPORT:
                result = await _graph_manager.create_graph(
                    name=request.name,
                    description=request.description,
                    metadata=getattr(request, 'metadata', {})
                )
            else:
                result = await _graph_manager.create_graph(
                    name=request.name,
                    description=request.description
                )
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建图谱失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"创建图谱失败: {str(e)}"
            )

    @router.get("/graphs/list", dependencies=[Depends(combined_auth)])
    async def list_knowledge_graphs():
        """
        列出所有可用的知识图谱

        Returns:
            List[GraphInfo]: 图谱信息列表
        """
        try:
            graphs = await _graph_manager.list_graphs()
            return {
                "status": "success",
                "graphs": graphs,
                "total": len(graphs)
            }
        except Exception as e:
            logger.error(f"获取图谱列表失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"获取图谱列表失败: {str(e)}"
            )

    @router.delete("/graphs/{graph_id}", dependencies=[Depends(combined_auth)])
    async def delete_knowledge_graph(graph_id: str):
        """
        删除指定的知识图谱

        Args:
            graph_id (str): 要删除的图谱ID

        Returns:
            Dict: 删除结果
        """
        try:
            result = await _graph_manager.delete_graph(graph_id)
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除图谱失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"删除图谱失败: {str(e)}"
            )

    @router.post("/graphs/{graph_id}/switch", dependencies=[Depends(combined_auth)])
    async def switch_knowledge_graph(graph_id: str):
        """
        切换到指定的知识图谱

        Args:
            graph_id (str): 要切换到的图谱ID

        Returns:
            Dict: 切换结果
        """
        try:
            result = await _graph_manager.switch_graph(graph_id)
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"切换图谱失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"切换图谱失败: {str(e)}"
            )

    @router.post("/graphs/{graph_id}/migrate", dependencies=[Depends(combined_auth)])
    async def migrate_data_to_graph(
        graph_id: str,
        source_dir: str = Query(..., description="源数据目录路径")
    ):
        """
        将数据从源目录迁移到指定图谱

        Args:
            graph_id (str): 目标图谱ID
            source_dir (str): 源数据目录路径

        Returns:
            Dict: 迁移结果
        """
        try:
            result = await _graph_manager.migrate_data_to_graph(source_dir, graph_id)
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"数据迁移失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"数据迁移失败: {str(e)}"
            )



    @router.put("/graphs/{graph_id}", dependencies=[Depends(combined_auth)])
    async def update_knowledge_graph(graph_id: str, request: GraphUpdateRequest if MULTI_GRAPH_SUPPORT else dict):
        """
        更新图谱信息

        Args:
            graph_id (str): 图谱ID
            request: 更新请求

        Returns:
            Dict: 更新结果
        """
        try:
            if MULTI_GRAPH_SUPPORT:
                update_data = request.dict(exclude_unset=True)
            else:
                update_data = request

            result = await _graph_manager.update_graph(graph_id, update_data)
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新图谱失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"更新图谱失败: {str(e)}"
            )
        except Exception as e:
            logger.error(f"切换图谱失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"切换图谱失败: {str(e)}"
            )

    @router.get("/graphs/current", dependencies=[Depends(combined_auth)])
    async def get_current_graph():
        """
        获取当前活跃的知识图谱信息

        Returns:
            Dict: 当前图谱信息
        """
        try:
            if _graph_manager.current_graph_id is None:
                return {
                    "status": "success",
                    "current_graph": None,
                    "message": "当前没有活跃的图谱"
                }

            config = _graph_manager._load_graphs_config()
            graph_info = config.get(_graph_manager.current_graph_id)

            if graph_info is None:
                return {
                    "status": "success",
                    "current_graph": None,
                    "message": "当前图谱配置不存在"
                }

            # 统计实体和关系数量
            entity_count, relation_count = await _graph_manager._count_graph_elements(
                graph_info["working_dir"]
            )

            return {
                "status": "success",
                "current_graph": {
                    "graph_id": _graph_manager.current_graph_id,  # 添加graph_id字段
                    "name": _graph_manager.current_graph_id,
                    "description": graph_info.get("description", ""),
                    "working_dir": graph_info["working_dir"],
                    "created_at": graph_info.get("created_at", ""),
                    "entity_count": entity_count,
                    "relation_count": relation_count
                }
            }
        except Exception as e:
            logger.error(f"获取当前图谱信息失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"获取当前图谱信息失败: {str(e)}"
            )

    # ==================== 手动节点管理API ====================

    @router.post("/graphs/nodes", dependencies=[Depends(combined_auth)])
    async def create_node(request: NodeCreateRequest):
        """
        手动添加新节点到当前图谱

        Args:
            request (NodeCreateRequest): 节点创建请求

        Returns:
            Dict: 创建结果和节点信息
        """
        try:
            # 构建实体数据
            entity_data = {
                "entity_type": request.entity_type,
                "description": request.description,
                "source_id": request.source_id,
                "file_path": request.file_path
            }

            # 使用LightRAG的create_entity方法
            result = await rag.acreate_entity(
                entity_name=request.entity_name,
                entity_data=entity_data
            )
            
            return {
                "status": "success",
                "message": f"节点 '{request.entity_name}' 创建成功",
                "node_info": result
            }
        except Exception as e:
            logger.error(f"创建节点失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"创建节点失败: {str(e)}"
            )

    @router.post("/graphs/nodes/batch", dependencies=[Depends(combined_auth)])
    async def create_nodes_batch(request: NodeBatchCreateRequest):
        """
        批量添加节点到当前图谱

        Args:
            request (NodeBatchCreateRequest): 批量节点创建请求

        Returns:
            Dict: 批量创建结果
        """
        try:
            results = []
            failed_nodes = []

            for node_req in request.nodes:
                try:
                    entity_data = {
                        "entity_type": node_req.entity_type,
                        "description": node_req.description,
                        "source_id": node_req.source_id,
                        "file_path": node_req.file_path
                    }

                    result = await rag.acreate_entity(
                        entity_name=node_req.entity_name,
                        entity_data=entity_data
                    )

                    results.append({
                        "entity_name": node_req.entity_name,
                        "status": "success",
                        "data": result
                    })

                except Exception as e:
                    failed_nodes.append({
                        "entity_name": node_req.entity_name,
                        "status": "failed",
                        "error": str(e)
                    })
                    logger.error(f"创建节点 '{node_req.entity_name}' 失败: {e}")
            
            return {
                "status": "completed",
                "message": f"批量创建完成，成功: {len(results)}, 失败: {len(failed_nodes)}",
                "successful_nodes": results,
                "failed_nodes": failed_nodes,
                "total_requested": len(request.nodes),
                "successful_count": len(results),
                "failed_count": len(failed_nodes)
            }
        except Exception as e:
            logger.error(f"批量创建节点失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"批量创建节点失败: {str(e)}"
            )

    # ==================== 手动节点管理API ====================

    @router.post("/graphs/nodes", dependencies=[Depends(combined_auth)])
    async def create_node(request: NodeCreateRequest):
        """
        手动添加新节点到当前图谱

        Args:
            request (NodeCreateRequest): 节点创建请求

        Returns:
            Dict: 创建结果和节点信息
        """
        try:
            # 构建实体数据
            entity_data = {
                "entity_type": request.entity_type,
                "description": request.description,
                "source_id": request.source_id,
                "file_path": request.file_path
            }

            # 使用LightRAG的create_entity方法
            result = await rag.acreate_entity(
                entity_name=request.entity_name,
                entity_data=entity_data
            )
            
            return {
                "status": "success",
                "message": f"节点 '{request.entity_name}' 创建成功",
                "node_info": result
            }
        except Exception as e:
            logger.error(f"创建节点失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"创建节点失败: {str(e)}"
            )

    @router.post("/graphs/nodes/batch", dependencies=[Depends(combined_auth)])
    async def create_nodes_batch(request: NodeBatchCreateRequest):
        """
        批量添加节点到当前图谱

        Args:
            request (NodeBatchCreateRequest): 批量节点创建请求

        Returns:
            Dict: 批量创建结果
        """
        try:
            results = []
            failed_nodes = []

            for node_req in request.nodes:
                try:
                    entity_data = {
                        "entity_type": node_req.entity_type,
                        "description": node_req.description,
                        "source_id": node_req.source_id,
                        "file_path": node_req.file_path
                    }

                    result = await rag.acreate_entity(
                        entity_name=node_req.entity_name,
                        entity_data=entity_data
                    )

                    results.append({
                        "entity_name": node_req.entity_name,
                        "status": "success",
                        "data": result
                    })

                except Exception as e:
                    failed_nodes.append({
                        "entity_name": node_req.entity_name,
                        "status": "failed",
                        "error": str(e)
                    })
                    logger.error(f"创建节点 '{node_req.entity_name}' 失败: {e}")
            
            return {
                "status": "completed",
                "message": f"批量创建完成，成功: {len(results)}, 失败: {len(failed_nodes)}",
                "successful_nodes": results,
                "failed_nodes": failed_nodes,
                "total_requested": len(request.nodes),
                "successful_count": len(results),
                "failed_count": len(failed_nodes)
            }
        except Exception as e:
            logger.error(f"批量创建节点失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"批量创建节点失败: {str(e)}"
            )

    @router.delete("/graphs/nodes/{node_name}", dependencies=[Depends(combined_auth)])
    async def delete_node(node_name: str):
        """
        删除指定节点及其所有关系

        Args:
            node_name (str): 要删除的节点名称

        Returns:
            Dict: 删除结果
        """
        try:
            # 使用LightRAG的delete_by_entity方法
            await rag.adelete_by_entity(node_name)
            
            return {
                "status": "success",
                "message": f"节点 '{node_name}' 及其所有关系已删除"
            }
        except Exception as e:
            logger.error(f"删除节点失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"删除节点失败: {str(e)}"
            )

    @router.get("/graphs/nodes/{node_name}", dependencies=[Depends(combined_auth)])
    async def get_node_info(node_name: str):
        """
        获取节点详细信息

        Args:
            node_name (str): 节点名称

        Returns:
            Dict: 节点信息
        """
        try:
            # 检查节点是否存在
            exists = await rag.chunk_entity_relation_graph.has_node(node_name)
            if not exists:
                raise HTTPException(status_code=404, detail=f"节点 '{node_name}' 不存在")

            # 获取节点数据
            node_data = await rag.chunk_entity_relation_graph.get_node(node_name)

            return {
                "status": "success",
                "node_name": node_name,
                "node_data": node_data,
                "exists": True
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取节点信息失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"获取节点信息失败: {str(e)}"
            )

    # ==================== 手动关系管理API ====================

    @router.post("/graphs/relations", dependencies=[Depends(combined_auth)])
    async def create_relation(request: RelationCreateRequest):
        """
        手动创建两个节点之间的关系

        Args:
            request (RelationCreateRequest): 关系创建请求

        Returns:
            Dict: 创建结果和关系信息
        """
        try:
            # 构建关系数据
            relation_data = {
                "description": request.description,
                "keywords": request.keywords,
                "weight": request.weight,
                "source_id": request.source_id,
                "file_path": request.file_path
            }

            # 使用LightRAG的create_relation方法
            result = await rag.acreate_relation(
                source_entity=request.source_entity,
                target_entity=request.target_entity,
                relation_data=relation_data
            )
            
            return {
                "status": "success",
                "message": f"关系 '{request.source_entity}' -> '{request.target_entity}' 创建成功",
                "relation_info": result
            }
        except Exception as e:
            logger.error(f"创建关系失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"创建关系失败: {str(e)}"
            )

    @router.post("/graphs/relations/batch", dependencies=[Depends(combined_auth)])
    async def create_relations_batch(request: RelationBatchCreateRequest):
        """
        批量创建关系

        Args:
            request (RelationBatchCreateRequest): 批量关系创建请求

        Returns:
            Dict: 批量创建结果
        """
        try:
            results = []
            failed_relations = []

            for rel_req in request.relations:
                try:
                    relation_data = {
                        "description": rel_req.description,
                        "keywords": rel_req.keywords,
                        "weight": rel_req.weight,
                        "source_id": rel_req.source_id,
                        "file_path": rel_req.file_path
                    }

                    result = await rag.acreate_relation(
                        source_entity=rel_req.source_entity,
                        target_entity=rel_req.target_entity,
                        relation_data=relation_data
                    )

                    results.append({
                        "source_entity": rel_req.source_entity,
                        "target_entity": rel_req.target_entity,
                        "status": "success",
                        "data": result
                    })

                except Exception as e:
                    failed_relations.append({
                        "source_entity": rel_req.source_entity,
                        "target_entity": rel_req.target_entity,
                        "status": "failed",
                        "error": str(e)
                    })
                    logger.error(f"创建关系 '{rel_req.source_entity}' -> '{rel_req.target_entity}' 失败: {e}")
            
            return {
                "status": "completed",
                "message": f"批量创建完成，成功: {len(results)}, 失败: {len(failed_relations)}",
                "successful_relations": results,
                "failed_relations": failed_relations,
                "total_requested": len(request.relations),
                "successful_count": len(results),
                "failed_count": len(failed_relations)
            }
        except Exception as e:
            logger.error(f"批量创建关系失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"批量创建关系失败: {str(e)}"
            )

    @router.delete("/graphs/relations/{source_entity}/{target_entity}", dependencies=[Depends(combined_auth)])
    async def delete_relation(source_entity: str, target_entity: str):
        """
        删除指定关系

        Args:
            source_entity (str): 源实体名称
            target_entity (str): 目标实体名称

        Returns:
            Dict: 删除结果
        """
        try:
            # 使用LightRAG的delete_by_relation方法
            await rag.adelete_by_relation(source_entity, target_entity)
            
            return {
                "status": "success",
                "message": f"关系 '{source_entity}' -> '{target_entity}' 已删除"
            }
        except Exception as e:
            logger.error(f"删除关系失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"删除关系失败: {str(e)}"
            )

    @router.put("/graphs/relations/{source_entity}/{target_entity}", dependencies=[Depends(combined_auth)])
    async def update_relation_by_entities(
        source_entity: str,
        target_entity: str,
        request: RelationUpdateRequest
    ):
        """
        修改指定关系的属性

        Args:
            source_entity (str): 源实体名称
            target_entity (str): 目标实体名称
            request (RelationUpdateRequest): 关系更新请求

        Returns:
            Dict: 更新结果
        """
        try:
            # 使用LightRAG的edit_relation方法
            result = await rag.aedit_relation(
                source_entity=source_entity,
                target_entity=target_entity,
                updated_data=request.updated_data
            )
            
            return {
                "status": "success",
                "message": f"关系 '{source_entity}' -> '{target_entity}' 更新成功",
                "relation_info": result
            }
        except Exception as e:
            logger.error(f"更新关系失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"更新关系失败: {str(e)}"
            )

    @router.delete("/graphs/nodes/{node_name}", dependencies=[Depends(combined_auth)])
    async def delete_node(node_name: str):
        """
        删除指定节点及其所有关系

        Args:
            node_name (str): 要删除的节点名称

        Returns:
            Dict: 删除结果
        """
        try:
            # 使用LightRAG的delete_by_entity方法
            await rag.adelete_by_entity(node_name)
            
            return {
                "status": "success",
                "message": f"节点 '{node_name}' 及其所有关系已删除"
            }
        except Exception as e:
            logger.error(f"删除节点失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"删除节点失败: {str(e)}"
            )

    @router.get("/graphs/nodes/{node_name}", dependencies=[Depends(combined_auth)])
    async def get_node_info(node_name: str):
        """
        获取节点详细信息

        Args:
            node_name (str): 节点名称

        Returns:
            Dict: 节点信息
        """
        try:
            # 检查节点是否存在
            exists = await rag.chunk_entity_relation_graph.has_node(node_name)
            if not exists:
                raise HTTPException(status_code=404, detail=f"节点 '{node_name}' 不存在")

            # 获取节点数据
            node_data = await rag.chunk_entity_relation_graph.get_node(node_name)

            return {
                "status": "success",
                "node_name": node_name,
                "node_data": node_data,
                "exists": True
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取节点信息失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"获取节点信息失败: {str(e)}"
            )

    @router.get("/graph/label/list", dependencies=[Depends(combined_auth)])
    async def get_graph_labels():
        """
        Get all graph labels

        Returns:
            List[str]: List of graph labels
        """
        try:
            return await rag.get_graph_labels()
        except Exception as e:
            logger.error(f"Error getting graph labels: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"Error getting graph labels: {str(e)}"
            )

    @router.get("/graphs", dependencies=[Depends(combined_auth)])
    async def get_knowledge_graph(
        label: str = Query(..., description="Label to get knowledge graph for"),
        max_depth: int = Query(3, description="Maximum depth of graph", ge=1),
        max_nodes: int = Query(1000, description="Maximum nodes to return", ge=1),
        graph_id: Optional[str] = Query(None, description="Graph ID to query (optional, uses current active graph if not specified)"),
    ):
        """
        Retrieve a connected subgraph of nodes where the label includes the specified label.
        When reducing the number of nodes, the prioritization criteria are as follows:
            1. Hops(path) to the staring node take precedence
            2. Followed by the degree of the nodes

        Args:
            label (str): Label of the starting node
            max_depth (int, optional): Maximum depth of the subgraph,Defaults to 3
            max_nodes: Maxiumu nodes to return
            graph_id (str, optional): Graph ID to query, uses current active graph if not specified

        Returns:
            Dict[str, List[str]]: Knowledge graph for label
        """
        try:
            # 如果支持多图谱且指定了graph_id，则切换到指定图谱
            if MULTI_GRAPH_SUPPORT and graph_id:
                try:
                    # 尝试切换图谱，但不要抛出异常
                    await _graph_manager.switch_graph(graph_id)
                except Exception as e:
                    logger.warning(f"切换到图谱 '{graph_id}' 失败: {str(e)}")
                    # 继续使用当前图谱

            # 使用当前活跃的RAG实例
            current_rag = _graph_manager.current_rag if MULTI_GRAPH_SUPPORT else rag

            # 确保有可用的RAG实例
            if not current_rag:
                # 如果没有当前RAG实例，使用全局RAG实例
                current_rag = rag

            if not current_rag:
                raise HTTPException(status_code=500, detail="No active RAG instance available")

            return await current_rag.get_knowledge_graph(
                node_label=label,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
        except Exception as e:
            logger.error(f"Error getting knowledge graph for label '{label}': {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"Error getting knowledge graph: {str(e)}"
            )

    @router.get("/graph/entity/exists", dependencies=[Depends(combined_auth)])
    async def check_entity_exists(
        name: str = Query(..., description="Entity name to check"),
        graph_id: Optional[str] = Query(None, description="Graph ID to check (optional, uses current active graph if not specified)"),
    ):
        """
        Check if an entity with the given name exists in the knowledge graph

        Args:
            name (str): Name of the entity to check
            graph_id (str, optional): Graph ID to check, uses current active graph if not specified

        Returns:
            Dict[str, bool]: Dictionary with 'exists' key indicating if entity exists
        """
        try:
            # 如果支持多图谱且指定了graph_id，则切换到指定图谱
            if MULTI_GRAPH_SUPPORT and graph_id:
                await _graph_manager.switch_graph(graph_id)

            # 使用当前活跃的RAG实例
            current_rag = _graph_manager.current_rag if MULTI_GRAPH_SUPPORT else rag
            if not current_rag:
                raise HTTPException(status_code=500, detail="No active RAG instance available")

            exists = await current_rag.chunk_entity_relation_graph.has_node(name)
            return {"exists": exists}
        except Exception as e:
            logger.error(f"Error checking entity existence for '{name}': {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"Error checking entity existence: {str(e)}"
            )

    @router.post("/graph/entity/edit", dependencies=[Depends(combined_auth)])
    async def update_entity(request: EntityUpdateRequest):
        """
        Update an entity's properties in the knowledge graph

        Args:
            request (EntityUpdateRequest): Request containing entity name, updated data, and rename flag

        Returns:
            Dict: Updated entity information
        """
        try:
            result = await rag.aedit_entity(
                entity_name=request.entity_name,
                updated_data=request.updated_data,
                allow_rename=request.allow_rename,
            )
            return {
                "status": "success",
                "message": "Entity updated successfully",
                "data": result,
            }
        except ValueError as ve:
            logger.error(
                f"Validation error updating entity '{request.entity_name}': {str(ve)}"
            )
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"Error updating entity '{request.entity_name}': {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"Error updating entity: {str(e)}"
            )

    @router.post("/graph/relation/edit", dependencies=[Depends(combined_auth)])
    async def update_relation(request: RelationUpdateRequest):
        """Update a relation's properties in the knowledge graph

        Args:
            request (RelationUpdateRequest): Request containing source ID, target ID and updated data

        Returns:
            Dict: Updated relation information
        """
        try:
            result = await rag.aedit_relation(
                source_entity=request.source_id,
                target_entity=request.target_id,
                updated_data=request.updated_data,
            )
            return {
                "status": "success",
                "message": "Relation updated successfully",
                "data": result,
            }
        except ValueError as ve:
            logger.error(
                f"Validation error updating relation between '{request.source_id}' and '{request.target_id}': {str(ve)}"
            )
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(
                f"Error updating relation between '{request.source_id}' and '{request.target_id}': {str(e)}"
            )
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"Error updating relation: {str(e)}"
            )

    return router
