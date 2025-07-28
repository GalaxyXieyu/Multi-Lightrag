# LightRAG Mini

轻量级的知识图谱 RAG (检索增强生成) 系统，基于 LightRAG 核心功能构建。

## 🚀 特性

- **智能文档处理**: 支持多种文件格式（TXT, PDF, DOCX, PPTX, XLSX 等）
- **知识图谱构建**: 自动提取实体和关系，构建语义丰富的知识网络
- **多模态查询**: 支持文本、实体、关系和混合查询模式
- **轻量级设计**: 简化版本，易于部署和集成
- **RESTful API**: 完整的 API 接口，便于前端集成
- **环境配置**: 通过 .env 文件灵活配置大模型参数

## 📁 项目结构

```
lightrag_mini/
├── .env                    # 环境配置文件
├── requirements.txt        # Python 依赖
├── main.py                # FastAPI 服务器
├── start.sh               # 启动脚本
├── test_demo.py           # 测试脚本
├── core/                  # 核心模块
│   ├── __init__.py
│   ├── lightrag.py        # 核心引擎
│   ├── operate.py         # 分块和实体提取
│   ├── document_processor.py # 文档处理
│   ├── graph_ops.py       # 图谱操作
│   ├── storage.py         # 存储实现
│   └── utils.py           # 工具函数
├── cache/                 # 数据存储目录
└── inputs/                # 文档输入目录
```

## 🛠️ 安装和配置

### 1. 环境要求

- Python 3.8+
- 大模型 API 访问权限（OpenAI 兼容）

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

复制并编辑 `.env` 文件，配置你的大模型参数：

```bash
# LLM 配置
LLM_BINDING=openai
LLM_MODEL=gpt-4o
LLM_BINDING_HOST=https://yunwu.ai/v1
LLM_BINDING_API_KEY=your-api-key-here

# Embedding 配置
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_BINDING_HOST=https://api.siliconflow.cn/v1/
EMBEDDING_BINDING_API_KEY=your-embedding-api-key-here

# 其他配置
SUMMARY_LANGUAGE=Chinese
CHUNK_SIZE=1200
CHUNK_OVERLAP_SIZE=100
```

## 🚀 启动服务

### 方法 1: 使用启动脚本

```bash
chmod +x start.sh
./start.sh
```

### 方法 2: 直接启动

```bash
python main.py
```

服务启动后，访问：
- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 📝 API 使用示例

### 1. 上传文档

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf"
```

### 2. 插入文本

```bash
curl -X POST "http://localhost:8000/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "人工智能是计算机科学的一个分支...",
    "source": "manual_input"
  }'
```

### 3. 查询

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？",
    "mode": "hybrid",
    "top_k": 10
  }'
```

### 4. 获取知识图谱

```bash
curl -X POST "http://localhost:8000/graph" \
  -H "Content-Type: application/json" \
  -d '{
    "max_nodes": 100,
    "max_depth": 2
  }'
```

### 5. 查看图谱统计

```bash
curl -X GET "http://localhost:8000/graph/stats"
```

## 🧪 测试

运行测试脚本验证功能：

```bash
# 确保服务正在运行
python test_demo.py
```

测试脚本会执行以下操作：
- 健康检查
- 文本插入
- 文件上传
- 多种查询模式
- 知识图谱获取
- 统计信息查看

## 🔧 查询模式

### 1. naive 模式
基于文本块的简单关键词匹配查询

### 2. local 模式
基于实体的局部知识图谱查询

### 3. global 模式
基于关系的全局知识图谱查询

### 4. hybrid 模式 (推荐)
结合实体和关系的混合查询模式

## 📊 支持的文件格式

- **文本文件**: .txt, .md, .log, .conf, .ini, .properties
- **文档文件**: .pdf, .docx, .pptx, .xlsx, .rtf, .odt
- **标记语言**: .html, .htm, .xml, .json, .yaml, .yml
- **代码文件**: .py, .js, .ts, .java, .cpp, .c, .go, .rb, .php
- **样式文件**: .css, .scss, .less
- **其他**: .tex, .epub, .csv, .sql, .bat, .sh

## 🔍 核心功能

### 文档处理流程
1. **文件解析**: 根据文件类型提取文本内容
2. **文本分块**: 按 token 大小智能分割文档
3. **实体抽取**: 使用 LLM 从文本块中提取实体和关系
4. **图谱构建**: 将实体和关系存储到知识图谱
5. **向量索引**: 为实体和关系创建向量表示

### 查询处理流程
1. **查询理解**: 分析用户查询意图
2. **相关检索**: 根据查询模式检索相关信息
3. **上下文构建**: 组织检索到的信息
4. **响应生成**: 使用 LLM 生成最终回答

## 🚧 开发说明

### 扩展 LLM 支持

在 `main.py` 中添加新的 LLM 函数：

```python
async def your_llm_func(prompt: str, **kwargs) -> str:
    # 实现你的 LLM 调用逻辑
    pass

def get_llm_func():
    llm_binding = os.getenv("LLM_BINDING", "openai").lower()
    if llm_binding == "your_provider":
        return your_llm_func
    # ...
```

### 自定义存储后端

继承基础存储类并实现你的存储逻辑：

```python
from core.storage import JsonKVStorage

class YourCustomStorage(JsonKVStorage):
    async def set(self, key: str, value: Any):
        # 实现你的存储逻辑
        pass
```

## 📚 与完整版 LightRAG 的差异

| 功能 | LightRAG Mini | 完整版 LightRAG |
|------|---------------|------------------|
| 代码量 | ~1500 行 | ~15000 行 |
| 存储后端 | JSON + NetworkX | 支持 Neo4j, PostgreSQL, MongoDB 等 |
| 部署复杂度 | 低 | 中等 |
| 功能完整性 | 核心功能 | 全功能 |
| 适用场景 | 原型开发、小规模应用 | 生产环境、大规模应用 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License