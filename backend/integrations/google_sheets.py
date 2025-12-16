"""
Google Sheets Integration
Import data from public Google Sheets without authentication
"""

import aiohttp
import pandas as pd
from io import StringIO
from typing import Optional, Dict, Any
import re


def extract_sheet_id(url: str) -> Optional[str]:
    """
    Extract Google Sheets ID from various URL formats
    
    Supports:
    - https://docs.google.com/spreadsheets/d/SHEET_ID/edit
    - https://docs.google.com/spreadsheets/d/SHEET_ID
    - Just the sheet ID directly
    """
    # Pattern for full URLs
    patterns = [
        r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'^([a-zA-Z0-9-_]{25,})$',  # Just the ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


async def fetch_google_sheet_csv(sheet_id: str, sheet_name: Optional[str] = None) -> str:
    """
    Fetch Google Sheet data as CSV
    Sheet must be published to web or shared as "Anyone with the link can view"
    
    Args:
        sheet_id: Google Sheets document ID
        sheet_name: Optional sheet/tab name (defaults to first sheet)
        
    Returns:
        CSV content as string
    """
    # Build the CSV export URL
    if sheet_name:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    else:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.text()
            else:
                raise Exception(f"Failed to fetch sheet: HTTP {response.status}")


async def import_google_sheet(url_or_id: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Import a Google Sheet as a pandas DataFrame
    
    Args:
        url_or_id: Google Sheets URL or sheet ID
        sheet_name: Optional sheet/tab name
        
    Returns:
        pandas DataFrame with the sheet data
    """
    # Extract ID from URL if needed
    sheet_id = extract_sheet_id(url_or_id)
    
    if not sheet_id:
        raise ValueError("Invalid Google Sheets URL or ID")
    
    # Fetch CSV data
    csv_content = await fetch_google_sheet_csv(sheet_id, sheet_name)
    
    # Parse CSV to DataFrame
    df = pd.read_csv(StringIO(csv_content))
    
    # Clean column names
    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
    
    return df


async def get_sheet_info(url_or_id: str) -> Dict[str, Any]:
    """
    Get basic information about a Google Sheet
    
    Returns:
        Dictionary with sheet info (columns, row count, sample data)
    """
    try:
        df = await import_google_sheet(url_or_id)
        
        return {
            "success": True,
            "columns": list(df.columns),
            "rowCount": len(df),
            "columnCount": len(df.columns),
            "sampleData": df.head(5).to_dict(orient='records'),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Example usage and testing
async def test_google_sheets():
    """Test with a sample public sheet"""
    # This is a sample public sheet for testing
    test_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
    
    info = await get_sheet_info(test_url)
    print(f"Sheet info: {info}")
