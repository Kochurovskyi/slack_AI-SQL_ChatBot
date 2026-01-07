"""LangChain tools for SQL database analytics agents.

This module defines all tools used by ReAct agents:
- generate_sql_tool: Generate SQL from natural language
- execute_sql_tool: Execute SQL queries
- format_result_tool: Format query results
- generate_csv_tool: Generate CSV exports
- get_sql_history_tool: Retrieve SQL query history
"""
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.sql_service import SQLService
from services.formatting_service import FormattingService
from services.csv_service import CSVService

logger = logging.getLogger(__name__)

# Database schema for SQL generation (static, included in system prompt)
DATABASE_SCHEMA = """
CREATE TABLE app_portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL,
    platform TEXT NOT NULL CHECK(platform IN ('iOS', 'Android')),
    date DATE NOT NULL,
    country TEXT NOT NULL,
    installs INTEGER DEFAULT 0,
    in_app_revenue DECIMAL(10, 2) DEFAULT 0.0,
    ads_revenue DECIMAL(10, 2) DEFAULT 0.0,
    ua_cost DECIMAL(10, 2) DEFAULT 0.0
);

Indexes:
- idx_app_name ON app_portfolio(app_name)
- idx_platform ON app_portfolio(platform)
- idx_date ON app_portfolio(date)
- idx_country ON app_portfolio(country)
"""

# Global service instances (initialized lazily)
_sql_service: Optional[SQLService] = None
_formatting_service: Optional[FormattingService] = None
_csv_service: Optional[CSVService] = None


def _get_sql_service() -> SQLService:
    """Get or create SQL service instance."""
    global _sql_service
    if _sql_service is None:
        _sql_service = SQLService()
        logger.debug("Initialized SQLService instance")
    return _sql_service


def _get_formatting_service() -> FormattingService:
    """Get or create formatting service instance."""
    global _formatting_service
    if _formatting_service is None:
        _formatting_service = FormattingService()
        logger.debug("Initialized FormattingService instance")
    return _formatting_service


def _get_csv_service() -> CSVService:
    """Get or create CSV service instance."""
    global _csv_service
    if _csv_service is None:
        _csv_service = CSVService()
        logger.debug("Initialized CSVService instance")
    return _csv_service


@tool
def generate_sql_tool(question: str, conversation_history: Optional[List[str]] = None) -> str:
    """Generate SQL query from natural language question.
    
    This tool converts a natural language question into a SQL SELECT query
    for the app_portfolio database. The database schema is provided in the
    system prompt (static), so this tool focuses on understanding the user's
    intent and generating appropriate SQL.
    
    Args:
        question: User's natural language question about the database
        conversation_history: Optional list of previous messages in the thread
                             for context (e.g., follow-up questions)
    
    Returns:
        Generated SQL query string (SELECT only)
    
    Example:
        Input: "How many iOS apps are there?"
        Output: "SELECT COUNT(*) as total FROM app_portfolio WHERE platform = 'iOS'"
    """
    logger.info(f"generate_sql_tool called with question: {question[:100]}...")
    
    try:
        # Import here to avoid circular dependencies
        from ai.llm_caller import call_llm
        
        # Build context from conversation history
        context_parts = []
        if conversation_history:
            context_parts.append("Previous conversation context:")
            for i, msg in enumerate(conversation_history[-3:], 1):  # Last 3 messages
                context_parts.append(f"{i}. {msg}")
        
        # Build prompt for SQL generation
        system_prompt = f"""You are a SQL query generator for an app portfolio database.

Database Schema:
{DATABASE_SCHEMA}

Rules:
1. Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
2. Always reference the 'app_portfolio' table
3. Use proper SQL syntax for SQLite
4. Consider conversation context when provided
5. Use appropriate aggregations (COUNT, SUM, AVG, MAX, MIN) when needed
6. Include WHERE clauses for filtering when appropriate
7. Use ORDER BY for sorting when relevant
8. Use LIMIT for top-N queries

Return ONLY the SQL query, no explanations or markdown formatting."""

        user_prompt = f"""Generate a SQL query for this question: {question}"""
        
        if context_parts:
            user_prompt += f"\n\n{chr(10).join(context_parts)}"
        
        # Call LLM to generate SQL
        logger.debug(f"Calling LLM for SQL generation with question: {question[:50]}...")
        response_chunks = []
        for chunk in call_llm(
            messages_in_thread=[{"role": "user", "content": user_prompt}],
            system_content=system_prompt
        ):
            response_chunks.append(chunk)
        
        sql_query = "".join(response_chunks).strip()
        
        # Clean up SQL query (remove markdown code blocks if present)
        if sql_query.startswith("```"):
            lines = sql_query.split("\n")
            # Remove first line if it's ```sql or ```
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            sql_query = "\n".join(lines).strip()
        
        logger.info(f"Generated SQL query: {sql_query[:100]}...")
        logger.debug(f"Full SQL query: {sql_query}")
        
        return sql_query
        
    except Exception as e:
        error_msg = f"Failed to generate SQL query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)


