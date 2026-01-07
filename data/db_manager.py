"""Database manager for SQLite operations."""
import sqlite3
import csv
import logging
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations with thread-safe connections."""
    
    def __init__(self, db_path: str = "app_portfolio.db"):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._lock = threading.Lock()  # Lock for write operations
        # Keep a connection for backward compatibility (for context manager)
        self.connection: Optional[sqlite3.Connection] = None
    
    def _get_connection(self) -> sqlite3.Connection:
        """Create a new thread-safe database connection.
        
        Returns:
            New SQLite connection with check_same_thread=False for thread safety
        """
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def connect(self) -> sqlite3.Connection:
        """Create or get database connection (for backward compatibility).
        
        Note: For thread-safe operations, use _get_connection() instead.
        This method maintains backward compatibility but creates a new connection
        if the existing one is from a different thread.
        """
        # For thread safety, always create a new connection
        # The old connection is kept for context manager compatibility
        return self._get_connection()
    
    def close(self):
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass  # Ignore errors when closing
            finally:
                self.connection = None
    
    def initialize(self, schema_file: str = "schema.sql"):
        """Initialize database with schema (thread-safe).
        
        Args:
            schema_file: Path to SQL schema file
        """
        conn = None
        try:
            with self._lock:  # Lock for write operation
                conn = self._get_connection()
                schema_path = Path(schema_file)
                
                if not schema_path.exists():
                    raise FileNotFoundError(f"Schema file not found: {schema_file}")
                
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                conn.executescript(schema_sql)
                conn.commit()
                logger.info(f"Database initialized from {schema_file}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def load_from_csv(self, csv_file: str):
        """Load data from CSV file into database (thread-safe).
        
        Args:
            csv_file: Path to CSV file
        """
        conn = None
        try:
            with self._lock:  # Lock for write operation
                conn = self._get_connection()
                csv_path = Path(csv_file)
                
                if not csv_path.exists():
                    raise FileNotFoundError(f"CSV file not found: {csv_file}")
                
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    records = list(reader)
                
                insert_sql = """
                    INSERT INTO app_portfolio 
                    (app_name, platform, date, country, installs, in_app_revenue, ads_revenue, ua_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor = conn.cursor()
                for record in records:
                    cursor.execute(insert_sql, (
                        record['app_name'],
                        record['platform'],
                        record['date'],
                        record['country'],
                        int(record['installs']),
                        float(record['in_app_revenue']),
                        float(record['ads_revenue']),
                        float(record['ua_cost'])
                    ))
                
                conn.commit()
                logger.info(f"Loaded {len(records)} records from {csv_file}")
                return len(records)
        except Exception as e:
            logger.error(f"Failed to load data from CSV: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results (thread-safe).
        
        Args:
            query: SQL query string
            
        Returns:
            List of dictionaries representing rows
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def get_schema(self) -> str:
        """Get database schema information (thread-safe).
        
        Returns:
            Schema description string
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='app_portfolio'
            """)
            result = cursor.fetchone()
            
            if result:
                return result[0]
            return ""
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def get_table_info(self) -> List[Dict[str, Any]]:
        """Get table column information (thread-safe).
        
        Returns:
            List of column information dictionaries
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(app_portfolio)")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def count_records(self) -> int:
        """Get total record count (thread-safe).
        
        Returns:
            Number of records in app_portfolio table
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM app_portfolio")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Failed to count records: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

