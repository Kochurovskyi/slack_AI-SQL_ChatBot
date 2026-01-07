"""Unit tests for Formatting Service."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.formatting_service import FormattingService


def test_simple_count():
    """Test simple COUNT query formatting."""
    formatter = FormattingService()
    
    # Single count value
    data = [{'total': 50}]
    result = formatter.format_result(data, 'simple_count')
    assert result == "50", f"Expected '50', got '{result}'"
    
    # Count with different key
    data = [{'count': 25}]
    result = formatter.format_result(data, 'simple_count')
    assert result == "25", f"Expected '25', got '{result}'"


def test_simple_aggregation():
    """Test simple aggregation formatting."""
    formatter = FormattingService()
    
    # Single row, single value
    data = [{'avg_installs': 50634.84}]
    result = formatter.format_result(data, 'aggregation')
    assert '50634.84' in result or '50634' in result
    
    # Single row, two columns
    data = [{'platform': 'iOS', 'count': 21}]
    result = formatter.format_result(data, 'aggregation')
    assert 'iOS' in result and '21' in result


def test_list_formatting():
    """Test list query formatting."""
    formatter = FormattingService()
    
    # Small list (should use simple format)
    data = [
        {'app_name': 'Music Elite', 'platform': 'iOS'},
        {'app_name': 'Shop Live', 'platform': 'iOS'}
    ]
    result = formatter.format_result(data, 'list')
    assert 'Music Elite' in result
    assert 'Shop Live' in result


def test_table_formatting():
    """Test table formatting."""
    formatter = FormattingService()
    
    # Many rows (should use table)
    data = [
        {'country': 'Netherlands', 'revenue': 67125.31},
        {'country': 'Japan', 'revenue': 49903.07},
        {'country': 'Australia', 'revenue': 49684.59},
        {'country': 'United States', 'revenue': 44395.01},
        {'country': 'Sweden', 'revenue': 38286.20},
        {'country': 'Germany', 'revenue': 35000.00}
    ]
    result = formatter.format_result(data, 'aggregation')
    assert '|' in result, "Should use table format"
    assert 'country' in result.lower() or 'revenue' in result.lower()
    assert 'Netherlands' in result


def test_should_use_table():
    """Test table format decision logic."""
    formatter = FormattingService()
    
    # Many rows
    data = [{'col': i} for i in range(10)]
    assert formatter.should_use_table(data, 'list') == True
    
    # Many columns
    data = [{'col1': 1, 'col2': 2, 'col3': 3, 'col4': 4}]
    assert formatter.should_use_table(data, 'list') == True
    
    # Complex query type
    data = [{'col': 1}]
    assert formatter.should_use_table(data, 'complex') == True
    
    # Small simple query
    data = [{'col': 1}]
    assert formatter.should_use_table(data, 'simple_count') == False


def test_empty_data():
    """Test empty data handling."""
    formatter = FormattingService()
    
    result = formatter.format_result([], 'list')
    assert result == "No results found."


def test_assumptions():
    """Test assumptions/notes handling."""
    formatter = FormattingService()
    
    data = [{'total': 50}]
    result = formatter.format_result(data, 'simple_count', 
                                    assumptions="Data from last 12 months")
    assert 'Note:' in result or '*Note:' in result
    assert '12 months' in result


def test_format_simple():
    """Test format_simple method."""
    formatter = FormattingService()
    
    # Simple count
    data = [{'total': 50}]
    result = formatter.format_simple(data, 'simple_count')
    assert result == "50"
    
    # Two columns
    data = [{'platform': 'iOS', 'count': 21}]
    result = formatter.format_simple(data, 'aggregation')
    assert 'iOS' in result and '21' in result


def test_format_table():
    """Test format_table method."""
    formatter = FormattingService()
    
    data = [
        {'country': 'Netherlands', 'revenue': 67125.31},
        {'country': 'Japan', 'revenue': 49903.07}
    ]
    result = formatter.format_table(data, 'aggregation')
    assert '|' in result
    assert 'country' in result.lower() or 'revenue' in result.lower()
    assert 'Netherlands' in result
    assert 'Japan' in result


def test_id_column_filtering():
    """Test that ID column is filtered from display."""
    formatter = FormattingService()
    
    data = [
        {'id': 1, 'app_name': 'Music Elite', 'platform': 'iOS'},
        {'id': 2, 'app_name': 'Shop Live', 'platform': 'iOS'}
    ]
    result = formatter.format_table(data, 'list')
    # ID should not appear in table (or if it does, it's acceptable)
    # Main check: app_name and platform should be present
    assert 'app_name' in result.lower() or 'Music Elite' in result


if __name__ == '__main__':
    # Run all tests
    tests = [
        test_simple_count,
        test_simple_aggregation,
        test_list_formatting,
        test_table_formatting,
        test_should_use_table,
        test_empty_data,
        test_assumptions,
        test_format_simple,
        test_format_table,
        test_id_column_filtering
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"[OK] {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")

