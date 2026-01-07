"""Formatting Service for query results."""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class FormattingService:
    """Service for formatting SQL query results for Slack."""
    
    # Maximum rows for simple text format (beyond this, use table)
    MAX_SIMPLE_ROWS = 5
    
    # Maximum columns for simple text format
    MAX_SIMPLE_COLUMNS = 3
    
    def __init__(self):
        """Initialize Formatting Service."""
        pass
    
    def format_simple(self, data: List[Dict[str, Any]], query_type: str) -> str:
        """Format query results as simple text.
        
        Args:
            data: Query result data (list of dictionaries)
            query_type: Type of query (simple_count, aggregation, list, complex)
            
        Returns:
            Formatted text string
        """
        if not data:
            return "No results found."
        
        # Simple COUNT queries
        if query_type == 'simple_count':
            count = data[0].get('total') or data[0].get('count') or list(data[0].values())[0]
            return str(count)
        
        # Single row aggregations
        if query_type == 'aggregation' and len(data) == 1:
            row = data[0]
            if len(row) == 1:
                # Single value result
                value = list(row.values())[0]
                return str(value)
            elif len(row) == 2:
                # Two columns: label and value
                values = list(row.values())
                return f"{values[0]}: {values[1]}"
            else:
                # Multiple columns - format as key-value pairs
                parts = []
                for key, value in row.items():
                    if key != 'id':  # Skip ID column
                        parts.append(f"{key}: {value}")
                return ", ".join(parts)
        
        # Multiple rows - format as list
        if len(data) <= self.MAX_SIMPLE_ROWS:
            lines = []
            for row in data:
                if len(row) == 1:
                    lines.append(str(list(row.values())[0]))
                elif len(row) == 2:
                    values = list(row.values())
                    lines.append(f"{values[0]}: {values[1]}")
                else:
                    # Take first two columns
                    items = list(row.items())[:2]
                    lines.append(f"{items[0][1]}: {items[1][1]}")
            return "\n".join(lines)
        
        # Too many rows for simple format
        return self.format_table(data, query_type)
    
    def format_table(self, data: List[Dict[str, Any]], query_type: str) -> str:
        """Format query results as Slack markdown table.
        
        Args:
            data: Query result data (list of dictionaries)
            query_type: Type of query (simple_count, aggregation, list, complex)
            
        Returns:
            Formatted markdown table string
        """
        if not data:
            return "No results found."
        
        if not data[0]:
            return "Empty result set."
        
        # Get column names
        columns = list(data[0].keys())
        
        # Filter out 'id' column if present (usually not needed in display)
        display_columns = [col for col in columns if col != 'id']
        if not display_columns:
            display_columns = columns
        
        # Build table header
        header = " | ".join(display_columns)
        separator = " | ".join(["---"] * len(display_columns))
        
        # Build table rows
        rows = []
        for row in data:
            values = []
            for col in display_columns:
                value = row.get(col, "")
                # Format values
                if isinstance(value, float):
                    # Format decimals nicely
                    if value == int(value):
                        values.append(str(int(value)))
                    else:
                        values.append(f"{value:.2f}")
                elif value is None:
                    values.append("")
                else:
                    values.append(str(value))
            rows.append(" | ".join(values))
        
        # Combine into markdown table
        table_lines = [header, separator] + rows
        return "\n".join(table_lines)
    
    def format_summary(self, data: List[Dict[str, Any]], query_type: str, 
                      assumptions: Optional[str] = None) -> str:
        """Format query results with summary and assumptions.
        
        Args:
            data: Query result data
            query_type: Type of query
            assumptions: Optional assumptions or context notes
            
        Returns:
            Formatted text with summary
        """
        # Determine format based on data size
        if len(data) <= self.MAX_SIMPLE_ROWS and len(data[0]) <= self.MAX_SIMPLE_COLUMNS:
            formatted = self.format_simple(data, query_type)
        else:
            formatted = self.format_table(data, query_type)
        
        # Add assumptions if provided
        if assumptions:
            return f"{formatted}\n\n*Note: {assumptions}*"
        
        return formatted
    
    def should_use_table(self, data: List[Dict[str, Any]], query_type: str) -> bool:
        """Determine if table format should be used.
        
        Args:
            data: Query result data
            query_type: Type of query
            
        Returns:
            True if table format should be used
        """
        if not data:
            return False
        
        # Always use table for complex queries
        if query_type == 'complex':
            return True
        
        # Use table if too many rows
        if len(data) > self.MAX_SIMPLE_ROWS:
            return True
        
        # Use table if too many columns
        if len(data[0]) > self.MAX_SIMPLE_COLUMNS:
            return True
        
        # Use table for aggregation queries with multiple rows
        if query_type == 'aggregation' and len(data) > 1:
            return True
        
        return False
    
    def format_result(self, data: List[Dict[str, Any]], query_type: str,
                     assumptions: Optional[str] = None) -> str:
        """Main method to format query results.
        
        Args:
            data: Query result data
            query_type: Type of query
            assumptions: Optional assumptions or context notes
            
        Returns:
            Formatted result string
        """
        if not data:
            return "No results found."
        
        # Determine format
        use_table = self.should_use_table(data, query_type)
        
        if use_table:
            formatted = self.format_table(data, query_type)
        else:
            formatted = self.format_simple(data, query_type)
        
        # Add assumptions if provided
        if assumptions:
            formatted = f"{formatted}\n\n*Note: {assumptions}*"
        
        return formatted

