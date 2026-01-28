# Notion API 测试脚本使用指南

## 概述

`test_notion.py` 是一个交互式测试脚本，用于验证您的 Notion Integration Token 和 Database ID 是否配置正确。

## 前置条件

1. 已在 Notion 中创建 Integration
   - 访问：https://www.notion.so/my-integrations
   - 创建一个 Integration，并获取 Token

2. 已在 Notion 中创建 Database
   - 创建一个 Table Database
   - 获取 Database ID（从 URL 中复制）

3. 已将 Integration 连接到 Database
   - 打开 Database 设置
   - 点击 "Add connections"
   - 添加您的 Integration

## 安装依赖

```bash
pip install -r requirements.txt
```

或者直接安装：

```bash
pip install notion-client
```

## 使用步骤

### 1. 运行测试脚本

```bash
python test_notion.py
```

### 2. 输入配置信息

脚本会依次提示：

1. **Notion Integration Token**
   - 从 https://www.notion.so/my-integrations 获取
   - 格式：`secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - 重要：复制完整 Token，包括 `secret_` 前缀

2. **Database ID**
   - 从 Notion Database 的 URL 中获取
   - 格式：32位字符，可能包含连字符
   - 示例：`a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### 3. 查看测试结果

脚本会自动执行三个测试：

**步骤 1: 测试 Integration Token**
- ✅ 验证 Token 格式
- ✅ 连接到 Notion API
- ✅ 获取用户信息

**步骤 2: 测试 Database 访问**
- ✅ 验证 Database ID 格式
- ✅ 查询 Database 信息
- ✅ 显示 Database 属性和记录数

**步骤 3: 测试创建测试页面（可选）**
- ✅ 创建测试页面
- ✅ 验证写入权限
- ✅ 提供页面 URL

## 测试成功后的输出示例

```
╔═════════════════════════════════════════════════════════╗
║            Notion API 集成测试工具                        ║
║                                                            ║
║  这个脚本将测试您的 Notion Integration Token 和          ║
║  Database ID 是否配置正确                                 ║
╚═════════════════════════════════════════════════════════╝

请输入您的Notion配置信息:

请输入 Notion Integration Token: secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
请输入 Database ID: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

============================================================
步骤 1: 测试Integration Token
============================================================
ℹ️  正在连接Notion API...
✅ Token有效！连接的用户: Story Agent (integration)
ℹ️  用户ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

============================================================
步骤 2: 测试Database访问
============================================================
ℹ️  正在查询Database: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
✅ 成功访问Database！
ℹ️  Database标题: 故事库
Database属性:
  • Title (title)
  • Genre (select)
  • Status (select)
  • CreatedAt (date)
  • WordCount (number)
✅ Database当前包含 0 条记录

============================================================
步骤 3: 测试创建测试页面（可选）
============================================================
是否创建测试页面来验证写入权限？(y/n): y
ℹ️  正在创建测试页面...
✅ 测试页面创建成功！
ℹ️  页面ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ℹ️  页面URL: https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

============================================================
🎉 测试完成！
============================================================

✅ Token: 有效
✅ Database: 可访问
✅ 写入权限: 正常

📝 您的配置信息:
  Token: secret_xxxxxxxxxxxxx...xxxxxxxxxx
  Database ID: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

💡 下一步:
  1. 将这些信息保存到 .env 文件:
     NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     NOTION_DATABASE_ID=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
  2. 确保您的Database有以下属性:
     - Title (Title类型)
     - Genre (Select类型)
     - Status (Select类型)
     - CreatedAt (Date类型)
     - WordCount (Number类型)
  3. 开始使用Story Agent！

============================================================
```

## 常见错误和解决方案

### 错误 1: Token无效

```
❌ Token无效或已过期
ℹ️  错误详情: [code: unauthorized] ...
```

**解决方案：**
1. 检查 Token 是否完整复制
2. 确保包含 `secret_` 前缀
3. 重新从 https://www.notion.so/my-integrations 获取 Token

### 错误 2: Database不存在

```
❌ Database不存在或ID错误
ℹ️  请检查:
   1. Database ID是否正确（32位）
   2. Database是否已删除
```

