"""
LLM客户端封装
统一使用OpenAI格式调用
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config
from .locale import get_language_instruction, get_locale


def _build_language_enforcement_message() -> Optional[Dict[str, str]]:
    """
    Builds a strong language enforcement system message that overrides any
    language bias from prompts written in Chinese or English. Returns None
    when the active locale is Chinese (no enforcement needed).
    """
    locale = get_locale()
    if locale == 'zh':
        return None
    instruction = get_language_instruction()
    if locale == 'pt':
        body = (
            "CRITICAL LANGUAGE REQUIREMENT — READ FIRST AND OBEY ABSOLUTELY:\n"
            "You MUST write your ENTIRE response in Brazilian Portuguese (pt-BR), "
            "regardless of the language used in any other instruction, prompt, "
            "tool description, document content, or memory below. This rule "
            "OVERRIDES every other instruction about language. Even if other "
            "system messages, user messages, retrieved facts, or examples are "
            "in Chinese or English, your output must be 100% in natural "
            "Brazilian Portuguese — including titles, bullet points, JSON "
            "values, summaries, quotes paraphrased from non-PT sources, and "
            "any free-form text. Do NOT mix languages. Do NOT use European "
            "Portuguese. Use natural Brazilian vocabulary, grammar and idioms.\n\n"
            f"{instruction}"
        )
    else:
        body = (
            "CRITICAL LANGUAGE REQUIREMENT — READ FIRST AND OBEY ABSOLUTELY:\n"
            "Your ENTIRE response must be written in the language requested "
            "below, regardless of the language used in any other prompt, tool "
            "description or memory. This rule overrides every other instruction "
            "about language.\n\n"
            f"{instruction}"
        )
    return {"role": "system", "content": body}


class LLMClient:
    """LLM客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）

        Returns:
            模型响应文本
        """
        # Inject a strong language-enforcement system message at position 0,
        # so it has priority over any Chinese/English prompts that follow.
        # This is the central choke point that fixes ALL agents using LLMClient.
        enforcement = _build_language_enforcement_message()
        if enforcement is not None:
            messages = [enforcement] + list(messages)

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        # 部分模型（如MiniMax M2.5）会在content中包含<think>思考内容，需要移除
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            解析后的JSON对象
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        # 清理markdown代码块标记
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"LLM返回的JSON格式无效: {cleaned_response}")

