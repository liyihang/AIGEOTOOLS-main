# JSON-LD Schema.org 结构化数据生成功能说明

## 功能概述

JSON-LD Schema.org 结构化数据生成模块帮助用户生成符合 Schema.org 规范的 JSON-LD 代码，提升品牌在 AI 模型中的实体识别和权威性。

## 为什么需要 Schema.org？

1. **帮助 AI 理解**：结构化数据让 AI 更容易理解您的品牌和产品
2. **提升权威性**：Schema.org 是国际标准，使用它能增加内容的可信度
3. **富媒体展示**：搜索引擎可以使用 Schema 数据生成富媒体搜索结果

## 支持的 Schema 类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| Organization | 组织/公司 | 企业品牌介绍 |
| SoftwareApplication | 软件应用 | SaaS 产品、软件工具 |
| Product | 产品 | 实体产品或数字产品 |
| Service | 服务 | 服务类业务 |
| FAQPage | FAQ 页面 | 常见问题解答 |
| HowTo | 操作指南 | 教程、步骤说明 |
| Article | 文章 | 博客、新闻文章 |
| Review | 评价 | 产品/服务评价 |

## 使用方式

### 1. 生成 Schema

在内容优化或自动创作完成后，系统会提示是否生成 Schema。

### 2. 选择 Schema 类型

根据内容类型选择合适的 Schema 类型。

### 3. 嵌入到网页

将生成的 JSON-LD 代码嵌入到网页的 `<head>` 标签中。

## 代码示例

### 基本用法

```python
from modules.schema_generator import SchemaGenerator

generator = SchemaGenerator()

# 生成 Organization Schema
schema = generator.generate_organization_schema(
    brand_name="YourBrand",
    description="YourBrand description",
    url="https://example.com"
)

# 生成 HTML 标签
html_tag = generator.generate_html_script_tag(schema)
print(html_tag)
```

### 生成 FAQ Schema

```python
# 从内容中自动提取 Q&A
faq_schema = generator.auto_generate_faq_schema(content)

# 手动创建 FAQ
faq_items = [
    {"question": "产品有什么优势？", "answer": "我们的产品具有..."},
    {"question": "如何开始使用？", "answer": "只需三步..."}
]
faq_schema = generator.generate_faq_schema(faq_items)
```

### 生成 HowTo Schema

```python
steps = [
    {"name": "注册账号", "text": "访问官网注册账号"},
    {"name": "配置设置", "text": "完成基础配置"},
    {"name": "开始使用", "text": "开始使用核心功能"}
]
howto_schema = generator.generate_howto_schema(
    title="如何开始使用",
    steps=steps,
    description="快速入门指南"
)
```

## 嵌入示例

### 示例 1：添加到网页 HTML

```html
<!DOCTYPE html>
<html>
<head>
    <!-- 将生成的 HTML Script 标签粘贴到这里 -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "YourBrand",
      "description": "Product description",
      ...
    }
    </script>
</head>
<body>
    ...
</body>
</html>
```

### 示例 2：添加到 GitHub README

在 GitHub 项目的 README.md 文件中，可以添加 JSON-LD Schema 的说明：

```markdown
# 我的项目

项目描述...

<!-- JSON-LD Schema -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "YourBrand"
}
</script>
```

## 最佳实践

1. **选择正确的类型**：根据内容选择最合适的 Schema 类型
2. **提供完整信息**：尽可能填写所有相关字段
3. **保持更新**：内容更新时同步更新 Schema
4. **验证有效性**：使用 Google Rich Results Test 验证

## 验证工具

- [Google Rich Results Test](https://search.google.com/test/rich-results)
- [Schema.org Validator](https://validator.schema.org/)

## 技术实现

### 核心模块

| 文件 | 说明 |
|------|------|
| `modules/schema_generator.py` | Schema 生成器 |

### API 接口

- `generate_organization_schema()` - 生成组织 Schema
- `generate_software_application_schema()` - 生成软件应用 Schema
- `generate_faq_schema()` - 生成 FAQ Schema
- `generate_howto_schema()` - 生成 HowTo Schema
- `generate_article_schema()` - 生成文章 Schema
- `generate_review_schema()` - 生成评价 Schema
- `auto_generate_faq_schema()` - 从内容自动提取 Q&A 并生成 Schema
