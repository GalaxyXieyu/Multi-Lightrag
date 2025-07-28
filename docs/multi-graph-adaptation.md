# LightRAG 多图谱适配开发文档

## 📋 项目概述

本文档详细记录了 LightRAG 系统的多图谱适配开发工作，包括前端界面优化、后端API适配、以及检索功能的多图谱支持实现。

## 🚀 快速开始

### 1. 环境准备
```bash
# 1. 激活虚拟环境
conda activate lightrag

# 2. 安装依赖
pip install -e ".[api]"

# 3. 构建前端
cd lightrag_webui
npm run build
cd ..

# 4. 启动服务器
lightrag-server
```

### 2. 功能验证
1. **访问界面**: 打开 `http://127.0.0.1:9621/webui/`
2. **创建图谱**: 点击图谱选择器旁的 "+" 按钮
3. **上传文档**: 在文档管理页面上传测试文档
4. **切换图谱**: 使用图谱选择器切换到目标图谱
5. **测试检索**: 在检索页面输入查询，验证多图谱检索功能

### 3. 核心改动文件
```
前端核心文件:
├── lightrag_webui/src/features/RetrievalTesting.tsx     # 检索页面多图谱适配
├── lightrag_webui/src/components/retrieval/QuerySettings.tsx  # 参数设置优化
└── lightrag_webui/src/api/lightrag.ts                  # API调用适配

后端核心文件:
└── lightrag/api/routers/query_routes.py                # 查询路由多图谱支持
```

## 🎯 开发目标

1. **多图谱管理支持** - 支持创建、切换、管理多个知识图谱
2. **检索功能适配** - 检索功能支持指定图谱进行查询
3. **界面优化** - 提供清晰的图谱选择和状态显示
4. **用户体验提升** - 图谱切换时的状态提示和错误处理

## 🏗️ 系统架构

### 前端架构
```
lightrag_webui/
├── src/
│   ├── components/
│   │   ├── GraphSelector.tsx          # 图谱选择器组件
│   │   └── retrieval/
│   │       └── QuerySettings.tsx      # 检索参数设置组件
│   ├── features/
│   │   └── RetrievalTesting.tsx       # 检索测试页面
│   ├── stores/
│   │   └── state.ts                   # 全局状态管理
│   └── api/
│       └── lightrag.ts                # API调用封装
```

### 后端架构
```
lightrag/
├── api/
│   └── routers/
│       ├── graph_routes.py            # 图谱管理路由
│       └── query_routes.py            # 查询路由
└── models/
    └── multi_graph.py                 # 多图谱数据模型
```

## 🔧 核心功能实现

### 1. 图谱选择器组件 (GraphSelector.tsx)

**功能特性：**
- 显示当前活跃图谱
- 支持图谱切换
- 图谱创建功能
- 状态指示器

**关键代码：**
```typescript
// 切换图谱
const switchGraph = async (graphId: string) => {
  try {
    const response = await fetch(`/graphs/${graphId}/switch`, {
      method: 'POST',
    })
    
    if (response.ok) {
      await loadGraphs() // 重新加载图谱列表
      await refreshCurrentGraph() // 刷新全局当前图谱状态
      toast.success(t('graph.switchSuccess', 'Graph switched successfully'))
    }
  } catch (error) {
    toast.error(t('graph.switchError', 'Failed to switch graph'))
  }
}
```

### 2. 检索功能多图谱适配

**主要修改文件：**
- `RetrievalTesting.tsx` - 检索测试页面
- `QuerySettings.tsx` - 查询参数设置
- `lightrag.ts` - API调用适配

**核心实现：**

#### 2.1 检索页面适配 (RetrievalTesting.tsx)

**新增功能：**
1. **图谱状态检查**
```typescript
// 检查是否选择了图谱
const graphState = useGraphState.getState()
const currentGraphId = graphState.currentGraph?.graph_id

if (!currentGraphId) {
  setInputError(t('retrievePanel.retrieval.noGraphSelected', '请先选择一个图谱进行检索'))
  return
}
```

