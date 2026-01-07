"""Sanity check test for Formatting Service."""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.formatting_service import FormattingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_formatting_service():
    """Sanity check for Formatting Service."""
    formatter = FormattingService()
    
    print("\n=== Formatting Service Sanity Check ===\n")
    
    # Test 1: Simple COUNT
    print("1. Testing simple COUNT format...")
    data = [{'total': 50}]
    result = formatter.format_result(data, 'simple_count')
    print(f"   Result: {result}")
    assert result == "50", "Simple count failed"
    print("   [OK] Simple COUNT format works\n")
    
    # Test 2: Platform COUNT (aggregation)
    print("2. Testing aggregation format...")
    data = [
        {'platform': 'iOS', 'count': 21},
        {'platform': 'Android', 'count': 29}
    ]
    result = formatter.format_result(data, 'aggregation')
    print(f"   Result:\n{result}")
    assert 'iOS' in result and 'Android' in result, "Aggregation format failed"
    print("   [OK] Aggregation format works\n")
    
    # Test 3: Table format (many rows)
    print("3. Testing table format...")
    data = [
        {'country': 'Netherlands', 'revenue': 67125.31},
        {'country': 'Japan', 'revenue': 49903.07},
        {'country': 'Australia', 'revenue': 49684.59},
        {'country': 'United States', 'revenue': 44395.01},
        {'country': 'Sweden', 'revenue': 38286.20},
        {'country': 'Germany', 'revenue': 35000.00}
    ]
    result = formatter.format_result(data, 'aggregation')
    print(f"   Result:\n{result}")
    assert '|' in result, "Table format failed"
    print("   [OK] Table format works\n")
    
    # Test 4: Empty data
    print("4. Testing empty data...")
    result = formatter.format_result([], 'list')
    print(f"   Result: {result}")
    assert result == "No results found.", "Empty data handling failed"
    print("   [OK] Empty data handling works\n")
    
    # Test 5: Assumptions
    print("5. Testing assumptions note...")
    data = [{'total': 50}]
    result = formatter.format_result(data, 'simple_count', 
                                    assumptions="Data from last 12 months")
    print(f"   Result:\n{result}")
    assert 'Note:' in result, "Assumptions handling failed"
    print("   [OK] Assumptions handling works\n")
    
    print("=== All sanity checks passed! ===\n")


if __name__ == '__main__':
    test_formatting_service()

