"""
LLM 工厂模块
提供统一的 LLM 客户端构建接口
"""

from typing import Optional
from contextlib import contextmanager
import os
import unicodedata


@contextmanager
def temp_env_vars(vars_dict):
    """临时设置环境变量的上下文管理器"""
    old_values = {}
    for key, value in vars_dict.items():
        old_values[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def build_deepseek(api_key: str, model: str, temperature: float):
    """构建 DeepSeek LLM"""
    from langchain_deepseek import ChatDeepSeek
    return ChatDeepSeek(api_key=api_key, model=model, temperature=temperature)


def build_openai(api_key: str, model: str, temperature: float):
    """构建 OpenAI LLM"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(api_key=api_key, model=model, temperature=temperature)


def build_tongyi(api_key: str, model: str, temperature: float):
    """构建通义千问 LLM"""
    try:
        from langchain_community.chat_models import ChatTongyi
        return ChatTongyi(api_key=api_key, model=model, model_kwargs={"temperature": temperature})
    except Exception:
        from langchain_aliyun import ChatTongyi  # type: ignore
        return ChatTongyi(api_key=api_key, model=model, temperature=temperature)


def build_groq(api_key: str, model: str, temperature: float):
    """构建 Groq LLM"""
    from langchain_groq import ChatGroq
    return ChatGroq(api_key=api_key, model=model, temperature=temperature)


def build_moonshot(api_key: str, model: str, temperature: float):
    """构建 Moonshot (Kimi) LLM"""
    try:
        from langchain_moonshot import ChatMoonshot  # type: ignore
        return ChatMoonshot(api_key=api_key, model=model, temperature=temperature)
    except Exception:
        from langchain_community.chat_models import MoonshotChat  # type: ignore
        return MoonshotChat(api_key=api_key, model=model, temperature=temperature)


def build_doubao(api_key: str, temperature: float):
    """构建豆包 LLM"""
    try:
        from modules.chat_doubao import create_chat_doubao
        return create_chat_doubao(api_key=api_key, temperature=temperature)
    except ImportError as e:
        raise ValueError(f"豆包初始化失败：缺少依赖库。请运行：pip install 'volcengine-python-sdk[ark]'。错误：{e}")
    except Exception as e:
        raise ValueError(f"豆包初始化失败：{e}。请确保 API Key 格式为：access_key:secret_key:endpoint_id")


def build_wenxin(api_key: str, model: str, temperature: float):
    """构建文心一言 LLM"""
    parts = api_key.split(":")
    if len(parts) != 2:
        raise ValueError("文心一言 API Key 格式错误，应为：app_key:app_secret（用冒号分隔）")
    
    app_key, app_secret = parts
    
    # 优先使用 langchain-community 的千帆接口（已包含在依赖中）
    try:
        from langchain_community.chat_models import QianfanChatEndpoint
        
        with temp_env_vars({"QIANFAN_AK": app_key, "QIANFAN_SK": app_secret}):
            return QianfanChatEndpoint(
                model=model if model else "ernie-bot-turbo",
                temperature=temperature,
            )
    except ImportError:
        # 备选方案：尝试 langchain-wenxin
        try:
            from langchain_wenxin import ChatWenxin
            return ChatWenxin(
                baidu_api_key=app_key,
                baidu_secret_key=app_secret,
                model=model if model else "ernie-bot-turbo",
                temperature=temperature,
            )
        except ImportError as e:
            raise ValueError(f"文心一言初始化失败：缺少依赖库。请运行：pip install qianfan（或使用已安装的 langchain-community）。错误：{e}")
    except Exception as e:
        raise ValueError(f"文心一言初始化失败：{e}")


# Provider 映射表
PROVIDER_BUILDERS = {
    "DeepSeek": lambda api_key, model, temp: build_deepseek(api_key, model, temp),
    "OpenAI (GPT)": lambda api_key, model, temp: build_openai(api_key, model, temp),
    "Tongyi (通义千问)": lambda api_key, model, temp: build_tongyi(api_key, model, temp),
    "Groq": lambda api_key, model, temp: build_groq(api_key, model, temp),
    "Moonshot (Kimi)": lambda api_key, model, temp: build_moonshot(api_key, model, temp),
    "豆包（字节跳动）": lambda api_key, model, temp: build_doubao(api_key, temp),
    "文心一言（百度）": lambda api_key, model, temp: build_wenxin(api_key, model, temp),
}


def _sanitize_api_key(key: str) -> str:
    """清理 API Key：规范化 Unicode、去除首尾空白，并确保仅保留 ASCII 字符。"""
    if not key:
        return ""
    key = unicodedata.normalize("NFKC", key).strip()
    return "".join(ch for ch in key if ord(ch) < 128)


def build_llm(provider: str, api_key: str, model: str, temperature: float):
    """
    统一的 LLM 构建接口
    
    Args:
        provider: 提供商名称
        api_key: API Key
        model: 模型名称
        temperature: 温度参数
        
    Returns:
        LLM 实例
        
    Raises:
        ValueError: 不支持的提供商或初始化失败
    """
    api_key = _sanitize_api_key(api_key)
    if not api_key:
        raise ValueError(f"{provider} API Key 不能为空")

    builder = PROVIDER_BUILDERS.get(provider)
    if builder is None:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")
    
    return builder(api_key, model, temperature)


def get_supported_providers():
    """获取支持的提供商列表"""
    return list(PROVIDER_BUILDERS.keys())


def get_default_model(provider: str) -> str:
    """获取提供商的默认模型"""
    defaults = {
        "DeepSeek": "deepseek-chat",
        "OpenAI (GPT)": "gpt-4o-mini",
        "Tongyi (通义千问)": "qwen-max",
        "Groq": "llama3-70b-8192",
        "Moonshot (Kimi)": "moonshot-v1-128k",
        "豆包（字节跳动）": "",
        "文心一言（百度）": "ernie-bot-turbo",
    }
    return defaults.get(provider, "")