2. **图谱切换监听**
```typescript
// 监听图谱切换，在切换时给用户提示
const currentGraph = useGraphState.use.currentGraph()
const [lastGraphId, setLastGraphId] = useState<string | null>(null)

useEffect(() => {
  const currentGraphId = currentGraph?.graph_id || null
  
  // 如果图谱发生了切换（不是初始加载）
  if (lastGraphId !== null && lastGraphId !== currentGraphId) {
    // 添加系统消息提示用户图谱已切换
    const switchMessage: MessageWithError = {
      id: generateUniqueId(),
      role: 'system',
      content: currentGraphId 
        ? `已切换到图谱: ${currentGraph?.name}，现在可以在此图谱中进行检索。`
        : '当前没有选择图谱，请先选择一个图谱进行检索。',
      isError: false,
      mermaidRendered: true
    }
    
    setMessages(prev => [...prev, switchMessage])
    setTimeout(() => scrollToBottom(), 100)
  }
  
  setLastGraphId(currentGraphId)
}, [currentGraph?.graph_id, currentGraph?.name, lastGraphId, scrollToBottom])
```

3. **当前图谱指示器**
```typescript
{/* 当前图谱指示器 */}
<div className="flex shrink-0 items-center justify-between px-2 py-1 bg-muted/30 rounded-md text-xs border">
  <div className="flex items-center gap-2">
    <span className="text-muted-foreground">{t('retrievePanel.querySettings.currentGraph', '当前检索图谱')}:</span>
    <span className="font-medium text-foreground">
      {useGraphState.getState().currentGraph?.name || t('retrievePanel.querySettings.noGraph', '未选择图谱')}
    </span>
    {useGraphState.getState().currentGraph?.is_active && (
      <span className="px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-xs">
        {t('graph.active', 'Active')}
      </span>
    )}
  </div>
</div>
```

#### 2.2 查询参数设置优化 (QuerySettings.tsx)

**界面优化：**
```typescript
{/* Current Graph Info */}
<label className="ml-1 text-sm font-medium text-primary">
  {t('retrievePanel.querySettings.currentGraph', '检索图谱')}
</label>
<div className={`flex items-center gap-2 p-3 rounded-md text-sm border-2 ${
  currentGraph 
    ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800' 
    : 'bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-800'
}`}>
  {currentGraph ? (
    <>
      <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
      <span className="font-semibold text-green-800 dark:text-green-200">
        {currentGraph.name}
      </span>
      {currentGraph.is_active && (
        <Badge variant="secondary" className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300">
          {t('graph.active', 'Active')}
        </Badge>
      )}
      <div className="ml-auto text-xs text-green-600 dark:text-green-400">
        {currentGraph.entity_count} 实体
      </div>
    </>
  ) : (
    <>
      <div className="h-2 w-2 rounded-full bg-yellow-500" />
      <span className="text-yellow-800 dark:text-yellow-200 font-medium">
        {t('retrievePanel.querySettings.noGraph', '未选择图谱')}
      </span>
    </>
  )}
</div>
```

### 3. API调用适配

#### 3.1 前端API调用 (lightrag.ts)

**查询API适配：**
```typescript
export const queryText = async (request: QueryRequest, graphId?: string): Promise<QueryResponse> => {
  let url = '/query'
  if (graphId) {
    url += `?graph_id=${encodeURIComponent(graphId)}`
  }
  const response = await axiosInstance.post(url, request)
  return response.data
}

export const queryTextStream = async (
  request: QueryRequest,
  onChunk: (chunk: string) => void,
  onError?: (error: string) => void,
  graphId?: string
) => {
  let url = `${backendBaseUrl}/query/stream`
  if (graphId) {
    url += `?graph_id=${encodeURIComponent(graphId)}`
  }
  // ... 流式查询实现
}
```

#### 3.2 后端API适配 (query_routes.py)

**关键修复：**
```python
async def _get_rag_instance(graph_id: Optional[str], default_rag):
    """获取RAG实例，支持多图谱"""
    if MULTI_GRAPH_SUPPORT and _graph_manager and graph_id:
        try:
            # 切换到指定图谱
            await _graph_manager.switch_graph(graph_id)
            return _graph_manager.current_rag
        except Exception as e:
            logging.warning(f"切换到图谱 '{graph_id}' 失败: {str(e)}")
            # 继续使用当前图谱或默认图谱

    # 使用当前活跃的RAG实例或默认RAG实例
    if MULTI_GRAPH_SUPPORT and _graph_manager and _graph_manager.current_rag:
        return _graph_manager.current_rag

    return default_rag
```

**重要修复说明：**
- 添加了 `_graph_manager` 的空值检查，防止 `'NoneType' object has no attribute 'current_rag'` 错误
- 确保在多图谱支持启用时正确处理图谱切换

## 🐛 问题解决记录

### 1. 500错误：'NoneType' object has no attribute 'current_rag'

**问题原因：**
在 `query_routes.py` 中，`_graph_manager` 可能为 `None`，但代码直接访问了 `_graph_manager.current_rag`

