# Tech Trend Spider 输出 Schema

线上 latest API 顶层响应包含快照信息和条目列表。

## 顶层响应

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `served_from` | string | 数据来源，例如 `redis`、`archive` 或其他后端返回值。 |
| `generated_at` | string | 后端采集并生成快照的时间。 |
| `source` | object | 来源定义，包含 `id`、`name`、`label`、`content_source`、`category`。 |
| `item_count` | number | 当前响应实际返回的条目数。 |
| `total_item_count` | number | 快照中该来源的总条目数；可能大于 `item_count`。 |
| `items` | array | 该来源的最新条目列表。 |

如果 API 返回空 `items`，说明该来源暂无可用快照。

## 条目字段

`items` 内条目沿用以下字段。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `source` | string | 人类可读的内容来源，例如 `GitHub Trending Daily`、`Hacker News` 或 `V2EX`。 |
| `category` | string | 来源分类，例如 `开源趋势`、`社区讨论`、`AI 快讯`、`AI 官方更新` 或 `AI 工程实践`。 |
| `title` | string | 条目标题。 |
| `url` | string | 条目的规范 URL。 |
| `published_at` | string | 发布时间或来源提供的时间；不可用时使用空字符串。 |
| `original_summary` | string | 原始描述、统计数据、来源元信息或原始摘要。 |
| `chinese_summary` | string | 启用且可用 AI 摘要时的中文摘要；不可用时使用降级文本或空字符串。 |
| `backend_focus` | string | 可用时的工程相关性或行动点；不可用时使用降级文本或空字符串。 |
| `meta` | object | 来源特定的结构化信息，例如语言、stars、分数、评论数、节点、回复数或 HN URL。 |

## Markdown 输出

除非用户明确要求 JSON，否则使用 Markdown。

推荐结构：

1. 说明查询的 source id、`generated_at`、`served_from`、返回条目数、topic 过滤状态和 count 截断状态。
2. 列出条目的标题、URL、来源、可用的发布时间和简洁摘要。
3. 在有帮助时补充 `meta` 中的来源特定信息。
4. 仅当某个请求来源失败时，添加简短的 `Errors` 小节。

## JSON 输出

推荐顶层对象：

```json
{
  "served_from": "redis",
  "generated_at": "ISO-8601 时间戳",
  "source": {
    "id": "github-weekly",
    "name": "GitHub Weekly",
    "label": "GitHub 周榜",
    "content_source": "GitHub Trending Weekly",
    "category": "开源趋势"
  },
  "sources": ["github-weekly"],
  "item_count": 1,
  "total_item_count": 10,
  "items": [
    {
      "source": "GitHub Trending Weekly",
      "category": "开源趋势-每周热点",
      "title": "owner/repo",
      "url": "https://github.com/owner/repo",
      "published_at": "",
      "original_summary": "描述 | 语言/stars/forks 信息",
      "chinese_summary": "可选中文摘要",
      "backend_focus": "可选工程关注点",
      "meta": {}
    }
  ],
  "errors": []
}
```

缺失值应显式保留为空字符串或空对象。除非用户要求新的 schema，否则不要为了单个来源发明新字段。
