"""
多图谱架构数据迁移脚本
"""

import os
import json
import shutil
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from ..models.multi_graph import GraphMetadata, GraphStatus
from ..base import DocProcessingStatus, DocStatus

logger = logging.getLogger(__name__)


class MultiGraphMigrator:
    """多图谱架构迁移器"""
    
    def __init__(self, working_dir: str = "./dickens", graphs_dir: str = "./graphs"):
        self.working_dir = Path(working_dir)
        self.graphs_dir = Path(graphs_dir)
        self.backup_dir = None
        
    async def migrate_to_multi_graph(self, default_graph_name: str = "Default Graph") -> bool:
        """
        迁移现有数据到多图谱架构
        
        Args:
            default_graph_name: 默认图谱名称
            
        Returns:
            bool: 迁移是否成功
        """
        try:
            logger.info("开始多图谱架构迁移...")
            
            # 1. 检查现有数据
            if not await self._check_existing_data():
                logger.info("没有发现现有数据，跳过迁移")
                return True
            
            # 2. 备份现有数据
            await self._backup_existing_data()
            
            # 3. 创建图谱目录结构
            await self._create_graphs_directory()
            
            # 4. 创建默认图谱
            default_graph = await self._create_default_graph(default_graph_name)
            
            # 5. 迁移数据文件
            await self._migrate_data_files(default_graph)
            
            # 6. 更新数据格式
            await self._update_data_format(default_graph)
            
            # 7. 验证迁移结果
            await self._verify_migration(default_graph)
            
            logger.info("✅ 多图谱架构迁移完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            await self._rollback_migration()
            return False
    
    async def _check_existing_data(self) -> bool:
        """检查是否存在现有数据"""
        if not self.working_dir.exists():
            return False
        
        # 检查关键文件
        key_files = [
            "kv_store.json",
            "doc_status.json",
            "entities_vdb.pkl",
            "relationships_vdb.pkl"
        ]
        
        existing_files = []
        for file_name in key_files:
            file_path = self.working_dir / file_name
            if file_path.exists():
                existing_files.append(file_name)
        
        if existing_files:
            logger.info(f"发现现有数据文件: {existing_files}")
            return True
        
        return False
    
    async def _backup_existing_data(self):
        """备份现有数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.working_dir.parent / f"backup_{timestamp}"
        
        logger.info(f"备份现有数据到: {self.backup_dir}")
        shutil.copytree(self.working_dir, self.backup_dir)
        
    async def _create_graphs_directory(self):
        """创建图谱目录结构"""
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建图谱目录: {self.graphs_dir}")
        
    async def _create_default_graph(self, name: str) -> GraphMetadata:
        """创建默认图谱"""
        graph_id = "default"
        graph_dir = self.graphs_dir / graph_id
        graph_dir.mkdir(parents=True, exist_ok=True)
        
        default_graph = GraphMetadata(
            graph_id=graph_id,
            name=name,
            description="Migrated from existing LightRAG data",
            working_dir=str(graph_dir),
            status=GraphStatus.ACTIVE,
            is_active=True
        )
        
        # 保存图谱配置
        await self._save_graph_config(default_graph)
        
        logger.info(f"创建默认图谱: {name} (ID: {graph_id})")
        return default_graph
        
    async def _save_graph_config(self, graph: GraphMetadata):
        """保存图谱配置"""
        config_file = self.graphs_dir / "graphs_config.json"
        
        # 加载现有配置
        config = {}
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # 更新配置
        config[graph.graph_id] = graph.to_dict()
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    async def _migrate_data_files(self, graph: GraphMetadata):
        """迁移数据文件"""
        graph_dir = Path(graph.working_dir)
        
        # 需要迁移的文件列表
        files_to_migrate = [
            "kv_store.json",
            "text_chunks.json", 
            "entities_vdb.pkl",
            "relationships_vdb.pkl",
            "graph.graphml",
            "doc_status.json",
            "kv_store_llm_response_cache.json"
        ]
        
        migrated_files = []
        for file_name in files_to_migrate:
            source_file = self.working_dir / file_name
            target_file = graph_dir / file_name
            
            if source_file.exists():
                shutil.copy2(source_file, target_file)
                migrated_files.append(file_name)
                logger.info(f"迁移文件: {file_name}")
        
        logger.info(f"共迁移 {len(migrated_files)} 个数据文件")
    
    async def _update_data_format(self, graph: GraphMetadata):
        """更新数据格式，添加graph_id字段"""
        graph_dir = Path(graph.working_dir)
        
        # 更新文档状态数据
        await self._update_doc_status_format(graph_dir, graph.graph_id)
        
        # 更新实体数据格式
        await self._update_entities_format(graph_dir, graph.graph_id)
        
        # 更新关系数据格式
        await self._update_relationships_format(graph_dir, graph.graph_id)
        
        logger.info("数据格式更新完成")
    
    async def _update_doc_status_format(self, graph_dir: Path, graph_id: str):
        """更新文档状态数据格式"""
        doc_status_file = graph_dir / "doc_status.json"
        if not doc_status_file.exists():
            return
        
        try:
            with open(doc_status_file, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            
            # 为每个文档添加graph_id
            updated_data = {}
            for doc_id, doc_info in doc_data.items():
                if isinstance(doc_info, dict):
                    doc_info['graph_id'] = graph_id
                    doc_info['graph_name'] = None  # 将在后续填充
                updated_data[doc_id] = doc_info
            
            # 保存更新后的数据
            with open(doc_status_file, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"更新了 {len(updated_data)} 个文档的状态格式")
            
        except Exception as e:
            logger.error(f"更新文档状态格式失败: {e}")
    
    async def _update_entities_format(self, graph_dir: Path, graph_id: str):
        """更新实体数据格式"""
        # 注意：实体数据通常存储在向量数据库中，格式更新可能需要特殊处理
        # 这里先记录日志，具体实现取决于存储格式
        logger.info(f"实体数据格式更新 (graph_id: {graph_id})")
    
    async def _update_relationships_format(self, graph_dir: Path, graph_id: str):
        """更新关系数据格式"""
        # 注意：关系数据通常存储在图数据库中，格式更新可能需要特殊处理
        # 这里先记录日志，具体实现取决于存储格式
        logger.info(f"关系数据格式更新 (graph_id: {graph_id})")
    
    async def _verify_migration(self, graph: GraphMetadata):
        """验证迁移结果"""
        graph_dir = Path(graph.working_dir)
        
        # 检查关键文件是否存在
        required_files = ["doc_status.json"]
        missing_files = []
        
        for file_name in required_files:
            if not (graph_dir / file_name).exists():
                missing_files.append(file_name)
        
        if missing_files:
            raise Exception(f"迁移验证失败，缺少文件: {missing_files}")
        
        # 检查配置文件
        config_file = self.graphs_dir / "graphs_config.json"
        if not config_file.exists():
            raise Exception("图谱配置文件不存在")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        if graph.graph_id not in config:
            raise Exception(f"图谱配置中缺少默认图谱: {graph.graph_id}")
        
        logger.info("✅ 迁移验证通过")
    
    async def _rollback_migration(self):
        """回滚迁移"""
        if self.backup_dir and self.backup_dir.exists():
            logger.info(f"回滚迁移，从备份恢复: {self.backup_dir}")
            
            # 删除可能创建的图谱目录
            if self.graphs_dir.exists():
                shutil.rmtree(self.graphs_dir)
            
            # 恢复原始数据
            if self.working_dir.exists():
                shutil.rmtree(self.working_dir)
            shutil.copytree(self.backup_dir, self.working_dir)
            
            logger.info("回滚完成")
        else:
            logger.warning("没有备份数据，无法回滚")


async def run_migration(working_dir: str = "./dickens", graphs_dir: str = "./graphs"):
    """运行迁移脚本"""
    migrator = MultiGraphMigrator(working_dir, graphs_dir)
    success = await migrator.migrate_to_multi_graph()
    
    if success:
        print("✅ 多图谱架构迁移成功完成！")
        print(f"📁 图谱数据目录: {graphs_dir}")
        print(f"📦 原始数据备份: {migrator.backup_dir}")
    else:
        print("❌ 迁移失败，请检查日志")
    
    return success


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行迁移
    asyncio.run(run_migration())