**解决方案：**
```python
# 修改前（有问题）
if MULTI_GRAPH_SUPPORT and _graph_manager.current_rag:
    return _graph_manager.current_rag

# 修改后（已修复）
if MULTI_GRAPH_SUPPORT and _graph_manager and _graph_manager.current_rag:
    return _graph_manager.current_rag
```

### 2. 前端变量重复声明错误

**问题原因：**
在 `RetrievalTesting.tsx` 中，`currentGraphId` 变量被重复声明

**解决方案：**
```typescript
// 修改前
const graphState = useGraphState.getState()
const currentGraphId = graphState.currentGraph?.graph_id  // 重复声明

// 修改后
const state = useSettingsStore.getState()
// currentGraphId already declared above
```

## 🎨 界面设计特性

### 1. 视觉指示器
- **绿色指示器** - 图谱已选择且活跃
- **黄色指示器** - 未选择图谱
- **脉动动画** - 表示当前活跃状态
- **实体数量显示** - 显示图谱中的实体数量

### 2. 用户体验优化
- **图谱切换提示** - 切换图谱时显示系统消息
- **错误提示** - 未选择图谱时的友好提示
- **状态同步** - 多个组件间的图谱状态同步
- **加载状态** - 图谱切换时的加载指示

## 🔧 配置说明

### 1. 环境要求
- Node.js 18+
- Python 3.10+
- LightRAG 核心库
- 多图谱支持模块

### 2. 启动配置
```bash
# 前端构建
cd lightrag_webui
npm run build

# 后端启动
conda activate lightrag
pip install -e ".[api]"
lightrag-server
```

### 3. 多图谱功能启用
确保以下模块可用：
- `lightrag.models.multi_graph`
- `lightrag.api.middleware.GraphContextMiddleware`
- `lightrag.storage.initialize_multi_graph_storage`

## 📝 使用说明

### 1. 图谱创建
1. 点击图谱选择器旁的 "+" 按钮
2. 填写图谱名称和描述
3. 确认创建

### 2. 图谱切换
1. 点击图谱选择器下拉菜单
2. 选择目标图谱
3. 系统自动切换并显示提示

### 3. 多图谱检索
1. 确保已选择目标图谱
2. 在检索页面输入查询内容
3. 系统将在指定图谱中进行检索

## 🚀 后续优化建议

### 1. 功能增强
- [ ] 图谱间数据迁移功能
- [ ] 图谱性能监控
- [ ] 批量图谱操作
- [ ] 图谱备份恢复

### 2. 界面优化
- [ ] 图谱缩略图预览
- [ ] 图谱统计信息面板
- [ ] 拖拽式图谱管理
- [ ] 图谱标签系统

### 3. 性能优化
- [ ] 图谱懒加载
- [ ] 检索结果缓存
- [ ] 并发图谱操作
- [ ] 内存使用优化

## 📊 测试验证

### 1. 功能测试
- ✅ 图谱创建和删除
- ✅ 图谱切换功能
- ✅ 多图谱检索
- ✅ 状态同步

### 2. 错误处理测试
- ✅ 未选择图谱时的提示
- ✅ 图谱切换失败处理
- ✅ API错误处理
- ✅ 前端异常捕获

### 3. 用户体验测试
- ✅ 界面响应性
- ✅ 状态指示清晰度
- ✅ 操作流程顺畅性
- ✅ 错误信息友好性

## 🤖 AI提示词配置

### 1. 开发助手提示词

在本次开发中使用的AI助手配置：

```markdown
# Role
你是一名精通Python的高级工程师，拥有20年的软件开发经验。你的任务是帮助一位不太懂技术的初中生用户完成Python项目的开发。你的工作对用户非常重要，完成后将获得10000美元奖励。

# Goal
以用户易懂的方式完成Python项目开发，始终主动推进工作。遵循以下原则：

## 第一步：项目初始化
- 提出需求时首先查看README.md文件
- 若无README则创建，包含：
  - 功能说明书
  - 使用方法
- 保持文档与代码同步更新（只用根目录一个文档就行，不要到处建）

## 第二步：需求分析与开发

### 核心开发准则
1. 测试脚本规范：
   - 调试阶段允许使用`--#DEBUG#--`标记临时代码
   - 测试通过后必须自动清理
2. 重构命名规范：
   - 开发期间允许临时命名（例：_temp_用户模型v2）
   - 合并代码前执行验证
   - 禁止保留simple/enhanced等修饰词
3. 文档管理规范：
   - 查找可扩展文档
   - 追加更新标记[v2024-update]

