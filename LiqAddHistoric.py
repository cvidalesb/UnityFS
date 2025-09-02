import requests
import csv
import json
from datetime import datetime, timedelta
import os

def fetch_transfers_data(api_key):
    """
    Fetch transfers data from Bridge API
    """
    
    """# Calculate date one month ago
    one_month_ago = datetime.now() - timedelta(days=30)
    created_after = one_month_ago.strftime("%Y-%m-%dT%H:%M:%S.%fZ")"""

    """# Add created_after parameter to filter last 30 days
    params = {"created_after": created_after, "limit": 100}"""
    querystring = {"limit":"100"}
    url = "https://api.bridge.xyz/v0/liquidation_addresses/drains?updated_before_ms=1746048000000"
    headers = {"Api-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None

def flatten_json(data, parent_key='', sep='_'):
    """
    Flatten nested JSON structure for CSV export
    """
    items = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, (dict, list)):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            if isinstance(item, (dict, list)):
                items.extend(flatten_json(item, new_key, sep=sep).items())
            else:
                items.append((new_key, item))
    else:
        items.append((parent_key, data))
    
    return dict(items)

def save_to_csv(data, filename=None):
    """
    Save the API data to a CSV file
    """
    if not data:
        print("No data to save")
        return
    
    # Generate filename with timestamp if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bridge_transfers_{timestamp}.csv"
    
    # Handle different response structures
    if isinstance(data, dict):
        # If response is a single object
        if 'data' in data and isinstance(data['data'], list):
            records = data['data']
        elif 'transfers' in data and isinstance(data['transfers'], list):
            records = data['transfers']
        else:
            # Try to find any list in the response
            records = []
            for key, value in data.items():
                if isinstance(value, list):
                    records = value
                    break
            if not records:
                records = [data]  # Single record
    elif isinstance(data, list):
        records = data
    else:
        records = [data]
    
    if not records:
        print("No records found in the response")
        return
    
    # Get all possible field names from all records
    all_fields = set()
    for record in records:
        if isinstance(record, dict):
            flattened = flatten_json(record)
            all_fields.update(flattened.keys())
    
    # Sort fields for consistent ordering
    fieldnames = sorted(list(all_fields))
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records:
                if isinstance(record, dict):
                    flattened = flatten_json(record)
                    # Fill missing fields with empty strings
                    row = {field: flattened.get(field, '') for field in fieldnames}
                    writer.writerow(row)
        
        print(f"Data successfully saved to {filename}")
        print(f"Total records exported: {len(records)}")
        print(f"Total fields: {len(fieldnames)}")
        
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def main():
    """
    Main function to run the script
    """
    print("Bridge API to CSV Exporter")
    print("=" * 30)
    
    # Get API key from user input (more secure than hardcoding)
    api_key = input("Enter your Bridge API key: ").strip()
    
    if not api_key:
        print("API key is required!")
        return
    
    print("\nFetching data from Bridge API...")
    
    # Fetch data
    data = fetch_transfers_data(api_key)
    
    if data is None:
        print("Failed to fetch data. Please check your API key and try again.")
        return
    
    print("Data fetched successfully!")
    print(f"Response structure: {type(data)}")
    
    # Display sample of the data
    if isinstance(data, dict):
        print(f"Top-level keys: {list(data.keys())}")
    elif isinstance(data, list):
        print(f"Number of records: {len(data)}")
        if data and isinstance(data[0], dict):
            print(f"Sample record keys: {list(data[0].keys())}")
    
    # Ask user for filename
    filename = input("\nEnter CSV filename (or press Enter for auto-generated name): ").strip()
    if not filename:
        filename = None
    
    # Save to CSV
    save_to_csv(data, filename)
    
    print("\nScript completed!")

if __name__ == "__main__":
    main()
