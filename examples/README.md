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

- 根据关键词搜索子页面
- 支持创建标题页面
- 支持内联页面和普通页面的移动
- 提供预览模式（dry-run）
- 详细的日志输出

#### 使用方法

```bash
python custom/reorganize_pages.py <page_url_or_id> <keyword> [options]
```

#### 参数说明

- `page_url_or_id`: Notion 页面的 URL 或 ID
- `keyword`: 搜索关键词
- `--title`: 自定义标题（可选）
- `--dry-run`: 预览模式，只显示匹配的页面而不实际移动
- `--debug`: 启用调试模式，显示详细日志

#### 示例

1. 使用页面 URL：
```bash
python custom/reorganize_pages.py "https://www.notion.so/your-workspace/page-title-page-id" "提示词"
```

2. 使用页面 ID：
```bash
python custom/reorganize_pages.py "1a406d9d-a9f4-8078-ab4a-f2ea19cc0bc8" "提示词"
```

3. 自定义标题：
```bash
python custom/reorganize_pages.py "page-id" "提示词" --title "我的提示词集合"
```

4. 预览模式：
```bash
python custom/reorganize_pages.py "page-id" "提示词" --dry-run
```

#### 注意事项

- 确保已正确设置 `NOTION_TOKEN` 环境变量
- 页面必须已与集成共享
- 集成需要有适当的权限（读取和更新内容）
- 内联页面会创建链接，普通页面会直接移动

#### 日志说明

- 日志格式：`[时间] [日志级别] [文件名:行号] 消息`
- 成功时只显示移动进度
- 失败时显示详细错误信息
- 预览模式下显示所有匹配的页面
