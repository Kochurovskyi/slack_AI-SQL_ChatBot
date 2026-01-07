"""SQL Query Agent for unified SQL generation, execution, and formatting.

This agent handles the complete SQL workflow:
1. Generate SQL from natural language
2. Execute SQL query
3. Format results for Slack display
"""
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage, ToolMessage

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.memory_store import memory_store
from ai.agents.tools import (
    generate_sql_tool,
    execute_sql_tool,
    format_result_tool,
    DATABASE_SCHEMA
)
from prompts.sql_query_prompt import SQL_QUERY_SYSTEM_PROMPT
import config

logger = logging.getLogger(__name__)


def _get_llm_model():
    """Get LangChain chat model instance for agent.
    
    Returns:
        LangChain chat model instance (ChatGoogleGenerativeAI or ChatOpenAI)
    """
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GOOGLE_API_KEY", "").strip()
    
    if openai_key:
        # Try to use OpenAI if available
        try:
            from langchain_openai import ChatOpenAI
            logger.debug("Initializing ChatOpenAI model")
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=openai_key,
                temperature=0.1
            )
        except ImportError:
            logger.warning("langchain-openai not installed, falling back to Gemini")
            pass
    
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.debug("Initializing ChatGoogleGenerativeAI model")
        return ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            api_key=gemini_key,
            temperature=config.GEMINI_TEMPERATURE
        )
    else:
        raise ValueError("Neither OPENAI_API_KEY nor GOOGLE_API_KEY is set")