@tool
def execute_sql_tool(sql_query: str) -> Dict[str, Any]:
    """Execute SQL query against the app_portfolio database.
    
    This tool validates and executes a SQL SELECT query, returning
    the results in a structured format. Only SELECT queries are allowed
    for security reasons.
    
    Args:
        sql_query: SQL SELECT query string to execute
    
    Returns:
        Dictionary with:
        - success: Boolean indicating if query executed successfully
        - data: List of dictionaries (rows) with query results
        - error: Error message if execution failed (None if success)
        - row_count: Number of rows returned
        - columns: List of column names
        - query: The executed SQL query
    
    Example:
        Input: "SELECT COUNT(*) as total FROM app_portfolio WHERE platform = 'iOS'"
        Output: {{"success": True, "data": [{{"total": 25}}], "error": None, 
                 "row_count": 1, "columns": ["total"], "query": "..."}}
    """
    logger.info(f"execute_sql_tool called with query: {sql_query[:100]}...")
    
    try:
        sql_service = _get_sql_service()
        
        # Execute query (validation happens inside SQLService)
        result = sql_service.execute_query(sql_query)
        
        if result['success']:
            logger.info(f"Query executed successfully: {result['row_count']} rows returned")
            logger.debug(f"Query columns: {result['columns']}")
        else:
            logger.warning(f"Query execution failed: {result['error']}")
        
        return result
        
    except Exception as e:
        error_msg = f"Failed to execute SQL query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'data': [],
            'error': error_msg,
            'row_count': 0,
            'columns': [],
            'query': sql_query
        }


@tool
def format_result_tool(results: Dict[str, Any], question: str) -> str:
    """Format query results for Slack display.
    
    This tool formats SQL query results as either simple text (for simple
    queries) or markdown tables (for complex queries). The formatting decision
    is based on the result complexity and query type. For complex queries,
    it automatically generates assumptions and explanations.
    
    Args:
        results: Dictionary from execute_sql_tool containing:
                - success: Boolean
                - data: List of result rows
                - row_count: Number of rows
                - columns: Column names
                - query: SQL query string
        question: Original user question for context
    
    Returns:
        Formatted string ready for Slack display (markdown format)
    
    Example:
        Input: {{"success": True, "data": [{{"total": 25}}], ...}}
        Output: "25"
    """
    logger.info(f"format_result_tool called with {results.get('row_count', 0)} rows")
    
    try:
        if not results.get('success', False):
            error_msg = results.get('error', 'Unknown error')
            logger.warning(f"Formatting failed query results: {error_msg}")
            return f"Error: {error_msg}"
        
        data = results.get('data', [])
        if not data:
            logger.info("No data to format")
            return "No results found."
        
        formatting_service = _get_formatting_service()
        sql_service = _get_sql_service()
        
        # Determine query type for formatting decisions
        query = results.get('query', '')
        query_type = sql_service.get_query_type(query)
        
        logger.debug(f"Query type determined: {query_type}")
        
        # Generate assumptions for complex queries
        assumptions = None
        if query_type in ['complex', 'aggregation'] and len(data) > 1:
            assumptions = _generate_assumptions(query, question, data, query_type)
        
        # Format results
        formatted = formatting_service.format_result(
            data=data,
            query_type=query_type,
            assumptions=assumptions
        )
        
        logger.info(f"Formatted result: {len(formatted)} characters")
        logger.debug(f"Formatted output preview: {formatted[:200]}...")
        
        return formatted
        
    except Exception as e:
        error_msg = f"Failed to format results: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"Error formatting results: {error_msg}"


