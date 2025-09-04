import psycopg2

# Database connection string
DATABASE_URL = "postgresql://postgres:ohLDfjuhoJrdoBjYTVSBtsypPMWfNaYI@gondola.proxy.rlwy.net:55128/railway"

# SQL to create the table
CREATE_TABLE_SQL = """
-- =====================================================================
-- Bridge Transfer — flattened superset schema for GET /v0/transfers/{id}
-- =====================================================================

CREATE TABLE bridge_transfers (
  -- Core identifiers & status
  id                             TEXT PRIMARY KEY,            -- transferID (docs show 1–42 char UUID-ish)
  client_reference_id            TEXT,
  state                          TEXT NOT NULL,               -- store as TEXT; optionally add a CHECK with known states
  on_behalf_of                   TEXT,                        -- customer id

  -- Amounts & fees (strings in API -> NUMERIC here; wide precision to be safe)
  amount                         NUMERIC(36,18),              -- transfer amount
  developer_fee                  NUMERIC(36,18),              -- fixed fee (not percent)
  currency                       TEXT,                        -- e.g. usd/eur/mxn (enum in docs; keep TEXT to avoid tight coupling)

  -- Source (origin of funds)
  source_payment_rail            TEXT,                        -- e.g. ethereum, ach, sepa, wire, polygon
  source_currency                TEXT,
  source_from_address            TEXT,
  source_external_account_id     TEXT,
  source_bridge_wallet_id        TEXT,
  -- Optional source-side bank metadata / confirmations (appear once funds land)
  source_bank_beneficiary_name   TEXT,
  source_bank_routing_number     TEXT,
  source_bank_account_number     TEXT,
  source_bank_name               TEXT,
  source_imad                    TEXT,                        -- wire message id (incoming)
  source_omad                    TEXT,                        -- legacy/deprecated, keep for safety
  source_payment_scheme          TEXT,                        -- e.g. reversed_payment (if used at creation)

  -- Destination (where funds go)
  destination_payment_rail       TEXT,
  destination_currency           TEXT,
  destination_to_address         TEXT,
  destination_external_account_id TEXT,
  destination_bridge_wallet_id   TEXT,
  -- Optional routing/reference fields (set at creation or added on processing)
  destination_wire_message       TEXT,
  destination_sepa_reference     TEXT,
  destination_swift_reference    TEXT,
  destination_spei_reference     TEXT,
  destination_swift_charges      TEXT,                        -- e.g. "our"/"shared"
  destination_ach_reference      TEXT,
  destination_blockchain_memo    TEXT,
  destination_deposit_id         TEXT,
  destination_imad               TEXT,                        -- wire confirmation (outgoing)

  -- Source deposit instructions (present when you must fund the transfer)
  sdi_payment_rail               TEXT,
  sdi_payment_rails              TEXT[],                      -- some examples show an array of allowed rails
  sdi_amount                     NUMERIC(36,18),
  sdi_currency                   TEXT,
  sdi_deposit_message            TEXT,                        -- memo / reference required by bank rails
  sdi_from_address               TEXT,
  sdi_to_address                 TEXT,
  -- Bank details for fiat rails (SEPA/ACH/Wire)
  sdi_bank_beneficiary_name      TEXT,
  sdi_bank_routing_number        TEXT,
  sdi_bank_account_number        TEXT,
  sdi_bank_name                  TEXT,
  sdi_iban                       TEXT,
  sdi_bic                        TEXT,
  sdi_account_holder_name        TEXT,
  sdi_bank_address               TEXT,

  -- Receipt breakdown (strings in API -> NUMERIC here)
  receipt_initial_amount         NUMERIC(36,18),
  receipt_developer_fee          NUMERIC(36,18),
  receipt_exchange_fee           NUMERIC(36,18),
  receipt_subtotal_amount        NUMERIC(36,18),
  receipt_gas_fee                NUMERIC(36,18),              -- normalize both `gas_fe` (typo) and `gas_fee` into this column
  receipt_final_amount           NUMERIC(36,18),
  receipt_source_tx_hash         TEXT,
  receipt_destination_tx_hash    TEXT,
  receipt_url                    TEXT,

  -- Feature flags
  features_flexible_amount       BOOLEAN,
  features_static_template       BOOLEAN,
  features_allow_any_from_address BOOLEAN,

  -- Timestamps
  created_at                     TIMESTAMPTZ NOT NULL,
  updated_at                     TIMESTAMPTZ NOT NULL
);
"""

def create_table():
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Execute the CREATE TABLE statement
        cursor.execute(CREATE_TABLE_SQL)
        
        # Commit the transaction
        conn.commit()
        
        print("✅ Table 'bridge_transfers' created successfully!")
        
        # Verify the table was created
        cursor.execute("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'bridge_transfers' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"\n�� Table structure ({len(columns)} columns):")
        for col in columns:
            print(f"  {col[1]}: {col[2]}")
            
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_table()