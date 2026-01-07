"""CSV Export Agent for generating CSV files from query results.

This agent handles CSV export workflow:
1. Retrieve last query results from memory store
2. Generate CSV file from results
3. Return CSV file path for Slack upload
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

from ai.agents.tools import (get_cached_results_tool, generate_csv_tool)
from prompts.csv_export_prompt import CSV_EXPORT_SYSTEM_PROMPT
import config

logger = logging.getLogger(__name__)


def _get_llm_model():
    """Get LangChain chat model instance for agent.
    Returns: LangChain chat model instance (ChatGoogleGenerativeAI)
    """
    gemini_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.debug("Initializing ChatGoogleGenerativeAI model for CSV Export Agent")
        return ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, api_key=gemini_key, temperature=config.GEMINI_TEMPERATURE)
    else:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables")


class CSVExportAgent:
    """CSV Export Agent for generating CSV files from query results."""
    # System prompt for CSV export agent (imported from prompts module)
    SYSTEM_PROMPT = CSV_EXPORT_SYSTEM_PROMPT
    
    def __init__(self):
        """Initialize CSV Export Agent."""
        try:
            self.llm = _get_llm_model()
            self.tools = [get_cached_results_tool, generate_csv_tool]
            # Create agent with tools
            self.agent = create_agent(model=self.llm, tools=self.tools, system_prompt=self.SYSTEM_PROMPT)
            logger.info("CSV Export Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CSV Export Agent: {e}", exc_info=True)
            raise
    
    def export(self, thread_ts: str, user_message: Optional[str] = None) -> Dict[str, Any]:
        """Export last query results to CSV.
        Args:
            thread_ts: Slack thread timestamp (for memory retrieval)
            user_message: Optional user message (defaults to export request)
        Returns:
            Dictionary with:
            - csv_file_path: Path to generated CSV file (if successful)
            - formatted_response: Formatted response for Slack
            - metadata: Additional metadata
        """
        logger.info(f"CSV Export Agent processing export request for thread: {thread_ts}")
        try:
            # Build user message with thread_ts context (but don't show it to user)
            if not user_message:
                user_message = f"Export the previous query results to CSV"
            # Include thread_ts in context for tool calls
            user_message_with_context = f"""{user_message}
            Use thread_ts="{thread_ts}" when calling get_cached_results_tool."""
            # Invoke agent
            logger.debug("Invoking CSV Export Agent")
            result = self.agent.invoke({"messages": [HumanMessage(content=user_message_with_context)]})
            # Extract response from agent result
            messages = result.get("messages", [])
            if not messages: raise ValueError("Agent returned no messages")
            # Extract CSV file path from tool calls first
            csv_file_path = None
            raw_results = None
            # Look for tool messages with CSV path and results
            for msg in messages:
                if hasattr(msg, 'name') and msg.name:
                    if msg.name == 'generate_csv_tool':
                        if hasattr(msg, 'content'): csv_file_path = msg.content.strip()
                    elif msg.name == 'get_cached_results_tool':
                        if hasattr(msg, 'content'):
                            try:
                                import json
                                raw_results = json.loads(msg.content)
                            except (json.JSONDecodeError, TypeError):
                                if isinstance(msg.content, dict): raw_results = msg.content
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
                if formatted_response.get('type') == 'text' and 'text' in formatted_response:
                    formatted_response = formatted_response['text']
                elif 'text' in formatted_response:
                    formatted_response = formatted_response['text']
                else:
                    formatted_response = str(formatted_response)
            
            # Ensure it's a string
            if not isinstance(formatted_response, str):
                formatted_response = str(formatted_response)
            
            # If CSV file was generated, create simple response (always override agent response)
            if csv_file_path:
                formatted_response = "CSV report generated."
            elif raw_results and not raw_results.get('results_found', False):
                formatted_response = "No previous query results found. Please run a query first."
            elif not csv_file_path:
                # If no CSV path but we have a response, check if it contains unwanted JSON
                if isinstance(formatted_response, str):
                    # Remove any raw JSON data from response
                    import json
                    import re
                    # Remove JSON objects from response
                    formatted_response = re.sub(r'\{[^{}]*"success"[^{}]*\}', '', formatted_response)
                    formatted_response = re.sub(r'\{[^{}]*"data"[^{}]*\}', '', formatted_response)
                    # Clean up multiple spaces/newlines
                    formatted_response = re.sub(r'\s+', ' ', formatted_response).strip()
                    
                    # If response is still too long or contains JSON-like content, simplify it
                    if len(formatted_response) > 200 or '"' in formatted_response[:50]:
                        formatted_response = "CSV export in progress. Please wait..."
            
            logger.info(f"CSV Export Agent completed: CSV path={csv_file_path}")
            logger.debug(f"Formatted response preview: {formatted_response[:200]}...")
            return {
                "csv_file_path": csv_file_path,
                "formatted_response": formatted_response,
                "metadata": {
                    "export_successful": csv_file_path is not None,
                    "thread_ts": thread_ts
                }
            }
            
        except Exception as e:
            error_msg = f"CSV Export Agent failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "csv_file_path": None,
                "formatted_response": f"I encountered an error processing your CSV export request: {str(e)}",
                "metadata": {
                    "export_successful": False,
                    "error": str(e),
                    "thread_ts": thread_ts
                }
            }
    
    def stream(self, thread_ts: str, user_message: Optional[str] = None):
        """Stream CSV export workflow results.
        Args:
            thread_ts: Slack thread timestamp
            user_message: Optional user message
        Yields:
            Chunks of formatted response
        """
        logger.info(f"CSV Export Agent streaming for thread: {thread_ts}")
        try:
            # Build user message with thread_ts context
            if not user_message:
                user_message = f"Export the previous query results to CSV"
            
            # Include thread_ts in context for tool calls
            user_message_with_context = f"""{user_message}
            Use thread_ts="{thread_ts}" when calling get_cached_results_tool."""
        
            # Get formatted response first (non-streaming to get clean output)
            logger.debug("Getting formatted answer from CSV Export Agent")
            result = self.export(thread_ts=thread_ts, user_message=user_message)
            formatted_response = result.get("formatted_response", "")
            
            # Stream the clean formatted response in chunks
            if formatted_response:
                chunk_size = 50
                for i in range(0, len(formatted_response), chunk_size):
                    chunk = formatted_response[i:i + chunk_size]
                    if chunk:
                        yield chunk
        except Exception as e:
            error_msg = f"CSV Export Agent streaming failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"Error: {error_msg}"


# Global CSV Export Agent instance
_csv_export_agent: Optional[CSVExportAgent] = None


def get_csv_export_agent() -> CSVExportAgent:
    """Get or create CSV Export Agent instance.
    Returns: CSVExportAgent instance
    """
    global _csv_export_agent
    if _csv_export_agent is None:
        _csv_export_agent = CSVExportAgent()
        logger.debug("Created CSV Export Agent instance")
    return _csv_export_agent

