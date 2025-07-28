# LightRAG WebUI

LightRAG WebUI is a React-based web interface for interacting with the LightRAG system. It provides a user-friendly interface for querying, managing, and exploring LightRAG's functionalities.

## ✨ 新功能：多图谱支持

### 🎯 功能特性
- **多图谱管理** - 支持创建、切换、管理多个知识图谱
- **智能检索** - 检索功能支持指定图谱进行查询
- **状态指示** - 清晰的图谱选择和状态显示
- **用户体验** - 图谱切换时的状态提示和错误处理

### 🔧 主要改进
1. **检索页面优化** - 添加当前图谱指示器，支持图谱切换监听
2. **参数设置增强** - 优化图谱显示界面，增加视觉指示器
3. **API调用适配** - 前后端API支持图谱ID参数传递
4. **错误处理完善** - 修复500错误，增加友好的错误提示

### 📖 详细文档
完整的开发文档请参考：[多图谱适配开发文档](../docs/multi-graph-adaptation.md)

## Installation

1.  **Install Bun:**

    If you haven't already installed Bun, follow the official documentation: [https://bun.sh/docs/installation](https://bun.sh/docs/installation)

2.  **Install Dependencies:**

    In the `lightrag_webui` directory, run the following command to install project dependencies:

    ```bash
    bun install --frozen-lockfile
    ```

3.  **Build the Project:**

    Run the following command to build the project:

    ```bash
    bun run build --emptyOutDir
    ```

    This command will bundle the project and output the built files to the `lightrag/api/webui` directory.

## Development

- **Start the Development Server:**

  If you want to run the WebUI in development mode, use the following command:

  ```bash
  bun run dev
  ```

## Script Commands

The following are some commonly used script commands defined in `package.json`:

- `bun install`: Installs project dependencies.
- `bun run dev`: Starts the development server.
- `bun run build`: Builds the project.
- `bun run lint`: Runs the linter.
