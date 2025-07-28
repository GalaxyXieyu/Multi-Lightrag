#!/usr/bin/env python3
"""
图谱存储结构迁移脚本

将现有的rag_storage数据迁移到新的graphs/子目录结构
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def count_graph_elements(working_dir: Path) -> tuple[int, int]:
    """统计图谱中的实体和关系数量"""
    try:
        import networkx as nx
        
        if not working_dir.exists():
            return 0, 0
        
        # 尝试读取GraphML文件
        graphml_files = list(working_dir.glob("graph_*.graphml"))
        if graphml_files:
            try:
                graph = nx.read_graphml(graphml_files[0])
                return graph.number_of_nodes(), graph.number_of_edges()
            except Exception as e:
                print(f"读取GraphML文件失败: {e}")
        
        # 尝试从向量数据库文件统计
        entity_count = 0
        relation_count = 0
        
        vdb_entities_file = working_dir / "vdb_entities.json"
        if vdb_entities_file.exists():
            try:
                with open(vdb_entities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "data" in data:
                        entity_count = len(data["data"])
            except Exception as e:
                print(f"读取实体向量数据库失败: {e}")
        
        vdb_relations_file = working_dir / "vdb_relationships.json"
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


def migrate_rag_storage_to_graphs():
    """将rag_storage迁移到graphs结构"""
    
    # 路径配置
    old_rag_storage = Path("/Volumes/DATABASE/code/LightRAG/rag_storage")
    graphs_dir = Path("/Volumes/DATABASE/code/LightRAG/lightrag_webui/graphs")
    config_file = graphs_dir / "graphs_config.json"
    
    print("🚀 开始迁移图谱存储结构...")
    print(f"源目录: {old_rag_storage}")
    print(f"目标目录: {graphs_dir}")
    
    # 检查源目录
    if not old_rag_storage.exists():
        print(f"❌ 源目录不存在: {old_rag_storage}")
        return False
    
    # 创建graphs目录
    graphs_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载现有配置
    config = {}
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
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
    
    # 检查哪些文件存在
    existing_files = []
    for file_name in files_to_migrate:
        source_file = old_rag_storage / file_name
        if source_file.exists():
            existing_files.append(file_name)
    
    if not existing_files:
        print("❌ 源目录中没有找到需要迁移的文件")
        return False
    
    print(f"📁 找到 {len(existing_files)} 个文件需要迁移:")
    for file_name in existing_files:
        print(f"  - {file_name}")
    
    # 确定主图谱名称
    main_graph_id = "主图谱"
    main_graph_name = "主图谱"
    
    # 检查是否已存在主图谱
    if main_graph_id in config:
        print(f"⚠️  图谱 '{main_graph_id}' 已存在，将更新其数据")
    else:
        print(f"📝 创建新图谱: {main_graph_name}")
    
    # 创建主图谱目录
    main_graph_dir = graphs_dir / main_graph_id
    main_graph_dir.mkdir(parents=True, exist_ok=True)
    
    # 迁移文件
    migrated_files = []
    for file_name in existing_files:
        source_file = old_rag_storage / file_name
        target_file = main_graph_dir / file_name
        
        try:
            if target_file.exists():
                # 备份现有文件
                backup_file = main_graph_dir / f"{file_name}.backup"
                shutil.copy2(target_file, backup_file)
                print(f"📦 备份: {file_name} -> {backup_file.name}")
            
            # 复制文件
            shutil.copy2(source_file, target_file)
            migrated_files.append(file_name)
            print(f"✅ 迁移: {file_name}")
            
        except Exception as e:
            print(f"❌ 迁移失败 {file_name}: {e}")
    
    # 统计图谱数据
    entity_count, relation_count = count_graph_elements(main_graph_dir)
    
    # 更新配置
    now = datetime.now().isoformat()
    
    # 先将所有现有图谱设为非活跃
    for graph_id in config:
        config[graph_id]["is_active"] = False
    
    # 添加或更新主图谱配置
    config[main_graph_id] = {
        "graph_id": main_graph_id,
        "name": main_graph_name,
        "description": "从原始rag_storage迁移的主图谱",
        "created_at": config.get(main_graph_id, {}).get("created_at", now),
        "updated_at": now,
        "working_dir": str(main_graph_dir),
        "status": "active",
        "is_active": True,  # 设为活跃图谱
        "entity_count": entity_count,
        "relation_count": relation_count,
        "document_count": 0,
        "metadata": {
            "migrated_from": str(old_rag_storage),
            "migration_date": now,
            "migrated_files": migrated_files
        }
    }
    
    # 保存配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 迁移完成!")
    print(f"📊 统计信息:")
    print(f"  - 迁移文件数: {len(migrated_files)}")
    print(f"  - 实体数量: {entity_count}")
    print(f"  - 关系数量: {relation_count}")
    print(f"  - 配置文件: {config_file}")
    print(f"  - 主图谱目录: {main_graph_dir}")
    
    # 询问是否备份原目录
    print(f"\n💡 建议:")
    print(f"1. 验证迁移结果正确后，可以备份原目录: {old_rag_storage}")
    print(f"2. 重启LightRAG服务以使用新的图谱结构")
    
    return True


def clean_empty_graphs():
    """清理空的图谱目录"""
    graphs_dir = Path("/Volumes/DATABASE/code/LightRAG/lightrag_webui/graphs")
    config_file = graphs_dir / "graphs_config.json"
    
    if not config_file.exists():
        print("❌ 配置文件不存在")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    empty_graphs = []
    
    for graph_id, graph_info in config.items():
        working_dir = Path(graph_info.get("working_dir", ""))
        if working_dir.exists():
            # 检查是否有实际的存储文件
            storage_files = list(working_dir.glob("*.json")) + list(working_dir.glob("*.graphml"))
            if not storage_files:
                empty_graphs.append(graph_id)
    
    if empty_graphs:
        print(f"🗑️  发现 {len(empty_graphs)} 个空图谱:")
        for graph_id in empty_graphs:
            print(f"  - {graph_id}")
        
        response = input("是否删除这些空图谱? (y/N): ")
        if response.lower() == 'y':
            for graph_id in empty_graphs:
                working_dir = Path(config[graph_id]["working_dir"])
                if working_dir.exists():
                    shutil.rmtree(working_dir)
                del config[graph_id]
                print(f"✅ 删除空图谱: {graph_id}")
            
            # 保存更新的配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print("🎉 清理完成!")
    else:
        print("✅ 没有发现空图谱")


def main():
    parser = argparse.ArgumentParser(description="图谱存储结构迁移工具")
    parser.add_argument("action", choices=["migrate", "clean"], 
                       help="执行的操作: migrate=迁移数据, clean=清理空图谱")
    
    args = parser.parse_args()
    
    if args.action == "migrate":
        migrate_rag_storage_to_graphs()
    elif args.action == "clean":
        clean_empty_graphs()


if __name__ == "__main__":
    main()
