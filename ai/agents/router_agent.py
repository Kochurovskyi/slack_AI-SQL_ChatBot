"""Router Agent for intent classification and routing.

This agent classifies user intent and routes to appropriate specialized agents:
- SQL_QUERY: Routes to SQL Query Agent
- CSV_EXPORT: Routes to CSV Export Agent
- SQL_RETRIEVAL: Routes to SQL Retrieval Agent
- OFF_TOPIC: Routes to Off-Topic Handler
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.llm_caller import call_llm
from ai.memory_store import memory_store
from ai.agents.router_tools import get_router_tools, IntentType
from prompts.router_prompt import ROUTER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class RouterAgent:
    """Router Agent for classifying user intent and routing to specialized agents."""
    
    # System prompt for router agent (imported from prompts module)
    ROUTER_SYSTEM_PROMPT = ROUTER_SYSTEM_PROMPT
    
    def __init__(self, llm_model: Optional[str] = None):
        """Initialize Router Agent.
        
        Args:
            llm_model: Optional model identifier (uses default from llm_caller if not provided)
        """
        self.llm_model = llm_model
        self.router_tools = get_router_tools()
        logger.info("Router Agent initialized")
    
    def _get_llm(self):
        """Get LLM instance for agent.
        
        Note: For now, we'll use call_llm directly. In future, we can integrate
        with LangChain's model initialization.
        """
        # This will be used when we create the agent
        # For now, we'll use a simple classification approach
        pass
    
    def classify_intent(
        self,
        user_message: str,
        thread_ts: str,
        conversation_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """Classify user intent and return routing decision.
        
        Args:
            user_message: User's message/question
            thread_ts: Slack thread timestamp (for memory access)
            conversation_history: Optional conversation history (if None, fetches from memory_store)
        
        Returns:
            Dictionary with:
            - intent: One of SQL_QUERY, CSV_EXPORT, SQL_RETRIEVAL, OFF_TOPIC
            - reasoning: Explanation of routing decision
            - confidence: Confidence score (0-1)
            - metadata: Additional metadata
        """
        logger.info(f"Classifying intent for message: {user_message[:100]}...")
        
        try:
            # Get conversation history if not provided
            if conversation_history is None:
                conversation_history = memory_store.get_messages(thread_ts)
            
            # Build context from conversation history
            context_parts = []
            if conversation_history:
                # Get last 3 messages for context
                recent_messages = conversation_history[-3:]
                for msg in recent_messages:
                    if hasattr(msg, 'content'):
                        role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                        context_parts.append(f"{role}: {msg.content}")
            
            conversation_context = "\n".join(context_parts) if context_parts else ""
            
            # Build prompt for intent classification
            user_prompt = f"""Classify the user's intent and route to the appropriate agent.

User Message: {user_message}"""

            if conversation_context:
                user_prompt += f"\n\nConversation Context:\n{conversation_context}"
            
            user_prompt += "\n\nAnalyze the user's message and use the appropriate routing tool to classify the intent."
            
            # Use LLM to classify intent
            logger.debug("Calling LLM for intent classification")
            
            # For now, we'll use a simple rule-based classification
            # In Phase 4, we can enhance this with the actual agent
            intent_result = self._classify_intent_simple(user_message, conversation_context)
            
            logger.info(f"Intent classified as: {intent_result['intent']} (confidence: {intent_result['confidence']})")
            logger.debug(f"Routing reasoning: {intent_result['reasoning']}")
            
            return {
                "intent": intent_result["intent"],
                "reasoning": intent_result["reasoning"],
                "confidence": intent_result["confidence"],
                "metadata": {
                    "routing_decision": intent_result["intent"],
                    "routing_confidence": intent_result["confidence"],
                    "user_message": user_message[:200],
                    "has_context": bool(conversation_context)
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to classify intent: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Default to SQL_QUERY on error (safest fallback)
            return {
                "intent": "SQL_QUERY",
                "reasoning": f"Error during classification, defaulting to SQL_QUERY: {error_msg}",
                "confidence": 0.5,
                "metadata": {
                    "routing_decision": "SQL_QUERY",
                    "routing_confidence": 0.5,
                    "error": str(e)
                }
            }
    
    def _classify_intent_simple(
        self,
        user_message: str,
        conversation_context: str
    ) -> Dict[str, Any]:
        """Simple rule-based intent classification.
        
        This is a fallback implementation. In Phase 4, this will be replaced
        with the actual ReAct agent using create_agent.
        
        Args:
            user_message: User's message
            conversation_context: Conversation context
        
        Returns:
            Dictionary with intent, reasoning, and confidence
        """
        message_lower = user_message.lower()
        context_lower = conversation_context.lower()
        
        # Check for CSV export keywords
        csv_keywords = ["export", "csv", "download", "file", "save as", "send me"]
        if any(keyword in message_lower for keyword in csv_keywords):
            return {
                "intent": "CSV_EXPORT",
                "reasoning": "User requested CSV export or file download",
                "confidence": 0.9
            }
        
        # Check for SQL retrieval keywords
        sql_keywords = ["show sql", "what sql", "sql query", "sql statement", "show query", "display query", 
                       "show me the sql", "show me sql", "the sql", "see sql", "view sql", "display the query",
                       "show the query", "the query", "query used", "used query"]
        if any(keyword in message_lower for keyword in sql_keywords):
            return {
                "intent": "SQL_RETRIEVAL",
                "reasoning": "User wants to see the SQL query/statement",
                "confidence": 0.9
            }
        
        # Check for off-topic indicators (must check before default SQL_QUERY)
        off_topic_keywords = [
            "hello", "hi", "greetings", "how are you", "what can you do", "help",
            "tell me a joke", "joke", "jokes",
            "weather", "what's the weather", "what is the weather", "temperature",
            "time", "what time", "date", "what date",
            "thanks", "thank you", "bye", "goodbye"
        ]
        # Only mark as off-topic if it's a greeting/general question without database-related context
        if any(keyword in message_lower for keyword in off_topic_keywords):
            # Check if there's database-related context
            db_keywords = ["app", "apps", "revenue", "install", "installs", "query", "database", "data", "country", "platform", "csv", "export", "sql"]
            if not any(keyword in message_lower or keyword in context_lower for keyword in db_keywords):
                return {
                    "intent": "OFF_TOPIC",
                    "reasoning": "User message appears to be a greeting or off-topic question",
                    "confidence": 0.7
                }
        
        # Default to SQL_QUERY (most common case)
        return {
            "intent": "SQL_QUERY",
            "reasoning": "User wants to query the database (default classification)",
            "confidence": 0.8
        }
    
    def route(
        self,
        user_message: str,
        thread_ts: str,
        conversation_history: Optional[List[BaseMessage]] = None
    ) -> IntentType:
        """Route user message to appropriate agent.
        
        This is a convenience method that returns just the intent.
        
        Args:
            user_message: User's message/question
            thread_ts: Slack thread timestamp
            conversation_history: Optional conversation history
        
        Returns:
            Intent type (SQL_QUERY, CSV_EXPORT, SQL_RETRIEVAL, or OFF_TOPIC)
        """
        result = self.classify_intent(user_message, thread_ts, conversation_history)
        return result["intent"]


# Global router agent instance
_router_agent: Optional[RouterAgent] = None


def get_router_agent() -> RouterAgent:
    """Get or create Router Agent instance.
    
    Returns:
        RouterAgent instance
    """
    global _router_agent
    if _router_agent is None:
        _router_agent = RouterAgent()
        logger.debug("Created Router Agent instance")
    return _router_agent

