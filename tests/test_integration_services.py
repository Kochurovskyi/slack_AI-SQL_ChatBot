"""Integration tests for SQL, Formatting, and CSV services."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.sql_service import SQLService
from services.formatting_service import FormattingService
from services.csv_service import CSVService


def test_sql_and_formatting_integration():
    """Test SQL Service + Formatting Service integration."""
    # Setup
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        print("Skipping: Database not found")
        return
    
    sql_service = SQLService(str(db_path))
    formatter = FormattingService()
    
    try:
        # Execute query
        query = "SELECT COUNT(*) as total FROM app_portfolio"
        result = sql_service.execute_query(query)
        
        assert result['success'], f"Query failed: {result['error']}"
        assert len(result['data']) == 1
        
        # Format result
        query_type = sql_service.get_query_type(query)
        formatted = formatter.format_result(result['data'], query_type)
        
        assert formatted == "50", f"Expected '50', got '{formatted}'"
        print("[OK] SQL + Formatting integration works")
        
    finally:
        sql_service.close()


def test_sql_and_csv_integration():
    """Test SQL Service + CSV Service integration."""
    # Setup
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        print("Skipping: Database not found")
        return
    
    sql_service = SQLService(str(db_path))
    csv_service = CSVService(str(project_root / "temp_test"))
    
    try:
        # Execute query
        query = "SELECT app_name, platform, country FROM app_portfolio LIMIT 5"
        result = sql_service.execute_query(query)
        
        assert result['success'], f"Query failed: {result['error']}"
        assert len(result['data']) > 0
        
        # Generate CSV
        csv_path = csv_service.generate_csv(result['data'], "integration_test.csv")
        
        assert Path(csv_path).exists(), "CSV file should exist"
        
        # Verify CSV content
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5, f"Expected 5 rows, got {len(rows)}"
            assert 'app_name' in rows[0]
        
        print("[OK] SQL + CSV integration works")
        
        # Cleanup
        csv_service.cleanup_temp_file(csv_path)
        
    finally:
        sql_service.close()


def test_full_workflow_integration():
    """Test full workflow: SQL -> Format -> CSV."""
    # Setup
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        print("Skipping: Database not found")
        return
    
    sql_service = SQLService(str(db_path))
    formatter = FormattingService()
    csv_service = CSVService(str(project_root / "temp_test"))
    
    try:
        # Step 1: Execute query
        query = "SELECT platform, COUNT(*) as count FROM app_portfolio GROUP BY platform"
        result = sql_service.execute_query(query)
        
        assert result['success'], f"Query failed: {result['error']}"
        assert len(result['data']) == 2  # iOS and Android
        
        # Step 2: Format result
        query_type = sql_service.get_query_type(query)
        formatted = formatter.format_result(result['data'], query_type)
        
        assert 'platform' in formatted.lower() or 'iOS' in formatted
        assert 'Android' in formatted or '29' in formatted
        
        # Step 3: Generate CSV
        csv_path = csv_service.generate_csv(result['data'], "full_workflow_test.csv")
        
        assert Path(csv_path).exists()
        
        # Verify CSV has correct data
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            platforms = [row['platform'] for row in rows]
            assert 'iOS' in platforms
            assert 'Android' in platforms
        
        print("[OK] Full workflow integration works")
        
        # Cleanup
        csv_service.cleanup_temp_file(csv_path)
        
    finally:
        sql_service.close()


def test_query_type_detection_and_formatting():
    """Test query type detection affects formatting."""
    # Setup
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        print("Skipping: Database not found")
        return
    
    sql_service = SQLService(str(db_path))
    formatter = FormattingService()
    
    try:
        # Simple COUNT query
        query1 = "SELECT COUNT(*) as total FROM app_portfolio"
        result1 = sql_service.execute_query(query1)
        query_type1 = sql_service.get_query_type(query1)
        formatted1 = formatter.format_result(result1['data'], query_type1)
        
        assert query_type1 == 'simple_count'
        assert formatted1 == "50"  # Should be simple format
        
        # Aggregation query
        query2 = "SELECT platform, COUNT(*) as count FROM app_portfolio GROUP BY platform"
        result2 = sql_service.execute_query(query2)
        query_type2 = sql_service.get_query_type(query2)
        formatted2 = formatter.format_result(result2['data'], query_type2)
        
        assert query_type2 == 'aggregation'
        assert '|' in formatted2  # Should be table format
        
        # List query
        query3 = "SELECT app_name, platform FROM app_portfolio LIMIT 3"
        result3 = sql_service.execute_query(query3)
        query_type3 = sql_service.get_query_type(query3)
        formatted3 = formatter.format_result(result3['data'], query_type3)
        
        assert query_type3 == 'list'
        assert len(result3['data']) == 3
        
        print("[OK] Query type detection + formatting works")
        
    finally:
        sql_service.close()


def test_error_handling_integration():
    """Test error handling across services."""
    # Setup
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        print("Skipping: Database not found")
        return
    
    sql_service = SQLService(str(db_path))
    formatter = FormattingService()
    csv_service = CSVService(str(project_root / "temp_test"))
    
    try:
        # Invalid query
        result = sql_service.execute_query("DROP TABLE app_portfolio")
        assert not result['success'], "Should reject dangerous query"
        
        # Format empty result
        formatted = formatter.format_result([], 'list')
        assert formatted == "No results found."
        
        # CSV with empty data
        try:
            csv_service.generate_csv([])
            assert False, "Should raise ValueError"
        except ValueError:
            pass  # Expected
        
        print("[OK] Error handling integration works")
        
    finally:
        sql_service.close()


def test_complex_query_workflow():
    """Test complex query with aggregation and formatting."""
    # Setup
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        print("Skipping: Database not found")
        return
    
    sql_service = SQLService(str(db_path))
    formatter = FormattingService()
    csv_service = CSVService(str(project_root / "temp_test"))
    
    try:
        # Complex aggregation query
        query = """
            SELECT country, 
                   SUM(in_app_revenue + ads_revenue) as total_revenue,
                   AVG(installs) as avg_installs
            FROM app_portfolio 
            GROUP BY country 
            ORDER BY total_revenue DESC 
            LIMIT 5
        """
        
        result = sql_service.execute_query(query)
        assert result['success']
        assert len(result['data']) == 5
        
        # Format as table
        query_type = sql_service.get_query_type(query)
        formatted = formatter.format_result(result['data'], query_type, 
                                           assumptions="Top 5 countries by revenue")
        
        assert '|' in formatted  # Should be table
        assert 'Note:' in formatted or '*Note:' in formatted
        assert 'country' in formatted.lower() or 'revenue' in formatted.lower()
        
        # Export to CSV
        csv_path = csv_service.generate_csv(result['data'], "complex_query.csv")
        assert Path(csv_path).exists()
        
        # Verify CSV structure
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5
            assert 'country' in rows[0]
            assert 'total_revenue' in rows[0]
            assert 'avg_installs' in rows[0]
        
        print("[OK] Complex query workflow works")
        
        # Cleanup
        csv_service.cleanup_temp_file(csv_path)
        
    finally:
        sql_service.close()


if __name__ == '__main__':
    # Run all integration tests
    tests = [
        test_sql_and_formatting_integration,
        test_sql_and_csv_integration,
        test_full_workflow_integration,
        test_query_type_detection_and_formatting,
        test_error_handling_integration,
        test_complex_query_workflow
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            if "Skipping" in str(e) or "not found" in str(e).lower():
                print(f"[SKIP] {test.__name__}: {e}")
                skipped += 1
            else:
                print(f"[ERROR] {test.__name__}: {e}")
                failed += 1
    
    print(f"\n=== Integration Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total: {passed + failed + skipped}")

