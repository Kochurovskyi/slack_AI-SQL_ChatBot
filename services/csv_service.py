"""CSV Export Service for generating and uploading CSV files."""
import csv
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVService:
    """Service for CSV generation and Slack file upload."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize CSV Service.
        
        Args:
            temp_dir: Directory for temporary files (defaults to system temp)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
    
    def generate_csv(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Generate CSV file from query results.
        
        Args:
            data: Query result data (list of dictionaries)
            filename: Optional filename (defaults to timestamp-based name)
            
        Returns:
            Path to generated CSV file
        """
        if not data:
            raise ValueError("Cannot generate CSV from empty data")
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"app_portfolio_export_{timestamp}.csv"
        
        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # Create full path
        csv_path = Path(self.temp_dir) / filename
        
        # Get column names from first row
        columns = list(data[0].keys())
        
        # Filter out 'id' column if present (optional - can be included)
        # For CSV export, we typically want all columns
        # display_columns = [col for col in columns if col != 'id']
        # if not display_columns:
        display_columns = columns
        
        # Write CSV file
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=display_columns)
                writer.writeheader()
                
                for row in data:
                    # Write only the columns we want
                    filtered_row = {col: row.get(col, '') for col in display_columns}
                    writer.writerow(filtered_row)
            
            logger.info(f"Generated CSV file: {csv_path} with {len(data)} rows")
            return str(csv_path)
        
        except Exception as e:
            logger.error(f"Failed to generate CSV: {e}")
            raise
    
    def upload_to_slack(self, csv_path: str, client, channel: str, 
                       thread_ts: Optional[str] = None, 
                       title: Optional[str] = None) -> Dict[str, Any]:
        """Upload CSV file to Slack.
        
        Args:
            csv_path: Path to CSV file
            client: Slack WebClient instance
            channel: Slack channel ID
            thread_ts: Optional thread timestamp for threaded replies
            title: Optional title for the file
            
        Returns:
            Slack API response dictionary
        """
        csv_file = Path(csv_path)
        
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Generate title if not provided
        if not title:
            title = f"App Portfolio Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        try:
            # Upload file to Slack
            with open(csv_file, 'rb') as f:
                response = client.files_upload_v2(
                    channel=channel,
                    file=f,
                    filename=csv_file.name,
                    title=title,
                    thread_ts=thread_ts
                )
            
            logger.info(f"Uploaded CSV to Slack: {response.get('file', {}).get('id', 'unknown')}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to upload CSV to Slack: {e}")
            raise
    
    def generate_and_upload(self, data: List[Dict[str, Any]], client, channel: str,
                           thread_ts: Optional[str] = None,
                           filename: Optional[str] = None,
                           title: Optional[str] = None) -> Dict[str, Any]:
        """Generate CSV and upload to Slack in one step.
        
        Args:
            data: Query result data
            client: Slack WebClient instance
            channel: Slack channel ID
            thread_ts: Optional thread timestamp
            filename: Optional CSV filename
            title: Optional file title
            
        Returns:
            Slack API response dictionary
        """
        csv_path = self.generate_csv(data, filename)
        
        try:
            response = self.upload_to_slack(csv_path, client, channel, thread_ts, title)
            return response
        finally:
            # Clean up temporary file after upload
            try:
                Path(csv_path).unlink()
                logger.debug(f"Cleaned up temporary CSV file: {csv_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up CSV file: {e}")
    
    def cleanup_temp_file(self, csv_path: str):
        """Clean up temporary CSV file.
        
        Args:
            csv_path: Path to CSV file to delete
        """
        try:
            Path(csv_path).unlink()
            logger.debug(f"Cleaned up CSV file: {csv_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up CSV file: {e}")

