"""
多图谱存储层扩展
支持按图谱隔离的数据存储和查询
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..models.multi_graph import GraphMetadata, GraphStatus, ExtendedDocProcessingStatus
from ..base import DocProcessingStatus, DocStatus

logger = logging.getLogger(__name__)


class MultiGraphStorageManager:
    """多图谱存储管理器"""
    
    def __init__(self, graphs_dir: str = "./graphs"):
        self.graphs_dir = Path(graphs_dir)
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.graphs_dir / "graphs_config.json"
        
    async def initialize_default_graph(self) -> GraphMetadata:
        """初始化默认图谱"""
        config = await self.load_config()
        
        # 检查是否已有默认图谱
        for graph_id, graph_info in config.items():
            if graph_info.get("is_active", False) or graph_id == "default":
                return GraphMetadata.from_dict({
                    "graph_id": graph_id,
                    **graph_info
                })
        
        # 创建默认图谱
        default_graph = GraphMetadata(
            graph_id="default",
            name="Default Graph",
            description="Default graph for LightRAG",
            working_dir=str(self.graphs_dir / "default"),
            status=GraphStatus.ACTIVE,
            is_active=True
        )
        
        # 创建工作目录
        graph_dir = Path(default_graph.working_dir)
        graph_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存配置
        config["default"] = default_graph.to_dict()
        await self.save_config(config)
        
        logger.info(f"创建默认图谱: {default_graph.name}")
        return default_graph
    
    async def load_config(self) -> Dict[str, Any]:
        """加载图谱配置"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载图谱配置失败: {e}")
            return {}
    
    async def save_config(self, config: Dict[str, Any]):
        """保存图谱配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存图谱配置失败: {e}")
            raise
    
    async def get_graph_working_dir(self, graph_id: str) -> Optional[Path]:
        """获取图谱工作目录"""
        config = await self.load_config()
        graph_info = config.get(graph_id)
        
        if not graph_info:
            return None
        
        return Path(graph_info["working_dir"])
    
    async def create_graph_storage(self, graph_id: str) -> bool:
        """为图谱创建存储结构"""
        graph_dir = await self.get_graph_working_dir(graph_id)
        if not graph_dir:
            return False
        
        try:
            graph_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建必要的存储文件（如果不存在）
            storage_files = [
                "kv_store.json",
                "text_chunks.json", 
                "doc_status.json",
                "entities_vdb.pkl",
                "relationships_vdb.pkl",
                "graph.graphml"
            ]
            
            for file_name in storage_files:
                file_path = graph_dir / file_name
                if not file_path.exists():
                    if file_name.endswith('.json'):
                        # 创建空的JSON文件
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump({}, f)
                    # 其他文件类型由相应的存储组件创建
            
            logger.info(f"为图谱 {graph_id} 创建存储结构")
            return True
            
        except Exception as e:
            logger.error(f"创建图谱存储失败: {e}")
            return False
    
    async def get_graph_doc_status(self, graph_id: str) -> Dict[str, Any]:
        """获取图谱的文档状态"""
        graph_dir = await self.get_graph_working_dir(graph_id)
        if not graph_dir:
            return {}
        
        doc_status_file = graph_dir / "doc_status.json"
        if not doc_status_file.exists():
            return {}
        
        try:
            with open(doc_status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取文档状态失败: {e}")
            return {}
    
    async def save_graph_doc_status(self, graph_id: str, doc_status: Dict[str, Any]):
        """保存图谱的文档状态"""
        graph_dir = await self.get_graph_working_dir(graph_id)
        if not graph_dir:
            raise ValueError(f"图谱 {graph_id} 不存在")
        
        doc_status_file = graph_dir / "doc_status.json"
        
        try:
            with open(doc_status_file, 'w', encoding='utf-8') as f:
                json.dump(doc_status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文档状态失败: {e}")
            raise
    
    async def add_document_to_graph(self, graph_id: str, doc_id: str, doc_status: DocProcessingStatus):
        """将文档添加到指定图谱"""
        # 获取现有文档状态
        current_status = await self.get_graph_doc_status(graph_id)
        
        # 创建扩展的文档状态
        extended_status = ExtendedDocProcessingStatus(
            content=doc_status.content,
            content_summary=doc_status.content_summary,
            content_length=doc_status.content_length,
            file_path=doc_status.file_path,
            status=doc_status.status.value,
            created_at=doc_status.created_at,
            updated_at=doc_status.updated_at,
            chunks_count=doc_status.chunks_count,
            error=doc_status.error,
            metadata=doc_status.metadata,
            graph_id=graph_id
        )
        
        # 添加到状态字典
        current_status[doc_id] = extended_status.to_dict()
        
        # 保存更新后的状态
        await self.save_graph_doc_status(graph_id, current_status)
        
        # 更新图谱统计信息
        await self.update_graph_stats(graph_id)
    
    async def get_documents_by_graph(self, graph_id: str) -> List[Dict[str, Any]]:
        """获取指定图谱的所有文档"""
        doc_status = await self.get_graph_doc_status(graph_id)
        
        documents = []
        for doc_id, doc_info in doc_status.items():
            doc_info["id"] = doc_id
            documents.append(doc_info)
        
        return documents
    
    async def update_graph_stats(self, graph_id: str):
        """更新图谱统计信息"""
        config = await self.load_config()
        graph_info = config.get(graph_id)
        
        if not graph_info:
            return
        
        # 统计文档数量
        documents = await self.get_documents_by_graph(graph_id)
        document_count = len(documents)
        
        # 统计实体和关系数量（简化实现，实际应该从存储中读取）
        entity_count = await self._count_entities(graph_id)
        relation_count = await self._count_relations(graph_id)
        
        # 更新配置
        graph_info["document_count"] = document_count
        graph_info["entity_count"] = entity_count
        graph_info["relation_count"] = relation_count
        graph_info["updated_at"] = datetime.now().isoformat()
        
        # 保存配置
        await self.save_config(config)
    
    async def _count_entities(self, graph_id: str) -> int:
        """统计图谱中的实体数量"""
        # 简化实现，返回0
        # 实际实现应该读取向量数据库或图数据库
        return 0
    
    async def _count_relations(self, graph_id: str) -> int:
        """统计图谱中的关系数量"""
        # 简化实现，返回0
        # 实际实现应该读取图数据库
        return 0
    
    async def delete_graph_storage(self, graph_id: str) -> bool:
        """删除图谱存储"""
        graph_dir = await self.get_graph_working_dir(graph_id)
        if not graph_dir or not graph_dir.exists():
            return False
        
        try:
            import shutil
            shutil.rmtree(graph_dir)
            
            # 从配置中移除
            config = await self.load_config()
            if graph_id in config:
                del config[graph_id]
                await self.save_config(config)
            
            logger.info(f"删除图谱 {graph_id} 的存储")
            return True
            
        except Exception as e:
            logger.error(f"删除图谱存储失败: {e}")
            return False


# 全局存储管理器实例
_storage_manager = None


def get_storage_manager() -> MultiGraphStorageManager:
    """获取全局存储管理器实例"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = MultiGraphStorageManager()
    return _storage_manager


async def initialize_multi_graph_storage():
    """初始化多图谱存储"""
    storage_manager = get_storage_manager()
    await storage_manager.initialize_default_graph()
    logger.info("多图谱存储初始化完成")
