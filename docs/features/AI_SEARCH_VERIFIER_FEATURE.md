# AI 搜索验证功能说明

## 功能概述

AI 搜索验证模块支持使用真实的 AI 搜索引擎（如 Perplexity）验证品牌是否被提及，解决传统验证方式的"自我确认偏差"问题。

## 核心问题

传统验证方式的问题：

```
用 LLM A 生成内容 → 用 LLM A 验证内容是否被引用 → 存在自我确认偏差
```

AI 搜索验证的解决方案：

```
用 LLM A 生成内容 → 用 Perplexity 真实搜索引擎验证 → 获得真实反馈
```

## 功能特性

### 1. Perplexity API 集成

- 接入 Perplexity 实时搜索引擎
- 获取真实的搜索结果和引用来源
- 支持搜索结果中的引用分析

### 2. 语义级提及检测

```python
# 支持多种提及形式
"YourBrand"           # 直接提及
"YourBrand ERP"       # 带后缀
"YB"                  # 英文缩写
```

### 3. 情感分析

分析品牌提及的语境情感：

| 情感类型 | 示例 |
|---------|------|
| ✅ 正面 | "YourBrand是行业领先的解决方案" |
| ➖ 中性 | "YourBrand提供管理功能" |
| ❌ 负面 | "YourBrand存在一些稳定性问题" |

### 4. 提及位置分析

分析品牌在 AI 回答中的位置：

| 位置 | 权重 | 说明 |
|------|------|------|
| 前 1/3 | ⭐⭐⭐ | 用户最可能看到 |
| 中 1/3 | ⭐⭐ | 可能看到 |
| 后 1/3 | ⭐ | 可能被忽略 |

### 5. 批量验证报告

```python
report = {
    "total_queries": 20,
    "mentioned_count": 15,
    "mention_rate": 0.75,
    "sentiment_distribution": {
        "positive": 10,
        "neutral": 4,
        "negative": 1
    }
}
```

## 使用方式

### 1. 配置 API Key

在 `.streamlit/secrets.toml` 中添加：

```toml
[api_keys]
perplexity = "pplx-xxxxxxxxxxxx"
```

### 2. 使用验证功能

在"多模型验证"或"AI 数据报表"Tab 中：
- 选择使用 AI 搜索验证
- 输入测试问题
- 查看真实搜索结果中的品牌提及情况

### 3. 查看验证报告

验证报告包含：
- 品牌提及率
- 提及位置分布
- 情感分析结果
- 竞品对比数据

## 技术实现

### 核心模块

| 文件 | 说明 |
|------|------|
| `modules/ai_search_verifier.py` | AI 搜索验证器 |

### API 接口

```python
from modules.ai_search_verifier import AISearchVerifier

# 初始化
verifier = AISearchVerifier(perplexity_api_key="pplx-xxx")

# 单次验证
result = verifier.verify_with_perplexity(
    query="最好的管理软件是什么？",
    brand="YourBrand"
)

# 批量验证
results = verifier.batch_verify(
    queries=["问题1", "问题2", ...],
    brand="YourBrand"
)

# 生成报告
report = verifier.generate_verification_report(results)
```

## 验证指标说明

| 指标 | 说明 | 目标值 |
|------|------|--------|
| mention_rate | 品牌被提及的问题比例 | > 60% |
| avg_mentions_per_query | 每个问题平均提及次数 | > 1.5 |
| positive_ratio | 正面提及占比 | > 70% |
| front_position_ratio | 前 1/3 位置占比 | > 50% |

## 与传统验证的区别

| 维度 | 传统验证 | AI 搜索验证 |
|------|---------|------------|
| 数据来源 | LLM 模拟 | 真实搜索引擎 |
| 实时性 | 静态 | 实时 |
| 可信度 | 低（自我验证） | 高（第三方验证） |
| 成本 | 低 | 需要 API 费用 |
| 引用来源 | 无 | 有真实来源 |

## 后续优化方向

1. **接入更多搜索引擎**：ChatGPT Search、Google SGE
2. **自动化定期验证**：定时任务自动验证品牌提及
3. **竞品监控**：自动监控竞品的 AI 搜索表现
4. **历史趋势**：跟踪品牌提及率的变化趋势
