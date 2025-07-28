# LightRAG Mini - 项目概览

## 🎯 项目目标

基于 LightRAG 核心功能，创建一个轻量级的知识图谱 RAG 系统，专注于：
- 核心功能保留
- 轻量化部署
- 易于集成
- 快速原型开发

## 📊 核心功能矩阵

| 功能模块 | 原始位置 | 轻量版实现 | 复杂度 | 状态 |
|---------|----------|-----------|--------|------|
| **文档处理** | `lightrag/api/routers/document_routes.py:542-732` | `core/document_processor.py` | 中等 | ✅ |
| **分块算法** | `lightrag/operate.py:47-99` | `core/operate.py:47-99` | 简单 | ✅ |
| **核心引擎** | `lightrag/lightrag.py:92-356` | `core/lightrag.py` | 高 | ✅ |
| **图谱操作** | `lightrag/api/routers/graph_routes.py` | `core/graph_ops.py` | 中等 | ✅ |
| **存储系统** | 多个存储后端 | `core/storage.py` | 低 | ✅ |
| **API 服务器** | `lightrag/api/lightrag_server.py` | `main.py` | 中等 | ✅ |
| **前端可视化** | `lightrag_webui/src/features/GraphViewer.tsx` | `frontend_example.html` | 简单 | ✅ |

## 🏗️ 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│           API Layer (FastAPI)       │  ← main.py
├─────────────────────────────────────┤
│       Business Logic Layer          │  ← core/lightrag.py
├─────────────────────────────────────┤
│         Operation Layer             │  ← core/operate.py
│  ┌─────────────┬─────────────────┐   │    core/document_processor.py
│  │ Text Chunk  │ Entity Extract  │   │    core/graph_ops.py
│  └─────────────┴─────────────────┘   │
├─────────────────────────────────────┤
│          Storage Layer              │  ← core/storage.py
│  ┌─────┬─────────┬───────┬────────┐  │
│  │ KV  │ Vector  │ Graph │DocStatus│  │
│  └─────┴─────────┴───────┴────────┘  │
└─────────────────────────────────────┘
```

### 数据流

```
文档/文本输入 → 文档处理器 → 分块算法 → 实体抽取 → 图谱构建 → 存储
                    ↓
用户查询 → 查询处理 → 相关检索 → 上下文构建 → LLM生成 → 返回结果
```

## 🔧 核心组件详解

### 1. 核心引擎 (`core/lightrag.py`)

**关键特性：**
- 简化的 LightRAG 类实现
- 支持文本和文件输入
- 4种查询模式（naive, local, global, hybrid）
- 内置缓存机制
- 环境配置支持

**主要方法：**
```python
async def ainsert(content, source)     # 插入内容
async def aquery(query, mode, top_k)   # 查询处理
async def get_knowledge_graph(...)     # 获取图谱
```

### 2. 文档处理器 (`core/document_processor.py`)

**支持格式：** 28种文件类型
**处理流程：**
1. 文件类型检测
2. 内容提取
3. 文本分块
4. 实体关系抽取
5. 状态跟踪

### 3. 分块算法 (`core/operate.py`)

**核心函数：** `chunking_by_token_size()`
**特性：**
- Token级别的精确分块
- 支持重叠片段
- 可配置分块大小
- 保持语义完整性

### 4. 图谱操作 (`core/graph_ops.py`)

**功能：**
- 实体/关系的增删改查
- 子图谱提取
- 向量相似度搜索
- 重复数据合并

### 5. 存储系统 (`core/storage.py`)

**简化实现：**
- JsonKVStorage: JSON文件存储
- NanoVectorDB: 内存向量数据库
- NetworkXStorage: 图数据存储
- DocStatusStorage: 文档状态管理

### 6. API 服务器 (`main.py`)

**端点设计：**
```
POST /upload        # 文件上传
POST /text          # 文本插入
POST /query         # 智能查询
POST /graph         # 图谱获取
GET  /graph/stats   # 统计信息
GET  /documents     # 文档状态
PUT  /entity/update # 实体更新
PUT  /relation/update # 关系更新
DELETE /entity/{id}  # 删除实体
DELETE /relation/{source}/{target} # 删除关系
```

## 📈 性能特征

### 复杂度分析

| 操作 | 时间复杂度 | 空间复杂度 | 备注 |
|------|-----------|-----------|------|
| 文档插入 | O(n·m) | O(n) | n=文档长度, m=LLM调用次数 |
| 实体检索 | O(k) | O(1) | k=检索数量 |
| 图谱遍历 | O(V+E) | O(V) | V=节点数, E=边数 |
| 向量搜索 | O(n·d) | O(n·d) | n=向量数量, d=维度 |

### 资源需求

**最小配置：**
- CPU: 2核
- 内存: 4GB
- 存储: 1GB
- Python: 3.8+

**推荐配置：**
- CPU: 4核
- 内存: 8GB
- 存储: 10GB
- GPU: 可选（用于本地模型）

## 🚀 部署方案

### 1. 本地开发

```bash
git clone <repository>
cd lightrag_mini
pip install -r requirements.txt
cp .env.example .env  # 配置环境变量
python main.py
```

### 2. Docker 部署

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

### 3. 云平台部署

- **Vercel/Netlify**: 适合演示
- **AWS/GCP/Azure**: 生产环境
- **Docker Compose**: 容器化部署

## 🔄 扩展指南

### 添加新的文档格式

```python
# 在 document_processor.py 中添加
async def _extract_new_format(self, file_path: Path) -> str:
    # 实现新格式的解析逻辑
    pass
