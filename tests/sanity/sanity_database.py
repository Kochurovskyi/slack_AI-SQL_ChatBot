"""Sanity check test for database setup and operations."""
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database():
    """Test database initialization and operations."""
    # Use absolute paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "data" / "app_portfolio.db"
    schema_file = project_root / "data" / "schema.sql"
    csv_file = project_root / "data" / "sample_data.csv"
    
    # Remove existing database if it exists
    if db_path.exists():
        db_path.unlink()
        logger.info("Removed existing database")
    
    # Initialize database
    db = DatabaseManager(str(db_path))
    
    try:
        # 1. Initialize schema
        logger.info("Initializing database schema...")
        db.initialize(str(schema_file))
        logger.info("[OK] Schema initialized")
        
        # 2. Load data from CSV
        logger.info("Loading data from CSV...")
        count = db.load_from_csv(str(csv_file))
        logger.info(f"[OK] Loaded {count} records")
        
        # 3. Test queries
        logger.info("\n--- Testing Database ---")
        
        # Count records
        total = db.count_records()
        logger.info(f"Total records: {total}")
        assert total == 50, f"Expected 50 records, got {total}"
        
        # Test query: Get all records
        all_records = db.execute_query("SELECT * FROM app_portfolio LIMIT 5")
        logger.info(f"\nSample records (first 5):")
        for record in all_records:
            logger.info(f"  {record['app_name']} ({record['platform']}) - {record['country']}")
        
        # Test query: Count by platform
        platform_counts = db.execute_query(
            "SELECT platform, COUNT(*) as count FROM app_portfolio GROUP BY platform"
        )
        logger.info(f"\nRecords by platform:")
        for row in platform_counts:
            logger.info(f"  {row['platform']}: {row['count']}")
        
        # Test query: Sum revenue by country
        revenue_by_country = db.execute_query(
            """SELECT country, SUM(in_app_revenue + ads_revenue) as total_revenue
               FROM app_portfolio 
               GROUP BY country 
               ORDER BY total_revenue DESC 
               LIMIT 5"""
        )
        logger.info(f"\nTop 5 countries by revenue:")
        for row in revenue_by_country:
            logger.info(f"  {row['country']}: ${row['total_revenue']:.2f}")
        
        # Test query: Average installs
        avg_installs = db.execute_query(
            "SELECT AVG(installs) as avg_installs FROM app_portfolio"
        )
        logger.info(f"\nAverage installs: {avg_installs[0]['avg_installs']:.2f}")
        
        # Get schema info
        table_info = db.get_table_info()
        logger.info(f"\nTable columns ({len(table_info)}):")
        for col in table_info:
            logger.info(f"  {col['name']} ({col['type']})")
        
        logger.info("\n[OK] All tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    test_database()