def _generate_assumptions(query: str, question: str, data: List[Dict], query_type: str) -> str:
    """Generate assumptions and explanations for complex queries.
    
    Args:
        query: SQL query string
        question: Original user question
        data: Query result data
        query_type: Type of query
    
    Returns:
        Assumptions/explanation string
    """
    try:
        assumptions_parts = []
        
        # Check for date/time assumptions
        if 'date' in query.lower() or 'time' in query.lower():
            # Try to infer timeframe from query
            if '2024' in query or '2025' in query:
                assumptions_parts.append("Timeframe based on dates in query")
            else:
                assumptions_parts.append("Timeframe: All available data")
        
        # Check for aggregation assumptions
        if query_type == 'aggregation':
            if 'SUM' in query.upper():
                assumptions_parts.append("Total values calculated across all matching records")
            elif 'AVG' in query.upper():
                assumptions_parts.append("Average calculated across all matching records")
            elif 'COUNT' in query.upper():
                assumptions_parts.append("Count includes all matching records")
        
        # Check for sorting/ordering
        if 'ORDER BY' in query.upper():
            if 'DESC' in query.upper():
                assumptions_parts.append("Results sorted in descending order")
            elif 'ASC' in query.upper():
                assumptions_parts.append("Results sorted in ascending order")
        
        # Check for popularity/ranking
        if 'popularity' in question.lower() or 'popular' in question.lower():
            # Try to infer popularity metric
            if 'installs' in query.lower():
                assumptions_parts.append("Popularity defined by number of installs")
            elif 'revenue' in query.lower():
                assumptions_parts.append("Popularity defined by revenue")
            else:
                assumptions_parts.append("Popularity metric inferred from query context")
        
        # Check for LIMIT/top-N
        if 'LIMIT' in query.upper():
            import re
            limit_match = re.search(r'LIMIT\s+(\d+)', query.upper())
            if limit_match:
                limit_num = limit_match.group(1)
                assumptions_parts.append(f"Showing top {limit_num} results")
        
        # If no specific assumptions, add general one
        if not assumptions_parts:
            assumptions_parts.append("Results based on current database state")
        
        return "; ".join(assumptions_parts)
        
    except Exception as e:
        logger.warning(f"Failed to generate assumptions: {e}")
        return "Results based on current database state"


