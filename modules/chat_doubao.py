"""
豆包（字节跳动）聊天模型封装模块
提供 LangChain 兼容的 ChatDoubao 类
"""

from typing import List, Optional, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ChatDoubao(BaseChatModel):
    """豆包聊天模型封装（LangChain 兼容）"""
    
    volc_ak: str
    volc_sk: str
    endpoint_id: str
    temperature: float = 0.7
    client: Any = None
    
    def __init__(self, volc_ak: str, volc_sk: str, endpoint_id: str, temperature: float = 0.7, **kwargs):
        super().__init__(
            volc_ak=volc_ak,
            volc_sk=volc_sk,
            endpoint_id=endpoint_id,
            temperature=temperature,
            **kwargs
        )
        self._init_client()
    
    def _init_client(self):
        """初始化 Ark 客户端，尝试多种导入方式"""
        try:
            from volcengine.ark import Ark
            self.client = Ark(ak=self.volc_ak, sk=self.volc_sk)
        except ImportError:
            try:
                from volcenginesdkarkruntime import Ark
                self.client = Ark(ak=self.volc_ak, sk=self.volc_sk)
            except ImportError as e:
                raise ImportError(
                    f"豆包初始化失败：缺少依赖库。请运行：pip install 'volcengine-python-sdk[ark]'。错误：{e}"
                )
    
    def _generate(
        self, 
        messages: List[BaseMessage], 
        stop: Optional[List[str]] = None, 
        run_manager: Optional[Any] = None, 
        **kwargs: Any
    ) -> ChatResult:
        """生成聊天响应"""
        volc_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                volc_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                volc_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                volc_messages.append({"role": "assistant", "content": msg.content})
            else:
                volc_messages.append({"role": "user", "content": str(msg.content)})
        
        response = self.client.chat.completions.create(
            model=self.endpoint_id,
            messages=volc_messages,
            temperature=self.temperature,
        )
        
        ai_message = AIMessage(content=response.choices[0].message.content)
        return ChatResult(generations=[ChatGeneration(message=ai_message)])
    
    @property
    def _llm_type(self) -> str:
        return "doubao"


def create_chat_doubao(api_key: str, temperature: float = 0.7) -> ChatDoubao:
    """
    创建豆包聊天模型实例
    
    Args:
        api_key: 豆包 API Key，格式：access_key:secret_key:endpoint_id
        temperature: 温度参数
        
    Returns:
        ChatDoubao 实例
        
    Raises:
        ValueError: API Key 格式错误
    """
    parts = api_key.split(":")
    if len(parts) < 3:
        raise ValueError("豆包 API Key 格式错误，应为：access_key:secret_key:endpoint_id（用冒号分隔）")
    
    return ChatDoubao(
        volc_ak=parts[0],
        volc_sk=parts[1],
        endpoint_id=parts[2],
        temperature=temperature
    )
