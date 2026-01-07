"""Sanity check test for Agent Tools."""
import logging
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.agents.tools import (
    generate_sql_tool,
    execute_sql_tool,
    format_result_tool,
    generate_csv_tool,
    get_sql_history_tool,
    get_tools
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_tools():
    """Sanity check for Agent Tools."""
    print("\n=== Agent Tools Sanity Check ===\n")
    
    # Ensure database exists
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        print("[SKIP] Database not found. Please run Phase 1 setup first.")
        return
    
    # Test 1: Tool Registry
    print("1. Testing tool registry...")
    tools = get_tools()
    assert len(tools) == 6, f"Expected 6 tools, got {len(tools)}"
    tool_names = [tool.name for tool in tools]
    print(f"   Found tools: {', '.join(tool_names)}")
    assert 'generate_sql_tool' in tool_names
    assert 'execute_sql_tool' in tool_names
    assert 'format_result_tool' in tool_names
    assert 'generate_csv_tool' in tool_names
    assert 'get_sql_history_tool' in tool_names
    print("   [OK] Tool registry works\n")
    
    # Test 2: Execute SQL Tool (direct test without LLM)
    print("2. Testing execute_sql_tool...")
    result = execute_sql_tool.invoke({
        "sql_query": "SELECT COUNT(*) as total FROM app_portfolio"
    })
    assert result['success'] is True, f"Query failed: {result.get('error')}"
    assert 'data' in result
    assert result['row_count'] > 0
    total = result['data'][0]['total']
    print(f"   Total records: {total}")
    print("   [OK] execute_sql_tool works\n")
    
    # Test 3: Format Result Tool - Simple Count
    print("3. Testing format_result_tool (simple count)...")
    simple_result = {
        'success': True,
        'data': [{'total': total}],
        'row_count': 1,
        'columns': ['total'],
        'query': 'SELECT COUNT(*) as total FROM app_portfolio'
    }
    formatted = format_result_tool.invoke({
        "results": simple_result,
        "question": "How many apps are there?"
    })
    print(f"   Formatted result: {formatted}")
    assert len(formatted) > 0
    assert str(total) in formatted
    print("   [OK] format_result_tool (simple) works\n")
    
    # Test 4: Format Result Tool - Table Format
    print("4. Testing format_result_tool (table format)...")
    table_result = execute_sql_tool.invoke({
        "sql_query": "SELECT platform, COUNT(*) as count FROM app_portfolio GROUP BY platform"
    })
    assert table_result['success'] is True
    formatted_table = format_result_tool.invoke({
        "results": table_result,
        "question": "Show apps by platform"
    })
    print(f"   Formatted result:\n{formatted_table}")
    assert '|' in formatted_table or 'platform' in formatted_table.lower()
    print("   [OK] format_result_tool (table) works\n")
    
    # Test 5: Generate CSV Tool
    print("5. Testing generate_csv_tool...")
    csv_data = execute_sql_tool.invoke({
        "sql_query": "SELECT app_name, platform, country FROM app_portfolio LIMIT 5"
    })
    assert csv_data['success'] is True
    csv_path = generate_csv_tool.invoke({
        "data": csv_data['data'],
        "filename": "sanity_test_export.csv"
    })
    assert Path(csv_path).exists(), "CSV file was not created"
    print(f"   CSV generated: {csv_path}")
    
    # Verify CSV content
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'app_name' in content, "Header missing"
        assert len(content.split('\n')) > 1, "Data rows missing"
    print("   [OK] generate_csv_tool works")
    
    # Cleanup CSV
    Path(csv_path).unlink()
    print("   [OK] CSV cleanup done\n")
    
    # Test 6: Generate SQL Tool (with mocked LLM)
    print("6. Testing generate_sql_tool...")
    with patch('ai.llm_caller.call_llm') as mock_llm:
        mock_llm.return_value = iter([
            "SELECT platform, COUNT(*) as count FROM app_portfolio GROUP BY platform"
        ])
        
        sql_query = generate_sql_tool.invoke({
            "question": "How many apps are there by platform?"
        })
        
        assert "SELECT" in sql_query.upper()
        assert "app_portfolio" in sql_query.lower()
        assert "platform" in sql_query.lower()
        print(f"   Generated SQL: {sql_query}")
        print("   [OK] generate_sql_tool works\n")
    
    # Test 7: Generate SQL Tool with conversation history
    print("7. Testing generate_sql_tool with conversation history...")
    with patch('ai.llm_caller.call_llm') as mock_llm:
        mock_llm.return_value = iter([
            "SELECT app_name FROM app_portfolio WHERE platform = 'iOS' LIMIT 5"
        ])
        
        sql_query = generate_sql_tool.invoke({
            "question": "What are the top 5?",
            "conversation_history": [
                "User: Show me iOS apps",
                "Assistant: Here are some iOS apps..."
            ]
        })
        
        assert "SELECT" in sql_query.upper()
        assert "app_portfolio" in sql_query.lower()
        print(f"   Generated SQL: {sql_query}")
        print("   [OK] generate_sql_tool with history works\n")
    
    # Test 8: Get SQL History Tool (placeholder)
    print("8. Testing get_sql_history_tool...")
    history_result = get_sql_history_tool.invoke({
        "thread_ts": "1234567890.123456"
    })
    assert 'sql_found' in history_result
    assert history_result['sql_found'] is False  # Placeholder returns False
    assert 'message' in history_result
    print(f"   Result: {history_result['message']}")
    print("   [OK] get_sql_history_tool works (placeholder)\n")
    
    # Test 9: End-to-end workflow
    print("9. Testing end-to-end workflow...")
    with patch('ai.llm_caller.call_llm') as mock_llm:
        # Mock SQL generation
        mock_llm.return_value = iter([
            "SELECT country, SUM(in_app_revenue + ads_revenue) as total_revenue "
            "FROM app_portfolio GROUP BY country ORDER BY total_revenue DESC LIMIT 3"
        ])
        
        # Step 1: Generate SQL
        sql_query = generate_sql_tool.invoke({
            "question": "What are the top 3 countries by revenue?"
        })
        print(f"   Step 1 - Generated SQL: {sql_query[:80]}...")
        
        # Step 2: Execute SQL
        exec_result = execute_sql_tool.invoke({"sql_query": sql_query})
        assert exec_result['success'] is True
        print(f"   Step 2 - Executed query: {exec_result['row_count']} rows")
        
        # Step 3: Format results
        formatted = format_result_tool.invoke({
            "results": exec_result,
            "question": "What are the top 3 countries by revenue?"
        })
        print(f"   Step 3 - Formatted result:\n{formatted[:200]}...")
        assert len(formatted) > 0
        
        # Step 4: Generate CSV
        csv_path = generate_csv_tool.invoke({
            "data": exec_result['data'],
            "filename": "sanity_workflow_export.csv"
        })
        assert Path(csv_path).exists()
        print(f"   Step 4 - Generated CSV: {Path(csv_path).name}")
        
        # Cleanup
        Path(csv_path).unlink()
        print("   [OK] End-to-end workflow works\n")
    
    # Test 10: Error handling
    print("10. Testing error handling...")
    
    # Invalid SQL
    invalid_result = execute_sql_tool.invoke({
        "sql_query": "SELECT * FROM nonexistent_table"
    })
    assert invalid_result['success'] is False
    assert 'error' in invalid_result
    print(f"   Invalid query handled: {invalid_result['error'][:50]}...")
    
    # Dangerous query
    dangerous_result = execute_sql_tool.invoke({
        "sql_query": "DROP TABLE app_portfolio"
    })
    assert dangerous_result['success'] is False
    print(f"   Dangerous query rejected: {dangerous_result['error'][:50]}...")
    
    # Empty data formatting
    empty_result = {
        'success': True,
        'data': [],
        'row_count': 0,
        'columns': [],
        'query': 'SELECT * FROM app_portfolio WHERE 1=0'
    }
    empty_formatted = format_result_tool.invoke({
        "results": empty_result,
        "question": "Show apps"
    })
    assert "no results" in empty_formatted.lower() or "not found" in empty_formatted.lower()
    print("   Empty result handled correctly")
    
    print("   [OK] Error handling works\n")
    
    print("=== All sanity checks passed! ===\n")


if __name__ == '__main__':
    test_tools()

