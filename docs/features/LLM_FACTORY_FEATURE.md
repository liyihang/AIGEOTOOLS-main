# LLM 工厂模块说明

## 模块概述

LLM 工厂模块提供统一的 LLM（大语言模型）客户端构建接口，支持多种 LLM 提供商的初始化和管理。

## 支持的 LLM 提供商

| 提供商 | 模型 | 说明 |
|-------|------|------|
| DeepSeek | deepseek-chat | 深度求索 |
| OpenAI | gpt-4o-mini, gpt-4 | OpenAI GPT 系列 |
| 通义千问 | qwen-max, qwen-turbo | 阿里云 |
| Groq | llama3-70b-8192 | Groq 推理加速 |
| Moonshot | moonshot-v1-128k | Kimi |
| 豆包 | 自定义 | 字节跳动 |
| 文心一言 | ernie-bot-turbo | 百度 |

## 使用方式

### 基本用法

```python
from modules.llm_factory import build_llm

# 构建 LLM 实例
llm = build_llm(
    provider="DeepSeek",
    api_key="sk-xxx",
    model="deepseek-chat",
    temperature=0.7
)

# 使用 LLM
response = llm.invoke("你好")
```

### 获取默认模型

```python
from modules.llm_factory import get_default_model

model = get_default_model("DeepSeek")
# 返回: "deepseek-chat"
```

### 获取支持的提供商列表

```python
from modules.llm_factory import get_supported_providers

providers = get_supported_providers()
# 返回: ["DeepSeek", "OpenAI (GPT)", "Tongyi (通义千问)", ...]
```

## 技术实现

### 核心文件

| 文件 | 说明 |
|------|------|
| `modules/llm_factory.py` | LLM 工厂模块 |
| `modules/chat_doubao.py` | 豆包聊天模型封装 |

### 设计模式

采用工厂模式，统一管理多种 LLM 提供商：

```
build_llm(provider, api_key, model, temperature)
    ├── DeepSeek → ChatDeepSeek
    ├── OpenAI → ChatOpenAI
    ├── Tongyi → ChatTongyi
    ├── Groq → ChatGroq
    ├── Moonshot → ChatMoonshot
    ├── 豆包 → ChatDoubao (自定义)
    └── 文心一言 → QianfanChatEndpoint
```

### 缓存机制

在 `geo_tool.py` 中使用 Streamlit 的 `@st.cache_resource` 装饰器缓存 LLM 实例：

```python
@st.cache_resource(show_spinner=False)
def build_llm(provider, api_key, model, temperature):
    from modules.llm_factory import build_llm as _build_llm
    return _build_llm(provider, api_key, model, temperature)
```

## 特殊配置

### 豆包 API Key 格式

豆包使用特殊的 API Key 格式：

```
access_key:secret_key:endpoint_id
```

示例：
```
AKLTxxx:SKxxx:ep-xxx
```

### 文心一言 API Key 格式

文心一言使用百度千帆平台的 API Key：

```
app_key:app_secret
```

## 错误处理

模块提供清晰的错误提示：

```python
try:
    llm = build_llm("Unknown", api_key, model, temperature)
except ValueError as e:
    print(e)  # "不支持的 LLM 提供商: Unknown"
```

## 后续优化方向

1. **负载均衡**：支持多个 API Key 轮询使用
2. **自动降级**：主提供商失败时自动切换到备用
3. **成本优化**：根据任务复杂度自动选择合适的模型
4. **性能监控**：记录每个提供商的响应时间和成功率
