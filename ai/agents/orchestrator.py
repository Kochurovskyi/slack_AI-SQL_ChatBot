"""Agent Orchestrator for coordinating multi-agent system with Slack integration.

This orchestrator coordinates the router agent and specialized agents, handles
streaming responses, and integrates with memory store.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file (same pattern as app.py and llm_caller.py)
load_dotenv(dotenv_path=project_root / ".env", override=False)

from ai.memory_store import memory_store
from ai.agents.router_agent import get_router_agent
from ai.agents.sql_query_agent import get_sql_query_agent
from ai.agents.csv_export_agent import get_csv_export_agent
from ai.agents.sql_retrieval_agent import get_sql_retrieval_agent
from ai.agents.off_topic_handler import get_off_topic_handler

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrator for coordinating agent execution and Slack integration.
    
    This is a coordinator/service class (NOT an agent) that:
    - Receives messages from Slack handlers
    - Calls router agent to classify intent
    - Routes to appropriate specialized agent
    - Streams agent responses to Slack
    - Handles memory store integration
    """
    
    def __init__(self):
        """Initialize Agent Orchestrator."""
        self.router_agent = get_router_agent()
        self.sql_query_agent = get_sql_query_agent()
        self.csv_export_agent = get_csv_export_agent()
        self.sql_retrieval_agent = get_sql_retrieval_agent()
        self.off_topic_handler = get_off_topic_handler()
        logger.info("Agent Orchestrator initialized")
    
    def process_message(self, user_message: str, thread_ts: str, conversation_history: Optional[List] = None) -> Dict[str, Any]:
        """Process user message through the multi-agent system.
        Args:
            user_message: User's message/question
            thread_ts: Slack thread timestamp (for memory)
            conversation_history: Optional conversation history (if None, fetches from memory_store)
        Returns:
            Dictionary with:
            - response: Full response text
            - intent: Classified intent
            - metadata: Additional metadata
        """
        logger.info(f"Processing message for thread: {thread_ts}")
        logger.debug(f"User message: {user_message[:200]}")
        
        try:
            # Get conversation history if not provided
            if conversation_history is None:
                conversation_history = memory_store.get_messages(thread_ts)
            # Step 1: Classify intent using router agent
            routing_result = self.router_agent.classify_intent(user_message=user_message, thread_ts=thread_ts, conversation_history=conversation_history)
            intent = routing_result["intent"]
            logger.info(f"Intent classified as: {intent}")
            # Step 2: Route to appropriate agent
            if intent == "SQL_QUERY":
                agent_result = self.sql_query_agent.query(
                    question=user_message,
                    thread_ts=thread_ts,
                    conversation_history=conversation_history
                )
                response = agent_result.get("formatted_response", "")
                
            elif intent == "CSV_EXPORT":
                agent_result = self.csv_export_agent.export(
                    thread_ts=thread_ts,
                    user_message=user_message
                )
                csv_file_path = agent_result.get("csv_file_path")
                response = agent_result.get("formatted_response", "")
                
                # Store CSV file path in metadata for listener to upload
                if csv_file_path:
                    agent_result["metadata"]["csv_file_path"] = csv_file_path
                
            elif intent == "SQL_RETRIEVAL":
                agent_result = self.sql_retrieval_agent.retrieve(
                    thread_ts=thread_ts,
                    user_message=user_message
                )
                response = agent_result.get("formatted_response", "")
                
            elif intent == "OFF_TOPIC":
                agent_result = self.off_topic_handler.handle(
                    user_message=user_message,
                    thread_ts=thread_ts
                )
                response = agent_result.get("formatted_response", "")
                
            else:
                # Fallback to SQL_QUERY if unknown intent
                logger.warning(f"Unknown intent: {intent}, defaulting to SQL_QUERY")
                agent_result = self.sql_query_agent.query(
                    question=user_message,
                    thread_ts=thread_ts,
                    conversation_history=conversation_history
                )
                response = agent_result.get("formatted_response", "")
            
            # Step 3: Save response to memory
            if response:
                memory_store.add_assistant_message(thread_ts, response)
            
            return {
                "response": response,
                "intent": intent,
                "metadata": {
                    "routing_confidence": routing_result.get("confidence", 0.0),
                    "routing_reasoning": routing_result.get("reasoning", ""),
                    "agent_metadata": agent_result.get("metadata", {}),
                    "thread_ts": thread_ts
                }
            }
            
        except Exception as e:
            error_msg = f"Orchestrator failed to process message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Return error response
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "intent": "ERROR",
                "metadata": {
                    "error": str(e),
                    "thread_ts": thread_ts
                }
            }
    
    def stream(
        self,
        user_message: str,
        thread_ts: str,
        conversation_history: Optional[List] = None
    ) -> Iterator[str]:
        """Stream agent response chunks.
        
        Args:
            user_message: User's message/question
            thread_ts: Slack thread timestamp (for memory)
            conversation_history: Optional conversation history (if None, fetches from memory_store)
        
        Yields:
            Chunks of response text
        """
        logger.info(f"Streaming response for thread: {thread_ts}")
        logger.debug(f"User message: {user_message[:200]}")
        
        try:
            # Get conversation history if not provided
            if conversation_history is None:
                conversation_history = memory_store.get_messages(thread_ts)
            
            # Step 1: Classify intent using router agent
            routing_result = self.router_agent.classify_intent(
                user_message=user_message,
                thread_ts=thread_ts,
                conversation_history=conversation_history
            )
            
            intent = routing_result["intent"]
            logger.info(f"Intent classified as: {intent}, streaming response")
            
            # Step 2: Route to appropriate agent and stream response
            full_response = ""
            
            if intent == "SQL_QUERY":
                for chunk in self.sql_query_agent.stream(
                    question=user_message,
                    thread_ts=thread_ts,
                    conversation_history=conversation_history
                ):
                    if chunk:
                        chunk_str = str(chunk) if not isinstance(chunk, str) else chunk
                        full_response += chunk_str
                        yield chunk_str
                        
            elif intent == "CSV_EXPORT":
                for chunk in self.csv_export_agent.stream(
                    thread_ts=thread_ts,
                    user_message=user_message
                ):
                    if chunk:
                        chunk_str = str(chunk) if not isinstance(chunk, str) else chunk
                        full_response += chunk_str
                        yield chunk_str
                        
            elif intent == "SQL_RETRIEVAL":
                for chunk in self.sql_retrieval_agent.stream(
                    thread_ts=thread_ts,
                    user_message=user_message
                ):
                    if chunk:
                        chunk_str = str(chunk) if not isinstance(chunk, str) else chunk
                        full_response += chunk_str
                        yield chunk_str
                        
            elif intent == "OFF_TOPIC":
                # Off-topic handler doesn't have stream method, use handle and yield chunks
                agent_result = self.off_topic_handler.handle(
                    user_message=user_message,
                    thread_ts=thread_ts
                )
                response = agent_result.get("formatted_response", "")
                if response:
                    # Yield response in chunks (simulate streaming)
                    chunk_size = 50
                    for i in range(0, len(response), chunk_size):
                        chunk = response[i:i + chunk_size]
                        full_response += chunk
                        yield chunk
            else:
                # Fallback to SQL_QUERY if unknown intent
                logger.warning(f"Unknown intent: {intent}, defaulting to SQL_QUERY")
                for chunk in self.sql_query_agent.stream(
                    question=user_message,
                    thread_ts=thread_ts,
                    conversation_history=conversation_history
                ):
                    if chunk:
                        full_response += chunk
                        yield chunk
            
            # Step 3: Save full response to memory
            if full_response:
                memory_store.add_assistant_message(thread_ts, full_response)
                logger.debug(f"Saved response to memory for thread: {thread_ts}")
            
        except Exception as e:
            error_msg = f"Orchestrator streaming failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"Error: {error_msg}"


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create Agent Orchestrator instance.
    
    Returns:
        AgentOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
        logger.debug("Created Agent Orchestrator instance")
    return _orchestrator

