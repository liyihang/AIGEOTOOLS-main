# 关键词数据增强功能说明

## 功能概述

关键词数据增强模块通过分析历史验证数据，提取高价值关键词，反哺关键词生成策略，实现数据驱动的关键词优化。

## 核心价值

| 问题 | 解决方案 |
|------|----------|
| 关键词生成靠 LLM 推理 | 基于真实验证数据优化 |
| 不知道哪些关键词有效 | 自动分析关键词表现 |
| 关键词策略缺乏数据支撑 | 数据驱动的决策 |

## 功能特性

### 1. 历史数据分析

分析维度：

| 指标 | 说明 |
|------|------|
| 提及率 | 品牌被提及的问题比例 |
| 平均提及次数 | 每个问题平均提及次数 |
| 提及位置 | 前 1/3、中 1/3、后 1/3 |
| 价值分数 | 综合评估 0-100 分 |

### 2. 高价值关键词识别

```python
high_value_keywords = [
    {
        "keyword": "管理软件哪个好",
        "mention_rate": 0.85,
        "avg_mentions": 2.3,
        "value_score": 92,
        "suggested_action": "✅ 高价值关键词，继续保持"
    },
    ...
]
```

### 3. 搜索意图分布分析

```python
intent_distribution = {
    "对比": 5,      # "XX vs XX", "哪个好"
    "评测": 3,      # "XX怎么样"
    "使用": 4,      # "XX怎么用"
    "购买": 2,      # "XX多少钱"
    "问题": 3,      # "XX报错怎么办"
    "推荐": 3       # "XX推荐"
}
```

### 4. 增强提示词生成

基于历史数据生成更精准的关键词生成提示词：

```python
prompt = enhancer.generate_enhanced_keyword_prompt(
    brand="YourBrand",
    advantages="核心优势描述",
    existing_keywords=["已有关键词1", "已有关键词2"]
)
```

## 使用方式

### 1. 查看关键词分析

在"AI 数据报表"Tab 中：
- 查看关键词表现排名
- 查看搜索意图分布
- 查看优化建议

### 2. 使用增强提示词

在"关键词蒸馏"Tab 中：
- 选择"数据增强"模式
- 系统自动基于历史数据生成提示词
- 生成更精准的关键词

### 3. 应用优化建议

根据分析结果：
- 保留高价值关键词
- 优化低效关键词
- 扩展高潜力关键词

## 技术实现

### 核心模块

| 文件 | 说明 |
|------|------|
| `modules/keyword_data_enhancer.py` | 关键词数据增强模块 |

### API 接口

```python
from modules.keyword_data_enhancer import KeywordDataEnhancer

# 初始化
enhancer = KeywordDataEnhancer(storage)

# 分析历史表现
analysis = enhancer.analyze_historical_performance(brand="YourBrand", days=30)

# 生成增强提示词
prompt = enhancer.generate_enhanced_keyword_prompt(
    brand="YourBrand",
    advantages="核心优势描述"
)

# 获取关键词趋势
trends = enhancer.get_keyword_trends(
    brand="YourBrand",
    keyword="管理软件哪个好"
)
```

## 价值分数计算

```
价值分数 = 提及率 × 40 + 平均提及次数 × 30 + 前1/3位置比例 × 30
```

| 分数范围 | 评价 | 建议操作 |
|---------|------|----------|
| ≥ 70 | 高价值 | 继续保持 |
| 40-69 | 中等价值 | 有提升空间 |
| < 40 | 低价值 | 考虑替换 |

## 优化建议类型

| 类型 | 触发条件 | 建议内容 |
|------|----------|----------|
| replace | 价值分数 < 30 | 建议替换关键词 |
| expand | 价值分数 ≥ 70 | 建议扩展相关内容 |
| optimize | 提及率 30%-50% | 建议优化内容 |

## 后续优化方向

1. **接入搜索量数据**：接入百度指数、Google Trends 等数据
2. **竞品关键词分析**：分析竞品的高价值关键词
3. **自动关键词更新**：根据验证结果自动更新关键词库
4. **A/B 测试**：对比不同关键词策略的效果
