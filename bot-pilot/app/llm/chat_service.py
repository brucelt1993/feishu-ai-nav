"""
聊天服务
整合 OpenAI API 和 MCP Tools
"""

import json
from collections import defaultdict
from typing import Any

from loguru import logger
from openai import AsyncOpenAI

from app.config import settings
from app.llm.mcp_tools import get_tools
from app.llm.prompt_manager import get_system_prompt
from app.llm.tool_executor import ToolExecutor


class ChatService:
    """聊天服务"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.tool_executor = ToolExecutor()
        # 对话历史 (按用户隔离)
        self._conversations: dict[str, list[dict]] = defaultdict(list)

    async def chat(
        self,
        user_id: str,
        message: str,
        chat_id: str = "",
    ) -> str:
        """
        处理用户消息并返回回复

        Args:
            user_id: 用户 ID
            message: 用户消息
            chat_id: 会话 ID (群聊 ID 或私聊标识)

        Returns:
            回复文本或卡片 JSON
        """
        # 获取对话历史
        conversation_key = f"{user_id}:{chat_id}"
        history = self._conversations[conversation_key]

        # 添加用户消息
        history.append({"role": "user", "content": message})

        # 保持上下文窗口
        if len(history) > settings.max_context_messages * 2:
            history = history[-(settings.max_context_messages * 2) :]
            self._conversations[conversation_key] = history

        # 构建消息列表
        messages = [
            {"role": "system", "content": get_system_prompt()},
            *history,
        ]

        try:
            # 调用 OpenAI API
            response = await self._call_openai(messages)

            # 保存助手回复
            history.append({"role": "assistant", "content": response})

            return response

        except Exception as e:
            logger.error(f"❌ OpenAI API 调用失败: {e}")
            import traceback
            logger.error(f"堆栈: {traceback.format_exc()}")
            raise

    async def _call_openai(self, messages: list[dict]) -> str:
        """
        调用 OpenAI API，支持 Function Calling
        """
        logger.debug(f"📤 调用 OpenAI, 消息数: {len(messages)}")

        # 第一次调用
        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=get_tools(),
            tool_choice="auto",
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature,
        )

        logger.debug(f"📥 OpenAI 响应 choices 数: {len(response.choices) if response.choices else 0}")

        if not response.choices:
            logger.error(f"❌ OpenAI 返回空 choices: {response}")
            return "抱歉，AI 服务暂时无法响应，请稍后再试。"

        assistant_message = response.choices[0].message

        # 检查是否有工具调用
        if assistant_message.tool_calls:
            logger.info(f"🔧 触发工具调用: {len(assistant_message.tool_calls)} 个")

            # 执行工具调用
            tool_results = await self._execute_tools(assistant_message.tool_calls)

            # 构建带工具结果的消息
            messages.append(assistant_message.model_dump())
            messages.extend(tool_results)

            # 第二次调用 (带工具结果)
            second_response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )

            if not second_response.choices:
                logger.error(f"❌ OpenAI 第二次调用返回空 choices: {second_response}")
                return "抱歉，AI 服务暂时无法响应，请稍后再试。"

            return second_response.choices[0].message.content or ""

        # 无工具调用，直接返回
        return assistant_message.content or ""

    async def _execute_tools(self, tool_calls: list) -> list[dict]:
        """
        执行工具调用并返回结果
        """
        results = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments or "{}")

            logger.info(f"🔧 执行工具: {function_name}, 参数: {function_args}")

            try:
                result = await self.tool_executor.execute(function_name, function_args)
                result_str = json.dumps(result, ensure_ascii=False, default=str)
            except Exception as e:
                logger.error(f"❌ 工具执行失败: {e}")
                result_str = json.dumps({"error": str(e)}, ensure_ascii=False)

            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            })

        return results

    def clear_history(self, user_id: str, chat_id: str = ""):
        """清除用户对话历史"""
        conversation_key = f"{user_id}:{chat_id}"
        self._conversations.pop(conversation_key, None)
