"""SQL Service for query validation and execution."""
import re
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class SQLService:
    """Service for SQL query validation and execution."""
    
    # Dangerous SQL keywords that should not be allowed
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE',
        'EXEC', 'EXECUTE', 'MERGE', 'REPLACE'
    ]
    
    # Allowed SQL keywords for SELECT queries
    ALLOWED_KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
        'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN',
        'UNION', 'UNION ALL', 'LIMIT', 'OFFSET', 'DISTINCT', 'AS',
        'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS NULL', 'IS NOT NULL',
        'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
    ]
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQL Service.
        
        Args:
            db_path: Path to SQLite database file (defaults to data/app_portfolio.db)
        """
        if db_path is None:
            # Default to data/app_portfolio.db relative to project root
            project_root = Path(__file__).parent.parent
            db_path = str(project_root / "data" / "app_portfolio.db")
        
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.connect()
    
    def validate_sql(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validate SQL query for security and correctness.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Empty query"
        
        query_upper = query.upper().strip()
        
        # Must start with SELECT
        if not query_upper.startswith('SELECT'):
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_upper):
                return False, f"Dangerous keyword '{keyword}' is not allowed"
        
        # Check for multiple statements (prevent injection via semicolon)
        if ';' in query.rstrip().rstrip(';'):
            # Allow trailing semicolon
            query_parts = [q.strip() for q in query.split(';') if q.strip()]
            if len(query_parts) > 1:
                return False, "Multiple statements are not allowed"
        
        # Must reference app_portfolio table (case-insensitive check in original query)
        if 'app_portfolio' not in query.lower():
            return False, "Query must reference 'app_portfolio' table"
        
        # Basic syntax check - ensure balanced parentheses
        if query.count('(') != query.count(')'):
            return False, "Unbalanced parentheses in query"
        
        return True, None
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute validated SQL query and return results.
        
        Args:
            query: SQL query string (will be validated)
            
        Returns:
            Dictionary with 'success', 'data', 'error', 'row_count', 'columns'
        """
        # Validate query first
        is_valid, error_msg = self.validate_sql(query)
        if not is_valid:
            logger.warning(f"Invalid query rejected: {error_msg}")
            return {
                'success': False,
                'data': [],
                'error': error_msg,
                'row_count': 0,
                'columns': [],
                'query': query
            }
        
        try:
            # Execute query
            results = self.db_manager.execute_query(query)
            
            # Extract column names from first row if available
            columns = list(results[0].keys()) if results else []
            
            logger.info(f"Query executed successfully: {len(results)} rows returned")
            
            return {
                'success': True,
                'data': results,
                'error': None,
                'row_count': len(results),
                'columns': columns,
                'query': query
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Query execution failed: {error_msg}")
            return {
                'success': False,
                'data': [],
                'error': error_msg,
                'row_count': 0,
                'columns': [],
                'query': query
            }
    
    def get_query_type(self, query: str) -> str:
        """Determine the type of query for formatting decisions.
        
        Args:
            query: SQL query string
            
        Returns:
            Query type: 'simple_count', 'aggregation', 'list', 'complex'
        """
        query_upper = query.upper()
        
        # Simple COUNT queries
        if re.search(r'SELECT\s+COUNT\s*\(', query_upper):
            if 'GROUP BY' not in query_upper:
                return 'simple_count'
        
        # Aggregation queries (GROUP BY, SUM, AVG, etc.)
        if 'GROUP BY' in query_upper:
            return 'aggregation'
        
        # Aggregations without GROUP BY (single row result)
        if any(func in query_upper for func in ['SUM(', 'AVG(', 'MAX(', 'MIN(', 'COUNT(']):
            return 'aggregation'
        
        # Simple list queries (SELECT * or SELECT columns)
        if 'SELECT' in query_upper and 'GROUP BY' not in query_upper:
            return 'list'
        
        # Complex queries (JOINs, subqueries, etc.)
        if any(keyword in query_upper for keyword in ['JOIN', 'UNION', 'CASE', 'HAVING']):
            return 'complex'
        
        return 'list'
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information for SQL generation context.
        
        Returns:
            Dictionary with schema information
        """
        try:
            table_info = self.db_manager.get_table_info()
            schema = self.db_manager.get_schema()
            
            return {
                'table_name': 'app_portfolio',
                'columns': [
                    {
                        'name': col['name'],
                        'type': col['type'],
                        'not_null': bool(col['notnull']),
                        'default': col['dflt_value']
                    }
                    for col in table_info
                ],
                'schema_sql': schema
            }
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            return {
                'table_name': 'app_portfolio',
                'columns': [],
                'schema_sql': ''
            }
    
    def close(self):
        """Close database connection."""
        self.db_manager.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

