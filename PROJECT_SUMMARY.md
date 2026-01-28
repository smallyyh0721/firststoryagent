# Story Agent - Project Summary

## 项目概述

Story Agent 是一个基于 LLM 的智能故事写作代理，可以自动在 Notion 中生成和管理故事。该项目借鉴了 moltbot 的模块化架构思想，构建了一个可扩展、易维护的 AI 写作系统。

## 已完成的工作

### 1. 架构设计 ✅
- 分析了 moltbot 的 skill 机制
- 设计了模块化的服务架构
- 确定了技术栈：FastAPI + Notion API + GLM-4.7

### 2. Notion 集成 ✅
- 创建了 Notion API 测试脚本 (`verify_notion.py`)
- 实现了 Notion 客户端封装
- 支持故事的 CRUD 操作

### 3. LLM 集成 ✅
- 实现了 GLM-4.7 客户端
- 创建了故事生成的提示模板
- 支持多种故事类型

### 4. FastAPI 后端 ✅
- 实现了完整的 REST API
- 创建了数据模型
- 实现了 API 端点
- 配置了 CORS 和生命周期管理

### 5. 项目文档 ✅
- 主 README.md
- Moltbot 架构分析文档
- Notion 测试文档

## 项目结构

```
story-agent/
├── backend/                      # FastAPI 后端
│   ├── __init__.py
│   ├── main.py                  # 应用入口
│   ├── api/                     # API 端点
│   │   ├── __init__.py
│   │   └── stories.py          # 故事相关端点
│   ├── core/                    # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── llm/               # LLM 服务
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # GLM-4.7 客户端
│   │   │   └── prompts.py     # 提示模板
│   │   └── notion/            # Notion 服务
│   │       ├── __init__.py
│   │       └── client.py      # Notion API 客户端
│   └── models/                 # 数据模型
│       ├── __init__.py
│       └── story.py           # 故事模型
├── tests/                      # 测试文件（待实现）
├── .env.example               # 环境变量示例
├── requirements.txt            # Python 依赖
├── verify_notion.py          # Notion 连接验证工具
├── README.md                 # 项目文档
└── MOLTBOT_ANALYSIS.md       # Moltbot 架构分析
```

## 核心功能

### 1. 故事生成
- 使用 GLM-4.7 模型生成故事
- 支持多种类型（奇幻、科幻、浪漫、悬疑等）
- 可控制故事长度（短、中、长）
- 自动生成故事标题

### 2. Notion 集成
- 自动将故事保存到 Notion
- 支持故事分类和状态管理
- 追踪字数和创建时间
- 提供故事的完整 URL

### 3. API 接口
- `POST /api/stories/generate` - 生成新故事
- `GET /api/stories` - 列出所有故事
- `GET /api/stories/{id}` - 获取单个故事
- `PUT /api/stories/{id}` - 更新故事
- `DELETE /api/stories/{id}` - 删除故事

## 技术栈

- **Web 框架**: FastAPI
- **LLM**: ZhipuAI GLM-4.7
- **存储**: Notion API
- **HTTP 客户端**: httpx
- **数据验证**: Pydantic
- **环境管理**: python-dotenv

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写你的凭证：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
ZHIPUAI_API_KEY=your_zhipuai_api_key
```

### 3. 设置 Notion 数据库

创建一个 Notion 数据库，包含以下属性：

- **Title** (Title 类型)
- **Genre** (Select 类型)
- **Status** (Select 类型)
- **CreatedAt** (Date 类型)
- **WordCount** (Number 类型)

并将你的 Integration 连接到数据库。

### 4. 验证 Notion 连接

```bash
python verify_notion.py
```

### 5. 启动应用

```bash
cd backend
python main.py
```

或者使用 uvicorn：

```bash
uvicorn backend.main:app --reload
```

API 将在 `http://localhost:8000` 运行

访问 API 文档：`http://localhost:8000/docs`

## API 使用示例

### 生成故事

```bash
curl -X POST "http://localhost:8000/api/stories/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a story about a young wizard discovering ancient magic",
    "genre": "Fantasy",
    "length": "medium"
  }'
```

### 获取所有故事

```bash
curl "http://localhost:8000/api/stories"
```

### 获取特定故事

```bash
curl "http://localhost:8000/api/stories/{story_id}"
```

### 更新故事

```bash
curl -X PUT "http://localhost:8000/api/stories/{story_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "Completed"
  }'
```

### 删除故事

```bash
curl -X DELETE "http://localhost:8000/api/stories/{story_id}"
```

## Moltbot 架构借鉴

本项目成功应用了 moltbot 的核心架构原则：

### 1. 模块化设计
- ✅ 独立的服务模块（LLM、Notion）
- ✅ 清晰的职责分离
- ✅ 易于测试和维护

### 2. 可扩展性
- ✅ 轻松添加新功能
- ✅ 不修改核心代码
- ✅ 支持插件式扩展

### 3. 依赖注入
- ✅ 服务在应用启动时初始化
- ✅ 明确的生命周期管理
- ✅ 优雅的资源清理

### 4. 事件驱动
- ✅ API 端点作为"命令"
- ✅ 服务编排业务逻辑
- ✅ 清晰的数据流

## 未来扩展方向

### 1. 前端界面
- React/Vue Web 界面
- 故事可视化展示
- 实时编辑功能

### 2. 增强功能
- 故事评分系统
- 批量生成
- 故事续写功能
- 多语言支持

### 3. 智能特性
- 故事风格迁移
- 角色一致性检查
- 情节建议
- 自动大纲生成

### 4. 集成扩展
- 支持 OpenAI GPT-4
- 集成其他存储系统
- 邮件通知
- Webhook 支持

## 测试建议

### 单元测试
```bash
pytest tests/
```

### API 测试
使用 Swagger UI (`/docs`) 进行交互式测试

### Notion 集成测试
```bash
python verify_notion.py
```

## 常见问题

### Q: 如何获取 Notion Integration Token？
A: 访问 https://www.notion.so/my-integrations 创建 Integration

### Q: 如何获取 Notion Database ID？
A: 在数据库 URL 中找到，或从数据库设置中复制

### Q: 如何获取 ZhipuAI API Key？
A: 访问 https://open.bigmodel.cn/ 注册并获取 API Key

### Q: 支持哪些故事类型？
A: 支持 Fantasy, Sci-Fi, Romance, Mystery, Horror, Adventure, Drama, Comedy, Thriller 等

### Q: 如何修改故事长度？
A: 在请求中设置 `length` 参数为 "short"、"medium" 或 "long"

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License

## 致谢

- 借鉴了 [moltbot](https://github.com/moltbot/moltbot) 的架构设计
- 使用 ZhipuAI 的 GLM-4.7 模型
- 集成 Notion API

## 联系方式

如有问题或建议，请创建 Issue 或 Pull Request。

---

**祝你使用愉快！** 🎉