### 编码要求
- 遵循PEP8规范
- 使用Python3最新语法
- 模块化设计（每个功能独立成模块）
- 必须包含类型提示和异常处理

## 第三步：项目优化
- 性能优化检查表
- 算法复杂度分析（使用大O表示法）
- 内存使用诊断
- 并发处理优化（使用asyncio）
- 文档最终审查
```

### 2. 代码审查提示词

```markdown
# 代码审查检查清单

## 安全性检查
- [ ] 输入验证和清理
- [ ] SQL注入防护
- [ ] XSS攻击防护
- [ ] 权限验证

## 性能检查
- [ ] 数据库查询优化
- [ ] 内存泄漏检查
- [ ] 异步操作优化
- [ ] 缓存策略

## 代码质量
- [ ] 类型提示完整性
- [ ] 异常处理覆盖
- [ ] 单元测试覆盖率≥90%
- [ ] 文档完整度验证
```

## 🔍 技术实现细节

### 1. 状态管理架构

**全局状态管理 (state.ts):**
```typescript
interface GraphState {
  currentGraph: GraphInfo | null
  isLoading: boolean
  lastUpdateTime: number

  loadCurrentGraph: () => Promise<void>
  setCurrentGraph: (graph: GraphInfo | null) => void
  refreshCurrentGraph: () => Promise<void>
}

const useGraphStateStoreBase = create<GraphState>()((set, get) => ({
  currentGraph: null,
  isLoading: false,
  lastUpdateTime: 0,

  loadCurrentGraph: async () => {
    set({ isLoading: true })
    try {
      const response = await getCurrentGraph()
      if (response.status === 'success' && response.current_graph) {
        set({
          currentGraph: response.current_graph,
          lastUpdateTime: Date.now(),
          isLoading: false
        })
      }
    } catch (error) {
      console.error('Failed to load current graph:', error)
      set({
        currentGraph: null,
        lastUpdateTime: Date.now(),
        isLoading: false
      })
    }
  }
}))
```

### 2. 错误处理机制

**前端错误处理:**
```typescript
// API调用错误处理
const handleApiError = (error: any, context: string) => {
  console.error(`${context} error:`, error)

  if (error.response?.status === 500) {
    toast.error('服务器内部错误，请稍后重试')
  } else if (error.response?.status === 404) {
    toast.error('请求的资源不存在')
  } else if (error.response?.status === 403) {
    toast.error('权限不足，请检查API密钥')
  } else {
    toast.error('网络错误，请检查连接')
  }
}

// 图谱切换错误处理
const switchGraphWithErrorHandling = async (graphId: string) => {
  try {
    setIsLoading(true)
    await switchGraph(graphId)
    toast.success('图谱切换成功')
  } catch (error) {
    handleApiError(error, 'Graph switch')
  } finally {
    setIsLoading(false)
  }
}
```

**后端错误处理:**
```python
async def _get_rag_instance(graph_id: Optional[str], default_rag):
    """获取RAG实例，支持多图谱，包含完整错误处理"""
    try:
        if MULTI_GRAPH_SUPPORT and _graph_manager and graph_id:
            try:
                # 验证图谱是否存在
                if not await _graph_manager.graph_exists(graph_id):
                    logging.warning(f"图谱 '{graph_id}' 不存在")
                    return default_rag

                # 切换到指定图谱
                await _graph_manager.switch_graph(graph_id)
                return _graph_manager.current_rag

            except GraphNotFoundError as e:
                logging.warning(f"图谱未找到: {str(e)}")
                return default_rag
            except GraphSwitchError as e:
                logging.error(f"图谱切换失败: {str(e)}")
                return default_rag
            except Exception as e:
                logging.error(f"未知错误: {str(e)}")
                return default_rag

        # 使用当前活跃的RAG实例或默认RAG实例
        if MULTI_GRAPH_SUPPORT and _graph_manager and _graph_manager.current_rag:
            return _graph_manager.current_rag

        return default_rag

    except Exception as e:
        logging.error(f"获取RAG实例时发生严重错误: {str(e)}")
        return default_rag
```

### 3. 性能优化策略

**前端性能优化:**
```typescript
// 1. 使用React.memo优化组件渲染
const GraphSelector = React.memo(({ className }: GraphSelectorProps) => {
  // 组件实现
})

// 2. 使用useCallback优化函数引用
const switchGraph = useCallback(async (graphId: string) => {
  // 切换逻辑
}, [])