**解决方案：**
1. 打开 Notion Database
2. 查看 URL：`https://www.notion.so/workspace/[database-id]?v=...`
3. 复制 `[database-id]` 部分（32位字符）
4. 重新运行测试脚本

### 错误 3: 未授权访问

```
❌ 未授权访问此Database
ℹ️  请确保:
   1. 在Database设置中添加了Integration连接
   2. Integration有正确的权限（Read content, Insert content）
```

**解决方案：**
1. 打开 Notion Database
2. 点击右上角 "..." 菜单
3. 选择 "Add connections"
4. 找到并选择您的 Integration
5. 确认添加

### 错误 4: 缺少依赖

```
ModuleNotFoundError: No module named 'notion_client'
```

**解决方案：**

```bash
pip install notion-client
```

## Database 属性要求

为了完整使用 Story Agent，建议您的 Notion Database 包含以下属性：

| 属性名 | 类型 | 必需 | 说明 |
|---------|------|--------|------|
| Title | Title | ✅ | 故事标题（默认属性） |
| Genre | Select | ✅ | 故事类型 |
| Status | Select | ✅ | 状态（草稿、完成、已发布） |
| CreatedAt | Date | ✅ | 创建日期 |
| WordCount | Number | ✅ | 字数统计 |
| Summary | Text | ⭕ | 故事摘要（可选） |
| Tags | Multi-select | ⭕ | 标签（可选） |

### 如何创建这些属性

1. 打开 Notion Database
2. 点击右上角 "+" 添加新属性
3. 选择类型（Title、Select、Date、Number 等）
4. 输入属性名称（必须与脚本中的名称一致）
5. 对于 Select 类型，添加选项：
   - Genre: 科幻、奇幻、悬疑、爱情、历史、现实主义
   - Status: 草稿、完成、已发布

## 测试成功后的下一步

### 1. 创建 .env 文件

在项目根目录创建 `.env` 文件：

```bash
# Notion 配置
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### 2. 确保忽略文件

将 `.env` 添加到 `.gitignore`，避免将敏感信息提交到版本控制：

```gitignore
# Environment variables
.env
.env.local
.env.*.local
```

### 3. 开始使用 Story Agent

测试成功后，您就可以：
- 运行完整的故事生成应用
- 自动将故事保存到 Notion
- 管理和查看您的故事库

## 高级用法

### 批量测试多个 Database

您可以修改脚本，循环测试多个 Database ID：

```python
databases = [
    "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7"
]

for db_id in databases:
    test_database(client, db_id)
```

### 自动化测试

可以将脚本集成到 CI/CD 流程中，定期检查 API 连接状态。

## 安全建议

1. **不要在代码中硬编码 Token**
   - 使用环境变量
   - 使用 `.env` 文件

2. **Token 定期轮换**
   - 在 Notion 设置中重新生成 Token
   - 建议每 6 个月更换一次

3. **最小权限原则**
   - 只勾选需要的 Capabilities
   - 避免使用 "Full Access"

4. **监控 API 使用**
   - Notion 免费版有 API 调用限制
   - 可在 Integrations 页面查看使用情况

## 故障排除

### 问题：脚本运行无响应

**可能原因：** 网络连接问题

**解决方案：**
1. 检查网络连接
2. 尝试使用代理
3. 检查 Notion 服务状态

### 问题：Token 格式验证失败

**可能原因：** 复制不完整

**解决方案：**
1. 确保从 Notion Integrations 页面完整复制
2. Token 应该以 `secret_` 开头
3. 长度应该超过 50 个字符

### 问题：Database ID 格式验证失败

**可能原因：** 复制了额外的字符

**解决方案：**
1. 只复制 32 位字符部分
2. 如果包含连字符，只保留字母和数字

## 获取帮助

如果您遇到问题：

1. 查看 Notion API 文档：https://developers.notion.com/
2. 检查 Notion 社区：https://www.notion.so/help
3. 查看错误日志获取详细信息

## 许可证

本测试脚本是开源的，可以自由使用和修改。