```

### 集成新的LLM提供商

```python
# 在 main.py 中添加
async def new_llm_func(prompt: str, **kwargs) -> str:
    # 实现新LLM的调用逻辑
    pass
```

### 自定义存储后端

```python
# 继承基础存储类
class CustomStorage(JsonKVStorage):
    async def set(self, key: str, value: Any):
        # 自定义存储逻辑
        pass
```

## 📋 测试策略

### 单元测试
- 各模块独立测试
- Mock LLM调用
- 存储层测试

### 集成测试
- API端点测试
- 端到端流程测试
- 性能测试

### 压力测试
- 并发请求测试
- 大文档处理测试
- 内存泄漏测试

## 🚧 已知限制

1. **向量搜索性能**: 简化实现，大规模数据时性能有限
2. **并发处理**: 未实现分布式锁机制
3. **数据持久化**: JSON文件存储，不适合高并发
4. **缓存策略**: 内存缓存，重启后丢失
5. **错误处理**: 基础异常处理，可扩展

## 🎯 未来规划

### 短期目标 (1-2个月)
- [ ] 添加配置验证
- [ ] 实现分布式缓存
- [ ] 性能监控
- [ ] 更多LLM提供商支持

### 中期目标 (3-6个月)
- [ ] 支持增量更新
- [ ] 图谱可视化优化
- [ ] 批量操作API
- [ ] 插件系统

### 长期目标 (6个月+)
- [ ] 分布式部署
- [ ] 实时更新
- [ ] 多语言支持
- [ ] 企业级特性

## 💡 最佳实践

### 环境配置
1. 使用环境变量管理敏感信息
2. 为不同环境维护不同配置
3. 定期更新依赖版本

### 数据管理
1. 定期备份图谱数据
2. 监控存储空间使用
3. 实施数据清理策略

### 性能优化
1. 合理设置chunk大小
2. 调整LLM调用频率
3. 使用缓存减少重复计算

### 安全考虑
1. API访问控制
2. 输入数据验证
3. 敏感信息脱敏

---

## 📞 支持与反馈

如有问题或建议，请：
1. 查看 [README.md](README.md) 获取使用说明
2. 运行 `test_demo.py` 验证功能
3. 提交 Issue 报告问题

**项目维护者**: LightRAG 社区
**更新频率**: 持续更新
**许可证**: MIT