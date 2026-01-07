"""SQL Retrieval Agent for retrieving and displaying cached SQL queries.

This agent handles SQL retrieval workflow:
1. Retrieve cached SQL query from cache
2. Format SQL for Slack display (code blocks)
3. Return formatted SQL response
"""
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.agents.tools import get_sql_history_tool
from prompts.sql_retrieval_prompt import SQL_RETRIEVAL_SYSTEM_PROMPT
import config

logger = logging.getLogger(__name__)


def _get_llm_model():
    """Get LangChain chat model instance for agent.
    
    Returns:
        LangChain chat model instance (ChatGoogleGenerativeAI)
    """
    gemini_key = os.getenv("GOOGLE_API_KEY", "").strip()
    
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.debug("Initializing ChatGoogleGenerativeAI model for SQL Retrieval Agent")
        return ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            api_key=gemini_key,
            temperature=config.GEMINI_TEMPERATURE
        )
    else:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables")


class SQLRetrievalAgent:
    """SQL Retrieval Agent for retrieving and displaying cached SQL queries."""
    
    # System prompt for SQL retrieval agent (imported from prompts module)
    SYSTEM_PROMPT = SQL_RETRIEVAL_SYSTEM_PROMPT
    
    def __init__(self):
        """Initialize SQL Retrieval Agent."""
        try:
            self.llm = _get_llm_model()
            self.tools = [get_sql_history_tool]
            
            # Create agent with tools
            self.agent = create_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            logger.info("SQL Retrieval Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SQL Retrieval Agent: {e}", exc_info=True)
            raise
    
    def retrieve(
        self,
        thread_ts: str,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve cached SQL query.
        
        Args:
            thread_ts: Slack thread timestamp (for cache retrieval)
            user_message: Optional user message (defaults to retrieval request)
        
        Returns:
            Dictionary with:
            - sql_statement: SQL query string (if found)
            - formatted_response: Formatted response for Slack
            - metadata: Additional metadata
        """
        logger.info(f"SQL Retrieval Agent processing retrieval request for thread: {thread_ts}")
        
        try:
            # Build user message with thread_ts context
            if not user_message:
                user_message = f"Show me the SQL query for this thread"
            
            # Include thread_ts in the message so the agent can use it with the tool
            # Format it explicitly so the LLM knows to use it
            user_message_with_context = f"""{user_message}

Use thread_ts="{thread_ts}" when calling get_sql_history_tool."""
            
            # Invoke agent
            logger.debug("Invoking SQL Retrieval Agent")
            result = self.agent.invoke({
                "messages": [HumanMessage(content=user_message_with_context)]
            })
            
            # Extract response from agent result
            messages = result.get("messages", [])
            if not messages:
                raise ValueError("Agent returned no messages")
            
            # Get the final assistant message
            final_message = None
            for msg in reversed(messages):
                if hasattr(msg, 'content') and msg.content:
                    final_message = msg
                    break
            
            if not final_message:
                raise ValueError("Agent returned no content in messages")
            
            formatted_response = final_message.content
            
            # Extract text from structured content (Gemini may return structured format)
            if isinstance(formatted_response, list):
                # Handle structured content blocks from Gemini
                text_parts = []
                for block in formatted_response:
                    if isinstance(block, dict):
                        if block.get('type') == 'text' and 'text' in block:
                            text_parts.append(block['text'])
                        elif 'text' in block:
                            text_parts.append(block['text'])
                    elif isinstance(block, str):
                        text_parts.append(block)
                if text_parts:
                    formatted_response = '\n'.join(text_parts)
                else:
                    formatted_response = str(formatted_response)
            elif isinstance(formatted_response, dict):
                # Handle dict format
                if formatted_response.get('type') == 'text' and 'text' in formatted_response:
                    formatted_response = formatted_response['text']
                elif 'text' in formatted_response:
                    formatted_response = formatted_response['text']
                else:
                    formatted_response = str(formatted_response)
            
            # Ensure it's a string
            if not isinstance(formatted_response, str):
                formatted_response = str(formatted_response)
            
            # Extract SQL statement from tool calls if available
            sql_statement = None
            
            # Look for tool messages with SQL
            for msg in messages:
                if hasattr(msg, 'name') and msg.name == 'get_sql_history_tool':
                    if hasattr(msg, 'content'):
                        try:
                            import json
                            tool_result = json.loads(msg.content)
                            if tool_result.get('sql_found'):
                                sql_statement = tool_result.get('sql_statement')
                                break
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, try to extract SQL from content
                            if 'SELECT' in msg.content or 'select' in msg.content:
                                sql_statement = msg.content
                                break
                # Also check ToolMessage instances
                elif msg.__class__.__name__ == 'ToolMessage':
                    if hasattr(msg, 'content'):
                        try:
                            import json
                            tool_result = json.loads(msg.content)
                            if tool_result.get('sql_found'):
                                sql_statement = tool_result.get('sql_statement')
                                break
                        except (json.JSONDecodeError, TypeError):
                            pass
            
            logger.info(f"SQL Retrieval Agent completed: {len(formatted_response)} characters")
            logger.debug(f"Formatted response preview: {formatted_response[:200]}...")
            
            return {
                "sql_statement": sql_statement,
                "formatted_response": formatted_response,
                "metadata": {
                    "sql_found": sql_statement is not None,
                    "thread_ts": thread_ts
                }
            }
            
        except Exception as e:
            error_msg = f"SQL Retrieval Agent failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "sql_statement": None,
                "formatted_response": f"I encountered an error processing your SQL retrieval request: {str(e)}",
                "metadata": {
                    "sql_found": False,
                    "error": str(e),
                    "thread_ts": thread_ts
                }
            }
    
    def stream(
        self,
        thread_ts: str,
        user_message: Optional[str] = None
    ):
        """Stream SQL retrieval workflow results.
        
        Args:
            thread_ts: Slack thread timestamp
            user_message: Optional user message
        
        Yields:
            Chunks of formatted response
        """
        logger.info(f"SQL Retrieval Agent streaming for thread: {thread_ts}")
        
        try:
            # Build user message if not provided
            if not user_message:
                user_message = f"Show me the SQL query for this thread"
            
            # Get formatted response first (non-streaming to get clean output)
            logger.debug("Getting formatted answer from SQL Retrieval Agent")
            result = self.retrieve(thread_ts=thread_ts, user_message=user_message)
            formatted_response = result.get("formatted_response", "")
            
            # Stream the clean formatted response in chunks
            if formatted_response:
                chunk_size = 50
                for i in range(0, len(formatted_response), chunk_size):
                    chunk = formatted_response[i:i + chunk_size]
                    if chunk:
                        yield chunk
                        
        except Exception as e:
            error_msg = f"SQL Retrieval Agent streaming failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"Error: {error_msg}"


# Global SQL Retrieval Agent instance
_sql_retrieval_agent: Optional[SQLRetrievalAgent] = None


def get_sql_retrieval_agent() -> SQLRetrievalAgent:
    """Get or create SQL Retrieval Agent instance.
    
    Returns:
        SQLRetrievalAgent instance
    """
    global _sql_retrieval_agent
    if _sql_retrieval_agent is None:
        _sql_retrieval_agent = SQLRetrievalAgent()
        logger.debug("Created SQL Retrieval Agent instance")
    return _sql_retrieval_agent

