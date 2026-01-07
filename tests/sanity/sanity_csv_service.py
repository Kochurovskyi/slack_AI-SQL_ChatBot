"""Sanity check test for CSV Service."""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.csv_service import CSVService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_csv_service():
    """Sanity check for CSV Service."""
    # Use a test temp directory
    test_temp_dir = Path(__file__).parent.parent.parent / "temp_test"
    test_temp_dir.mkdir(exist_ok=True)
    
    csv_service = CSVService(str(test_temp_dir))
    
    print("\n=== CSV Service Sanity Check ===\n")
    
    # Test 1: Generate CSV from simple data
    print("1. Testing CSV generation...")
    data = [
        {'app_name': 'Music Elite', 'platform': 'iOS', 'country': 'United States', 'installs': 66420},
        {'app_name': 'Shop Live', 'platform': 'iOS', 'country': 'Sweden', 'installs': 63630}
    ]
    csv_path = csv_service.generate_csv(data, "test_export.csv")
    assert Path(csv_path).exists(), "CSV file was not created"
    print(f"   [OK] CSV generated: {csv_path}")
    
    # Verify CSV content
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'app_name' in content, "Header missing"
        assert 'Music Elite' in content, "Data missing"
    print("   [OK] CSV content verified\n")
    
    # Test 2: Generate CSV with timestamp filename
    print("2. Testing auto-generated filename...")
    csv_path2 = csv_service.generate_csv(data)
    assert Path(csv_path2).exists(), "CSV file was not created"
    assert csv_path2.endswith('.csv'), "Filename should end with .csv"
    print(f"   [OK] Auto-generated filename: {Path(csv_path2).name}\n")
    
    # Test 3: Generate CSV from aggregation data
    print("3. Testing CSV from aggregation data...")
    agg_data = [
        {'platform': 'iOS', 'count': 21},
        {'platform': 'Android', 'count': 29}
    ]
    csv_path3 = csv_service.generate_csv(agg_data, "test_aggregation.csv")
    assert Path(csv_path3).exists(), "CSV file was not created"
    print(f"   [OK] Aggregation CSV generated\n")
    
    # Test 4: Empty data handling
    print("4. Testing empty data handling...")
    try:
        csv_service.generate_csv([])
        print("   [FAIL] Should have raised ValueError")
    except ValueError:
        print("   [OK] Empty data correctly rejected\n")
    
    # Test 5: Cleanup
    print("5. Testing file cleanup...")
    csv_service.cleanup_temp_file(csv_path)
    assert not Path(csv_path).exists(), "File should be deleted"
    print("   [OK] File cleanup works\n")
    
    # Cleanup test files
    for path in [csv_path2, csv_path3]:
        if Path(path).exists():
            csv_service.cleanup_temp_file(path)
    
    print("=== All sanity checks passed! ===\n")


if __name__ == '__main__':
    test_csv_service()

