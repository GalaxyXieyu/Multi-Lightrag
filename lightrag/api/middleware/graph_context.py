"""
图谱上下文中间件
为所有请求注入当前图谱信息，实现数据隔离
"""

import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class GraphContextMiddleware(BaseHTTPMiddleware):
    """图谱上下文中间件，为所有请求注入当前图谱信息"""
    
    def __init__(self, app, graphs_dir: str = "./graphs"):
        super().__init__(app)
        self.graphs_dir = Path(graphs_dir)
        self.graphs_config_file = self.graphs_dir / "graphs_config.json"
        
    async def dispatch(self, request: Request, call_next):
        """处理请求，注入图谱上下文"""
        try:
            # 获取图谱ID
            graph_id = await self._get_graph_id(request)
            
            # 验证图谱存在性
            if graph_id and not await self._graph_exists(graph_id):
                raise HTTPException(404, f"Graph '{graph_id}' not found")
            
            # 注入图谱上下文到请求状态
            request.state.graph_id = graph_id
            request.state.graph_info = await self._get_graph_info(graph_id) if graph_id else None
            
            # 处理请求
            response = await call_next(request)
            
            # 在响应头中返回当前图谱信息
            if graph_id:
                response.headers["X-Current-Graph-ID"] = graph_id
                if hasattr(request.state, 'graph_info') and request.state.graph_info:
                    graph_name = request.state.graph_info.get('name', graph_id)
                    response.headers["X-Current-Graph-Name"] = graph_name
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"图谱上下文中间件错误: {e}")
            # 继续处理请求，不因中间件错误而中断
            request.state.graph_id = None
            request.state.graph_info = None
            return await call_next(request)
    
    async def _get_graph_id(self, request: Request) -> Optional[str]:
        """从请求中获取图谱ID"""
        # 优先级：
        # 1. 请求头 X-Graph-ID
        # 2. 查询参数 graph_id
        # 3. 请求体中的 graph_id（对于POST/PUT请求）
        # 4. 当前活跃图谱
        
        # 1. 检查请求头
        graph_id = request.headers.get("X-Graph-ID")
        if graph_id:
            return graph_id
        
        # 2. 检查查询参数
        graph_id = request.query_params.get("graph_id")
        if graph_id:
            return graph_id
        
        # 3. 检查请求体（仅对特定方法）
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # 尝试读取请求体
                body = await request.body()
                if body:
                    # 重新设置请求体，以便后续处理可以再次读取
                    request._body = body
                    
                    # 解析JSON
                    try:
                        data = json.loads(body.decode())
                        if isinstance(data, dict) and "graph_id" in data:
                            return data["graph_id"]
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
            except Exception:
                pass
        
        # 4. 获取当前活跃图谱
        return await self._get_current_active_graph()
    
    async def _get_current_active_graph(self) -> Optional[str]:
        """获取当前活跃图谱ID"""
        try:
            config = await self._load_graphs_config()
            for graph_id, graph_info in config.items():
                if graph_info.get("is_active", False):
                    return graph_id
        except Exception as e:
            logger.warning(f"获取活跃图谱失败: {e}")
        
        return None
    
    async def _graph_exists(self, graph_id: str) -> bool:
        """检查图谱是否存在"""
        try:
            config = await self._load_graphs_config()
            return graph_id in config
        except Exception:
            return False
    
    async def _get_graph_info(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """获取图谱信息"""
        try:
            config = await self._load_graphs_config()
            return config.get(graph_id)
        except Exception:
            return None
    
    async def _load_graphs_config(self) -> Dict[str, Any]:
        """加载图谱配置"""
        if not self.graphs_config_file.exists():
            return {}
        
        try:
            with open(self.graphs_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载图谱配置失败: {e}")
            return {}


class BackwardCompatibilityHandler:
    """向后兼容处理器"""
    
    def __init__(self, graphs_dir: str = "./graphs"):
        self.graphs_dir = Path(graphs_dir)
        self.graphs_config_file = self.graphs_dir / "graphs_config.json"
    
    async def handle_legacy_request(self, request: Request) -> str:
        """处理旧版本API请求"""
        # 如果请求没有指定图谱，使用默认图谱
        if not hasattr(request.state, 'graph_id') or not request.state.graph_id:
            default_graph = await self.get_or_create_default_graph()
            request.state.graph_id = default_graph["graph_id"]
            request.state.graph_info = default_graph
        
        return request.state.graph_id
    
    async def get_or_create_default_graph(self) -> Dict[str, Any]:
        """获取或创建默认图谱"""
        config = await self._load_graphs_config()
        
        # 查找默认图谱
        for graph_id, graph_info in config.items():
            if graph_info.get('is_default', False) or graph_id == 'default':
                return {
                    "graph_id": graph_id,
                    **graph_info
                }
        
        # 查找第一个图谱
        if config:
            first_graph_id = list(config.keys())[0]
            return {
                "graph_id": first_graph_id,
                **config[first_graph_id]
            }
        
        # 如果没有图谱，创建默认图谱
        return await self._create_default_graph()
    
    async def _create_default_graph(self) -> Dict[str, Any]:
        """创建默认图谱"""
        from datetime import datetime
        
        graph_id = "default"
        graph_dir = self.graphs_dir / graph_id
        graph_dir.mkdir(parents=True, exist_ok=True)
        
        default_graph = {
            "graph_id": graph_id,
            "name": "Default Graph",
            "description": "Default graph for backward compatibility",
            "working_dir": str(graph_dir),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "is_active": True,
            "is_default": True,
            "entity_count": 0,
            "relation_count": 0,
            "document_count": 0,
            "metadata": {}
        }
        
        # 保存配置
        config = await self._load_graphs_config()
        config[graph_id] = default_graph
        await self._save_graphs_config(config)
        
        logger.info(f"创建默认图谱: {graph_id}")
        return default_graph
    
    async def _load_graphs_config(self) -> Dict[str, Any]:
        """加载图谱配置"""
        if not self.graphs_config_file.exists():
            return {}
        
        try:
            with open(self.graphs_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载图谱配置失败: {e}")
            return {}
    
    async def _save_graphs_config(self, config: Dict[str, Any]):
        """保存图谱配置"""
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.graphs_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存图谱配置失败: {e}")
            raise


def get_current_graph_id(request: Request) -> Optional[str]:
    """从请求中获取当前图谱ID"""
    return getattr(request.state, 'graph_id', None)


def get_current_graph_info(request: Request) -> Optional[Dict[str, Any]]:
    """从请求中获取当前图谱信息"""
    return getattr(request.state, 'graph_info', None)


def require_graph_context(request: Request) -> str:
    """要求图谱上下文，如果没有则抛出异常"""
    graph_id = get_current_graph_id(request)
    if not graph_id:
        raise HTTPException(400, "No graph context available")
    return graph_id
