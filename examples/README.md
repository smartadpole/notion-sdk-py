# Notion SDK Python Examples

这里包含了 Notion API 的使用示例。

## 基础示例

基础示例展示了 Notion API 的基本使用方法：

- `basic.py` - 基本的 API 调用示例
- `async_basic.py` - 异步 API 调用示例
- `pagination.py` - 分页处理示例
- `error_handling.py` - 错误处理示例

## 自定义工具

### 页面重组工具 (custom/reorganize_pages.py)

这个工具用于根据关键词重组 Notion 页面中的子页面。

#### 功能特点

- 支持多个关键词同时处理
- 为每个关键词创建独立的标题页面
- 支持内联页面和普通页面的移动
- 提供预览模式（dry-run）
- 详细的进度显示（页面和关键词进度）
- 完整的错误处理和验证

#### 使用方法

```bash
# 单个关键词
python custom/reorganize_pages.py <page_url_or_id> <keyword> [options]

# 多个关键词
python custom/reorganize_pages.py <page_url_or_id> <keyword1> <keyword2> <keyword3> [options]
```

#### 参数说明

- `page_url_or_id`: Notion 页面的 URL 或 ID
- `keyword`: 搜索关键词（支持多个）
- `--title`: 自定义标题（可选，会应用到所有关键词）
- `--dry-run`: 预览模式，只显示匹配的页面而不实际移动
- `--debug`: 启用调试模式，显示详细日志

#### 示例

1. 使用多个关键词：
```bash
python custom/reorganize_pages.py "https://www.notion.so/your-workspace/page-title-page-id" "AI" "Python" "提示词"
```

2. 自定义标题：
```bash
python custom/reorganize_pages.py "page-id" "AI" "Python" --title "技术文章"
```

3. 预览模式：
```bash
python custom/reorganize_pages.py "page-id" "AI" "Python" --dry-run
```

#### 进度显示

工具会显示详细的处理进度：

#### 注意事项

- 确保已正确设置 `NOTION_TOKEN` 环境变量
- 页面必须已与集成共享
- 集成需要有适当的权限（读取和更新内容）
- 内联页面会创建链接，普通页面会直接移动
- 每个关键词会创建独立的标题页面

#### 错误处理

工具提供详细的错误信息和故障排除指南：

1. 页面 ID 验证
2. 页面共享设置
3. 集成权限检查
4. 集成令牌验证

#### 日志说明

- 日志格式：`[时间] [日志级别] [文件名:行号] 消息`
- 成功时只显示移动进度
- 失败时显示详细错误信息和解决步骤
- 预览模式下显示所有匹配的页面
