"""Off-Topic Handler Agent for handling non-database questions.

This agent handles off-topic questions by:
1. Politely declining off-topic questions
2. Suggesting appropriate use cases
3. Providing helpful guidance
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

from prompts.off_topic_prompt import OFF_TOPIC_SYSTEM_PROMPT
import config

logger = logging.getLogger(__name__)


def _get_llm_model():
    """Get LangChain chat model instance for agent.
    Returns:
        LangChain chat model instance (ChatGoogleGenerativeAI)
    """
    gemini_key = os.getenv("GOOGLE_API_KEY") or ""
    gemini_key = gemini_key.strip() if gemini_key else ""
    
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.debug("Initializing ChatGoogleGenerativeAI model for Off-Topic Handler")
        return ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, api_key=gemini_key, temperature=config.GEMINI_TEMPERATURE)
    else:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables")


class OffTopicHandler:
    """Off-Topic Handler Agent for handling non-database questions."""    
    # System prompt for off-topic handler (imported from prompts module)
    SYSTEM_PROMPT = OFF_TOPIC_SYSTEM_PROMPT

    def __init__(self):
        """Initialize Off-Topic Handler Agent."""
        try:
            self.llm = _get_llm_model()
            # Off-Topic Handler doesn't need tools - it just responds directly
            self.tools = []
            # Create agent without tools (direct response agent)
            self.agent = create_agent(model=self.llm, tools=self.tools, system_prompt=self.SYSTEM_PROMPT)
            logger.info("Off-Topic Handler Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Off-Topic Handler Agent: {e}", exc_info=True)
            raise
    
    def handle(self, user_message: str, thread_ts: str) -> Dict[str, Any]:
        """Handle off-topic question.
        Args:
            user_message: User's off-topic message/question
            thread_ts: Slack thread timestamp (for context)
        Returns:
            Dictionary with:
            - formatted_response: Formatted response for Slack
            - metadata: Additional metadata
        """
        logger.info(f"Off-Topic Handler processing message for thread: {thread_ts}")
        logger.debug(f"User message: {user_message[:200]}")
        try:
            # Create human message
            messages = [HumanMessage(content=user_message)]
            # Invoke agent (no tools, direct response)
            response = self.agent.invoke({"messages": messages})
            # Extract response text
            if isinstance(response, dict) and "messages" in response:
                # Get last message (agent response)
                last_message = response["messages"][-1]
                if hasattr(last_message, "content"):
                    formatted_response = last_message.content
                else:
                    formatted_response = str(last_message)
            else:
                formatted_response = str(response)
            
            logger.info(f"Off-Topic Handler response generated successfully")
            logger.debug(f"Response: {formatted_response[:200]}")
            return {
                "formatted_response": formatted_response,
                "metadata": {
                    "handled_as_off_topic": True,
                    "thread_ts": thread_ts,
                    "user_message_length": len(user_message)
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to handle off-topic question: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Fallback response
            fallback_response = (
                "I'm a database analytics assistant focused on app portfolio queries. "
                "I can help you analyze app data, export results, or view SQL queries. "
                "What would you like to know about the app portfolio?"
            )
            
            return {
                "formatted_response": fallback_response,
                "metadata": {
                    "handled_as_off_topic": True,
                    "thread_ts": thread_ts,
                    "error": str(e),
                    "fallback_used": True
                }
            }


# Global off-topic handler instance
_off_topic_handler: Optional[OffTopicHandler] = None


def get_off_topic_handler() -> OffTopicHandler:
    """Get or create Off-Topic Handler instance.
    Returns: OffTopicHandler instance
    """
    global _off_topic_handler
    if _off_topic_handler is None:
        _off_topic_handler = OffTopicHandler()
        logger.debug("Created Off-Topic Handler instance")
    return _off_topic_handler

