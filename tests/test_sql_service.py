"""Test SQL Service functionality."""
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.sql_service import SQLService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_sql_service():
    """Test SQL Service with various query types."""
    # Ensure database exists
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        logger.error("Database not found. Please run Phase 1 setup first.")
        return
    
    service = SQLService(str(db_path))
    
    try:
        print("\n=== Testing SQL Service ===\n")
        
        # Test 1: Simple COUNT query
        print("1. Testing simple COUNT query...")
        result = service.execute_query("SELECT COUNT(*) as total FROM app_portfolio")
        assert result['success'], f"Query failed: {result['error']}"
        print(f"   [OK] Total apps: {result['data'][0]['total']}")
        
        # Test 2: Platform COUNT
        print("\n2. Testing platform COUNT query...")
        result = service.execute_query("SELECT platform, COUNT(*) as count FROM app_portfolio GROUP BY platform")
        assert result['success'], f"Query failed: {result['error']}"
        print(f"   [OK] Results:")
        for row in result['data']:
            print(f"     {row['platform']}: {row['count']}")
        
        # Test 3: Revenue aggregation
        print("\n3. Testing revenue aggregation...")
        result = service.execute_query(
            "SELECT country, SUM(in_app_revenue + ads_revenue) as total_revenue "
            "FROM app_portfolio GROUP BY country ORDER BY total_revenue DESC LIMIT 5"
        )
        assert result['success'], f"Query failed: {result['error']}"
        print(f"   [OK] Top 5 countries by revenue:")
        for row in result['data']:
            print(f"     {row['country']}: ${row['total_revenue']:.2f}")
        
        # Test 4: List query
        print("\n4. Testing list query...")
        result = service.execute_query(
            "SELECT app_name, platform, country FROM app_portfolio WHERE platform = 'iOS' LIMIT 5"
        )
        assert result['success'], f"Query failed: {result['error']}"
        print(f"   [OK] Sample iOS apps:")
        for row in result['data']:
            print(f"     {row['app_name']} - {row['country']}")
        
        # Test 5: Query type detection
        print("\n5. Testing query type detection...")
        queries = [
            ("SELECT COUNT(*) FROM app_portfolio", "simple_count"),
            ("SELECT platform, COUNT(*) FROM app_portfolio GROUP BY platform", "aggregation"),
            ("SELECT * FROM app_portfolio LIMIT 10", "list"),
        ]
        for query, expected_type in queries:
            query_type = service.get_query_type(query)
            status = "[OK]" if query_type == expected_type else "[FAIL]"
            print(f"   {status} '{query[:50]}...' -> {query_type} (expected: {expected_type})")
        
        # Test 6: Security validation - dangerous query
        print("\n6. Testing security validation...")
        dangerous_queries = [
            "DROP TABLE app_portfolio",
            "DELETE FROM app_portfolio",
            "UPDATE app_portfolio SET app_name = 'test'",
            "SELECT * FROM other_table",
        ]
        for query in dangerous_queries:
            is_valid, error = service.validate_sql(query)
            if not is_valid:
                print(f"   [OK] Rejected dangerous query: {query[:50]}...")
            else:
                print(f"   [FAIL] Failed to reject: {query[:50]}...")
        
        # Test 7: Schema info
        print("\n7. Testing schema info retrieval...")
        schema_info = service.get_schema_info()
        print(f"   [OK] Table: {schema_info['table_name']}")
        print(f"   [OK] Columns: {len(schema_info['columns'])}")
        for col in schema_info['columns'][:5]:
            print(f"     - {col['name']} ({col['type']})")
        
        print("\n=== All tests passed! ===\n")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        service.close()


if __name__ == '__main__':
    test_sql_service()

