# Story Agent - Frontend

AI故事生成器的Web界面

## 功能特性

### 🎭 故事生成
- 选择故事类型（奇幻、科幻、悬疑、浪漫、冒险、恐怖）
- 设置故事长度（短篇、中篇、长篇）
- 输入创意提示
- AI自动生成故事
- 实时生成状态显示

### 📖 故事管理
- 查看所有已生成的故事
- 按类型筛选故事
- 查看故事详情
- 删除不需要的故事
- 一键打开Notion查看完整内容

### ✨ 其他功能
- 复制故事内容到剪贴板
- 重新生成故事
- 清除结果重新开始
- 响应式设计，支持移动端
- 友好的错误提示

## 快速开始

### 1. 启动后端服务

```bash
# 在项目根目录
python -m uvicorn backend.main:app --reload
```

后端将在 http://localhost:8000 启动

### 2. 打开前端页面

有两种方式：

#### 方式1：直接打开HTML文件
```bash
# 在浏览器中打开
frontend/index.html
```

#### 方式2：使用本地服务器（推荐）

使用Python的HTTP服务器：
```bash
cd frontend
python -m http.server 3000
```

然后访问：http://localhost:3000

或使用Node.js的http-server：
```bash
cd frontend
npx http-server -p 3000
```

然后访问：http://localhost:3000

## 使用指南

### 生成故事

1. 选择故事类型
   - 点击不同的类型图标选择（默认：奇幻）
   
2. 选择故事长度
   - 短篇：约500字
   - 中篇：约1500字（默认）
   - 长篇：约3000字

3. 输入创意提示
   - 在文本框中输入你的故事构思
   - 提示越详细，生成的故事越好
   - 至少10个字符

4. 点击"生成故事"按钮
   - 等待AI创作（可能需要几秒钟）
   - 生成成功后自动显示结果

5. 查看结果
   - 故事标题和预览会显示在页面上
   - 可以复制内容或打开Notion查看完整版
   - 点击"重新生成"可以生成新版本
   - 点击"清除"可以清空结果重新开始

### 管理故事

1. 点击"故事列表"标签
2. 查看所有已生成的故事
3. 使用下拉菜单按类型筛选
4. 点击故事卡片查看详情
5. 点击链接图标打开Notion
6. 点击删除图标删除故事

## 文件结构

```
frontend/
├── index.html      # 主页面
├── styles.css      # 样式文件
├── app.js          # 应用逻辑
└── README.md       # 说明文档
```

## API端点

前端调用以下后端API：

- `GET /health` - 健康检查
- `POST /api/stories/generate` - 生成故事
- `GET /api/stories` - 获取故事列表
- `GET /api/stories/{id}` - 获取单个故事
- `DELETE /api/stories/{id}` - 删除故事

## 浏览器兼容性

- Chrome/Edge (推荐)
- Firefox
- Safari
- 其他现代浏览器

## 技术栈

- **HTML5** - 页面结构
- **CSS3** - 样式和动画
- **JavaScript (ES6+)** - 应用逻辑
- **Fetch API** - HTTP请求

## 故障排除

### 无法连接到API服务

**症状**：页面显示"无法连接到API服务"

**解决方案**：
1. 确认后端服务已启动
2. 检查后端是否运行在 http://localhost:8000
3. 检查浏览器控制台是否有CORS错误

### 生成故事失败

**症状**：点击生成后显示错误提示

**解决方案**：
1. 检查提示词是否至少10个字符
2. 查看后端日志了解详细错误
3. 确认OpenAI API密钥配置正确
4. 确认Notion API密钥和数据库ID配置正确

### 无法打开Notion链接

**症状**：点击"在Notion中查看"没有反应

**解决方案**：
1. 确认故事已成功保存到Notion
2. 检查Notion链接是否正确
3. 确认Notion数据库有访问权限

### 故事列表为空

**症状**：故事列表页面没有显示任何故事

**解决方案**：
1. 确认已经生成过故事
2. 检查Notion数据库是否为空
3. 检查网络连接
4. 点击"刷新"按钮重新加载

## 自定义配置

### 修改API地址

编辑 `frontend/app.js` 文件：

```javascript
const API_BASE_URL = 'http://localhost:8000'; // 修改为你的API地址
```

### 修改默认选项

编辑 `frontend/index.html` 文件：

```html
<!-- 默认选中的类型 -->
<input type="radio" name="genre" value="Fantasy" checked>

<!-- 默认选中的长度 -->
<input type="radio" name="length" value="medium" checked>
```

### 自定义样式

编辑 `frontend/styles.css` 文件，修改CSS变量：

```css
:root {
    --primary-color: #6366f1;    /* 主色调 */
    --secondary-color: #8b5cf6;  /* 次要色调 */
    --success-color: #10b981;    /* 成功色 */
    --danger-color: #ef4444;     /* 危险色 */
    /* ... 其他颜色 */
}
```

## 开发建议

### 添加新功能

1. 在 `index.html` 中添加UI元素
2. 在 `styles.css` 中添加样式
3. 在 `app.js` 中添加事件处理和逻辑

### 调试

1. 打开浏览器开发者工具（F12）
2. 查看Console选项卡的错误信息
3. 查看Network选项卡的API请求
4. 使用console.log()输出调试信息

## 性能优化

- 使用CDN托管静态文件
- 启用浏览器缓存
- 压缩CSS和JavaScript文件
- 使用图片懒加载

## 安全建议

- 在生产环境中禁用CORS的allow_origins="*"
- 添加HTTPS支持
- 实现用户认证
- 添加请求频率限制

## 许可证

本项目采用MIT许可证。

## 支持

如有问题或建议，请：
1. 查看后端文档：`../README.md`
2. 检查API文档：http://localhost:8000/docs
3. 查看项目文档：`../ADAPTATION_SUMMARY.md`