#!/usr/bin/env python3
"""
图谱数据迁移工具

用于管理LightRAG图谱数据的迁移和整理
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class GraphMigrationTool:
    """图谱迁移工具"""
    
    def __init__(self, graphs_dir: str = "./graphs"):
        self.graphs_dir = Path(graphs_dir)
        self.config_file = self.graphs_dir / "graphs_config.json"
        
    def load_config(self) -> Dict:
        """加载图谱配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_config(self, config: Dict):
        """保存图谱配置"""
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def count_graph_elements(self, working_dir: str) -> Tuple[int, int]:
        """统计图谱中的实体和关系数量"""
        try:
            import networkx as nx
            
            graph_dir = Path(working_dir)
            if not graph_dir.exists():
                return 0, 0
            
            # 尝试读取GraphML文件
            graphml_files = list(graph_dir.glob("graph_*.graphml"))
            if graphml_files:
                try:
                    graph = nx.read_graphml(graphml_files[0])
                    return graph.number_of_nodes(), graph.number_of_edges()
                except Exception as e:
                    print(f"读取GraphML文件失败: {e}")
            
            # 尝试从向量数据库文件统计
            entity_count = 0
            relation_count = 0
            
            vdb_entities_file = graph_dir / "vdb_entities.json"
            if vdb_entities_file.exists():
                try:
                    with open(vdb_entities_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "data" in data:
                            entity_count = len(data["data"])
                except Exception as e:
                    print(f"读取实体向量数据库失败: {e}")
            
            vdb_relations_file = graph_dir / "vdb_relationships.json"
            if vdb_relations_file.exists():
                try:
                    with open(vdb_relations_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "data" in data:
                            relation_count = len(data["data"])
                except Exception as e:
                    print(f"读取关系向量数据库失败: {e}")
            
            return entity_count, relation_count
            
        except Exception as e:
            print(f"统计图谱元素失败: {e}")
            return 0, 0
    
    def migrate_data(self, source_dir: str, target_graph_id: str) -> bool:
        """迁移数据到指定图谱"""
        try:
            config = self.load_config()
            
            if target_graph_id not in config:
                print(f"错误: 图谱 '{target_graph_id}' 不存在")
                return False
            
            source_path = Path(source_dir)
            target_path = Path(config[target_graph_id]["working_dir"])
            
            if not source_path.exists():
                print(f"错误: 源目录 '{source_dir}' 不存在")
                return False
            
            # 确保目标目录存在
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 需要迁移的文件
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
            
            for file_name in files_to_migrate:
                source_file = source_path / file_name
                target_file = target_path / file_name
                
                if source_file.exists():
                    if target_file.exists():
                        # 备份现有文件
                        backup_file = target_path / f"{file_name}.backup"
                        shutil.copy2(target_file, backup_file)
                        print(f"备份: {target_file} -> {backup_file}")
                    
                    # 复制文件
                    shutil.copy2(source_file, target_file)
                    migrated_files.append(file_name)
                    print(f"迁移: {source_file} -> {target_file}")
            
            # 更新统计信息
            entity_count, relation_count = self.count_graph_elements(str(target_path))
            config[target_graph_id]["entity_count"] = entity_count
            config[target_graph_id]["relation_count"] = relation_count
            config[target_graph_id]["updated_at"] = datetime.now().isoformat()
            
            self.save_config(config)
            
            print(f"\n迁移完成!")
            print(f"迁移文件数: {len(migrated_files)}")
            print(f"实体数量: {entity_count}")
            print(f"关系数量: {relation_count}")
            
            return True
            
        except Exception as e:
            print(f"迁移失败: {e}")
            return False
    
    def create_graph(self, graph_id: str, name: str, description: str = "") -> bool:
        """创建新图谱"""
        try:
            config = self.load_config()
            
            if graph_id in config:
                print(f"错误: 图谱 '{graph_id}' 已存在")
                return False
            
            # 创建图谱目录
            graph_dir = self.graphs_dir / graph_id
            graph_dir.mkdir(parents=True, exist_ok=True)
            
            # 添加到配置
            config[graph_id] = {
                "graph_id": graph_id,
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "working_dir": str(graph_dir),
                "status": "active",
                "is_active": len(config) == 0,  # 第一个图谱设为活跃
                "entity_count": 0,
                "relation_count": 0,
                "document_count": 0,
                "metadata": {}
            }
            
            self.save_config(config)
            print(f"图谱 '{name}' 创建成功，ID: {graph_id}")
            return True
            
        except Exception as e:
            print(f"创建图谱失败: {e}")
            return False
    
    def list_graphs(self):
        """列出所有图谱"""
        config = self.load_config()
        
        if not config:
            print("没有找到图谱配置")
            return
        
        print("\n图谱列表:")
        print("-" * 80)
        print(f"{'ID':<20} {'名称':<20} {'实体':<8} {'关系':<8} {'状态':<8} {'活跃'}")
        print("-" * 80)
        
        for graph_id, info in config.items():
            entity_count = info.get("entity_count", 0)
            relation_count = info.get("relation_count", 0)
            status = info.get("status", "unknown")
            is_active = "是" if info.get("is_active", False) else "否"
            
            print(f"{graph_id:<20} {info.get('name', ''):<20} {entity_count:<8} {relation_count:<8} {status:<8} {is_active}")
    
    def refresh_stats(self):
        """刷新所有图谱的统计信息"""
        config = self.load_config()
        
        for graph_id, info in config.items():
            working_dir = info.get("working_dir", "")
            if working_dir:
                entity_count, relation_count = self.count_graph_elements(working_dir)
                config[graph_id]["entity_count"] = entity_count
                config[graph_id]["relation_count"] = relation_count
                config[graph_id]["updated_at"] = datetime.now().isoformat()
                print(f"更新 {graph_id}: {entity_count} 实体, {relation_count} 关系")
        
        self.save_config(config)
        print("统计信息刷新完成")


def main():
    parser = argparse.ArgumentParser(description="LightRAG图谱迁移工具")
    parser.add_argument("--graphs-dir", default="./graphs", help="图谱目录路径")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 列出图谱
    subparsers.add_parser("list", help="列出所有图谱")
    
    # 创建图谱
    create_parser = subparsers.add_parser("create", help="创建新图谱")
    create_parser.add_argument("graph_id", help="图谱ID")
    create_parser.add_argument("name", help="图谱名称")
    create_parser.add_argument("--description", default="", help="图谱描述")
    
    # 迁移数据
    migrate_parser = subparsers.add_parser("migrate", help="迁移数据到图谱")
    migrate_parser.add_argument("source_dir", help="源数据目录")
    migrate_parser.add_argument("target_graph_id", help="目标图谱ID")
    
    # 刷新统计
    subparsers.add_parser("refresh", help="刷新所有图谱统计信息")
    
    args = parser.parse_args()
    
    tool = GraphMigrationTool(args.graphs_dir)
    
    if args.command == "list":
        tool.list_graphs()
    elif args.command == "create":
        tool.create_graph(args.graph_id, args.name, args.description)
    elif args.command == "migrate":
        tool.migrate_data(args.source_dir, args.target_graph_id)
    elif args.command == "refresh":
        tool.refresh_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
