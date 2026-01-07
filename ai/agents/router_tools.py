"""Routing tools for Router Agent.

These tools are used by the Router Agent to classify user intent
and route to appropriate specialized agents.
"""
import logging
from typing import Literal

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Intent types
IntentType = Literal["SQL_QUERY", "CSV_EXPORT", "SQL_RETRIEVAL", "OFF_TOPIC"]


@tool
def route_to_sql_agent_tool(user_message: str, conversation_context: str = "") -> dict:
    """Route to SQL Query Agent for database queries.
    
    Use this tool when the user wants to query the database or ask questions
    about app portfolio data. This includes:
    - Questions about apps, revenue, installs, countries, platforms
    - Aggregations (counts, sums, averages)
    - Filtering and sorting queries
    - Follow-up questions about previous query results
    
    Args:
        user_message: The user's message/question
        conversation_context: Optional context from previous messages in the thread
    
    Returns:
        Dictionary with intent classification and reasoning
    """
    logger.info(f"route_to_sql_agent_tool called for message: {user_message[:100]}...")
    
    return {
        "intent": "SQL_QUERY",
        "reasoning": f"User wants to query the database: {user_message}",
        "confidence": 1.0
    }


@tool
def route_to_csv_export_tool(user_message: str, conversation_context: str = "") -> dict:
    """Route to CSV Export Agent for exporting query results.
    
    Use this tool when the user wants to export data to CSV, download results,
    or get a file export. Common phrases include:
    - "export to CSV", "download", "save as CSV", "get CSV file"
    - "export the results", "send me a file"
    
    Args:
        user_message: The user's message/question
        conversation_context: Optional context from previous messages in the thread
    
    Returns:
        Dictionary with intent classification and reasoning
    """
    logger.info(f"route_to_csv_export_tool called for message: {user_message[:100]}...")
    
    return {
        "intent": "CSV_EXPORT",
        "reasoning": f"User wants CSV export: {user_message}",
        "confidence": 1.0
    }


@tool
def route_to_sql_retrieval_tool(user_message: str, conversation_context: str = "") -> dict:
    """Route to SQL Retrieval Agent for viewing SQL statements.
    
    Use this tool when the user wants to see the SQL query that was used,
    view the SQL statement, or understand how data was retrieved. Common phrases:
    - "show me the SQL", "what SQL was used", "display the query"
    - "show query", "SQL statement", "how was this queried"
    
    Args:
        user_message: The user's message/question
        conversation_context: Optional context from previous messages in the thread
    
    Returns:
        Dictionary with intent classification and reasoning
    """
    logger.info(f"route_to_sql_retrieval_tool called for message: {user_message[:100]}...")
    
    return {
        "intent": "SQL_RETRIEVAL",
        "reasoning": f"User wants to see SQL statement: {user_message}",
        "confidence": 1.0
    }


@tool
def route_to_off_topic_tool(user_message: str, conversation_context: str = "") -> dict:
    """Route to Off-Topic Handler for non-database questions.
    
    Use this tool when the user's question is not related to the database,
    app portfolio, or SQL queries. This includes:
    - General questions unrelated to the database
    - Questions about other topics
    - Requests that cannot be fulfilled by database queries
    
    Args:
        user_message: The user's message/question
        conversation_context: Optional context from previous messages in the thread
    
    Returns:
        Dictionary with intent classification and reasoning
    """
    logger.info(f"route_to_off_topic_tool called for message: {user_message[:100]}...")
    
    return {
        "intent": "OFF_TOPIC",
        "reasoning": f"User question is off-topic: {user_message}",
        "confidence": 1.0
    }


# Router tools registry
ROUTER_TOOLS = [
    route_to_sql_agent_tool,
    route_to_csv_export_tool,
    route_to_sql_retrieval_tool,
    route_to_off_topic_tool
]


def get_router_tools():
    """Get all routing tools for the Router Agent.
    
    Returns:
        List of routing tool instances
    """
    logger.debug(f"Returning {len(ROUTER_TOOLS)} router tools")
    return ROUTER_TOOLS

