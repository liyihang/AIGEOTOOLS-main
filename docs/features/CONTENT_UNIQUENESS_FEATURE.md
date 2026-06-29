# 内容独特性检测功能说明

## 功能概述

内容独特性检测模块用于检测批量生成内容的相似度，避免"多篇文章说同一件事"的问题，确保每篇内容都有独特的价值和角度。

## 核心问题

批量生成内容时常见问题：

```
生成 20 篇内容 → 多篇文章内容高度相似 → 用户体验差 → AI 搜索降权
```

解决方案：

```
生成 20 篇内容 → 独特性检测 → 标记相似内容 → 提供修改建议 → 确保内容差异化
```

## 功能特性

### 1. 多维度相似度计算


| 维度      | 权重  | 说明          |
| ------- | --- | ----------- |
| 词汇重叠度   | 40% | Jaccard 相似度 |
| 结构相似度   | 30% | 标题、列表、段落结构  |
| 关键信息重叠度 | 30% | 数字、引号、专业术语  |


### 2. 批量检测

```python
# 检测多篇内容的独特性
contents = ["内容1", "内容2", "内容3", ...]
result = checker.check_batch_uniqueness(contents)
```

### 3. 重复句子检测

自动找出在多篇内容中重复出现的句子：

```python
duplicates = checker.find_duplicate_sentences(contents)
# 返回：
# [
#   {"sentence": "重复的句子", "appears_in": [0, 2, 5], "count": 3},
#   ...
# ]
```

### 4. 独特性评分

```python
report = {
    "uniqueness_score": 85,  # 0-100，越高越独特
    "high_similarity_pairs": [...],  # 高度相似的内容对
    "duplicate_sentences": [...],  # 重复句子
    "suggestions": [...]  # 改进建议
}
```

## 使用方式

### 1. 批量生成时检测

在"自动创作"Tab 中批量生成内容后，系统会自动检测内容独特性。

### 2. 查看检测报告

检测报告包含：

- 整体独特性评分
- 高度相似的内容对
- 重复句子列表
- 针对性改进建议

### 3. 根据建议修改

针对检测结果，可以：

- 调整相似内容的角度
- 替换重复句子
- 添加独特的案例或数据

## 技术实现

### 核心模块


| 文件                              | 说明        |
| ------------------------------- | --------- |
| `modules/content_uniqueness.py` | 内容独特性检测模块 |


### API 接口

```python
from modules.content_uniqueness import ContentUniquenessChecker

# 初始化
checker = ContentUniquenessChecker(similarity_threshold=0.7)

# 批量检测
result = checker.check_batch_uniqueness(contents)

# 生成报告
report = checker.generate_uniqueness_report(contents)

# 查找重复句子
duplicates = checker.find_duplicate_sentences(contents)

# 检查两段内容的相似度
from modules.content_uniqueness import check_content_similarity
result = check_content_similarity(content1, content2)
```

## 相似度阈值说明


| 阈值        | 含义    | 建议操作     |
| --------- | ----- | -------- |
| < 0.3     | 低相似度  | 内容独特性良好  |
| 0.3 - 0.5 | 中等相似度 | 可接受，但可优化 |
| 0.5 - 0.7 | 较高相似度 | 建议修改     |
| > 0.7     | 高度相似  | 必须修改     |


## 最佳实践

### 确保内容差异化的策略

1. **选择不同角度**
  - 产品功能 vs 客户案例
  - 技术架构 vs 使用体验
  - 行业趋势 vs 具体应用
2. **添加独特元素**
  - 真实客户案例
  - 具体数据和指标
  - 独特的见解和观点
3. **调整表达方式**
  - 不同的开头方式
  - 不同的段落结构
  - 不同的专业术语

## 后续优化方向

1. **语义相似度**：接入 Embedding 模型，支持语义级别的相似度检测
2. **自动改写建议**：基于相似度分析，自动生成差异化改写建议
3. **内容模板库**：提供多样化的内容模板，从源头避免内容雷同
4. **实时检测**：在生成过程中实时检测，避免生成后再修改

