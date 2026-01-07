import os
import logging
from typing import Dict, List, Iterator, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

import openai
from openai import Stream
from openai.types.responses import ResponseStreamEvent

import config

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_CONTENT = """
You're an assistant in a Slack workspace.
Users in the workspace will ask you to help them write something or to think better about a specific topic.
You'll respond to those questions in a professional way.
When you include markdown text, convert them to Slack compatible ones.
When a prompt has Slack's special syntax like <@USER_ID> or <#CHANNEL_ID>, you must keep them as-is in your response.
"""


def _call_openai(messages_in_thread: List[Dict[str, str]], system_content: str = DEFAULT_SYSTEM_CONTENT,
    langchain_messages: Optional[List[BaseMessage]] = None) -> Iterator[str]:
    """Call OpenAI API and return streaming text chunks."""
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # Use langchain_messages if provided (for memory), otherwise use messages_in_thread
    if langchain_messages:
        # Convert LangChain messages to OpenAI format
        messages = [{"role": "system", "content": system_content}]
        for msg in langchain_messages:
            if isinstance(msg, SystemMessage): continue  # Already have system message
            elif isinstance(msg, HumanMessage): messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage): messages.append({"role": "assistant", "content": msg.content})
    else:
        messages = [{"role": "system", "content": system_content}]
        messages.extend(messages_in_thread)
    response: Stream[ResponseStreamEvent] = openai_client.responses.create(model="gpt-4o-mini", input=messages, stream=True)
    for event in response:
        if event.type == "response.output_text.delta": yield event.delta


def _call_gemini(messages_in_thread: List[Dict[str, str]], system_content: str = DEFAULT_SYSTEM_CONTENT,
    langchain_messages: Optional[List[BaseMessage]] = None) -> Iterator[str]:
    """Call Gemini API and return streaming text chunks."""
    llm = ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=config.GEMINI_TEMPERATURE
    )
    # Use langchain_messages if provided (for memory), otherwise build from messages_in_thread
    if langchain_messages:
        # Ensure system message is first
        final_messages: List[BaseMessage] = [SystemMessage(content=system_content)]
        for msg in langchain_messages:
            if isinstance(msg, SystemMessage): continue  # Already have system message
            final_messages.append(msg)
    else:
        final_messages: List[BaseMessage] = [SystemMessage(content=system_content)]
        for msg in messages_in_thread:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user": final_messages.append(HumanMessage(content=content))
            elif role == "assistant": final_messages.append(AIMessage(content=content))
            elif role == "system": final_messages.append(SystemMessage(content=content))
    
    for chunk in llm.stream(final_messages):
        if hasattr(chunk, 'content') and chunk.content: yield chunk.content
        elif isinstance(chunk, str): yield chunk


def call_llm(messages_in_thread: List[Dict[str, str]], system_content: str = DEFAULT_SYSTEM_CONTENT,
    langchain_messages: Optional[List[BaseMessage]] = None) -> Iterator[str]:
    """
    Call LLM - uses OpenAI if available, otherwise Gemini.
    Args:
        messages_in_thread: List of message dicts (for backward compatibility)
        system_content: System message content
        langchain_messages: Optional list of LangChain BaseMessage objects (from memory)
                          If provided, this takes precedence over messages_in_thread
    """
    # Check which API key is available at the start (check for both None and empty string)
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GOOGLE_API_KEY", "").strip()
    
    if openai_key:
        logger.info("Using OpenAI API")
        yield from _call_openai(messages_in_thread, system_content, langchain_messages)
    elif gemini_key:
        logger.info("Using Gemini API")
        yield from _call_gemini(messages_in_thread, system_content, langchain_messages)
    else:
        raise ValueError("Neither OPENAI_API_KEY nor GOOGLE_API_KEY is set in environment variables")
