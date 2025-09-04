import psycopg2
from typing import Dict, Any
from datetime import datetime

DATABASE_URL = "postgresql://postgres:ohLDfjuhoJrdoBjYTVSBtsypPMWfNaYI@gondala.proxy.rlwy.net:55128/railway"

def _flatten_json(data: Dict[str, Any], parent: str = "", sep: str = "_") -> Dict[str, Any]:
    """Flatten nested JSON into flat key-value pairs"""
    out: Dict[str, Any] = {}
    for k, v in data.items():
        new_key = f"{parent}{sep}{k}" if parent else k
        if isinstance(v, dict):
            out.update(_flatten_json(v, new_key, sep))
        elif isinstance(v, list):
            out[new_key] = v
        else:
            out[new_key] = v
    return out

def insert_user(conn: psycopg2.extensions.connection, user_json: Dict[str, Any]) -> bool:
    """Insert flattened user JSON into users table"""
    try:
        # Flatten the JSON
        flat_data = _flatten_json(user_json)
        
        # Map the flattened keys to table columns
        column_mapping = {
            'id': 'id',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'status': 'status',
            'capabilities_payin_crypto': 'payin_crypto',
            'capabilities_payout_crypto': 'payout_crypto',
            'capabilities_payin_fiat': 'payin_fiat',
            'capabilities_payout_fiat': 'payout_fiat',
            'created_at': 'created_at',
            'updated_at': 'updated_at'
        }
        
        # Build the INSERT statement
        columns = []
        values = []
        placeholders = []
        
        for json_key, table_column in column_mapping.items():
            if json_key in flat_data:
                columns.append(table_column)
                values.append(flat_data[json_key])
                placeholders.append('%s')
        
        if not columns:
            print("❌ No valid columns found in JSON")
            return False
        
        # Create INSERT SQL
        sql = f"""
        INSERT INTO users ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        """
        
        # Execute INSERT
        with conn.cursor() as cursor:
            cursor.execute(sql, values)
        
        conn.commit()
        print(f"✅ User inserted successfully! ID: {flat_data.get('id', 'unknown')}")
        return True
        
    except Exception as e:
        print(f"❌ Error inserting user: {e}")
        conn.rollback()
        return False

def upsert_user(conn: psycopg2.extensions.connection, user_json: Dict[str, Any]) -> bool:
    """Insert or update user (upsert) based on ID"""
    try:
        # Flatten the JSON
        flat_data = _flatten_json(user_json)
        
        # Check if user exists
        user_id = flat_data.get('id')
        if not user_id:
            print("❌ User ID is required for upsert")
            return False
        
        # Check if user exists
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            exists = cursor.fetchone()
        
        if exists:
            # Update existing user
            return update_user(conn, user_json)
        else:
            # Insert new user
            return insert_user(conn, user_json)
            
    except Exception as e:
        print(f"❌ Error in upsert: {e}")
        return False

def update_user(conn: psycopg2.extensions.connection, user_json: Dict[str, Any]) -> bool:
    """Update existing user"""
    try:
        # Flatten the JSON
        flat_data = _flatten_json(user_json)
        
        # Map the flattened keys to table columns
        column_mapping = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'status': 'status',
            'capabilities_payin_crypto': 'payin_crypto',
            'capabilities_payout_crypto': 'payout_crypto',
            'capabilities_payin_fiat': 'payin_fiat',
            'capabilities_payout_fiat': 'payout_fiat',
            'updated_at': 'updated_at'
        }
        
        # Build the UPDATE statement
        set_clauses = []
        values = []
        
        for json_key, table_column in column_mapping.items():
            if json_key in flat_data:
                set_clauses.append(f"{table_column} = %s")
                values.append(flat_data[json_key])
        
        if not set_clauses:
            print("❌ No valid columns to update")
            return False
        
        # Add user ID to values
        values.append(flat_data.get('id'))
        
        # Create UPDATE SQL
        sql = f"""
        UPDATE users 
        SET {', '.join(set_clauses)}
        WHERE id = %s
        """
        
        # Execute UPDATE
        with conn.cursor() as cursor:
            cursor.execute(sql, values)
        
        conn.commit()
        print(f"✅ User updated successfully! ID: {flat_data.get('id')}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        conn.rollback()
        return False

# Example usage
def main():
    # Example JSON data
    user_data = {
        "id": "user_123",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "status": "active",
        "capabilities": {
            "payin_crypto": "enabled",
            "payout_crypto": "enabled",
            "payin_fiat": "disabled",
            "payout_fiat": "disabled"
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        
        # Insert new user
        insert_user(conn, user_data)
        
        # Or upsert (insert or update)
        # upsert_user(conn, user_data)
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()