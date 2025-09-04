import psycopg2

DATABASE_URL = "postgresql://postgres:ohLDfjuhoJrdoBjYTVSBtsypPMWfNaYI@gondola.proxy.rlwy.net:55128/railway"

def create_users_table():
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        sql = """
        CREATE TABLE users (
            id TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            status TEXT,
            payin_crypto TEXT,
            payout_crypto TEXT,
            payin_fiat TEXT,
            payout_fiat TEXT,
            created_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ
        );
        """

        cursor.execute(sql)
        conn.commit()
        print("✅ Table 'users' created successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

create_users_table()