@tool
def generate_csv_tool(data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
    """Generate CSV file from query results.
    
    This tool creates a CSV file from query result data. The CSV file
    is saved to a temporary directory and can be uploaded to Slack.
    
    Args:
        data: List of dictionaries (rows) from query results
        filename: Optional filename for the CSV file (defaults to timestamp-based name)
    
    Returns:
        Path to the generated CSV file
    
    Example:
        Input: [{{"app_name": "App1", "revenue": 1000}}, {{"app_name": "App2", "revenue": 2000}}]
        Output: "/tmp/app_portfolio_export_20240101_120000.csv"
    """
    logger.info(f"generate_csv_tool called with {len(data)} rows")
    
    try:
        if not data:
            raise ValueError("Cannot generate CSV from empty data")
        
        csv_service = _get_csv_service()
        
        # Generate CSV file
        csv_path = csv_service.generate_csv(data, filename)
        
        logger.info(f"Generated CSV file: {csv_path}")
        logger.debug(f"CSV file contains {len(data)} rows")
        
        return csv_path
        
    except Exception as e:
        error_msg = f"Failed to generate CSV: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)


@tool
def get_sql_history_tool(thread_ts: str, query_description: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve SQL query history for a thread.
    
    This tool retrieves previously executed SQL queries from memory store
    for a given thread. Can retrieve the last query or search by description.
    
    Args:
        thread_ts: Slack thread timestamp
        query_description: Optional description to search for specific query
                          (e.g., "all the apps", "total apps", "how many apps")
    
    Returns:
        Dictionary with:
        - sql_found: Boolean indicating if SQL was found
        - sql_statement: SQL query string (if found)
        - query_timestamp: Timestamp when query was executed (if found)
        - question: Original question that generated this SQL (if found)
        - message: Status message
    
    Example:
        Input: ("1234567890.123456", "all the apps")
        Output: {{"sql_found": True, "sql_statement": "SELECT COUNT(*) FROM app_portfolio", 
                 "query_timestamp": "2024-01-01 12:00:00", "question": "how many apps do we have?", "message": "..."}}
    """
    logger.info(f"get_sql_history_tool called for thread: {thread_ts}, description: {query_description}")
    
    try:
        from ai.memory_store import memory_store
        
        queries = memory_store.get_sql_queries(thread_ts)
        
        if not queries:
            return {
                'sql_found': False,
                'sql_statement': None,
                'query_timestamp': None,
                'question': None,
                'message': 'No SQL queries found for this thread. Please run a query first.'
            }
        
        # If description provided, search for matching query
        if query_description:
            query_lower = query_description.lower()
            for query_info in reversed(queries):  # Search from most recent
                question = query_info.get('question', '').lower()
                sql = query_info.get('sql', '').lower()
                
                # Check if description matches question or SQL
                if query_lower in question or any(word in question for word in query_lower.split() if len(word) > 3):
                    logger.info(f"Found matching query by description: {query_info.get('question')[:50]}")
                    return {
                        'sql_found': True,
                        'sql_statement': query_info.get('sql'),
                        'query_timestamp': query_info.get('timestamp'),
                        'question': query_info.get('question'),
                        'message': f"Found SQL query matching: {query_description}"
                    }
        
        # Return last query if no description or no match
        last_query = queries[-1]
        logger.info(f"Returning last SQL query: {last_query.get('question', '')[:50]}")
        return {
            'sql_found': True,
            'sql_statement': last_query.get('sql'),
            'query_timestamp': last_query.get('timestamp'),
            'question': last_query.get('question'),
            'message': 'Retrieved last SQL query from thread history.'
        }
        
    except Exception as e:
        error_msg = f"Failed to retrieve SQL history: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'sql_found': False,
            'sql_statement': None,
            'query_timestamp': None,
            'question': None,
            'message': error_msg
        }


@tool
def get_cached_results_tool(thread_ts: str) -> Dict[str, Any]:
    """Retrieve last query results for a thread.
    
    This tool retrieves the last executed query results from memory store
    for a given thread. Used for CSV export without regenerating SQL.
    
    Args:
        thread_ts: Slack thread timestamp
    
    Returns:
        Dictionary with:
        - results_found: Boolean indicating if results were found
        - data: Query result data (list of dictionaries) if found
        - row_count: Number of rows in results
        - query_timestamp: Timestamp when query was executed (if found)
        - sql_query: SQL query that generated these results
        - message: Status message
    
    Example:
        Input: "1234567890.123456"
        Output: {"results_found": True, "data": [{"app_name": "App1", ...}], 
                 "row_count": 50, "query_timestamp": "2024-01-01 12:00:00", "message": "..."}
    """
    logger.info(f"get_cached_results_tool called for thread: {thread_ts}")
    
    try:
        from ai.memory_store import memory_store
        
        last_query = memory_store.get_last_sql_query(thread_ts)
        
        if not last_query:
            return {
                'results_found': False,
                'data': None,
                'row_count': 0,
                'query_timestamp': None,
                'sql_query': None,
                'message': 'No previous query results found. Please run a query first.'
            }
        
        results = last_query.get('results')
        
        if not results or not results.get('success', False):
            return {
                'results_found': False,
                'data': None,
                'row_count': 0,
                'query_timestamp': last_query.get('timestamp'),
                'sql_query': last_query.get('sql'),
                'message': 'Previous query did not return results or query failed.'
            }
        
        data = results.get('data', [])
        logger.info(f"Retrieved {len(data)} rows from last query")
        
        return {
            'results_found': True,
            'data': data,
            'row_count': len(data),
            'query_timestamp': last_query.get('timestamp'),
            'sql_query': last_query.get('sql'),
            'message': f'Retrieved {len(data)} rows from last query.'
        }
        
    except Exception as e:
        error_msg = f"Failed to retrieve query results: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'results_found': False,
            'data': None,
            'row_count': 0,
            'query_timestamp': None,
            'sql_query': None,
            'message': error_msg
        }


# Tool registry for easy access
ALL_TOOLS = [
    generate_sql_tool,
    execute_sql_tool,
    format_result_tool,
    generate_csv_tool,
    get_sql_history_tool,
    get_cached_results_tool
]


def get_tools() -> List:
    """Get all available tools for agents.
    
    Returns:
        List of tool instances
    """
    logger.debug(f"Returning {len(ALL_TOOLS)} tools")
    return ALL_TOOLS

