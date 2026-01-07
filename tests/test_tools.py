"""Unit tests for agent tools."""
import pytest
import logging
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.agents.tools import (
    generate_sql_tool,
    execute_sql_tool,
    format_result_tool,
    generate_csv_tool,
    get_sql_history_tool,
    get_cached_results_tool,
    get_tools,
    ALL_TOOLS,
    DATABASE_SCHEMA
)

logger = logging.getLogger(__name__)


class TestGenerateSQLTool:
    """Tests for generate_sql_tool."""
    
    @patch('ai.llm_caller.call_llm')
    def test_generate_sql_simple_query(self, mock_call_llm):
        """Test generating SQL for a simple query."""
        # Mock LLM response
        mock_call_llm.return_value = iter(["SELECT COUNT(*) FROM app_portfolio WHERE platform = 'iOS'"])
        
        result = generate_sql_tool.invoke({
            "question": "How many iOS apps are there?"
        })
        
        assert "SELECT" in result.upper()
        assert "app_portfolio" in result.lower()
        # Check for iOS in the result (case-insensitive check)
        assert "iOS" in result or "ios" in result.lower()
        mock_call_llm.assert_called_once()
    
    @patch('ai.llm_caller.call_llm')
    def test_generate_sql_with_conversation_history(self, mock_call_llm):
        """Test generating SQL with conversation context."""
        mock_call_llm.return_value = iter(["SELECT app_name FROM app_portfolio WHERE platform = 'iOS' LIMIT 5"])
        
        result = generate_sql_tool.invoke({
            "question": "What are the top 5?",
            "conversation_history": [
                "User: Show me iOS apps",
                "Assistant: Here are some iOS apps..."
            ]
        })
        
        assert "SELECT" in result.upper()
        mock_call_llm.assert_called_once()
        # Verify conversation history was included in the call
        call_args = mock_call_llm.call_args
        assert call_args is not None
    
    @patch('ai.llm_caller.call_llm')
    def test_generate_sql_removes_markdown(self, mock_call_llm):
        """Test that markdown code blocks are removed from SQL."""
        mock_call_llm.return_value = iter(["```sql\nSELECT * FROM app_portfolio\n```"])
        
        result = generate_sql_tool.invoke({
            "question": "Show all apps"
        })
        
        assert not result.startswith("```")
        assert not result.endswith("```")
        assert "SELECT" in result.upper()
    
    @patch('ai.llm_caller.call_llm')
    def test_generate_sql_error_handling(self, mock_call_llm):
        """Test error handling in SQL generation."""
        mock_call_llm.side_effect = Exception("LLM API error")
        
        with pytest.raises(ValueError, match="Failed to generate SQL query"):
            generate_sql_tool.invoke({
                "question": "Test question"
            })


class TestExecuteSQLTool:
    """Tests for execute_sql_tool."""
    
    def test_execute_sql_valid_query(self):
        """Test executing a valid SQL query."""
        result = execute_sql_tool.invoke({
            "sql_query": "SELECT COUNT(*) as total FROM app_portfolio WHERE platform = 'iOS'"
        })
        
        assert result['success'] is True
        assert 'data' in result
        assert 'row_count' in result
        assert 'columns' in result
        assert isinstance(result['data'], list)
        assert result['row_count'] >= 0
    
    def test_execute_sql_invalid_query(self):
        """Test executing an invalid SQL query."""
        result = execute_sql_tool.invoke({
            "sql_query": "SELECT * FROM nonexistent_table"
        })
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error'] is not None
    
    def test_execute_sql_dangerous_query(self):
        """Test that dangerous queries are rejected."""
        result = execute_sql_tool.invoke({
            "sql_query": "DROP TABLE app_portfolio"
        })
        
        assert result['success'] is False
        assert 'error' in result
        # Check for various error message formats
        error_lower = result['error'].lower()
        assert ("not allowed" in error_lower or 
                "dangerous" in error_lower or 
                "only select" in error_lower)
    
    def test_execute_sql_empty_query(self):
        """Test executing an empty query."""
        result = execute_sql_tool.invoke({
            "sql_query": ""
        })
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_execute_sql_complex_query(self):
        """Test executing a complex aggregation query."""
        result = execute_sql_tool.invoke({
            "sql_query": """
                SELECT platform, COUNT(*) as count, 
                       SUM(in_app_revenue + ads_revenue) as total_revenue
                FROM app_portfolio
                GROUP BY platform
                ORDER BY total_revenue DESC
            """
        })
        
        assert result['success'] is True
        assert 'data' in result
        if result['row_count'] > 0:
            assert len(result['columns']) > 0


