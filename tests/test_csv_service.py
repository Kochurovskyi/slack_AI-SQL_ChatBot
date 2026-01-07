"""Unit tests for CSV Service."""
import csv
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.csv_service import CSVService


def test_generate_csv_basic():
    """Test basic CSV generation."""
    temp_dir = Path(__file__).parent.parent / "temp_test"
    temp_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(temp_dir))
    
    data = [
        {'app_name': 'Music Elite', 'platform': 'iOS', 'installs': 66420},
        {'app_name': 'Shop Live', 'platform': 'Android', 'installs': 63630}
    ]
    
    csv_path = csv_service.generate_csv(data, "test_basic.csv")
    assert Path(csv_path).exists(), "CSV file should exist"
    assert csv_path.endswith('.csv'), "Should have .csv extension"
    
    # Verify content
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2, "Should have 2 data rows"
        assert rows[0]['app_name'] == 'Music Elite'
        assert rows[1]['app_name'] == 'Shop Live'
    
    # Cleanup
    csv_service.cleanup_temp_file(csv_path)


def test_generate_csv_auto_filename():
    """Test CSV generation with auto-generated filename."""
    temp_dir = Path(__file__).parent.parent / "temp_test"
    temp_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(temp_dir))
    
    data = [{'col1': 'val1', 'col2': 'val2'}]
    csv_path = csv_service.generate_csv(data)
    
    assert Path(csv_path).exists()
    assert csv_path.endswith('.csv')
    assert 'app_portfolio_export' in Path(csv_path).name
    
    csv_service.cleanup_temp_file(csv_path)


def test_generate_csv_without_extension():
    """Test CSV generation adds .csv extension if missing."""
    temp_dir = Path(__file__).parent.parent / "temp_test"
    temp_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(temp_dir))
    
    data = [{'col': 'val'}]
    csv_path = csv_service.generate_csv(data, "test_no_ext")
    
    assert csv_path.endswith('.csv')
    assert Path(csv_path).exists()
    
    csv_service.cleanup_temp_file(csv_path)


def test_generate_csv_empty_data():
    """Test CSV generation with empty data raises error."""
    temp_dir = Path(__file__).parent.parent / "temp_test"
    temp_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(temp_dir))
    
    try:
        csv_service.generate_csv([])
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_generate_csv_all_columns():
    """Test CSV includes all columns."""
    temp_dir = Path(__file__).parent.parent / "temp_test"
    temp_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(temp_dir))
    
    data = [
        {'id': 1, 'app_name': 'Music', 'platform': 'iOS', 'country': 'US'},
        {'id': 2, 'app_name': 'Shop', 'platform': 'Android', 'country': 'UK'}
    ]
    
    csv_path = csv_service.generate_csv(data, "test_all_cols.csv")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert 'id' in rows[0], "Should include id column"
        assert 'app_name' in rows[0]
        assert 'platform' in rows[0]
        assert 'country' in rows[0]
    
    csv_service.cleanup_temp_file(csv_path)


def test_generate_csv_special_characters():
    """Test CSV handles special characters."""
    temp_dir = Path(__file__).parent.parent / "temp_test"
    temp_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(temp_dir))
    
    data = [
        {'name': 'App "Quoted"', 'desc': 'Has, commas'},
        {'name': 'App\nNewline', 'desc': 'Has "quotes"'}
    ]
    
    csv_path = csv_service.generate_csv(data, "test_special.csv")
    
    # Should not raise exception
    assert Path(csv_path).exists()
    
    csv_service.cleanup_temp_file(csv_path)


def test_cleanup_temp_file():
    """Test file cleanup."""
    temp_dir = Path(__file__).parent.parent / "temp_test"
    temp_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(temp_dir))
    
    data = [{'col': 'val'}]
    csv_path = csv_service.generate_csv(data, "test_cleanup.csv")
    
    assert Path(csv_path).exists()
    csv_service.cleanup_temp_file(csv_path)
    assert not Path(csv_path).exists(), "File should be deleted"


def test_cleanup_nonexistent_file():
    """Test cleanup of non-existent file doesn't crash."""
    temp_dir = Path(__file__).parent.parent / "temp_test"
    temp_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(temp_dir))
    
    # Should not raise exception
    csv_service.cleanup_temp_file("nonexistent.csv")


def test_csv_service_custom_temp_dir():
    """Test CSV service with custom temp directory."""
    custom_dir = Path(__file__).parent.parent / "custom_temp"
    custom_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(custom_dir))
    
    data = [{'col': 'val'}]
    csv_path = csv_service.generate_csv(data, "test_custom.csv")
    
    assert str(custom_dir) in csv_path
    assert Path(csv_path).exists()
    
    csv_service.cleanup_temp_file(csv_path)


if __name__ == '__main__':
    # Run all tests
    tests = [
        test_generate_csv_basic,
        test_generate_csv_auto_filename,
        test_generate_csv_without_extension,
        test_generate_csv_empty_data,
        test_generate_csv_all_columns,
        test_generate_csv_special_characters,
        test_cleanup_temp_file,
        test_cleanup_nonexistent_file,
        test_csv_service_custom_temp_dir
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