class SQLQueryAgent:
    """SQL Query Agent for unified SQL workflow."""
    
    # System prompt with static database schema (imported from prompts module)
    SYSTEM_PROMPT = SQL_QUERY_SYSTEM_PROMPT
    
    def __init__(self):
        """Initialize SQL Query Agent."""
        try:
            self.llm = _get_llm_model()
            self.tools = [generate_sql_tool, execute_sql_tool, format_result_tool]
            
            # Create agent with tools
            self.agent = create_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            logger.info("SQL Query Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SQL Query Agent: {e}", exc_info=True)
            raise
    
    def query(
        self,
        question: str,
        thread_ts: str,
        conversation_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """Execute SQL query workflow.
        
        Args:
            question: User's natural language question
            thread_ts: Slack thread timestamp (for memory access)
            conversation_history: Optional conversation history (if None, fetches from memory_store)
        
        Returns:
            Dictionary with:
            - formatted_response: Formatted response for Slack
            - sql_query: Generated SQL query
            - query_results: Raw query results
            - metadata: Additional metadata
        """
        logger.info(f"SQL Query Agent processing question: {question[:100]}...")
        
        try:
            # Get conversation history if not provided
            if conversation_history is None:
                conversation_history = memory_store.get_messages(thread_ts)
            
            # Build conversation history string for generate_sql_tool
            history_strings = []
            if conversation_history:
                for msg in conversation_history[-3:]:  # Last 3 messages
                    if hasattr(msg, 'content'):
                        role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                        history_strings.append(f"{role}: {msg.content}")
            
            conversation_history_list = history_strings if history_strings else None
            
            # Build user message for agent
            # The agent will automatically use tools based on the question
            user_message = question
            
            # Add conversation context if available
            if conversation_history_list:
                context = "\n".join(conversation_history_list)
                user_message = f"""Question: {question}

Previous conversation:
{context}

Please answer the question using the available tools."""
            
            # Invoke agent
            logger.debug("Invoking SQL Query Agent")
            result = self.agent.invoke({
                "messages": [HumanMessage(content=user_message)]
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
            
            # Extract SQL query and results from tool calls if available
            sql_query = None
            query_results = None
            formatted_from_tool = None
            
            # Look for tool messages to extract SQL and results
            for msg in messages:
                if hasattr(msg, 'name') and msg.name:
                    if msg.name == 'generate_sql_tool':
                        # Extract SQL query from tool result
                        if hasattr(msg, 'content'):
                            try:
                                sql_query = msg.content.strip()
                                # Remove markdown code blocks if present
                                if sql_query.startswith("```"):
                                    lines = sql_query.split("\n")
                                    if lines[0].strip().startswith("```"):
                                        lines = lines[1:]
                                    if lines and lines[-1].strip() == "```":
                                        lines = lines[:-1]
                                    sql_query = "\n".join(lines).strip()
                            except:
                                pass
                    elif msg.name == 'execute_sql_tool':
                        # Extract query results from tool message
                        if hasattr(msg, 'content'):
                            try:
                                import json
                                query_results = json.loads(msg.content)
                            except (json.JSONDecodeError, TypeError):
                                # If not JSON, try to parse as dict
                                if isinstance(msg.content, dict):
                                    query_results = msg.content
                            except Exception:
                                pass
                    elif msg.name == 'format_result_tool':
                        # Extract formatted result from format_result_tool
                        if hasattr(msg, 'content'):
                            formatted_from_tool = msg.content
            
            # If agent returned raw JSON instead of formatted response, format it ourselves
            if isinstance(formatted_response, str) and (formatted_response.strip().startswith('{') or '"success"' in formatted_response or '"data"' in formatted_response):
                logger.warning("Agent returned raw JSON, formatting it ourselves")
                try:
                    import json
                    # Try to parse as JSON if it's a string
                    try:
                        parsed_json = json.loads(formatted_response)
                        if isinstance(parsed_json, dict) and 'success' in parsed_json:
                            query_results = parsed_json
                    except json.JSONDecodeError:
                        pass
                    
                    # Use format_result_tool to format the results
                    if query_results and isinstance(query_results, dict):
                        formatted_from_tool = format_result_tool(query_results, question)
                        if formatted_from_tool:
                            formatted_response = formatted_from_tool
                except Exception as e:
                    logger.error(f"Failed to format raw JSON response: {e}")
            
            # Use formatted result from tool if available (prefer tool output over agent output)
            if formatted_from_tool:
                formatted_response = formatted_from_tool
            # If we have query_results but no formatted response, format it
            elif query_results and isinstance(query_results, dict) and not formatted_from_tool:
                try:
                    formatted_response = format_result_tool(query_results, question)
                except Exception as e:
                    logger.error(f"Failed to format query results: {e}")
            
            # Store SQL query and results in memory store
            if sql_query:
                memory_store.store_sql_query(
                    thread_ts=thread_ts,
                    sql_query=sql_query,
                    question=question,
                    results=query_results
                )
                logger.debug(f"Stored SQL query in memory store for thread: {thread_ts}")
            
            logger.info(f"SQL Query Agent completed: {len(formatted_response)} characters")
            logger.debug(f"Formatted response preview: {formatted_response[:200]}...")
            
            return {
                "formatted_response": formatted_response,
                "sql_query": sql_query,
                "query_results": query_results,
                "metadata": {
                    "query_executed": query_results is not None,
                    "result_count": query_results.get('row_count', 0) if query_results else 0,
                    "format_type": "simple" if len(formatted_response) < 200 else "table",
                    "thread_ts": thread_ts
                }
            }
            
        except Exception as e:
            error_msg = f"SQL Query Agent failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "formatted_response": f"I encountered an error processing your query: {str(e)}",
                "sql_query": None,
                "query_results": None,
                "metadata": {
                    "query_executed": False,
                    "result_count": 0,
                    "format_type": "error",
                    "error": str(e),
                    "thread_ts": thread_ts
                }
            }
    
    def stream(
        self,
        question: str,
        thread_ts: str,
        conversation_history: Optional[List[BaseMessage]] = None
    ):
        """Stream SQL query workflow results.
        
        Args:
            question: User's natural language question
            thread_ts: Slack thread timestamp
            conversation_history: Optional conversation history
        
        Yields:
            Chunks of formatted response
        """
        logger.info(f"SQL Query Agent streaming for question: {question[:100]}...")
        
        try:
            # Get conversation history if not provided
            if conversation_history is None:
                conversation_history = memory_store.get_messages(thread_ts)
            
            # Build user message
            user_message = question
            
            # Add conversation context if available
            if conversation_history:
                context_parts = []
                for msg in conversation_history[-3:]:
                    if hasattr(msg, 'content'):
                        role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                        context_parts.append(f"{role}: {msg.content}")
                if context_parts:
                    context = "\n".join(context_parts)
                    user_message = f"""Question: {question}

Previous conversation:
{context}

Please answer the question using the available tools."""
            
            # Use non-streaming query method to get clean formatted answer, then stream it
            # This ensures we only show the final formatted result, not intermediate reasoning
            logger.debug("Getting formatted answer from SQL Query Agent")
            
            result = self.query(question, thread_ts, conversation_history)
            formatted_response = result.get("formatted_response", "I couldn't process your query. Please try again.")
            
            # Extract text from structured content if needed
            if isinstance(formatted_response, list):
                text_parts = []
                for block in formatted_response:
                    if isinstance(block, dict) and block.get('type') == 'text' and 'text' in block:
                        text_parts.append(block['text'])
                    elif isinstance(block, str):
                        text_parts.append(block)
                if text_parts:
                    formatted_response = '\n'.join(text_parts)
                else:
                    formatted_response = str(formatted_response)
            elif isinstance(formatted_response, dict):
                if formatted_response.get('type') == 'text' and 'text' in formatted_response:
                    formatted_response = formatted_response['text']
                elif 'text' in formatted_response:
                    formatted_response = formatted_response['text']
                else:
                    formatted_response = str(formatted_response)
            
            # Ensure it's a string
            if not isinstance(formatted_response, str):
                formatted_response = str(formatted_response)
            
            # Stream the formatted response in chunks for better UX
            chunk_size = 50
            for i in range(0, len(formatted_response), chunk_size):
                yield formatted_response[i:i + chunk_size]
                        
        except Exception as e:
            error_msg = f"SQL Query Agent streaming failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"Error: {error_msg}"


# Global SQL Query Agent instance
_sql_query_agent: Optional[SQLQueryAgent] = None


def get_sql_query_agent() -> SQLQueryAgent:
    """Get or create SQL Query Agent instance.
    
    Returns:
        SQLQueryAgent instance
    """
    global _sql_query_agent
    if _sql_query_agent is None:
        _sql_query_agent = SQLQueryAgent()
        logger.debug("Created SQL Query Agent instance")
    return _sql_query_agent