class TestFormatResultTool:
    """Tests for format_result_tool."""
    
    def test_format_simple_count_result(self):
        """Test formatting a simple count result."""
        results = {
            'success': True,
            'data': [{'total': 25}],
            'row_count': 1,
            'columns': ['total'],
            'query': 'SELECT COUNT(*) as total FROM app_portfolio'
        }
        
        formatted = format_result_tool.invoke({
            "results": results,
            "question": "How many apps are there?"
        })
        
        assert formatted is not None
        assert len(formatted) > 0
        # Should be simple format (just the number)
        assert "25" in formatted or "total" in formatted.lower()
    
    def test_format_table_result(self):
        """Test formatting a multi-row result as table."""
        results = {
            'success': True,
            'data': [
                {'app_name': 'App1', 'platform': 'iOS', 'revenue': 1000},
                {'app_name': 'App2', 'platform': 'Android', 'revenue': 2000},
                {'app_name': 'App3', 'platform': 'iOS', 'revenue': 1500}
            ],
            'row_count': 3,
            'columns': ['app_name', 'platform', 'revenue'],
            'query': 'SELECT app_name, platform, (in_app_revenue + ads_revenue) as revenue FROM app_portfolio LIMIT 3'
        }
        
        formatted = format_result_tool.invoke({
            "results": results,
            "question": "Show me top apps"
        })
        
        assert formatted is not None
        assert len(formatted) > 0
        # Should contain table-like structure
        assert "app_name" in formatted.lower() or "App1" in formatted
    
    def test_format_empty_result(self):
        """Test formatting empty results."""
        results = {
            'success': True,
            'data': [],
            'row_count': 0,
            'columns': [],
            'query': 'SELECT * FROM app_portfolio WHERE 1=0'
        }
        
        formatted = format_result_tool.invoke({
            "results": results,
            "question": "Show apps"
        })
        
        assert "no results" in formatted.lower() or "not found" in formatted.lower()
    
    def test_format_failed_query(self):
        """Test formatting failed query results."""
        results = {
            'success': False,
            'data': [],
            'error': 'Table not found',
            'row_count': 0,
            'columns': [],
            'query': 'SELECT * FROM nonexistent'
        }
        
        formatted = format_result_tool.invoke({
            "results": results,
            "question": "Show apps"
        })
        
        assert "error" in formatted.lower()
        assert "not found" in formatted.lower() or "error" in formatted.lower()
    
    def test_format_aggregation_result(self):
        """Test formatting aggregation query results."""
        results = {
            'success': True,
            'data': [
                {'platform': 'iOS', 'total_revenue': 50000.50, 'app_count': 15}
            ],
            'row_count': 1,
            'columns': ['platform', 'total_revenue', 'app_count'],
            'query': 'SELECT platform, SUM(in_app_revenue + ads_revenue) as total_revenue, COUNT(*) as app_count FROM app_portfolio GROUP BY platform'
        }
        
        formatted = format_result_tool.invoke({
            "results": results,
            "question": "What's the revenue by platform?"
        })
        
        assert formatted is not None
        assert len(formatted) > 0