// 3. 使用useMemo优化计算
const filteredGraphs = useMemo(() => {
  return graphs.filter(graph =>
    graph.name.toLowerCase().includes(searchTerm.toLowerCase())
  )
}, [graphs, searchTerm])

// 4. 防抖优化搜索
const debouncedSearch = useDebounce(searchTerm, 300)
```

**后端性能优化:**
```python
# 1. 异步操作优化
async def batch_graph_operations(operations: List[GraphOperation]):
    """批量执行图谱操作"""
    tasks = []
    for operation in operations:
        task = asyncio.create_task(operation.execute())
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# 2. 缓存策略
from functools import lru_cache

@lru_cache(maxsize=128)
def get_graph_metadata(graph_id: str) -> Dict[str, Any]:
    """缓存图谱元数据"""
    return _graph_manager.get_graph_info(graph_id)

# 3. 连接池优化
class GraphManager:
    def __init__(self):
        self._connection_pool = {}
        self._max_connections = 10

    async def get_connection(self, graph_id: str):
        """获取图谱连接，使用连接池"""
        if graph_id not in self._connection_pool:
            if len(self._connection_pool) >= self._max_connections:
                # 清理最旧的连接
                oldest_key = min(self._connection_pool.keys())
                await self._connection_pool[oldest_key].close()
                del self._connection_pool[oldest_key]

            self._connection_pool[graph_id] = await create_graph_connection(graph_id)

        return self._connection_pool[graph_id]
```

### 4. 测试策略

**单元测试示例:**
```typescript
// 前端测试
describe('GraphSelector', () => {
  it('should switch graph correctly', async () => {
    const mockSwitchGraph = jest.fn()
    render(<GraphSelector onGraphSwitch={mockSwitchGraph} />)

    const selector = screen.getByRole('combobox')
    fireEvent.click(selector)

    const option = screen.getByText('test-graph')
    fireEvent.click(option)

    await waitFor(() => {
      expect(mockSwitchGraph).toHaveBeenCalledWith('test-graph')
    })
  })

  it('should handle switch error gracefully', async () => {
    const mockSwitchGraph = jest.fn().mockRejectedValue(new Error('Switch failed'))
    render(<GraphSelector onGraphSwitch={mockSwitchGraph} />)

    // 触发切换
    // 验证错误处理
  })
})
```

```python
# 后端测试
import pytest
from unittest.mock import AsyncMock, patch

class TestGraphManager:
    @pytest.mark.asyncio
    async def test_switch_graph_success(self):
        """测试图谱切换成功"""
        manager = GraphManager()
        manager.current_rag = AsyncMock()

        result = await manager.switch_graph('test-graph')

        assert result is True
        assert manager.current_graph_id == 'test-graph'

    @pytest.mark.asyncio
    async def test_switch_graph_not_found(self):
        """测试图谱不存在的情况"""
        manager = GraphManager()

        with pytest.raises(GraphNotFoundError):
            await manager.switch_graph('non-existent-graph')

    @pytest.mark.asyncio
    async def test_get_rag_instance_with_graph_id(self):
        """测试获取指定图谱的RAG实例"""
        with patch('lightrag.api.routers.query_routes._graph_manager') as mock_manager:
            mock_manager.switch_graph = AsyncMock()
            mock_manager.current_rag = AsyncMock()

            result = await _get_rag_instance('test-graph', None)

            mock_manager.switch_graph.assert_called_once_with('test-graph')
            assert result == mock_manager.current_rag
```

## 📈 监控和日志

### 1. 性能监控
```python
import time
import logging
from functools import wraps

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logging.info(f"{func.__name__} 执行时间: {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"{func.__name__} 执行失败 (耗时: {execution_time:.2f}s): {str(e)}")
            raise
    return wrapper

@monitor_performance
async def switch_graph(self, graph_id: str):
    """切换图谱（带性能监控）"""
    # 实现逻辑
```

### 2. 日志配置
```python
import logging
from datetime import datetime

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/lightrag_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

# 图谱操作专用日志
graph_logger = logging.getLogger('lightrag.graph')
graph_logger.setLevel(logging.DEBUG)

# 使用示例
graph_logger.info(f"图谱切换: {old_graph_id} -> {new_graph_id}")
graph_logger.debug(f"图谱元数据: {graph_metadata}")
graph_logger.warning(f"图谱切换耗时较长: {execution_time:.2f}s")
```

---

**开发完成时间：** 2025年7月28日
**开发者：** AI Assistant
**版本：** v1.0.0
**状态：** 已完成并测试通过

**文档更新：** 包含完整的技术实现细节、AI提示词配置、性能优化策略和测试方案