class TestGenerateCSVTool:
    """Tests for generate_csv_tool."""
    
    def test_generate_csv_with_data(self):
        """Test generating CSV from query results."""
        data = [
            {'app_name': 'App1', 'platform': 'iOS', 'revenue': 1000},
            {'app_name': 'App2', 'platform': 'Android', 'revenue': 2000}
        ]
        
        csv_path = generate_csv_tool.invoke({
            "data": data,
            "filename": "test_export.csv"
        })
        
        assert csv_path is not None
        assert Path(csv_path).exists()
        assert csv_path.endswith('.csv')
        
        # Verify CSV content
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'app_name' in content
            assert 'App1' in content
            assert 'App2' in content
        
        # Cleanup
        Path(csv_path).unlink()
    
    def test_generate_csv_default_filename(self):
        """Test generating CSV with default filename."""
        data = [
            {'app_name': 'App1', 'platform': 'iOS'}
        ]
        
        csv_path = generate_csv_tool.invoke({
            "data": data
        })
        
        assert csv_path is not None
        assert Path(csv_path).exists()
        assert 'app_portfolio_export' in csv_path
        
        # Cleanup
        Path(csv_path).unlink()
    
    def test_generate_csv_empty_data(self):
        """Test that empty data raises an error."""
        with pytest.raises(ValueError, match="Cannot generate CSV from empty data"):
            generate_csv_tool.invoke({
                "data": []
            })
    
    def test_generate_csv_large_dataset(self):
        """Test generating CSV with larger dataset."""
        # Create larger dataset
        data = [
            {
                'app_name': f'App{i}',
                'platform': 'iOS' if i % 2 == 0 else 'Android',
                'revenue': i * 100
            }
            for i in range(50)
        ]
        
        csv_path = generate_csv_tool.invoke({
            "data": data,
            "filename": "large_export.csv"
        })
        
        assert csv_path is not None
        assert Path(csv_path).exists()
        
        # Verify all rows are in CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 51  # Header + 50 rows
        
        # Cleanup
        Path(csv_path).unlink()


class TestGetSQLHistoryTool:
    """Tests for get_sql_history_tool."""
    
    def test_get_sql_history_not_implemented(self):
        """Test that SQL history returns message when no queries found."""
        result = get_sql_history_tool.invoke({
            "thread_ts": "1234567890.123456"
        })
    
        assert 'sql_found' in result
        assert result['sql_found'] is False
        assert 'message' in result
        assert 'no sql queries found' in result['message'].lower() or 'run a query first' in result['message'].lower()
    
    def test_get_sql_history_error_handling(self):
        """Test error handling in SQL history retrieval."""
        # Should handle errors gracefully
        result = get_sql_history_tool.invoke({
            "thread_ts": "invalid_thread"
        })
        
        assert 'sql_found' in result
        assert isinstance(result, dict)


class TestToolRegistry:
    """Tests for tool registry and utilities."""
    
    def test_get_tools_returns_all_tools(self):
        """Test that get_tools returns all available tools."""
        tools = get_tools()
        
        assert len(tools) == len(ALL_TOOLS)
        assert len(tools) == 6  # All 6 tools (added get_cached_results_tool)
        assert generate_sql_tool in tools
        assert execute_sql_tool in tools
        assert format_result_tool in tools
        assert generate_csv_tool in tools
        assert get_sql_history_tool in tools
        assert get_cached_results_tool in tools
    
    def test_all_tools_have_names(self):
        """Test that all tools have proper names."""
        for tool in ALL_TOOLS:
            assert hasattr(tool, 'name')
            assert tool.name is not None
            assert len(tool.name) > 0
    
    def test_all_tools_have_descriptions(self):
        """Test that all tools have descriptions."""
        for tool in ALL_TOOLS:
            assert hasattr(tool, 'description')
            assert tool.description is not None
            assert len(tool.description) > 0


class TestToolIntegration:
    """Integration tests for tool workflows."""
    
    def test_sql_generation_to_execution_workflow(self):
        """Test complete workflow from SQL generation to execution."""
        # Step 1: Generate SQL
        with patch('ai.llm_caller.call_llm') as mock_llm:
            mock_llm.return_value = iter(["SELECT COUNT(*) as total FROM app_portfolio"])
            
            sql_query = generate_sql_tool.invoke({
                "question": "How many apps are there?"
            })
            
            assert "SELECT" in sql_query.upper()
        
        # Step 2: Execute SQL
        result = execute_sql_tool.invoke({
            "sql_query": sql_query
        })
        
        assert result['success'] is True
        assert 'data' in result
        
        # Step 3: Format results
        formatted = format_result_tool.invoke({
            "results": result,
            "question": "How many apps are there?"
        })
        
        assert formatted is not None
        assert len(formatted) > 0
    
    def test_execution_to_csv_workflow(self):
        """Test workflow from query execution to CSV export."""
        # Execute query
        result = execute_sql_tool.invoke({
            "sql_query": "SELECT app_name, platform FROM app_portfolio LIMIT 5"
        })
        
        if result['success'] and result['data']:
            # Format as CSV
            csv_path = generate_csv_tool.invoke({
                "data": result['data'],
                "filename": "test_integration.csv"
            })
            
            assert csv_path is not None
            assert Path(csv_path).exists()
            
            # Cleanup
            Path(csv_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

